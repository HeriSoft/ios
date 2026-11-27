"""Adapter provider với client giả lập (không gọi mạng): streaming, usage, hủy, ánh xạ lỗi."""
from types import SimpleNamespace as NS

import pytest

from app_builder.providers.base import (
    AIRequest, CancelToken, ChatMessage, Done, ErrorKind, InvalidBaseURL, ProviderError, TextDelta,
    kind_from_status, validate_base_url,
)
from app_builder.providers._errors import to_provider_error

REQ = AIRequest("m", [ChatMessage("user", "Xin chào")], system="Bạn là trợ lý", max_output_tokens=100)


def run(provider, req=REQ, cancel=None):
    events = list(provider.stream(req, cancel))
    text = "".join(e.text for e in events if isinstance(e, TextDelta))
    done = events[-1]
    assert isinstance(done, Done)
    return text, done


# ---- Anthropic --------------------------------------------------------------------
class _AnthStream:
    def __init__(self, events, final):
        self.events, self.final = events, final

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def __iter__(self):
        return iter(self.events)

    def get_final_message(self):
        return self.final


def _anth_client(events, final, calls):
    def stream(**kw):
        calls.append(("plain", kw))
        return _AnthStream(events, final)

    def beta_stream(**kw):
        calls.append(("beta", kw))
        return _AnthStream(events, final)

    return NS(messages=NS(stream=stream), beta=NS(messages=NS(stream=beta_stream)),
              models=NS(list=lambda limit=100: [NS(id="claude-opus-5-5", display_name="Claude Opus 5.5", max_input_tokens=1_000_000)]))


ANTH_EVENTS = [
    NS(type="message_start", message=NS(model="claude-opus-5-5", usage=NS(input_tokens=10, cache_read_input_tokens=90, cache_creation_input_tokens=0))),
    NS(type="content_block_start"),
    NS(type="content_block_delta", delta=NS(type="text_delta", text="Chào ")),
    NS(type="content_block_delta", delta=NS(type="thinking_delta", thinking="...")),
    NS(type="content_block_delta", delta=NS(type="text_delta", text="bạn")),
    NS(type="message_delta", delta=NS(stop_reason="end_turn"), usage=NS(output_tokens=7)),
    NS(type="message_stop"),
]
ANTH_FINAL = NS(model="claude-opus-5-5", stop_reason="end_turn",
                usage=NS(input_tokens=10, cache_read_input_tokens=90, cache_creation_input_tokens=0, output_tokens=7, iterations=[]))


def test_anthropic_stream_usage_and_fallback_params():
    from app_builder.providers.anthropic_provider import AnthropicProvider
    calls = []
    p = AnthropicProvider("k", client=_anth_client(ANTH_EVENTS, ANTH_FINAL, calls))
    text, done = run(p, AIRequest("claude-opus-5-5", REQ.messages, REQ.system, 100))
    assert text == "Chào bạn"
    assert (done.usage.input_tokens, done.usage.cached_tokens, done.usage.output_tokens) == (100, 90, 7)
    assert done.stop_reason == "end_turn" and not done.fallback_used
    kind, kw = calls[0]
    # Opus 5.5: bật dự phòng phía server khi model từ chối
    assert kind == "beta" and kw["fallbacks"] == "default" and kw["betas"] == ["server-side-fallback-2026-07-01"]
    assert kw["system"] == "Bạn là trợ lý" and kw["max_tokens"] == 100
    assert p.list_models()[0].context_tokens == 1_000_000


def test_anthropic_older_model_uses_plain_stream_and_reports_fallback():
    from app_builder.providers.anthropic_provider import AnthropicProvider, supports_fallback
    assert supports_fallback("claude-sonnet-5-5") and supports_fallback("claude-opus-5")
    assert not supports_fallback("claude-haiku-4-5") and not supports_fallback("claude-opus-5-1x")
    calls = []
    final = NS(model="claude-opus-4-8", stop_reason="end_turn",
               usage=NS(input_tokens=5, cache_read_input_tokens=0, cache_creation_input_tokens=0, output_tokens=3,
                        iterations=[NS(type="message"), NS(type="fallback_message")]))
    p = AnthropicProvider("k", client=_anth_client(ANTH_EVENTS, final, calls))
    _, done = run(p, AIRequest("claude-haiku-4-5", REQ.messages))
    assert calls[0][0] == "plain"
    assert done.fallback_used and done.model == "claude-opus-4-8"


def test_anthropic_cancel_stops_early():
    from app_builder.providers.anthropic_provider import AnthropicProvider
    tok = CancelToken()
    p = AnthropicProvider("k", client=_anth_client(ANTH_EVENTS, ANTH_FINAL, []))
    out = []
    for ev in p.stream(AIRequest("claude-opus-5-5", REQ.messages), tok):
        out.append(ev)
        if isinstance(ev, TextDelta):
            tok.cancel()
    assert [e.text for e in out if isinstance(e, TextDelta)] == ["Chào "]
    assert out[-1].stop_reason == "cancelled"


# ---- OpenAI (Responses API) ---------------------------------------------------------
def test_openai_responses_stream():
    from app_builder.providers.openai_provider import OpenAIProvider
    captured = {}

    class S(list):
        closed = False

        def close(self):
            S.closed = True

    def create(**kw):
        captured.update(kw)
        return S([
            NS(type="response.created"),
            NS(type="response.output_text.delta", delta="Xin "),
            NS(type="response.output_text.delta", delta="chào"),
            NS(type="response.completed", response=NS(model="gpt-x", incomplete_details=None, usage=NS(
                input_tokens=20, output_tokens=12, input_tokens_details=NS(cached_tokens=8),
                output_tokens_details=NS(reasoning_tokens=4)))),
        ])

    client = NS(responses=NS(create=create),
                models=NS(list=lambda: [NS(id="gpt-x"), NS(id="text-embedding-3"), NS(id="whisper-1")]))
    p = OpenAIProvider("k", client=client)
    text, done = run(p)
    assert text == "Xin chào" and S.closed
    assert (done.usage.input_tokens, done.usage.cached_tokens, done.usage.output_tokens, done.usage.reasoning_tokens) == (20, 8, 12, 4)
    assert captured["instructions"] == "Bạn là trợ lý" and captured["stream"] and captured["store"] is False
    assert [m.id for m in p.list_models()] == ["gpt-x"]


def test_openai_failed_event_raises():
    from app_builder.providers.openai_provider import OpenAIProvider
    client = NS(responses=NS(create=lambda **kw: iter([NS(type="response.failed", response=NS(error=NS(message="hết quota")))])))
    with pytest.raises(ProviderError) as e:
        run(OpenAIProvider("k", client=client))
    assert "hết quota" in e.value.detail


# ---- DeepSeek (OpenAI-compatible chat) ------------------------------------------------
def test_deepseek_chat_stream_puts_system_first():
    from app_builder.providers.deepseek_provider import DeepSeekProvider
    captured = {}

    def create(**kw):
        captured.update(kw)
        return iter([
            NS(model="deepseek-chat", choices=[NS(delta=NS(content="A"), finish_reason=None)], usage=None),
            NS(model="deepseek-chat", choices=[NS(delta=NS(content="B"), finish_reason="stop")], usage=None),
            NS(model="deepseek-chat", choices=[], usage=NS(prompt_tokens=30, completion_tokens=2,
                                                           prompt_cache_hit_tokens=10, completion_tokens_details=None)),
        ])

    p = DeepSeekProvider("k", client=NS(chat=NS(completions=NS(create=create))))
    text, done = run(p)
    assert text == "AB" and done.stop_reason == "stop"
    assert (done.usage.input_tokens, done.usage.cached_tokens, done.usage.output_tokens) == (30, 10, 2)
    assert captured["messages"][0] == {"role": "system", "content": "Bạn là trợ lý"}
    assert captured["stream_options"] == {"include_usage": True}


# ---- Gemini ---------------------------------------------------------------------------
def test_gemini_stream_counts_thoughts_as_output():
    from app_builder.providers.gemini_provider import GeminiProvider
    captured = {}

    def gen(model, contents, config):
        captured.update(model=model, contents=contents, config=config)
        return iter([
            NS(text="Mộ", candidates=[], model_version=None, usage_metadata=None),
            NS(text="t", candidates=[NS(finish_reason=NS(value="STOP"))], model_version="gemini-x-001",
               usage_metadata=NS(prompt_token_count=40, candidates_token_count=5, thoughts_token_count=15,
                                 cached_content_token_count=0)),
        ])

    client = NS(models=NS(generate_content_stream=gen, list=lambda: [
        NS(name="models/gemini-x", display_name="Gemini X", supported_actions=["generateContent"], input_token_limit=1000),
        NS(name="models/embedding-001", display_name="Emb", supported_actions=["embedContent"], input_token_limit=1)]))
    p = GeminiProvider("k", client=client)
    text, done = run(p)
    assert text == "Một" and done.stop_reason == "STOP" and done.model == "gemini-x-001"
    assert (done.usage.input_tokens, done.usage.output_tokens, done.usage.reasoning_tokens) == (40, 20, 15)
    assert captured["config"].system_instruction == "Bạn là trợ lý"
    assert captured["contents"][0].role == "user"
    assert [m.id for m in p.list_models()] == ["gemini-x"]


# ---- Fake + lỗi + URL -------------------------------------------------------------------
def test_fake_provider_echo_error_and_cancel():
    from app_builder.providers.fake_provider import FakeProvider
    text, done = run(FakeProvider(), AIRequest("fake-echo", [ChatMessage("user", "một hai")]))
    assert text == "[TEST] Bạn vừa hỏi: một hai" and done.stop_reason == "end_turn"
    with pytest.raises(ProviderError) as e:
        run(FakeProvider(), AIRequest("fake-error", REQ.messages))
    assert e.value.kind is ErrorKind.rate_limit and e.value.kind.retryable
    tok = CancelToken()
    tok.cancel()
    _, done = run(FakeProvider(), AIRequest("fake-echo", REQ.messages), tok)
    assert done.stop_reason == "cancelled"


@pytest.mark.parametrize("status,kind", [(401, ErrorKind.auth), (403, ErrorKind.permission), (404, ErrorKind.not_found),
                                         (429, ErrorKind.rate_limit), (400, ErrorKind.invalid_request),
                                         (500, ErrorKind.server), (529, ErrorKind.server)])
def test_status_mapping(status, kind):
    class StatusErr(Exception):
        status_code = status
    assert to_provider_error(StatusErr("x")).kind is kind
    if status != 529:
        assert kind_from_status(status) is kind


def test_error_detail_is_redacted_and_network_kinds():
    class APIConnectionError(Exception):
        pass

    class APITimeoutError(Exception):
        pass

    err = to_provider_error(APIConnectionError("failed with key sk-ant-abcdefghijklmnop1234"))
    assert err.kind is ErrorKind.network and "abcdefghijklmnop" not in err.detail
    assert to_provider_error(APITimeoutError("t")).kind is ErrorKind.timeout


@pytest.mark.parametrize("url,ok", [
    ("https://api.openai.com/v1/", "https://api.openai.com/v1"),
    ("https://my-gateway.example.com", "https://my-gateway.example.com"),
    ("http://api.openai.com", None), ("https://user:pw@api.x.com", None), ("https://localhost:8080", None),
    ("https://127.0.0.1", None), ("https://10.0.0.5/v1", None), ("https://api.x.com/v1?key=1", None), ("", None),
    ("ftp://api.x.com", None),
])
def test_validate_base_url(url, ok):
    if ok:
        assert validate_base_url(url) == ok
    else:
        with pytest.raises(InvalidBaseURL):
            validate_base_url(url)


def test_real_sdk_clients_construct_without_network():
    from app_builder.providers.factory import create_provider
    for pid in ("openai", "deepseek", "gemini", "anthropic", "fake"):
        assert create_provider(pid, "sk-test-0000000000000000").provider_id == pid
