"""Chuyển lỗi của các SDK (openai, anthropic, google-genai, httpx/httpx2) về ProviderError."""
from __future__ import annotations

from app_builder.core.redaction import redact
from app_builder.providers.base import ErrorKind, ProviderError, kind_from_status


def to_provider_error(exc: BaseException) -> ProviderError:
    if isinstance(exc, ProviderError):
        return exc
    name = type(exc).__name__
    detail = redact(str(exc))[:500]
    # openai / anthropic: APIStatusError có status_code; google-genai: APIError có code
    status = getattr(exc, "status_code", None)
    if not isinstance(status, int):
        status = getattr(exc, "code", None) if isinstance(getattr(exc, "code", None), int) else None
    if isinstance(status, int):
        kind = kind_from_status(status)
        # Anthropic trả 529 khi quá tải
        if status == 529:
            kind = ErrorKind.server
        return ProviderError(kind, detail, status)
    if "Timeout" in name:
        return ProviderError(ErrorKind.timeout, detail)
    if "Connect" in name or "Network" in name or isinstance(exc, (ConnectionError, OSError)):
        return ProviderError(ErrorKind.network, detail)
    return ProviderError(ErrorKind.unknown, f"{name}: {detail}")
