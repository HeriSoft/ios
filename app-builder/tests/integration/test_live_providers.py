"""Kiểm thử gọi API THẬT (tốn một ít tiền) — chỉ chạy khi đặt key qua biến môi trường:

    APPBUILDER_LIVE_OPENAI_KEY / _DEEPSEEK_KEY / _GEMINI_KEY / _ANTHROPIC_KEY
    (tùy chọn) APPBUILDER_LIVE_<PROVIDER>_MODEL để chọn model

Không có key → test bị bỏ qua (ghi BLOCKED trong PROGRESS.md).
"""
import os

import pytest

from app_builder.providers.base import AIRequest, ChatMessage, Done, TextDelta
from app_builder.providers.factory import create_provider

pytestmark = pytest.mark.live

DEFAULT_MODEL = {"anthropic": "claude-haiku-5-5"}


@pytest.mark.parametrize("pid", ["openai", "deepseek", "gemini", "anthropic"])
def test_live_list_models_and_short_stream(pid):
    key = os.environ.get(f"APPBUILDER_LIVE_{pid.upper()}_KEY")
    if not key:
        pytest.skip(f"BLOCKED: chưa có APPBUILDER_LIVE_{pid.upper()}_KEY")
    provider = create_provider(pid, key)
    models = provider.list_models()
    assert models
    model = os.environ.get(f"APPBUILDER_LIVE_{pid.upper()}_MODEL") or DEFAULT_MODEL.get(pid) or models[0].id
    events = list(provider.stream(AIRequest(model, [ChatMessage("user", "Trả lời đúng một từ: xin chào")],
                                            max_output_tokens=200)))
    assert any(isinstance(e, TextDelta) for e in events)
    done = events[-1]
    assert isinstance(done, Done) and done.usage.input_tokens > 0 and done.usage.output_tokens > 0
