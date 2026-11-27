"""Registry provider: thông tin chính thức, cấu hình (không secret) trong SQLite, API key trong keyring,
cache danh sách model, tạo adapter.

- Mỗi provider có credential riêng; KHÔNG gửi key của provider này cho provider khác.
- Base URL phải là HTTPS. URL tùy chỉnh (không phải host chính thức) bị cảnh báo và dùng credential riêng
  (key ref gắn với host), để key chính thức không bao giờ bị gửi tới endpoint lạ.
- Không đọc cookie/session của ChatGPT/Claude Desktop.
"""
from __future__ import annotations

import ipaddress
import json
import os
from dataclasses import dataclass, field
from typing import Callable
from urllib.parse import urlparse

from app_builder.core.database import Database
from app_builder.core.schemas import utcnow_iso
from app_builder.core.secret_store import SecretStore
from app_builder.providers.base import AIProvider, ModelInfo


@dataclass(frozen=True)
class ProviderSpec:
    id: str
    name: str
    default_base_url: str | None
    official_hosts: tuple[str, ...]
    allows_custom_base_url: bool
    key_url: str
    key_hint: str
    note: str
    default_model: str | None = None
    test_only: bool = False


SPECS: dict[str, ProviderSpec] = {
    "openai": ProviderSpec(
        "openai", "OpenAI (ChatGPT API)", "https://api.openai.com/v1", ("api.openai.com",), True,
        "https://platform.openai.com/api-keys", "sk-…",
        "Dùng Responses API. API key và billing tách biệt với gói ChatGPT Plus/Pro."),
    "deepseek": ProviderSpec(
        "deepseek", "DeepSeek", "https://api.deepseek.com", ("api.deepseek.com",), True,
        "https://platform.deepseek.com/api_keys", "sk-…",
        "API tương thích OpenAI (chat/completions). Giá giờ cao điểm cao gấp đôi giờ thấp điểm."),
    "gemini": ProviderSpec(
        "gemini", "Google Gemini", None, ("generativelanguage.googleapis.com",), False,
        "https://aistudio.google.com/app/apikey", "AIza…",
        "Google Gen AI SDK, API key từ Google AI Studio."),
    "anthropic": ProviderSpec(
        "anthropic", "Claude API (Anthropic)", "https://api.anthropic.com", ("api.anthropic.com",), False,
        "https://platform.claude.com/settings/keys", "sk-ant-…",
        "Messages API. Key từ Anthropic Console, billing riêng — gói Claude Pro/Max không kèm API credits.",
        default_model="claude-opus-5-5"),
    "fake": ProviderSpec(
        "fake", "TEST — provider giả lập", None, (), False, "", "", "Chỉ dùng để kiểm thử offline. Không phải AI thật.",
        default_model="fake-echo", test_only=True),
}


def fake_enabled() -> bool:
    return os.environ.get("APPBUILDER_ENABLE_FAKE_PROVIDER") == "1"


def visible_specs() -> list[ProviderSpec]:
    return [s for s in SPECS.values() if not s.test_only or fake_enabled()]


class BaseUrlError(ValueError):
    pass


def validate_base_url(spec: ProviderSpec, url: str | None) -> tuple[str | None, bool, str]:
    """Trả (url chuẩn hóa, is_custom, cảnh báo). Raise BaseUrlError nếu không hợp lệ."""
    if not url or not url.strip():
        return spec.default_base_url, False, ""
    url = url.strip().rstrip("/")
    p = urlparse(url)
    if p.scheme != "https":
        raise BaseUrlError("Base URL phải dùng HTTPS.")
    host = (p.hostname or "").lower()
    if not host or "." not in host or p.username or p.password:
        raise BaseUrlError("Host không hợp lệ (không chấp nhận user:pass trong URL).")
    try:
        ip = ipaddress.ip_address(host)
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            raise BaseUrlError("Không gửi API key tới địa chỉ IP nội bộ.")
    except ValueError:
        pass
    if host in spec.official_hosts:
        return url, False, ""
    if not spec.allows_custom_base_url:
        raise BaseUrlError(f"{spec.name} chỉ dùng endpoint chính thức.")
    return url, True, (f"Endpoint tùy chỉnh ({host}) — không phải host chính thức của {spec.name}. "
                       "Dùng API key RIÊNG cho endpoint này; key chính thức sẽ không được gửi tới đây.")


def key_ref(provider_id: str, base_url: str | None = None) -> str:
    spec = SPECS[provider_id]
    if base_url:
        host = (urlparse(base_url).hostname or "").lower()
        if host and host not in spec.official_hosts:
            return f"provider:{provider_id}@{host}"
    return f"provider:{provider_id}"


@dataclass
class ProviderConfig:
    provider_id: str
    base_url: str | None = None
    selected_model: str = ""
    status: str = "not_configured"   # not_configured | authenticated | auth_failed | network | error
    status_message: str = ""
    checked_at: str = ""
    options: dict = field(default_factory=dict)  # vd: {"refusal_fallback": true}


def _factory(provider_id: str) -> Callable[..., AIProvider]:
    if provider_id == "openai":
        from app_builder.providers.openai_provider import OpenAIProvider
        return OpenAIProvider
    if provider_id == "deepseek":
        from app_builder.providers.deepseek_provider import DeepSeekProvider
        return DeepSeekProvider
    if provider_id == "gemini":
        from app_builder.providers.gemini_provider import GeminiProvider
        return GeminiProvider
    if provider_id == "anthropic":
        from app_builder.providers.anthropic_provider import AnthropicProvider
        return AnthropicProvider
    if provider_id == "fake":
        from app_builder.providers.fake_provider import FakeProvider
        return FakeProvider
    raise KeyError(provider_id)


class ProviderRegistry:
    def __init__(self, db: Database, secrets: SecretStore) -> None:
        self.db = db
        self.secrets = secrets

    # ---- config ------------------------------------------------------------
    def _key(self, pid: str) -> str:
        return f"provider_config:{pid}"

    def get_config(self, pid: str) -> ProviderConfig:
        r = self.db.query_one("SELECT value FROM settings WHERE key=?", (self._key(pid),))
        if r:
            try:
                d = json.loads(r["value"])
                return ProviderConfig(**{k: v for k, v in d.items() if k in ProviderConfig.__dataclass_fields__})
            except (json.JSONDecodeError, TypeError):
                pass
        return ProviderConfig(pid, base_url=SPECS[pid].default_base_url)

    def save_config(self, cfg: ProviderConfig) -> None:
        data = json.dumps(cfg.__dict__, ensure_ascii=False)  # không chứa key (key nằm trong keyring)
        self.db.execute("INSERT INTO settings(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                        (self._key(cfg.provider_id), data))

    # ---- keys ----------------------------------------------------------------
    def set_api_key(self, pid: str, api_key: str, base_url: str | None = None) -> None:
        spec = SPECS[pid]
        url, _custom, _warn = validate_base_url(spec, base_url)
        api_key = api_key.strip()
        if not api_key or any(c.isspace() for c in api_key):
            raise ValueError("API key trống hoặc chứa khoảng trắng.")
        self.secrets.set(key_ref(pid, url), api_key)
        cfg = self.get_config(pid)
        cfg.base_url = url
        cfg.status, cfg.status_message = "not_configured", "Đã lưu key — chưa kiểm tra kết nối"
        self.save_config(cfg)
        self.db.audit("provider.key_saved", None, provider=pid, custom_endpoint=_custom,
                      storage=self.secrets.backend_name)

    def has_api_key(self, pid: str) -> bool:
        if SPECS[pid].test_only:
            return True
        cfg = self.get_config(pid)
        return bool(self.secrets.get(key_ref(pid, cfg.base_url)))

    def masked_key(self, pid: str) -> str:
        cfg = self.get_config(pid)
        return SecretStore.mask(self.secrets.get(key_ref(pid, cfg.base_url)))

    def disconnect(self, pid: str) -> None:
        cfg = self.get_config(pid)
        self.secrets.delete(key_ref(pid, cfg.base_url))
        self.db.execute("DELETE FROM settings WHERE key=?", (self._key(pid),))
        self.db.execute("DELETE FROM model_cache WHERE provider=?", (pid,))
        self.db.audit("provider.disconnected", None, provider=pid)

    def connected_providers(self) -> list[str]:
        return [s.id for s in visible_specs() if self.has_api_key(s.id) and
                (s.test_only or self.get_config(s.id).status == "authenticated")]

    # ---- adapter ----------------------------------------------------------------
    def create(self, pid: str) -> AIProvider:
        spec = SPECS[pid]
        cfg = self.get_config(pid)
        if spec.test_only:
            return _factory(pid)()
        api_key = self.secrets.get(key_ref(pid, cfg.base_url))
        if not api_key:
            raise RuntimeError(f"Chưa có API key cho {spec.name}.")
        kwargs = {}
        if pid == "anthropic":
            kwargs["refusal_fallback"] = bool(cfg.options.get("refusal_fallback", True))
        base = cfg.base_url if spec.allows_custom_base_url else None
        return _factory(pid)(api_key=api_key, base_url=base, **kwargs)

    def record_status(self, pid: str, status: str, message: str = "") -> None:
        cfg = self.get_config(pid)
        cfg.status, cfg.status_message, cfg.checked_at = status, message, utcnow_iso()
        self.save_config(cfg)

    # ---- model cache ----------------------------------------------------------
    def save_models(self, pid: str, models: list[ModelInfo]) -> None:
        now = utcnow_iso()
        with self.db.transaction() as cur:
            cur.execute("DELETE FROM model_cache WHERE provider=?", (pid,))
            for m in models:
                cur.execute("INSERT INTO model_cache(provider, model_id, metadata, fetched_at) VALUES (?,?,?,?)",
                            (pid, m.id, json.dumps(m.to_dict(), ensure_ascii=False), now))
        cfg = self.get_config(pid)
        if cfg.selected_model and cfg.selected_model not in {m.id for m in models}:
            cfg.status_message = f"Model đã chọn '{cfg.selected_model}' không còn trong danh sách — hãy chọn lại."
            cfg.selected_model = ""
            self.save_config(cfg)

    def cached_models(self, pid: str) -> tuple[list[ModelInfo], str | None]:
        rows = self.db.query("SELECT metadata, fetched_at FROM model_cache WHERE provider=? ORDER BY model_id", (pid,))
        models = [ModelInfo.from_dict(json.loads(r["metadata"])) for r in rows]
        return models, (rows[0]["fetched_at"] if rows else None)

    def select_model(self, pid: str, model_id: str) -> None:
        cfg = self.get_config(pid)
        cfg.selected_model = model_id
        self.save_config(cfg)


def filter_models(models: list[ModelInfo], required: set[str], include_unknown: bool = True) -> list[ModelInfo]:
    """Lọc theo khả năng. Khả năng None (provider không công bố) được giữ nếu include_unknown."""
    out = []
    for m in models:
        ok = True
        for cap in required:
            v = m.capabilities.get(cap)
            if v is False or (v is None and not include_unknown):
                ok = False
                break
        if ok:
            out.append(m)
    return out
