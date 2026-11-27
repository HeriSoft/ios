"""DeepSeek qua SDK `openai` (API tương thích OpenAI Chat Completions, streaming)."""
from __future__ import annotations

from typing import Any, Iterator

from app_builder.providers._errors import to_provider_error
from app_builder.providers.base import (
    AIEvent, AIRequest, CancelToken, Done, ModelInfo, PROVIDERS, ProviderError, TextDelta, Usage,
)


class DeepSeekProvider:
    provider_id = "deepseek"

    def __init__(self, api_key: str, base_url: str | None = None, client: Any = None) -> None:
        if client is None:
            import openai
            client = openai.OpenAI(api_key=api_key, base_url=base_url or PROVIDERS["deepseek"].default_base_url,
                                   max_retries=2)
        self.client = client

    def list_models(self) -> list[ModelInfo]:
        try:
            return [ModelInfo(m.id) for m in sorted(self.client.models.list(), key=lambda m: m.id)]
        except Exception as exc:
            raise to_provider_error(exc) from exc

    def stream(self, request: AIRequest, cancel: CancelToken | None = None) -> Iterator[AIEvent]:
        messages: list[dict[str, str]] = []
        if request.system:
            messages.append({"role": "system", "content": request.system})
        messages += [{"role": m.role, "content": m.content} for m in request.messages]
        usage = Usage()
        model = request.model
        stop_reason: str | None = None
        stream = None
        try:
            stream = self.client.chat.completions.create(
                model=request.model, messages=messages, max_tokens=request.max_output_tokens,
                stream=True, stream_options={"include_usage": True},
            )
            for chunk in stream:
                if cancel and cancel.cancelled:
                    stop_reason = "cancelled"
                    break
                model = getattr(chunk, "model", None) or model
                for choice in getattr(chunk, "choices", None) or []:
                    text = getattr(choice.delta, "content", None)
                    if text:
                        yield TextDelta(text)
                    if getattr(choice, "finish_reason", None):
                        stop_reason = choice.finish_reason
                u = getattr(chunk, "usage", None)
                if u is not None:
                    usage.input_tokens = u.prompt_tokens or 0
                    usage.output_tokens = u.completion_tokens or 0
                    # DeepSeek báo phần đọc từ cache ở prompt_cache_hit_tokens
                    usage.cached_tokens = getattr(u, "prompt_cache_hit_tokens", 0) or 0
                    details = getattr(u, "completion_tokens_details", None)
                    usage.reasoning_tokens = getattr(details, "reasoning_tokens", 0) or 0
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
