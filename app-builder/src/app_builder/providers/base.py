"""Giao diện chung cho mọi provider AI.

Mỗi adapter nhận `AIRequest`, phát ra chuỗi `AIEvent` (TextDelta… rồi Done) và ném `ProviderError`
với `kind` đã chuẩn hóa để UI hiển thị thông báo dễ hiểu và quyết định có thử lại hay không.
"""
from __future__ import annotations

import ipaddress
import threading
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Iterator, Literal, Protocol
from urllib.parse import urlsplit, urlunsplit


@dataclass(frozen=True)
class ChatMessage:
    role: Literal["user", "assistant"]
    content: str


@dataclass
class AIRequest:
    model: str
    messages: list[ChatMessage]
    system: str = ""
    max_output_tokens: int = 16_000
    request_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])


@dataclass
class Usage:
    """Token đã chuẩn hóa giữa các provider.

    input_tokens: tổng token đầu vào (đã gồm phần đọc từ cache).
    cached_tokens: phần đầu vào đọc từ cache (giá rẻ hơn).
    output_tokens: tổng token đầu ra được tính tiền (đã gồm token suy luận).
    reasoning_tokens: phần suy luận trong output_tokens (chỉ để hiển thị).
    """
    input_tokens: int = 0
    output_tokens: int = 0
    cached_tokens: int = 0
    reasoning_tokens: int = 0


@dataclass
class TextDelta:
    text: str


@dataclass
class Done:
    usage: Usage
    stop_reason: str | None = None
    # Model thực sự trả lời (có thể khác model yêu cầu, ví dụ khi Anthropic chuyển sang model dự phòng)
    model: str | None = None
    fallback_used: bool = False


AIEvent = TextDelta | Done


class ErrorKind(str, Enum):
    auth = "auth"                    # 401: key sai/hết hạn
    permission = "permission"        # 403: không có quyền / chưa bật billing
    not_found = "not_found"          # 404: model/endpoint không tồn tại
    rate_limit = "rate_limit"        # 429
    invalid_request = "invalid_request"  # 400/422
    server = "server"                # 5xx / quá tải
    network = "network"              # không kết nối được
    timeout = "timeout"
    cancelled = "cancelled"
    unknown = "unknown"

    @property
    def retryable(self) -> bool:
        return self in (ErrorKind.rate_limit, ErrorKind.server, ErrorKind.network, ErrorKind.timeout)


class ProviderError(Exception):
    def __init__(self, kind: ErrorKind, detail: str = "", status: int | None = None) -> None:
        super().__init__(detail or kind.value)
        self.kind = kind
        self.detail = detail
        self.status = status


def kind_from_status(status: int | None) -> ErrorKind:
    if status is None:
        return ErrorKind.unknown
    if status == 401:
        return ErrorKind.auth
    if status in (402, 403):
        return ErrorKind.permission
    if status == 404:
        return ErrorKind.not_found
    if status == 429:
        return ErrorKind.rate_limit
    if status in (400, 409, 413, 422):
        return ErrorKind.invalid_request
    if status == 408:
        return ErrorKind.timeout
    if status >= 500:
        return ErrorKind.server
    return ErrorKind.unknown


@dataclass(frozen=True)
class ModelInfo:
    id: str
    display_name: str = ""
    context_tokens: int | None = None

    @property
    def label(self) -> str:
        return self.display_name if self.display_name and self.display_name != self.id else self.id


class CancelToken:
    """Cờ hủy dùng chung giữa luồng UI và luồng gọi API."""

    def __init__(self) -> None:
        self._event = threading.Event()

    def cancel(self) -> None:
        self._event.set()

    @property
    def cancelled(self) -> bool:
        return self._event.is_set()


class AIProvider(Protocol):
    provider_id: str

    def list_models(self) -> list[ModelInfo]: ...

    def stream(self, request: AIRequest, cancel: CancelToken | None = None) -> Iterator[AIEvent]: ...


# ---- Thông tin provider & kiểm tra base URL ------------------------------------------

@dataclass(frozen=True)
class ProviderMeta:
    id: str
    name: str
    default_base_url: str
    key_url: str
    key_prefix_hint: str = ""
    test_only: bool = False


PROVIDERS: dict[str, ProviderMeta] = {
    "openai": ProviderMeta("openai", "OpenAI", "https://api.openai.com/v1",
                           "https://platform.openai.com/api-keys", "sk-"),
    "deepseek": ProviderMeta("deepseek", "DeepSeek", "https://api.deepseek.com",
                             "https://platform.deepseek.com/api_keys", "sk-"),
    "gemini": ProviderMeta("gemini", "Google Gemini", "https://generativelanguage.googleapis.com",
                           "https://aistudio.google.com/apikey", "AIza"),
    "anthropic": ProviderMeta("anthropic", "Claude (Anthropic)", "https://api.anthropic.com",
                              "https://platform.claude.com/settings/keys", "sk-ant-"),
    "fake": ProviderMeta("fake", "TEST – Provider giả (không gọi mạng)", "https://fake.invalid",
                         "", test_only=True),
}

REAL_PROVIDERS = [p for p in PROVIDERS.values() if not p.test_only]


class InvalidBaseURL(ValueError):
    pass


def validate_base_url(url: str) -> str:
    """Chỉ cho phép HTTPS tới tên miền công khai; trả về URL đã chuẩn hóa (không có / cuối).

    Chặn: http, thiếu host, user:pass@ trong URL, query/fragment, IP nội bộ/loopback, localhost.
    """
    url = (url or "").strip()
    if not url:
        raise InvalidBaseURL("Base URL trống")
    parts = urlsplit(url)
    if parts.scheme.lower() != "https":
        raise InvalidBaseURL("Chỉ chấp nhận https://")
    if parts.username or parts.password:
        raise InvalidBaseURL("Không được đặt tài khoản/mật khẩu trong URL")
    if parts.query or parts.fragment:
        raise InvalidBaseURL("Base URL không được có ?query hoặc #fragment")
    host = (parts.hostname or "").lower()
    if not host or "." not in host and host != "localhost":
        raise InvalidBaseURL("Host không hợp lệ")
    if host == "localhost" or host.endswith(".localhost") or host.endswith(".local"):
        raise InvalidBaseURL("Không cho phép host nội bộ")
    try:
        ip = ipaddress.ip_address(host.strip("[]"))
    except ValueError:
        ip = None
    if ip is not None and (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_unspecified):
        raise InvalidBaseURL("Không cho phép địa chỉ IP nội bộ")
    path = parts.path.rstrip("/")
    return urlunsplit(("https", parts.netloc.lower(), path, "", ""))


def is_default_base_url(provider_id: str, url: str) -> bool:
    meta = PROVIDERS.get(provider_id)
    return bool(meta) and url.rstrip("/") == meta.default_base_url.rstrip("/")
