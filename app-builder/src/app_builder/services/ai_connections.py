"""Quản lý kết nối provider: API key trong keyring (SecretStore), base URL trong bảng settings,
danh sách model cache trong bảng model_cache. Không ghi key ra log/JSON/SQLite."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass

from app_builder.core.database import Database
from app_builder.core.schemas import utcnow_iso
from app_builder.core.secret_store import SecretStore
from app_builder.providers.base import PROVIDERS, AIProvider, ModelInfo, validate_base_url
from app_builder.providers.factory import create_provider


def key_ref(provider_id: str) -> str:
    return f"ai.{provider_id}.api_key"


def _base_url_key(provider_id: str) -> str:
    return f"ai.{provider_id}.base_url"


def fake_enabled() -> bool:
    """Provider TEST chỉ hiện khi bật APPBUILDER_FAKE_PROVIDER=1 (test/demo)."""
    return os.environ.get("APPBUILDER_FAKE_PROVIDER") == "1"


@dataclass
class ConnectionInfo:
    provider_id: str
    has_key: bool
    base_url: str
    models: list[ModelInfo]
    models_fetched_at: str | None


class ConnectionManager:
    def __init__(self, db: Database, secrets: SecretStore) -> None:
        self.db = db
        self.secrets = secrets

    def provider_ids(self) -> list[str]:
        return [p.id for p in PROVIDERS.values() if not p.test_only or fake_enabled()]

    # ---- cấu hình --------------------------------------------------------------------
    def base_url(self, provider_id: str) -> str:
        row = self.db.query_one("SELECT value FROM settings WHERE key=?", (_base_url_key(provider_id),))
        return row["value"] if row else PROVIDERS[provider_id].default_base_url

    def save(self, provider_id: str, api_key: str | None, base_url: str | None) -> None:
        """api_key=None giữ nguyên key cũ. base_url được kiểm tra (chỉ HTTPS, host công khai)."""
        if base_url:
            url = validate_base_url(base_url)
            if url.rstrip("/") == PROVIDERS[provider_id].default_base_url.rstrip("/"):
                self.db.execute("DELETE FROM settings WHERE key=?", (_base_url_key(provider_id),))
            else:
                self.db.execute("INSERT INTO settings(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                                (_base_url_key(provider_id), url))
        if api_key:
            self.secrets.set(key_ref(provider_id), api_key.strip())
        self.db.audit("ai.connection_saved", provider=provider_id, key_changed=bool(api_key))

    def disconnect(self, provider_id: str) -> None:
        self.secrets.delete(key_ref(provider_id))
        self.db.execute("DELETE FROM settings WHERE key=?", (_base_url_key(provider_id),))
        self.db.execute("DELETE FROM model_cache WHERE provider=?", (provider_id,))
        self.db.audit("ai.disconnected", provider=provider_id)

    def api_key(self, provider_id: str) -> str | None:
        if provider_id == "fake":
            return "fake"
        return self.secrets.get(key_ref(provider_id))

    def is_connected(self, provider_id: str) -> bool:
        return bool(self.api_key(provider_id))

    def connected(self) -> list[str]:
        return [p for p in self.provider_ids() if self.is_connected(p)]

    def info(self, provider_id: str) -> ConnectionInfo:
        models, fetched = self.cached_models(provider_id)
        return ConnectionInfo(provider_id, self.is_connected(provider_id), self.base_url(provider_id), models, fetched)

    # ---- provider & model --------------------------------------------------------------
    def provider(self, provider_id: str, api_key: str | None = None, base_url: str | None = None) -> AIProvider:
        key = api_key or self.api_key(provider_id)
        if not key:
            raise PermissionError("Chưa có API key")
        url = validate_base_url(base_url) if base_url else self.base_url(provider_id)
        return create_provider(provider_id, key, url)

    def cache_models(self, provider_id: str, models: list[ModelInfo]) -> None:
        now = utcnow_iso()
        with self.db.transaction() as cur:
            cur.execute("DELETE FROM model_cache WHERE provider=?", (provider_id,))
            for m in models:
                cur.execute("INSERT INTO model_cache(provider, model_id, metadata, fetched_at) VALUES (?,?,?,?)",
                            (provider_id, m.id, json.dumps({"display_name": m.display_name,
                                                           "context_tokens": m.context_tokens}, ensure_ascii=False), now))

    def cached_models(self, provider_id: str) -> tuple[list[ModelInfo], str | None]:
        if provider_id == "fake":
            from app_builder.providers.fake_provider import FAKE_MODELS
            return list(FAKE_MODELS), None
        rows = self.db.query("SELECT model_id, metadata, fetched_at FROM model_cache WHERE provider=? ORDER BY model_id",
                             (provider_id,))
        models = []
        for r in rows:
            try:
                meta = json.loads(r["metadata"])
            except json.JSONDecodeError:
                meta = {}
            models.append(ModelInfo(r["model_id"], meta.get("display_name") or "", meta.get("context_tokens")))
        return models, (rows[0]["fetched_at"] if rows else None)
