"""Ngân sách & sổ chi phí AI.

- Bảng giá có nguồn + ngày cập nhật. Giá có sẵn chỉ cho Claude (lấy từ tài liệu Claude API, cập nhật
  2026-11-03). Giá OpenAI / Gemini / DeepSeek thay đổi thường xuyên nên KHÔNG ghi cứng từ trí nhớ:
  người dùng nhập trong hộp thoại "Chi phí AI"; model chưa có giá → phải xác nhận trước khi gửi.
- Trước mỗi request: ước lượng chi phí tối đa (đầu vào ước lượng + max_output_tokens) và giữ chỗ
  (reservation) để nhiều request song song không vượt ngân sách.
- Sau request: ghi `usage_records` (không lưu nội dung chat), giải phóng chỗ giữ.
- Cảnh báo khi đã dùng ≥ 80% ngân sách phiên hoặc dự án; chặn khi vượt.
"""
from __future__ import annotations

import json
import math
import threading
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from app_builder.core.database import Database
from app_builder.core.schemas import utcnow_iso
from app_builder.providers.base import Usage

WARN_RATIO = 0.8
PRICE_SETTINGS_KEY = "ai.prices"
SESSION_BUDGET_KEY = "ai.session_budget_usd"


@dataclass(frozen=True)
class Price:
    """USD cho 1 triệu token."""
    input_per_m: float
    output_per_m: float
    cached_input_per_m: float | None = None
    source: str = ""
    updated: str = ""


_CLAUDE_SRC = "Claude API docs (bảng giá)"
_CLAUDE_DATE = "2026-11-03"


def _claude(inp: float, out: float, cached: float | None = None) -> Price:
    return Price(inp, out, cached, _CLAUDE_SRC, _CLAUDE_DATE)


BUILTIN_PRICES: dict[tuple[str, str], Price] = {
    ("anthropic", "claude-fable-5-2"): _claude(8, 40, 0.20),
    ("anthropic", "claude-fable-5-1"): _claude(10, 50),
    ("anthropic", "claude-fable-5"): _claude(10, 50),
    ("anthropic", "claude-opus-5-5"): _claude(4, 20, 0.20),
    ("anthropic", "claude-opus-5"): _claude(5, 25),
    ("anthropic", "claude-opus-4-8"): _claude(5, 25),
    ("anthropic", "claude-opus-4-7"): _claude(5, 25),
    ("anthropic", "claude-opus-4-6"): _claude(5, 25),
    ("anthropic", "claude-sonnet-5-5"): _claude(2, 10, 0.10),
    ("anthropic", "claude-sonnet-5"): _claude(2, 10),
    ("anthropic", "claude-sonnet-4-6"): _claude(3, 15),
    # Haiku 5.5: giá cho prompt ≤ 100K token ($0,50 / $2,50 khi vượt) — app dùng mức thấp, ghi chú trong UI
    ("anthropic", "claude-haiku-5-5"): _claude(0.10, 0.50),
    ("anthropic", "claude-haiku-4-5"): _claude(1, 5),
    ("fake", "fake-echo"): Price(0, 0, 0, "TEST", "—"),
    ("fake", "fake-error"): Price(0, 0, 0, "TEST", "—"),
}


class PriceBook:
    def __init__(self, db: Database) -> None:
        self.db = db

    def user_prices(self) -> dict[tuple[str, str], Price]:
        row = self.db.query_one("SELECT value FROM settings WHERE key=?", (PRICE_SETTINGS_KEY,))
        if not row:
            return {}
        try:
            data = json.loads(row["value"])
            return {(d["provider"], d["model"]): Price(float(d["input_per_m"]), float(d["output_per_m"]),
                                                       None if d.get("cached_input_per_m") in (None, "") else float(d["cached_input_per_m"]),
                                                       "Người dùng nhập", d.get("updated", ""))
                    for d in data}
        except (ValueError, KeyError, TypeError):
            return {}

    def set_user_price(self, provider: str, model: str, price: Price | None) -> None:
        prices = self.user_prices()
        if price is None:
            prices.pop((provider, model), None)
        else:
            prices[(provider, model)] = Price(price.input_per_m, price.output_per_m, price.cached_input_per_m,
                                              "Người dùng nhập", datetime.now(timezone.utc).date().isoformat())
        data = [{"provider": p, "model": m, **{k: v for k, v in asdict(pr).items() if k != "source"}}
                for (p, m), pr in sorted(prices.items())]
        self.db.execute("INSERT INTO settings(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                        (PRICE_SETTINGS_KEY, json.dumps(data, ensure_ascii=False)))

    def lookup(self, provider: str, model: str) -> Price | None:
        user = self.user_prices()
        for table in (user, BUILTIN_PRICES):
            if (provider, model) in table:
                return table[(provider, model)]
        # Model có hậu tố ngày/phiên bản (ví dụ "x-2026-05-01"): dùng giá của tiền tố dài nhất
        best: tuple[int, Price] | None = None
        for table in (user, BUILTIN_PRICES):
            for (p, m), price in table.items():
                if p == provider and model.startswith(m + "-") and (best is None or len(m) > best[0]):
                    best = (len(m), price)
            if best:
                return best[1]
        return None


def estimate_tokens(text: str) -> int:
    """Ước lượng thô, thiên về cao (~3 ký tự/token) để không vượt ngân sách."""
    return math.ceil(len(text) / 3) + 4


def cost_of(price: Price, usage: Usage) -> float:
    cached = min(usage.cached_tokens, usage.input_tokens)
    cached_price = price.cached_input_per_m if price.cached_input_per_m is not None else price.input_per_m
    return ((usage.input_tokens - cached) * price.input_per_m + cached * cached_price
            + usage.output_tokens * price.output_per_m) / 1_000_000


def max_cost(price: Price, input_tokens: int, max_output_tokens: int) -> float:
    return cost_of(price, Usage(input_tokens=input_tokens, output_tokens=max_output_tokens))


@dataclass
class BudgetDecision:
    allowed: bool
    needs_confirmation: bool  # giá chưa biết
    estimate_usd: float | None
    reason: str = ""  # "over_session" | "over_project" | "unknown_price" | ""
    warn: list[str] = None  # "session" / "project" khi ≥ 80%

    def __post_init__(self) -> None:
        if self.warn is None:
            self.warn = []


class BudgetManager:
    def __init__(self, db: Database, session_started: str | None = None) -> None:
        self.db = db
        self.prices = PriceBook(db)
        self.session_started = session_started or utcnow_iso()
        self._reserved: dict[str, tuple[int | None, float]] = {}
        self._lock = threading.Lock()

    # ---- giới hạn ------------------------------------------------------------------
    def session_limit(self) -> float | None:
        row = self.db.query_one("SELECT value FROM settings WHERE key=?", (SESSION_BUDGET_KEY,))
        try:
            v = float(row["value"]) if row else None
        except ValueError:
            v = None
        return v if v and v > 0 else None

    def set_session_limit(self, usd: float | None) -> None:
        if not usd:
            self.db.execute("DELETE FROM settings WHERE key=?", (SESSION_BUDGET_KEY,))
        else:
            self.db.execute("INSERT INTO settings(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                            (SESSION_BUDGET_KEY, str(float(usd))))

    # ---- đã chi --------------------------------------------------------------------
    def spent_session(self) -> float:
        row = self.db.query_one("SELECT COALESCE(SUM(cost_usd), 0) AS s FROM usage_records WHERE created_at >= ?",
                                (self.session_started,))
        return float(row["s"]) if row else 0.0

    def spent_project(self, project_id: int | None) -> float:
        if project_id is None:
            return 0.0
        row = self.db.query_one("SELECT COALESCE(SUM(cost_usd), 0) AS s FROM usage_records WHERE project_id = ?",
                                (project_id,))
        return float(row["s"]) if row else 0.0

    def spent_total(self) -> float:
        row = self.db.query_one("SELECT COALESCE(SUM(cost_usd), 0) AS s FROM usage_records")
        return float(row["s"]) if row else 0.0

    def _reserved_for(self, project_id: int | None = None, session: bool = False) -> float:
        with self._lock:
            return sum(v for pid, v in self._reserved.values() if session or pid == project_id)

    # ---- kiểm tra & giữ chỗ ----------------------------------------------------------
    def check(self, provider: str, model: str, prompt_text: str, max_output_tokens: int,
              project_id: int | None = None, project_limit: float | None = None) -> BudgetDecision:
        price = self.prices.lookup(provider, model)
        if price is None:
            return BudgetDecision(True, True, None, "unknown_price")
        est = max_cost(price, estimate_tokens(prompt_text), max_output_tokens)
        decision = BudgetDecision(True, False, est)
        for scope, limit, spent in (
            ("session", self.session_limit(), self.spent_session() + self._reserved_for(session=True)),
            ("project", project_limit if project_limit and project_limit > 0 else None,
             self.spent_project(project_id) + self._reserved_for(project_id)),
        ):
            if limit is None:
                continue
            if spent + est > limit:
                return BudgetDecision(False, False, est, f"over_{scope}", decision.warn)
            if spent + est >= WARN_RATIO * limit:
                decision.warn.append(scope)
        return decision

    def reserve(self, request_id: str, usd: float | None, project_id: int | None) -> None:
        with self._lock:
            self._reserved[request_id] = (project_id, usd or 0.0)

    def release(self, request_id: str) -> None:
        with self._lock:
            self._reserved.pop(request_id, None)

    # ---- ghi sổ --------------------------------------------------------------------
    def record(self, request_id: str, provider: str, model: str, usage: Usage, status: str,
               project_id: int | None = None, approximate: bool = False) -> float | None:
        """Ghi một dòng usage_records. Trả về chi phí (None nếu chưa biết giá)."""
        self.release(request_id)
        price = self.prices.lookup(provider, model)
        cost = cost_of(price, usage) if price else None
        self.db.execute(
            "INSERT INTO usage_records(project_id, provider, model, request_id, input_tokens, output_tokens, "
            "cached_tokens, reasoning_tokens, cost_usd, cost_known, status, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (project_id, provider, model, request_id, usage.input_tokens, usage.output_tokens, usage.cached_tokens,
             usage.reasoning_tokens, cost, 1 if (cost is not None and not approximate) else 0, status, utcnow_iso()),
        )
        return cost

    def recent(self, limit: int = 200) -> list[dict]:
        rows = self.db.query("SELECT * FROM usage_records ORDER BY id DESC LIMIT ?", (limit,))
        return [dict(r) for r in rows]
