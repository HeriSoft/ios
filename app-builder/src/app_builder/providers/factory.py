"""Tạo adapter theo provider id."""
from __future__ import annotations

from typing import Any

from app_builder.providers.base import AIProvider


def create_provider(provider_id: str, api_key: str, base_url: str | None = None, client: Any = None) -> AIProvider:
    if provider_id == "openai":
        from app_builder.providers.openai_provider import OpenAIProvider
        return OpenAIProvider(api_key, base_url, client)
    if provider_id == "deepseek":
        from app_builder.providers.deepseek_provider import DeepSeekProvider
        return DeepSeekProvider(api_key, base_url, client)
    if provider_id == "gemini":
        from app_builder.providers.gemini_provider import GeminiProvider
        return GeminiProvider(api_key, base_url, client)
    if provider_id == "anthropic":
        from app_builder.providers.anthropic_provider import AnthropicProvider
        return AnthropicProvider(api_key, base_url, client)
    if provider_id == "fake":
        from app_builder.providers.fake_provider import FakeProvider
        return FakeProvider(api_key, base_url)
    raise ValueError(f"Provider không hỗ trợ: {provider_id}")
