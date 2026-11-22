"""Task 13 step 5: Google GenAI calls use the same decoding controls as
OpenAI, and the Google rotation list is real.

OpenAI calls use temperature 0.35 and max_tokens from MAX_OUTPUT_TOKENS
(default 4096). The Google GenAI calls previously passed no generation
config at all, and the rotation list held a single model
("gemini-3.8-flash"). Both the sync path (_complete_google) and the
streaming path (_stream_google) must now send
types.GenerateContentConfig(temperature=0.35, max_output_tokens=...) and
rotate to the next model on a retryable error (429/503/404) when zero
tokens were produced.

No live LLM calls: the Google client is stubbed with SimpleNamespace.
The Google API has no frequency/presence penalty parameters, so none are
asserted (or set) here.
"""

from types import SimpleNamespace

import pytest

from nakshatra.ai.synthesize import (
    GOOGLE_PRIMARY_MODEL,
    GOOGLE_ROTATION_MODELS,
    GOOGLE_TEMPERATURE,
    LLMSynthesizer,
    _google_generation_config,
)


def _google_synth(model=GOOGLE_PRIMARY_MODEL):
    return LLMSynthesizer(provider="google", model=model, api_key="sk-test")


def test_google_generation_config_matches_openai_defaults():
    """Helper builds a real GenerateContentConfig: 0.35 / 4096 default."""
    config = _google_generation_config()
    assert config.temperature == 0.35
    assert config.temperature == GOOGLE_TEMPERATURE
    assert config.max_output_tokens == 4096


def test_google_generation_config_reads_max_output_tokens_env(monkeypatch):
    monkeypatch.setenv("MAX_OUTPUT_TOKENS", "1234")
    config = _google_generation_config()
    assert config.temperature == 0.35
    assert config.max_output_tokens == 1234


def test_rotation_list_is_real_and_primary_unchanged():
    """More than one model; primary is still gemini-3.8-flash, first."""
    assert len(GOOGLE_ROTATION_MODELS) > 1
    assert GOOGLE_ROTATION_MODELS[0] == "gemini-3.8-flash"
    assert GOOGLE_PRIMARY_MODEL == "gemini-3.8-flash"
    assert len(set(GOOGLE_ROTATION_MODELS)) == len(GOOGLE_ROTATION_MODELS)


def test_complete_google_sends_temperature_and_max_tokens():
    """Sync path: generate_content receives temperature 0.35, max 4096."""
    synth = _google_synth()
    seen: list[dict] = []

    def _generate_content(model, contents, config=None):
        seen.append({"model": model, "config": config})
        return SimpleNamespace(text="Sync answer from Google.")

    synth._client = SimpleNamespace(
        models=SimpleNamespace(generate_content=_generate_content)
    )
    answer = synth._complete_google("prompt", system_prompt="sys")

    assert answer == "Sync answer from Google."
    assert len(seen) == 1
    assert seen[0]["model"] == "gemini-3.8-flash"
    config = seen[0]["config"]
    assert config is not None
    assert config.temperature == 0.35
    assert config.max_output_tokens == 4096


def test_complete_google_config_follows_max_output_tokens_env(monkeypatch):
    """Sync path honours MAX_OUTPUT_TOKENS like the OpenAI path does."""
    monkeypatch.setenv("MAX_OUTPUT_TOKENS", "2048")
    synth = _google_synth()
    seen: list[dict] = []

    def _generate_content(model, contents, config=None):
        seen.append({"config": config})
        return SimpleNamespace(text="answer")

    synth._client = SimpleNamespace(
        models=SimpleNamespace(generate_content=_generate_content)
    )
    synth._complete_google("prompt")

    assert seen[0]["config"].max_output_tokens == 2048


def test_stream_google_sends_temperature_and_max_tokens():
    """Streaming path: generate_content_stream receives the same config."""
    synth = _google_synth()
    seen: list[dict] = []

    def _generate_content_stream(model, contents, config=None):
        seen.append({"model": model, "config": config})
        yield SimpleNamespace(text="Streamed ")
        yield SimpleNamespace(text="answer.")

    synth._client = SimpleNamespace(
        models=SimpleNamespace(generate_content_stream=_generate_content_stream)
    )
    tokens = list(synth._stream_google("prompt", system_prompt="sys"))

    assert "".join(tokens) == "Streamed answer."
    assert len(seen) == 1
    assert seen[0]["model"] == "gemini-3.8-flash"
    config = seen[0]["config"]
    assert config is not None
    assert config.temperature == 0.35
    assert config.max_output_tokens == 4096


def test_complete_google_429_rotates_to_next_model():
    """Sync: 429 on the primary with zero tokens -> fallback model tried."""
    synth = _google_synth()
    calls: list[str] = []
    configs: list[object] = []

    def _generate_content(model, contents, config=None):
        calls.append(model)
        configs.append(config)
        if len(calls) == 1:
            raise Exception("429 RESOURCE_EXHAUSTED")
        return SimpleNamespace(text="Answer from the fallback model.")

    synth._client = SimpleNamespace(
        models=SimpleNamespace(generate_content=_generate_content)
    )
    answer = synth._complete_google("prompt")

    assert answer == "Answer from the fallback model."
    assert calls == list(GOOGLE_ROTATION_MODELS[:2])
    assert calls[0] == "gemini-3.8-flash"
    # The retry gets the same decoding controls, not an uncontrolled call.
    assert configs[1] is not None
    assert configs[1].temperature == 0.35
    assert configs[1].max_output_tokens == 4096
    assert synth.model == calls[-1]


@pytest.mark.parametrize("err", ["503 UNAVAILABLE", "404 NOT_FOUND"])
def test_complete_google_503_and_404_rotate(err):
    """Sync: 503 and 404 are retryable and rotate to the next model."""
    synth = _google_synth()
    calls: list[str] = []

    def _generate_content(model, contents, config=None):
        calls.append(model)
        if len(calls) == 1:
            raise Exception(err)
        return SimpleNamespace(text="Answer from the fallback model.")

    synth._client = SimpleNamespace(
        models=SimpleNamespace(generate_content=_generate_content)
    )
    assert synth._complete_google("prompt") == "Answer from the fallback model."
    assert len(calls) == 2
    assert calls[0] == "gemini-3.8-flash"


def test_complete_google_non_retryable_error_does_not_rotate():
    """Sync: a non-retryable error raises immediately, no second model."""
    synth = _google_synth()
    calls: list[str] = []

    def _generate_content(model, contents, config=None):
        calls.append(model)
        raise ValueError("INVALID_ARGUMENT: bad request")

    synth._client = SimpleNamespace(
        models=SimpleNamespace(generate_content=_generate_content)
    )
    with pytest.raises(ValueError, match="INVALID_ARGUMENT"):
        synth._complete_google("prompt")

    assert calls == ["gemini-3.8-flash"]


def test_stream_google_429_zero_tokens_rotates_to_next_model():
    """Streaming: 429 before any token -> next model streams the answer."""
    synth = _google_synth()
    calls: list[str] = []

    def _generate_content_stream(model, contents, config=None):
        calls.append(model)
        if len(calls) == 1:
            raise Exception("429 RESOURCE_EXHAUSTED")
        yield SimpleNamespace(text="Full answer from the second model.")

    synth._client = SimpleNamespace(
        models=SimpleNamespace(generate_content_stream=_generate_content_stream)
    )
    tokens = list(synth._stream_google("prompt"))

    assert "".join(tokens) == "Full answer from the second model."
    assert calls == list(GOOGLE_ROTATION_MODELS[:2])
    assert synth.model == calls[-1]


def test_stream_google_config_present_on_retry(monkeypatch):
    """Streaming retry also carries temperature/max-tokens (not uncontrolled)."""
    synth = _google_synth()
    configs: list[object] = []

    def _generate_content_stream(model, contents, config=None):
        configs.append(config)
        if len(configs) == 1:
            raise Exception("503 UNAVAILABLE")
        yield SimpleNamespace(text="ok")

    synth._client = SimpleNamespace(
        models=SimpleNamespace(generate_content_stream=_generate_content_stream)
    )
    assert list(synth._stream_google("prompt")) == ["ok"]
    assert len(configs) == 2
    assert all(c is not None and c.temperature == 0.35 for c in configs)
    assert all(c.max_output_tokens == 4096 for c in configs)


def test_google_config_uses_real_genai_config_type():
    """The config passed is a real google.genai GenerateContentConfig."""
    from google.genai import types

    assert isinstance(_google_generation_config(), types.GenerateContentConfig)
