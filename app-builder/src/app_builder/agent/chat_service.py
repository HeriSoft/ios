"""Phiên chat: giữ lịch sử, dựng AIRequest, stream qua provider, đặt/giải phóng reservation và ghi ledger
cho MỌI kết thúc (hoàn tất / lỗi / dừng). Không phụ thuộc Qt."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import AsyncIterator

from app_builder.agent.budget import BudgetDecision, BudgetManager
from app_builder.providers.base import AIEvent, AIProvider, AIRequest, ChatMessage, ContextFile, Usage

# Chế độ (đặc tả 4.2) -> giới hạn output & số lượt lịch sử gửi kèm
MODE_LIMITS = {
    "economy": {"max_output": 2048, "history_turns": 6},
    "balanced": {"max_output": 4096, "history_turns": 12},
    "advanced": {"max_output": 8192, "history_turns": 24},
}


@dataclass
class ChatTurnResult:
    text: str = ""
    usage: Usage | None = None
    cost_usd: float | None = None
    status: str = "completed"  # completed | error | cancelled
    error: str = ""
    warnings: list[str] = field(default_factory=list)


class ChatSession:
    def __init__(self, provider_id: str, model: str, mode: str = "economy") -> None:
        self.provider_id = provider_id
        self.model = model
        self.mode = mode if mode in MODE_LIMITS else "economy"
        self.history: list[ChatMessage] = []

    def build_request(self, text: str, system: str, context_files: list[ContextFile] | None = None,
                      max_output: int | None = None) -> AIRequest:
        lim = MODE_LIMITS[self.mode]
        turns = self.history[-lim["history_turns"] * 2:]
        while turns and turns[0].role != "user":  # luôn bắt đầu bằng user
            turns = turns[1:]
        return AIRequest(model=self.model, messages=[*turns, ChatMessage("user", text)], system=system,
                         max_output_tokens=max_output or lim["max_output"], context_files=list(context_files or []))

    async def run(self, provider: AIProvider, request: AIRequest, budget: BudgetManager,
                  decision: BudgetDecision, project_id: int | None = None,
                  ) -> AsyncIterator[tuple[AIEvent, ChatTurnResult]]:
        """Stream sự kiện; luôn ghi ledger khi kết thúc. Người gọi phải đã duyệt `decision`."""
        result = ChatTurnResult()
        budget.reserve(request.request_id, decision.estimate_usd, project_id)
        recorded = False

        def _record(status: str, note: str = "") -> None:
            nonlocal recorded
            if recorded:
                return
            recorded = True
            result.cost_usd = budget.record(
                request_id=request.request_id, provider=self.provider_id, model=request.model, usage=result.usage,
                status=status, project_id=project_id, estimate=decision.estimate_usd, note=note)

        try:
            async for ev in provider.stream(request):
                if ev.type == "text_delta":
                    result.text += ev.text
                elif ev.type == "usage":
                    result.usage = ev.usage
                elif ev.type == "warning":
                    result.warnings.append(ev.text)
                elif ev.type == "error" and ev.error is not None:
                    result.status, result.error = "error", ev.error.user_message
                    _record("error", ev.error.kind.value)
                elif ev.type == "completed":
                    _record("completed")
                yield ev, result
        except asyncio.CancelledError:
            result.status = "cancelled"
            _record("cancelled", "dừng bởi người dùng — chi phí thực có thể đã phát sinh")
            raise
        finally:
            if not recorded:
                _record(result.status if result.status != "completed" else "incomplete")
        if result.status == "completed":
            self.history.append(request.messages[-1])
            self.history.append(ChatMessage("assistant", result.text))
