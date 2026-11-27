"""Provider giả lập cho kiểm thử offline — LUÔN gắn nhãn TEST, không gọi mạng, không tốn phí."""
from __future__ import annotations

import asyncio
from typing import AsyncIterator

from app_builder.providers.base import (
    AIEvent, AIRequest, BaseProvider, ConnectionResult, ErrorKind, ModelInfo, ProviderError, RetryPolicy, Usage,
)

FAKE_LABEL = "TEST — provider giả lập (không phải AI thật)"


class FakeProvider(BaseProvider):
    provider_id = "fake"

    def __init__(self, api_key: str = "", base_url: str | None = None, *, delay: float = 0.0,
                 fail_times: int = 0, fail_kind: ErrorKind = ErrorKind.RATE_LIMIT, fail_after_start: bool = False,
                 chunks: int = 5, retry: RetryPolicy | None = None) -> None:
        super().__init__(retry=retry or RetryPolicy(max_attempts=3, base_delay=0.01, max_delay=0.05))
        self.delay = delay
        self.fail_times = fail_times
        self.fail_kind = fail_kind
        self.fail_after_start = fail_after_start
        self.chunks = chunks
        self.calls = 0

    async def test_connection(self) -> ConnectionResult:
        return ConnectionResult(True, "authenticated", FAKE_LABEL, 0, 1)

    async def list_models(self) -> list[ModelInfo]:
        return [ModelInfo("fake", "fake-echo", "TEST Echo",
                          {"streaming": True, "vision": False, "tools": False, "structured": False, "reasoning": False},
                          context_window=100_000, max_output=4096)]

    async def _stream_once(self, request: AIRequest) -> AsyncIterator[AIEvent]:
        self.calls += 1
        retryable = self.fail_kind in (ErrorKind.RATE_LIMIT, ErrorKind.SERVER, ErrorKind.NETWORK)
        if self.fail_times > 0 and not self.fail_after_start:
            self.fail_times -= 1
            raise ProviderError(self.fail_kind, "TEST failure", retryable=retryable)
        last = request.messages[-1].text
        reply = f"[TEST] Đã nhận {len(last)} ký tự: {last[:60]}"
        size = max(1, len(reply) // self.chunks)
        for i in range(0, len(reply), size):
            if self.delay:
                await asyncio.sleep(self.delay)
            yield AIEvent("text_delta", text=reply[i:i + size])
            if self.fail_after_start and self.fail_times > 0:
                self.fail_times -= 1
                raise ProviderError(self.fail_kind, "TEST failure mid-stream", retryable=retryable)
        yield AIEvent("usage", usage=Usage(input_tokens=len(last) // 3 + 10, output_tokens=len(reply) // 3,
                                           cached_input_tokens=0, served_model=request.model))
        yield AIEvent("completed")
