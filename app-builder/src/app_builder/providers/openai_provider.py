"""OpenAI qua SDK chính thức `openai` — Responses API (streaming)."""
from __future__ import annotations

from typing import Any, Iterator

from app_builder.providers._errors import to_provider_error
from app_builder.providers.base import (
    AIEvent, AIRequest, CancelToken, Done, ErrorKind, ModelInfo, ProviderError, TextDelta, Usage,
    is_default_base_url,
)

# Bỏ các model không dùng cho chat văn bản khi liệt kê
_NON_CHAT = ("embedding", "whisper", "tts", "dall-e", "moderation", "image", "audio", "realtime", "transcribe", "search")


class OpenAIProvider:
    provider_id = "openai"

    def __init__(self, api_key: str, base_url: str | None = None, client: Any = None) -> None:
        if client is None:
            import openai
            kwargs: dict[str, Any] = {"api_key": api_key, "max_retries": 2}
            if base_url and not is_default_base_url(self.provider_id, base_url):
                kwargs["base_url"] = base_url
            client = openai.OpenAI(**kwargs)
        self.client = client

    def list_models(self) -> list[ModelInfo]:
        try:
            ids = sorted(m.id for m in self.client.models.list())
        except Exception as exc:
            raise to_provider_error(exc) from exc
        return [ModelInfo(i) for i in ids if not any(x in i for x in _NON_CHAT)]

    def stream(self, request: AIRequest, cancel: CancelToken | None = None) -> Iterator[AIEvent]:
        params: dict[str, Any] = {
            "model": request.model,
            "input": [{"role": m.role, "content": m.content} for m in request.messages],
            "max_output_tokens": request.max_output_tokens,
            "stream": True,
            "store": False,
        }
        if request.system:
            params["instructions"] = request.system
        usage = Usage()
        model = request.model
        stop_reason: str | None = None
        stream = None
        try:
            stream = self.client.responses.create(**params)
            for event in stream:
                if cancel and cancel.cancelled:
                    stop_reason = "cancelled"
                    break
                etype = getattr(event, "type", "")
                if etype == "response.output_text.delta":
                    if event.delta:
                        yield TextDelta(event.delta)
                elif etype in ("response.completed", "response.incomplete"):
                    resp = event.response
                    model = getattr(resp, "model", None) or model
                    stop_reason = "end_turn" if etype == "response.completed" else (
                        getattr(getattr(resp, "incomplete_details", None), "reason", None) or "incomplete")
                    u = getattr(resp, "usage", None)
                    if u is not None:
                        usage.input_tokens = u.input_tokens or 0
                        usage.output_tokens = u.output_tokens or 0
                        usage.cached_tokens = getattr(getattr(u, "input_tokens_details", None), "cached_tokens", 0) or 0
                        usage.reasoning_tokens = getattr(getattr(u, "output_tokens_details", None), "reasoning_tokens", 0) or 0
                elif etype in ("response.failed", "error"):
                    err = getattr(getattr(event, "response", None), "error", None) or event
                    msg = getattr(err, "message", None) or str(err)
                    raise ProviderError(ErrorKind.unknown, str(msg)[:500])
        except ProviderError:
            raise
        except Exception as exc:
            raise to_provider_error(exc) from exc
        finally:
            if stream is not None and hasattr(stream, "close"):
                try:
                    stream.close()
                except Exception:
                    pass
        yield Done(usage, stop_reason, model)
