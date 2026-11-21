import pytest

from nakshatra.ai.service import _default_synthesizer
from nakshatra.ai.synthesize import LLMSynthesizer

pytest.importorskip("openai")


def test_9router_priority_over_ambient_google_key(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "9router")
    monkeypatch.setenv("OPENAI_BASE_URL", "http://localhost:20128/v1")
    monkeypatch.setenv("OPENAI_MODEL", "nakshatra-combo")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    monkeypatch.setenv("GOOGLE_API_KEY", "AQ.dummy-antigravity-token")

    synth = _default_synthesizer()
    assert isinstance(synth, LLMSynthesizer)
    assert synth.provider == "openai"
    assert synth.model == "nakshatra-combo"
    assert synth._base_url == "http://localhost:20128/v1"


def test_router_lowercase_priority(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "router")
    monkeypatch.setenv("OPENAI_BASE_URL", "http://localhost:20128/v1")
    monkeypatch.setenv("OPENAI_MODEL", "nakshatra-combo")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    monkeypatch.setenv("GOOGLE_API_KEY", "AQ.dummy-antigravity-token")

    synth = _default_synthesizer()
    assert isinstance(synth, LLMSynthesizer)
    assert synth.provider == "openai"
    assert synth.model == "nakshatra-combo"
