"""Provider GIẢ có nhãn TEST: không gọi mạng, dùng cho test và demo offline."""
from __future__ import annotations

import time
from typing import Iterator

from app_builder.providers.base import (
    AIEvent, AIRequest, CancelToken, Done, ErrorKind, ModelInfo, ProviderError, TextDelta, Usage,
)

FAKE_MODELS = [ModelInfo("fake-echo", "TEST · Echo"), ModelInfo("fake-error", "TEST · Luôn lỗi 429")]


class FakeProvider:
    provider_id = "fake"

    def __init__(self, api_key: str = "", base_url: str | None = None, delay: float = 0.0) -> None:
        self.delay = delay

    def list_models(self) -> list[ModelInfo]:
        return list(FAKE_MODELS)

    def stream(self, request: AIRequest, cancel: CancelToken | None = None) -> Iterator[AIEvent]:
        if request.model == "fake-error":
            raise ProviderError(ErrorKind.rate_limit, "TEST: giả lập lỗi 429", 429)
        last = request.messages[-1].content if request.messages else ""
        reply = f"[TEST] Bạn vừa hỏi: {last}"
        words = reply.split(" ")
        sent = []
        for i, w in enumerate(words):
            if cancel and cancel.cancelled:
                yield Done(Usage(_count(request), len(sent)), "cancelled", request.model)
                return
            piece = w if i == 0 else " " + w
            sent.append(piece)
            yield TextDelta(piece)
            if self.delay:
                time.sleep(self.delay)
        yield Done(Usage(_count(request), len(words)), "end_turn", request.model)


def _count(request: AIRequest) -> int:
    return sum(len(m.content.split()) for m in request.messages) + len(request.system.split())
