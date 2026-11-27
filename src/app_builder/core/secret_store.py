"""Lưu secret qua keyring (Windows Credential Manager). Không bao giờ ghi secret ra JSON/SQLite.

Nếu keyring không khả dụng, chỉ giữ secret trong bộ nhớ của phiên hiện tại.
"""
from __future__ import annotations

import logging

from app_builder import APP_ID

log = logging.getLogger(__name__)
SERVICE = APP_ID


class SecretStore:
    def __init__(self, service: str = SERVICE, use_keyring: bool = True) -> None:
        self.service = service
        self._memory: dict[str, str] = {}
        self._keyring = None
        if use_keyring:
            try:
                import keyring
                from keyring.backends import fail

                backend = keyring.get_keyring()
                if not isinstance(backend, fail.Keyring):
                    self._keyring = keyring
            except Exception as exc:  # pragma: no cover
                log.warning("Keyring không khả dụng: %s", type(exc).__name__)

    @property
    def persistent(self) -> bool:
        return self._keyring is not None

    @property
    def backend_name(self) -> str:
        if self._keyring is None:
            return "memory-only"
        return type(self._keyring.get_keyring()).__name__

    def set(self, ref: str, value: str) -> None:
        if self._keyring is not None:
            self._keyring.set_password(self.service, ref, value)
        else:
            self._memory[ref] = value

    def get(self, ref: str) -> str | None:
        if self._keyring is not None:
            try:
                return self._keyring.get_password(self.service, ref)
            except Exception:
                return None
        return self._memory.get(ref)

    def delete(self, ref: str) -> None:
        self._memory.pop(ref, None)
        if self._keyring is not None:
            try:
                self._keyring.delete_password(self.service, ref)
            except Exception:
                pass

    @staticmethod
    def mask(value: str | None) -> str:
        if not value:
            return ""
        if len(value) <= 8:
            return "•" * len(value)
        return value[:4] + "•" * 8 + value[-4:]
