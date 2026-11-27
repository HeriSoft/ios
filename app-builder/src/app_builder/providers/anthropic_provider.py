"""Claude API qua SDK chính thức `anthropic` (Messages API, streaming). Key từ Anthropic Console, billing riêng
với gói Claude Pro/Max.

Với các model có bộ phân loại an toàn có thể trả `stop_reason: "refusal"` (Fable 5.x, Opus 5.x, Sonnet 5.5),
adapter mặc định bật server-side fallback (`fallbacks="default"`, beta `server-side-fallback-2026-07-01`) để
API tự chạy lại trên model dự phòng khi bị từ chối. Có thể tắt trong Kết nối AI. Chi phí được tính theo model
thực sự phục vụ (`response.model`).
"""
from __future__ import annotations

import base64
import time
from typing import Any, AsyncIterator

from app_builder.providers.base import (
    AIEvent, AIRequest, BaseProvider, ConnectionResult, ErrorKind, ModelInfo, Usage, classify_exception,
    request_messages_with_context,
)

FALLBACK_BETA = "server-side-fallback-2026-07-01"
FALLBACK_MODELS = {"claude-fable-5-2", "claude-fable-5-1", "claude-opus-5-5", "claude-opus-5", "claude-sonnet-5-5"}
DEFAULT_MODEL = "claude-opus-5-5"


def _supported(cap: Any, name: str) -> bool | None:
    v = getattr(cap, name, None) if cap is not None else None
    s = getattr(v, "supported", None) if v is not None else None
    return bool(s) if s is not None else None


def _n(v: Any) -> int:
    return int(v or 0)


class AnthropicProvider(BaseProvider):
    provider_id = "anthropic"

    def __init__(self, api_key: str, base_url: str | None = None, client: Any = None, timeout: float = 600.0,
                 refusal_fallback: bool = True, **kw) -> None:
        super().__init__(**kw)
        if client is None:
            from anthropic import AsyncAnthropic
            client = AsyncAnthropic(api_key=api_key, max_retries=0, timeout=timeout)
        self.client = client
        self.refusal_fallback = refusal_fallback

    async def test_connection(self) -> ConnectionResult:
        t0 = time.monotonic()
        try:
            models = await self.list_models()
        except Exception as exc:  # noqa: BLE001
            err = classify_exception(exc)
            status = "auth_failed" if err.kind in (ErrorKind.AUTH, ErrorKind.PERMISSION) else (
                "network" if err.kind is ErrorKind.NETWORK else "error")
            return ConnectionResult(False, status, err.user_message)
        return ConnectionResult(True, "authenticated", "", int((time.monotonic() - t0) * 1000), len(models))

    async def list_models(self) -> list[ModelInfo]:
        out = []
        async for m in self.client.models.list():
            cap = getattr(m, "capabilities", None)
            out.append(ModelInfo(
                self.provider_id, m.id, getattr(m, "display_name", "") or m.id,
                {"streaming": True, "tools": True,  # tool use là tính năng lõi của Messages API
                 "vision": _supported(cap, "image_input"), "structured": _supported(cap, "structured_outputs"),
                 "reasoning": True if getattr(cap, "thinking", None) is not None else None},
                context_window=getattr(m, "max_input_tokens", None),
                max_output=getattr(m, "max_tokens", None),
                deprecated=bool(getattr(m, "deprecated_at", None)),
            ))
        return out

    @staticmethod
    def build_messages(request: AIRequest) -> list[dict]:
        msgs = []
        for m in request_messages_with_context(request):
            if m.images and m.role == "user":
                content: list[dict] = [{"type": "image", "source": {"type": "base64", "media_type": img.media_type,
                                                                    "data": base64.standard_b64encode(img.data).decode()}}
                                       for img in m.images]
                content.append({"type": "text", "text": m.text})
                msgs.append({"role": m.role, "content": content})
            else:
                msgs.append({"role": m.role, "content": m.text})
        return msgs

    async def _stream_once(self, request: AIRequest) -> AsyncIterator[AIEvent]:
        kwargs: dict[str, Any] = {"model": request.model, "max_tokens": request.max_output_tokens,
                                  "messages": self.build_messages(request)}
        if request.system:
            kwargs["system"] = request.system
        use_fallback = self.refusal_fallback and request.model in FALLBACK_MODELS
        if use_fallback:
            manager = self.client.beta.messages.stream(betas=[FALLBACK_BETA], fallbacks="default", **kwargs)
        else:
            manager = self.client.messages.stream(**kwargs)
        async with manager as stream:
            async for text in stream.text_stream:
                yield AIEvent("text_delta", text=text)
            final = await stream.get_final_message()
        u = getattr(final, "usage", None)
        cache_read = getattr(u, "cache_read_input_tokens", None)
        cache_write = getattr(u, "cache_creation_input_tokens", None)
        usage = Usage(
            # Anthropic tách input chưa cache / cache read / cache write -> chuẩn hóa: input gồm cả cached
            input_tokens=_n(getattr(u, "input_tokens", 0)) + _n(cache_read) + _n(cache_write) if u else None,
            output_tokens=getattr(u, "output_tokens", None),
            cached_input_tokens=cache_read,
            served_model=getattr(final, "model", None),
        )
        stop = getattr(final, "stop_reason", None)
        if use_fallback:
            for block in getattr(final, "content", None) or []:
                if getattr(block, "type", "") == "fallback":
                    yield AIEvent("warning", text=f"Model {block.from_.model} từ chối; {block.to.model} đã tiếp tục.")
        if stop == "refusal":
            details = getattr(final, "stop_details", None)
            cat = getattr(details, "category", None)
            yield AIEvent("warning", text=f"Claude từ chối yêu cầu (refusal{f': {cat}' if cat else ''}).")
        elif stop == "max_tokens":
            yield AIEvent("warning", text="Phản hồi bị cắt do đạt giới hạn output.")
        yield AIEvent("usage", usage=usage)
        yield AIEvent("completed", data={"provider_response_id": getattr(final, "id", None), "stop_reason": stop})
