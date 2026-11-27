"""OpenAI qua SDK `openai`, Responses API (streaming). API key/billing riêng với gói ChatGPT."""
from __future__ import annotations

import base64
import re
import time
from typing import Any, AsyncIterator

from app_builder.providers.base import (
    AIEvent, AIRequest, BaseProvider, ConnectionResult, ErrorKind, ModelInfo, ProviderError, Usage,
    classify_exception, request_messages_with_context,
)

DEFAULT_BASE_URL = "https://api.openai.com/v1"
# /v1/models trả cả model embedding/tts/ảnh...; chỉ giữ model sinh văn bản dùng được với Responses API
_EXCLUDE = re.compile(r"(embedding|tts|whisper|transcribe|audio|realtime|image|dall-e|moderation|search|sora|"
                      r"babbage|davinci|computer-use|codex-mini-latest)", re.I)
_INCLUDE = re.compile(r"^(gpt-|o\d|chatgpt-)", re.I)


def _attr(obj: Any, *names: str) -> Any:
    for n in names:
        if obj is None:
            return None
        obj = getattr(obj, n, None)
    return obj


class OpenAIProvider(BaseProvider):
    provider_id = "openai"

    def __init__(self, api_key: str, base_url: str | None = None, client: Any = None, timeout: float = 120.0,
                 **kw) -> None:
        super().__init__(**kw)
        if client is None:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=api_key, base_url=base_url or DEFAULT_BASE_URL, max_retries=0,
                                 timeout=timeout)
        self.client = client

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
        out: list[ModelInfo] = []
        async for m in self.client.models.list():
            mid = getattr(m, "id", "")
            if not _INCLUDE.search(mid) or _EXCLUDE.search(mid):
                continue
            # OpenAI /models không công bố khả năng -> để None (không đoán), trừ streaming của Responses API
            out.append(ModelInfo(self.provider_id, mid, mid,
                                 {"streaming": True, "vision": None, "tools": None, "structured": None, "reasoning": None},
                                 deprecated=bool(getattr(m, "shutdown_date", None))))
        return sorted(out, key=lambda x: x.id)

    @staticmethod
    def build_input(request: AIRequest) -> list[dict]:
        items: list[dict] = []
        for msg in request_messages_with_context(request):
            if msg.role == "assistant":
                items.append({"role": "assistant", "content": msg.text})
            elif msg.images:
                parts: list[dict] = [{"type": "input_text", "text": msg.text}]
                for img in msg.images:
                    url = f"data:{img.media_type};base64,{base64.b64encode(img.data).decode()}"
                    parts.append({"type": "input_image", "image_url": url})
                items.append({"role": "user", "content": parts})
            else:
                items.append({"role": "user", "content": msg.text})
        return items

    async def _stream_once(self, request: AIRequest) -> AsyncIterator[AIEvent]:
        kwargs: dict[str, Any] = {"model": request.model, "input": self.build_input(request),
                                  "max_output_tokens": request.max_output_tokens}
        if request.system:
            kwargs["instructions"] = request.system
        async with self.client.responses.stream(**kwargs) as stream:
            async for event in stream:
                et = getattr(event, "type", "")
                if et == "response.output_text.delta":
                    yield AIEvent("text_delta", text=event.delta)
                elif et == "response.refusal.delta":
                    yield AIEvent("text_delta", text=getattr(event, "delta", ""))
                elif et == "error":
                    raise ProviderError(ErrorKind.UNKNOWN, str(getattr(event, "message", "stream error")))
            final = await stream.get_final_response()
        u = getattr(final, "usage", None)
        usage = Usage(
            input_tokens=_attr(u, "input_tokens"),
            output_tokens=_attr(u, "output_tokens"),
            cached_input_tokens=_attr(u, "input_tokens_details", "cached_tokens"),
            reasoning_tokens=_attr(u, "output_tokens_details", "reasoning_tokens"),
            served_model=getattr(final, "model", None),
        )
        if getattr(final, "status", None) == "incomplete":
            reason = _attr(final, "incomplete_details", "reason") or "?"
            yield AIEvent("warning", text=f"Phản hồi chưa hoàn tất: {reason}"
                          + (" — tăng giới hạn output." if reason == "max_output_tokens" else ""))
        yield AIEvent("usage", usage=usage)
        yield AIEvent("completed", data={"provider_response_id": getattr(final, "id", None)})
