"""Google Gemini qua SDK chính thức `google-genai` (generate_content_stream)."""
from __future__ import annotations

from typing import Any, Iterator

from app_builder.providers._errors import to_provider_error
from app_builder.providers.base import (
    AIEvent, AIRequest, CancelToken, Done, ModelInfo, ProviderError, TextDelta, Usage, is_default_base_url,
)


class GeminiProvider:
    provider_id = "gemini"

    def __init__(self, api_key: str, base_url: str | None = None, client: Any = None) -> None:
        if client is None:
            from google import genai
            from google.genai import types
            http_options = None
            if base_url and not is_default_base_url(self.provider_id, base_url):
                http_options = types.HttpOptions(base_url=base_url)
            client = genai.Client(api_key=api_key, http_options=http_options)
        self.client = client

    def list_models(self) -> list[ModelInfo]:
        try:
            out = []
            for m in self.client.models.list():
                actions = getattr(m, "supported_actions", None) or []
                if actions and "generateContent" not in actions:
                    continue
                mid = (m.name or "").removeprefix("models/")
                if mid:
                    out.append(ModelInfo(mid, getattr(m, "display_name", "") or "", getattr(m, "input_token_limit", None)))
            return sorted(out, key=lambda x: x.id)
        except Exception as exc:
            raise to_provider_error(exc) from exc

    def stream(self, request: AIRequest, cancel: CancelToken | None = None) -> Iterator[AIEvent]:
        from google.genai import types
        contents = [types.Content(role="user" if m.role == "user" else "model", parts=[types.Part(text=m.content)])
                    for m in request.messages]
        config = types.GenerateContentConfig(
            system_instruction=request.system or None,
            max_output_tokens=request.max_output_tokens,
        )
        usage = Usage()
        model = request.model
        stop_reason: str | None = None
        try:
            for chunk in self.client.models.generate_content_stream(model=request.model, contents=contents, config=config):
                if cancel and cancel.cancelled:
                    stop_reason = "cancelled"
                    break
                text = getattr(chunk, "text", None)
                if text:
                    yield TextDelta(text)
                for cand in getattr(chunk, "candidates", None) or []:
                    fr = getattr(cand, "finish_reason", None)
                    if fr:
                        stop_reason = str(getattr(fr, "value", fr))
                model = getattr(chunk, "model_version", None) or model
                um = getattr(chunk, "usage_metadata", None)
                if um is not None:
                    thoughts = getattr(um, "thoughts_token_count", 0) or 0
                    usage.input_tokens = getattr(um, "prompt_token_count", 0) or 0
                    # Token suy nghĩ của Gemini được tính tiền như token đầu ra
                    usage.output_tokens = (getattr(um, "candidates_token_count", 0) or 0) + thoughts
                    usage.cached_tokens = getattr(um, "cached_content_token_count", 0) or 0
                    usage.reasoning_tokens = thoughts
        except ProviderError:
            raise
        except Exception as exc:
            raise to_provider_error(exc) from exc
        yield Done(usage, stop_reason, model)
