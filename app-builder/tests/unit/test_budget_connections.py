"""Ngân sách, bảng giá, sổ chi phí và lưu kết nối (key chỉ nằm trong secret store)."""
import pytest

from app_builder.agent.budget import BudgetManager, Price, PriceBook, cost_of, estimate_tokens, max_cost
from app_builder.core.secret_store import SecretStore
from app_builder.providers.base import InvalidBaseURL, ModelInfo, Usage
from app_builder.services.ai_connections import ConnectionManager, key_ref


def test_builtin_claude_prices_and_cached_cost():
    pb = PriceBook.__new__(PriceBook)
    pb.db = None
    price = Price(4, 20, 0.20)
    # 1M đầu vào, trong đó 0,5M đọc cache; 0,1M đầu ra
    assert cost_of(price, Usage(1_000_000, 100_000, 500_000)) == pytest.approx(0.5 * 4 + 0.5 * 0.2 + 0.1 * 20)
    # Không có giá cache → tính như đầu vào thường
    assert cost_of(Price(2, 10), Usage(1_000_000, 0, 1_000_000)) == pytest.approx(2)
    assert max_cost(price, 1000, 16_000) == pytest.approx((1000 * 4 + 16_000 * 20) / 1e6)
    assert estimate_tokens("x" * 300) >= 100


def test_price_lookup_builtin_user_and_prefix(db):
    pb = PriceBook(db)
    assert pb.lookup("anthropic", "claude-opus-5-5").input_per_m == 4
    assert pb.lookup("openai", "gpt-x") is None
    pb.set_user_price("openai", "gpt-x", Price(1.5, 6, 0.15))
    p = pb.lookup("openai", "gpt-x")
    assert (p.input_per_m, p.output_per_m, p.cached_input_per_m, p.source) == (1.5, 6, 0.15, "Người dùng nhập")
    # model có hậu tố ngày dùng giá của tiền tố
    assert pb.lookup("openai", "gpt-x-2026-05-01").input_per_m == 1.5
    pb.set_user_price("openai", "gpt-x", None)
    assert pb.lookup("openai", "gpt-x") is None


def test_budget_unknown_price_needs_confirmation(db):
    bm = BudgetManager(db)
    d = bm.check("openai", "gpt-unknown", "hello", 1000)
    assert d.allowed and d.needs_confirmation and d.reason == "unknown_price" and d.estimate_usd is None


def test_budget_warn_block_and_reservations(db):
    bm = BudgetManager(db, session_started="2000-01-01T00:00:00+00:00")
    bm.set_session_limit(1.0)
    # Opus 5.5: 16 000 token ra ≈ $0,32
    d = bm.check("anthropic", "claude-opus-5-5", "hi", 16_000)
    assert d.allowed and not d.warn
    bm.reserve("r1", 0.6, None)
    d = bm.check("anthropic", "claude-opus-5-5", "hi", 16_000)
    assert d.allowed and d.warn == ["session"]            # 0,6 + 0,32 ≥ 80%
    bm.reserve("r2", 0.2, None)
    d = bm.check("anthropic", "claude-opus-5-5", "hi", 16_000)
    assert not d.allowed and d.reason == "over_session"   # 0,8 + 0,32 > 1
    bm.release("r1")
    bm.release("r2")
    cost = bm.record("r3", "anthropic", "claude-opus-5-5", Usage(1000, 2000), "ok", project_id=7)
    assert cost == pytest.approx((1000 * 4 + 2000 * 20) / 1e6)
    assert bm.spent_session() == pytest.approx(cost) and bm.spent_project(7) == pytest.approx(cost)
    # Ngân sách dự án
    d = bm.check("anthropic", "claude-opus-5-5", "hi", 16_000, project_id=7, project_limit=0.3)
    assert not d.allowed and d.reason == "over_project"
    row = bm.recent()[0]
    assert row["cost_known"] == 1 and row["status"] == "ok" and row["input_tokens"] == 1000


def test_record_unknown_and_approximate(db):
    bm = BudgetManager(db)
    assert bm.record("a", "openai", "gpt-unknown", Usage(10, 10), "ok") is None
    bm.record("b", "anthropic", "claude-opus-5-5", Usage(10, 10), "ok", approximate=True)
    rows = {r["request_id"]: r for r in bm.recent()}
    assert rows["a"]["cost_usd"] is None and rows["a"]["cost_known"] == 0
    assert rows["b"]["cost_usd"] > 0 and rows["b"]["cost_known"] == 0


def test_connections_key_only_in_secret_store(db):
    secrets = SecretStore(use_keyring=False)
    cm = ConnectionManager(db, secrets)
    assert "fake" not in cm.provider_ids()
    assert not cm.is_connected("openai")
    cm.save("openai", "sk-test-secret-value-123456", "https://gateway.example.com/v1/")
    assert cm.is_connected("openai") and secrets.get(key_ref("openai")) == "sk-test-secret-value-123456"
    assert cm.base_url("openai") == "https://gateway.example.com/v1"
    # Key không được nằm trong SQLite (settings, audit, ...)
    dump = "\n".join(str(tuple(r)) for t in ("settings", "audit_events", "model_cache")
                     for r in db.query(f"SELECT * FROM {t}"))
    assert "secret-value" not in dump
    # Lưu lại không đổi key, quay về URL mặc định
    cm.save("openai", None, "https://api.openai.com/v1")
    assert cm.base_url("openai") == "https://api.openai.com/v1"
    assert secrets.get(key_ref("openai")) == "sk-test-secret-value-123456"
    with pytest.raises(InvalidBaseURL):
        cm.save("openai", None, "http://insecure.example.com")
    cm.cache_models("openai", [ModelInfo("gpt-x", "GPT X", 1000), ModelInfo("gpt-y")])
    models, fetched = cm.cached_models("openai")
    assert [m.id for m in models] == ["gpt-x", "gpt-y"] and models[0].context_tokens == 1000 and fetched
    cm.disconnect("openai")
    assert not cm.is_connected("openai") and cm.cached_models("openai")[0] == []


def test_fake_provider_only_when_enabled(db, monkeypatch):
    monkeypatch.setenv("APPBUILDER_FAKE_PROVIDER", "1")
    cm = ConnectionManager(db, SecretStore(use_keyring=False))
    assert "fake" in cm.provider_ids() and cm.is_connected("fake")
    assert [m.id for m in cm.cached_models("fake")[0]] == ["fake-echo", "fake-error"]
