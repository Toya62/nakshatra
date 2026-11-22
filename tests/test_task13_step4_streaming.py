"""Task 13 step 4: streaming must emit exactly one answer.

If the LLM yields partial tokens and then fails mid-stream, the stream must
end with a short interruption notice and NO appended fallback answer. The
fallback (FallbackSynthesizer) may only be yielded when ZERO tokens were
produced. The 429/503/404 retry path in _stream_google must likewise never
produce a second complete answer after partial tokens.

No live LLM calls: providers are stubbed to yield tokens then raise.
"""

from types import SimpleNamespace

import pytest

from nakshatra.ai import synthesize as synth_mod
from nakshatra.ai.corpus import CorpusChunk
from nakshatra.ai.retrieval import SearchResult
from nakshatra.ai.synthesize import LLMSynthesizer

FALLBACK_MARKER = "FALLBACK-ANSWER-MARKER-STEP4"


@pytest.fixture
def sample_results():
    chunk1 = CorpusChunk(
        work="Brihat Parashara Hora Shastra",
        chapter="12",
        verse="5",
        text="Jupiter in the 1st house confers high intellect, noble character, and profound wisdom.",
        source_file="bphs.txt",
        char_start=0,
        char_end=80,
        tier="verse",
    )
    chunk2 = CorpusChunk(
        work="Phaladeepika",
        chapter="8",
        verse="14",
        text="When Jupiter occupies the Lagna, the native will be handsome, virtuous, and long-lived.",
        source_file="phaladeepika.txt",
        char_start=81,
        char_end=170,
        tier="verse",
    )
    return [SearchResult(chunk=chunk1, score=0.95), SearchResult(chunk=chunk2, score=0.88)]


@pytest.fixture
def fallback_spy(monkeypatch):
    """Replace FallbackSynthesizer.synthesize_stream with a recording stub."""
    calls: list[dict] = []

    def _spy(self, question, results, birth_context=None, language="en"):
        calls.append({"question": question})
        yield FALLBACK_MARKER

    monkeypatch.setattr(
        synth_mod.FallbackSynthesizer, "synthesize_stream", _spy
    )
    return calls


def _openai_synth():
    return LLMSynthesizer(
        provider="openai",
        model="gpt-4o-mini",
        base_url="http://127.0.0.1:59999/v1",
        api_key="sk-test",
    )


def _google_synth(model="gemini-3.8-flash"):
    return LLMSynthesizer(provider="google", model=model, api_key="sk-test")


def _partial_then_fail(tokens, exc):
    def _gen(*args, **kwargs):
        for tok in tokens:
            yield tok
        raise exc

    return _gen


def test_midstream_failure_openai_emits_one_answer(
    monkeypatch, sample_results, fallback_spy
):
    """Partial OpenAI tokens + failure -> partial text + notice, no fallback."""
    synth = _openai_synth()
    monkeypatch.setattr(
        synth,
        "_stream_openai",
        _partial_then_fail(
            ["Partial answer about Jupiter. "], RuntimeError("connection reset")
        ),
    )
    tokens = list(
        synth.synthesize_stream("What does Jupiter in 1st house do?", sample_results)
    )
    full = "".join(tokens)

    assert "Partial answer about Jupiter." in full
    assert full.count("Partial answer about Jupiter.") == 1
    # Short interruption notice, not a second answer.
    assert "interrupted" in full.lower()
    assert "Please try again" in full
    # No fallback answer appended, and the fallback was never invoked.
    assert FALLBACK_MARKER not in full
    assert fallback_spy == []
    assert "Retrieved classical scriptural citations" not in full


def test_midstream_failure_google_emits_one_answer(
    monkeypatch, sample_results, fallback_spy
):
    """Partial Google tokens + failure -> partial text + notice, no fallback."""
    synth = _google_synth()
    monkeypatch.setattr(
        synth,
        "_stream_google",
        _partial_then_fail(
            ["Partial answer about Jupiter. "], RuntimeError("stream aborted")
        ),
    )
    tokens = list(
        synth.synthesize_stream("What does Jupiter in 1st house do?", sample_results)
    )
    full = "".join(tokens)

    assert "Partial answer about Jupiter." in full
    assert full.count("Partial answer about Jupiter.") == 1
    assert "interrupted" in full.lower()
    assert "Please try again" in full
    assert FALLBACK_MARKER not in full
    assert fallback_spy == []
    assert "Retrieved classical scriptural citations" not in full


def test_zero_token_failure_yields_fallback(
    monkeypatch, sample_results, fallback_spy
):
    """Zero tokens + failure -> existing behaviour: notice + fallback answer."""
    synth = _openai_synth()

    def _fail(*args, **kwargs):
        raise RuntimeError("connection refused")
        yield  # pragma: no cover - makes this a generator function

    monkeypatch.setattr(synth, "_stream_openai", _fail)
    tokens = list(
        synth.synthesize_stream("What does Jupiter in 1st house do?", sample_results)
    )
    full = "".join(tokens)

    assert "Notice:" in full
    assert "temporarily unavailable" in full
    assert FALLBACK_MARKER in full
    assert len(fallback_spy) == 1


def test_google_429_after_partial_tokens_no_second_answer(
    sample_results, fallback_spy
):
    """Google 429 after partial tokens must not try the next model.

    The fake client yields one partial chunk then raises 429 on the first
    model; if the retry path were reached, the second model would stream a
    second complete answer. That must not happen.
    """
    synth = _google_synth(model="gemini-3.5-flash-lite")
    calls: list[str] = []

    def _generate_content_stream(model, contents):
        calls.append(model)
        if len(calls) == 1:
            yield SimpleNamespace(text="Partial answer about Jupiter. ")
            raise Exception("429 RESOURCE_EXHAUSTED")
        yield SimpleNamespace(text="SECOND-COMPLETE-ANSWER")
        yield SimpleNamespace(text=" more of the second answer.")

    synth._client = SimpleNamespace(
        models=SimpleNamespace(generate_content_stream=_generate_content_stream)
    )
    tokens = list(
        synth.synthesize_stream("What does Jupiter in 1st house do?", sample_results)
    )
    full = "".join(tokens)

    assert "Partial answer about Jupiter." in full
    assert "SECOND-COMPLETE-ANSWER" not in full
    assert "more of the second answer" not in full
    # The retry to the second model never happened.
    assert calls == ["gemini-3.5-flash-lite"]
    # And no fallback answer was appended either.
    assert FALLBACK_MARKER not in full
    assert fallback_spy == []
    assert "interrupted" in full.lower()


def test_google_429_zero_tokens_retries_next_model(sample_results, fallback_spy):
    """Zero-token 429 still retries the next model (existing behaviour kept)."""
    synth = _google_synth(model="gemini-3.5-flash-lite")
    calls: list[str] = []

    def _generate_content_stream(model, contents):
        calls.append(model)
        if len(calls) == 1:
            raise Exception("429 RESOURCE_EXHAUSTED")
        yield SimpleNamespace(text="Full answer from the second model.")

    synth._client = SimpleNamespace(
        models=SimpleNamespace(generate_content_stream=_generate_content_stream)
    )
    tokens = list(
        synth.synthesize_stream("What does Jupiter in 1st house do?", sample_results)
    )
    full = "".join(tokens)

    assert full == "Full answer from the second model."
    assert calls == ["gemini-3.5-flash-lite", "gemini-3.8-flash"]
    assert FALLBACK_MARKER not in full
    assert fallback_spy == []
    assert "interrupted" not in full.lower()


def test_openai_second_candidate_not_tried_after_partial_tokens():
    """_stream_openai: mid-stream failure must not fall to the next model."""
    synth = _openai_synth()
    calls: list[str] = []

    def _chunk(content):
        return SimpleNamespace(
            choices=[SimpleNamespace(delta=SimpleNamespace(content=content))]
        )

    def _create(**kwargs):
        calls.append(kwargs["model"])
        if len(calls) == 1:
            yield _chunk("partial-token ")
            raise RuntimeError("connection reset")
        yield _chunk("SECOND-COMPLETE-ANSWER")

    synth._client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=_create))
    )
    tokens: list[str] = []
    with pytest.raises(RuntimeError, match="connection reset"):
        for tok in synth._stream_openai("prompt"):
            tokens.append(tok)

    assert tokens == ["partial-token "]
    assert calls == ["gpt-4o-mini"]
