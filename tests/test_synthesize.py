"""
Tests for LLM synthesis: prompt building, citation extraction,
and synthesizer providers.
"""

from __future__ import annotations

import importlib.util
import os

import pytest

from nakshatra.ai.corpus import CorpusChunk
from nakshatra.ai.retrieval import SearchResult
from nakshatra.ai.synthesize import (
    FallbackSynthesizer,
    LLMSynthesizer,
    build_prompt,
    extract_citations,
)


def _module_available(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except ImportError:
        return False


def _chunk(
    work: str = "BPHS",
    chapter: str = "1",
    verse: str = "1",
    text: str = "The Sun in the first house.",
) -> CorpusChunk:
    return CorpusChunk(
        work=work,
        chapter=chapter,
        verse=verse,
        text=text,
        topics=["Sun"],
        source_file="test.txt",
        char_start=0,
        char_end=len(text),
        tier="verse",
    )


def _result(
    verse: str = "1",
    text: str = "The Sun in the first house.",
    score: float = 0.9,
) -> SearchResult:
    return SearchResult(chunk=_chunk(verse=verse, text=text), score=score)


class TestBuildPrompt:
    """Consultation prompt assembly."""

    def test_contains_question_and_reference(self):
        prompt = build_prompt("What about my career?", [_result()])
        assert "Question: What about my career?" in prompt
        assert "[1] BPHS Chapter 1 Verse 1" in prompt
        assert "The Sun in the first house." in prompt

    def test_numbered_references(self):
        results = [_result(verse="1"), _result(verse="2", text="Moon text.")]
        prompt = build_prompt("Q", results)
        assert "[1] BPHS Chapter 1 Verse 1" in prompt
        assert "[2] BPHS Chapter 1 Verse 2" in prompt

    def test_birth_context_included(self):
        prompt = build_prompt(
            "Q",
            [_result()],
            birth_context={"ascendant": "Aries", "moon_sign": "Cancer"},
        )
        assert "Birth chart context:" in prompt
        assert '"ascendant": "Aries"' in prompt

    def test_no_birth_context_omitted(self):
        prompt = build_prompt("Q", [_result()])
        assert "Birth chart context" not in prompt

    def test_citation_instruction(self):
        prompt = build_prompt("Q", [_result()])
        assert "citing them with bracketed numbers" in prompt

    def test_verse_only_chunk_label(self):
        chunk = _chunk(chapter="", verse="12")
        prompt = build_prompt("Q", [SearchResult(chunk=chunk, score=1.0)])
        assert "[1] BPHS Verse 12" in prompt
        assert "Chapter" not in prompt


class TestExtractCitations:
    """[n] marker parsing from model output."""

    def test_parses_markers(self):
        results = [_result(verse="1"), _result(verse="2", text="Moon.")]
        citations = extract_citations("According to [1] and also [2], the Sun rules.", results)
        assert len(citations) == 2
        assert citations[0].verse == "1"
        assert citations[0].work == "BPHS"
        assert citations[0].text == "The Sun in the first house."

    def test_ignores_out_of_range(self):
        results = [_result()]
        assert extract_citations("See [5] for details.", results) == []

    def test_dedupes_markers(self):
        results = [_result()]
        citations = extract_citations("[1] and again [1]", results)
        assert len(citations) == 1

    def test_no_markers(self):
        results = [_result()]
        assert extract_citations("No citations here.", results) == []


class TestFallbackSynthesizer:
    """Deterministic verbatim-reference synthesis."""

    def test_formats_results(self):
        results = [
            _result(verse="1"),
            _result(verse="2", text="The Moon in the second house."),
        ]
        answer = FallbackSynthesizer().synthesize("career?", results)
        assert "Regarding your question 'career?'" in answer.answer
        assert answer.model == "fallback"
        assert answer.question == "career?"
        assert len(answer.citations) == 2
        assert answer.citations[0].verse == "1"

    def test_empty_results(self):
        answer = FallbackSynthesizer().synthesize("Q", [])
        assert "No relevant references" in answer.answer
        assert answer.citations == []

    def test_birth_context_accepted(self):
        answer = FallbackSynthesizer().synthesize(
            "Q", [_result()], birth_context={"ascendant": "Aries"}
        )
        assert answer.answer  # context accepted, formatted verbatim


class TestLLMSynthesizer:
    """LLM provider synthesis with a stubbed completion."""

    def test_synthesize_with_stub(self):
        class StubSynthesizer(LLMSynthesizer):
            def _complete(self, prompt: str) -> str:
                assert "Question:" in prompt
                return "The Sun gives career success [1]."

        synthesizer = StubSynthesizer(provider="openai", model="gpt-test")
        answer = synthesizer.synthesize("career?", [_result()])
        assert answer.answer == "The Sun gives career success [1]."
        assert answer.model == "gpt-test"
        assert len(answer.citations) == 1
        assert answer.citations[0].verse == "1"

    def test_unknown_provider_raises(self):
        synthesizer = LLMSynthesizer(provider="bogus")
        with pytest.raises(ValueError, match="Unknown LLM provider"):
            synthesizer._complete("prompt")

    def test_openai_missing_dependency_raises(self):
        if _module_available("openai"):
            pytest.skip("openai is installed")
        synthesizer = LLMSynthesizer(provider="openai")
        with pytest.raises(ImportError, match=r"nakshatra\[ai\]"):
            synthesizer._complete("prompt")

    def test_google_missing_dependency_raises(self):
        if _module_available("google.genai"):
            pytest.skip("google-genai is installed")
        synthesizer = LLMSynthesizer(provider="google")
        with pytest.raises(ImportError, match=r"nakshatra\[ai\]"):
            synthesizer._complete("prompt")

    def test_synthesize_empty_results_with_stub(self):
        class StubSynthesizer(LLMSynthesizer):
            def _complete(self, prompt: str) -> str:
                return "The corpus has no relevant references."

        synthesizer = StubSynthesizer()
        answer = synthesizer.synthesize("Q", [])
        assert answer.citations == []
        assert "References:" in build_prompt("Q", [])

    def test_google_live_when_key_present(self):
        if not os.environ.get("NAKSHATRA_LIVE"):
            pytest.skip("Live test (set NAKSHATRA_LIVE=1 to run)")
        google_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
        if not google_key or not _module_available("google.genai"):
            pytest.skip("No Google API key or google-genai package")
        synthesizer = LLMSynthesizer(provider="google", model="gemini-3.8-flash")
        answer = synthesizer.synthesize("career?", [_result()])
        assert answer.model == "gemini-3.8-flash"
        assert len(answer.answer.strip()) > 0
