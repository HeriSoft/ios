"""DeepSeek qua API tương thích OpenAI (chat/completions) theo api-docs.deepseek.com, dùng SDK `openai`."""
from __future__ import annotations

import time
from typing import Any, AsyncIterator

from app_builder.providers.base import (
    AIEvent, AIRequest, BaseProvider, ConnectionResult, ErrorKind, ModelInfo, ProviderError, Usage,
    classify_exception, request_messages_with_context,
)

DEFAULT_BASE_URL = "https://api.deepseek.com"


def _get(obj: Any, name: str) -> Any:
    if obj is None:
        return None
    v = getattr(obj, name, None)
    if v is None:
        extra = getattr(obj, "model_extra", None) or {}
        v = extra.get(name)
    return v


class DeepSeekProvider(BaseProvider):
    provider_id = "deepseek"

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
        out = []
        async for m in self.client.models.list():
            mid = getattr(m, "id", "")
            # DeepSeek /models chỉ trả id: không đoán khả năng (vision/tools...) -> None
            out.append(ModelInfo(self.provider_id, mid, mid, {"streaming": True, "vision": None, "tools": None,
                                                              "structured": None, "reasoning": None}))
        return sorted(out, key=lambda x: x.id)

    def check_request(self, request: AIRequest) -> None:
        super().check_request(request)
        if any(m.images for m in request.messages):
            raise ProviderError(ErrorKind.UNSUPPORTED, "Adapter DeepSeek hiện chỉ gửi văn bản (chưa hỗ trợ ảnh).")

    @staticmethod
    def build_messages(request: AIRequest) -> list[dict]:
        msgs: list[dict] = []
        if request.system:
            msgs.append({"role": "system", "content": request.system})
        for m in request_messages_with_context(request):
            msgs.append({"role": m.role, "content": m.text})
        return msgs

    async def _stream_once(self, request: AIRequest) -> AsyncIterator[AIEvent]:
        stream = await self.client.chat.completions.create(
            model=request.model, messages=self.build_messages(request), stream=True,
            stream_options={"include_usage": True}, max_tokens=request.max_output_tokens,
        )
        usage: Usage | None = None
        finish = None
        served = None
        try:
            async for chunk in stream:
                served = getattr(chunk, "model", served)
                for ch in getattr(chunk, "choices", None) or []:
                    delta = getattr(ch, "delta", None)
                    text = getattr(delta, "content", None) if delta else None
                    if text:
                        yield AIEvent("text_delta", text=text)
                    finish = getattr(ch, "finish_reason", None) or finish
                u = getattr(chunk, "usage", None)
                if u is not None:
                    usage = Usage(
                        input_tokens=_get(u, "prompt_tokens"),
                        output_tokens=_get(u, "completion_tokens"),
                        cached_input_tokens=_get(u, "prompt_cache_hit_tokens")
                        if _get(u, "prompt_cache_hit_tokens") is not None
                        else _get(_get(u, "prompt_tokens_details"), "cached_tokens"),
                        reasoning_tokens=_get(_get(u, "completion_tokens_details"), "reasoning_tokens"),
                    )
        finally:
            close = getattr(stream, "close", None)
            if close:
                await close()
        if finish == "length":
            yield AIEvent("warning", text="Phản hồi bị cắt do đạt giới hạn output.")
        if usage:
            usage.served_model = served
        else:
            yield AIEvent("warning", text="Provider không trả về usage cho request này.")
        yield AIEvent("usage", usage=usage or Usage(served_model=served))
        yield AIEvent("completed")
