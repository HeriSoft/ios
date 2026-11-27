"""Claude qua SDK chính thức `anthropic` (Messages API, streaming).

- Streaming: `client.messages.stream(...)`; token vào ở `message_start`, token ra ở `message_delta`.
- Với các model có hỗ trợ, bật dự phòng phía server khi model từ chối (refusal):
  beta `server-side-fallback-2026-07-01` + `fallbacks="default"` — API tự chạy lại yêu cầu trên model
  phù hợp; chi phí khi đó tính theo model dự phòng nên app ghi nhận là "ước tính".
"""
from __future__ import annotations

from typing import Any, Iterator

from app_builder.providers._errors import to_provider_error
from app_builder.providers.base import (
    AIEvent, AIRequest, CancelToken, Done, ErrorKind, ModelInfo, ProviderError, TextDelta, Usage,
    is_default_base_url,
)

DEFAULT_MODEL = "claude-opus-5-5"
FALLBACK_BETA = "server-side-fallback-2026-07-01"
# Model hỗ trợ `fallbacks="default"` (theo tài liệu Claude API, 2026-11)
FALLBACK_MODELS = ("claude-fable-5-2", "claude-fable-5-1", "claude-opus-5-5", "claude-sonnet-5-5")
FALLBACK_EXACT = ("claude-opus-5",)


def supports_fallback(model: str) -> bool:
    return model in FALLBACK_EXACT or any(model == m or model.startswith(m + "-") for m in FALLBACK_MODELS)


class AnthropicProvider:
    provider_id = "anthropic"

    def __init__(self, api_key: str, base_url: str | None = None, client: Any = None,
                 use_fallback: bool = True) -> None:
        if client is None:
            import anthropic
            kwargs: dict[str, Any] = {"api_key": api_key, "max_retries": 2}
            if base_url and not is_default_base_url(self.provider_id, base_url):
                kwargs["base_url"] = base_url
            client = anthropic.Anthropic(**kwargs)
        self.client = client
        self.use_fallback = use_fallback

    def list_models(self) -> list[ModelInfo]:
        try:
            return [ModelInfo(m.id, getattr(m, "display_name", "") or "", getattr(m, "max_input_tokens", None))
                    for m in self.client.models.list(limit=100)]
        except Exception as exc:
            raise to_provider_error(exc) from exc

    def stream(self, request: AIRequest, cancel: CancelToken | None = None) -> Iterator[AIEvent]:
        params: dict[str, Any] = {
            "model": request.model,
            "max_tokens": request.max_output_tokens,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
        }
        if request.system:
            params["system"] = request.system
        fallback = self.use_fallback and supports_fallback(request.model)
        usage = Usage()
        input_uncached = cache_read = cache_write = 0
        model = request.model
        stop_reason: str | None = None
        try:
            if fallback:
                ctx = self.client.beta.messages.stream(betas=[FALLBACK_BETA], fallbacks="default", **params)
            else:
                ctx = self.client.messages.stream(**params)
            with ctx as stream:
                for event in stream:
                    if cancel and cancel.cancelled:
                        stop_reason = "cancelled"
                        break
                    etype = getattr(event, "type", "")
                    if etype == "message_start":
                        msg = event.message
                        model = getattr(msg, "model", None) or model
                        u = getattr(msg, "usage", None)
                        if u is not None:
                            input_uncached = getattr(u, "input_tokens", 0) or 0
                            cache_read = getattr(u, "cache_read_input_tokens", 0) or 0
                            cache_write = getattr(u, "cache_creation_input_tokens", 0) or 0
                    elif etype == "content_block_delta":
                        delta = event.delta
                        if getattr(delta, "type", "") == "text_delta" and delta.text:
                            yield TextDelta(delta.text)
                    elif etype == "message_delta":
                        u = getattr(event, "usage", None)
                        if u is not None and getattr(u, "output_tokens", None) is not None:
                            usage.output_tokens = u.output_tokens
                        stop_reason = getattr(event.delta, "stop_reason", None) or stop_reason
                fallback_used = False
                if stop_reason != "cancelled":
                    try:
                        final = stream.get_final_message()
                        model = getattr(final, "model", None) or model
                        fu = getattr(final, "usage", None)
                        if fu is not None:
                            input_uncached = getattr(fu, "input_tokens", input_uncached) or input_uncached
                            cache_read = getattr(fu, "cache_read_input_tokens", cache_read) or cache_read
                            cache_write = getattr(fu, "cache_creation_input_tokens", cache_write) or cache_write
                            usage.output_tokens = getattr(fu, "output_tokens", usage.output_tokens) or usage.output_tokens
                            iterations = getattr(fu, "iterations", None) or []
                            fallback_used = any(getattr(i, "type", "") == "fallback_message" for i in iterations)
                        stop_reason = getattr(final, "stop_reason", stop_reason) or stop_reason
                    except Exception:
                        pass
        except ProviderError:
            raise
        except Exception as exc:
            raise to_provider_error(exc) from exc
        usage.input_tokens = input_uncached + cache_read + cache_write
        usage.cached_tokens = cache_read
        yield Done(usage, stop_reason, model, fallback_used or model != request.model)
