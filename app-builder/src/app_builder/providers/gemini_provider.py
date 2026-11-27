"""Google Gemini qua Google Gen AI SDK (`google-genai`), API key từ Google AI Studio."""
from __future__ import annotations

import time
from typing import Any, AsyncIterator

from app_builder.providers.base import (
    AIEvent, AIRequest, BaseProvider, ConnectionResult, ErrorKind, ModelInfo, Usage, classify_exception,
    request_messages_with_context,
)


def _sum(*vals: int | None) -> int | None:
    nums = [v for v in vals if v is not None]
    return sum(nums) if nums else None


class GeminiProvider(BaseProvider):
    provider_id = "gemini"

    def __init__(self, api_key: str, base_url: str | None = None, client: Any = None, timeout_ms: int = 120_000,
                 **kw) -> None:
        super().__init__(**kw)
        if client is None:
            from google import genai
            from google.genai import types
            # Tắt retry nội bộ của SDK: retry do BaseProvider kiểm soát (không gửi lại request có thể tính phí)
            client = genai.Client(api_key=api_key, http_options=types.HttpOptions(
                timeout=timeout_ms, retry_options=types.HttpRetryOptions(attempts=1)))
        self.client = client

    async def test_connection(self) -> ConnectionResult:
        t0 = time.monotonic()
        try:
            models = await self.list_models()
        except Exception as exc:  # noqa: BLE001
            err = classify_exception(exc)
            status = "auth_failed" if err.kind in (ErrorKind.AUTH, ErrorKind.PERMISSION, ErrorKind.BAD_REQUEST) else (
                "network" if err.kind is ErrorKind.NETWORK else "error")
            return ConnectionResult(False, status, err.user_message)
        return ConnectionResult(True, "authenticated", "", int((time.monotonic() - t0) * 1000), len(models))

    async def list_models(self) -> list[ModelInfo]:
        out = []
        pager = await self.client.aio.models.list()
        async for m in pager:
            actions = getattr(m, "supported_actions", None) or []
            if "generateContent" not in actions:
                continue
            mid = (getattr(m, "name", "") or "").removeprefix("models/")
            thinking = getattr(m, "thinking", None)
            out.append(ModelInfo(
                self.provider_id, mid, getattr(m, "display_name", "") or mid,
                {"streaming": "streamGenerateContent" in actions or None, "vision": None, "tools": None,
                 "structured": None, "reasoning": bool(thinking) if thinking is not None else None},
                context_window=getattr(m, "input_token_limit", None),
                max_output=getattr(m, "output_token_limit", None),
            ))
        return sorted(out, key=lambda x: x.id)

    @staticmethod
    def build_contents(request: AIRequest) -> list:
        from google.genai import types
        contents = []
        for m in request_messages_with_context(request):
            parts = [types.Part.from_text(text=m.text)]
            for img in m.images:
                parts.append(types.Part.from_bytes(data=img.data, mime_type=img.media_type))
            contents.append(types.Content(role="model" if m.role == "assistant" else "user", parts=parts))
        return contents

    async def _stream_once(self, request: AIRequest) -> AsyncIterator[AIEvent]:
        from google.genai import types
        config = types.GenerateContentConfig(max_output_tokens=request.max_output_tokens,
                                             system_instruction=request.system or None)
        it = await self.client.aio.models.generate_content_stream(
            model=request.model, contents=self.build_contents(request), config=config)
        meta = None
        finish = None
        served = None
        async for chunk in it:
            served = getattr(chunk, "model_version", None) or served
            for cand in getattr(chunk, "candidates", None) or []:
                content = getattr(cand, "content", None)
                for part in getattr(content, "parts", None) or []:
                    if getattr(part, "thought", False):
                        continue
                    if getattr(part, "text", None):
                        yield AIEvent("text_delta", text=part.text)
                finish = getattr(cand, "finish_reason", None) or finish
            meta = getattr(chunk, "usage_metadata", None) or meta
        if finish is not None and str(getattr(finish, "value", finish)) == "MAX_TOKENS":
            yield AIEvent("warning", text="Phản hồi bị cắt do đạt giới hạn output.")
        elif finish is not None and str(getattr(finish, "value", finish)) in ("SAFETY", "PROHIBITED_CONTENT", "RECITATION"):
            yield AIEvent("warning", text=f"Gemini dừng phản hồi: {getattr(finish, 'value', finish)}")
        usage = Usage(
            input_tokens=getattr(meta, "prompt_token_count", None),
            # Gemini tính phí output gồm cả thinking (thoughts_token_count tách riêng trong metadata)
            output_tokens=_sum(getattr(meta, "candidates_token_count", None), getattr(meta, "thoughts_token_count", None)),
            cached_input_tokens=getattr(meta, "cached_content_token_count", None),
            reasoning_tokens=getattr(meta, "thoughts_token_count", None),
            served_model=served,
        )
        yield AIEvent("usage", usage=usage)
        yield AIEvent("completed")
