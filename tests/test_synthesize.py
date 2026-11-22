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
    ConsultationIntent,
    FallbackSynthesizer,
    LLMSynthesizer,
    _format_birth_summary,
    build_prompt,
    classify_intent,
    extract_citations,
    get_system_prompt,
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

    def test_4_pillar_prediction_architecture_in_prompt(self):
        prompt = build_prompt("When will I get promoted?", [_result()])
        assert "### 1. Direct Verdict & Timing" in prompt
        assert "### 2. Astrological Mechanism & Calculation Proof" in prompt
        assert "### 3. Concrete Timeline Windows" in prompt
        assert "### 4. Classical Lal Kitab Prescription" in prompt
        assert "Zero conversational fluff" in prompt

    def test_nepali_4_pillar_instruction_in_prompt(self):
        prompt = build_prompt("मेरो जागिर कहिले हुन्छ?", [_result()], language="ne")
        assert "### १. प्रत्यक्ष फलादेश र मुख्य निर्णय" in prompt
        assert "### २. ज्योतिषीय आधार र गणितीय प्रमाण" in prompt
        assert "### ३. यकिन समय-तालिका" in prompt
        assert "### ४. प्रामाणिक लाल किताब उपाय तथा सावधानी" in prompt

    def test_lal_kitab_remedies_in_birth_summary(self):
        birth_context = {
            "remedies": {
                "afflicted_planets": [
                    {
                        "planet": "Saturn",
                        "house": 8,
                        "severity": "high",
                        "lal_kitab": {
                            "household_remedy": "Drop raw mustard oil in dirt",
                            "symbolic_action": "Float 8 almonds in river",
                            "forbidden_actions": ["Never drink alcohol", "Never tell lies"],
                            "creature_service": "Feed stray black dogs",
                        },
                    }
                ]
            }
        }
        prompt = build_prompt("Remedies?", [_result()], birth_context=birth_context)
        assert "Classical Lal Kitab 108 Upayas & Inviolable Precautions" in prompt
        assert "Saturn in House 8 [HIGH AFFLICTION]" in prompt
        assert "Float 8 almonds in river" in prompt
        assert "Feed stray black dogs" in prompt
        assert "Never drink alcohol" in prompt

    def test_natal_identity_architecture_in_prompt(self):
        prompt = build_prompt("tell me about myself", [_result()])
        assert "NATAL IDENTITY & COSMIC PROFILE DIRECTIVE" in prompt
        assert "### 1. Cosmic Blueprint & Ascendant Archetype" in prompt
        assert "### 2. Emotional Landscape & Mind (Chandra & Nakshatra)" in prompt
        assert "### 3. Soul Purpose & Driving Vitality (Surya & Karakas)" in prompt
        assert "### 4. Key Strengths, Yogas & Karmic Evolution" in prompt
        assert "Do NOT invent job application windows" in prompt
        assert "dog-feeding" in prompt

    def test_nepali_natal_identity_architecture_in_prompt(self):
        prompt = build_prompt("आफ्नो बारेमा भन्नुहोस्", [_result()], language="ne")
        assert "### १. कुण्डलीको मूल संरचना र लग्न स्वरूप" in prompt
        assert "### २. मानसिक-भावनात्मक धरातल र चन्द्र-नक्षत्र" in prompt
        assert "### ३. आत्मिक उद्देश्य र आत्मकारक ग्रह" in prompt
        assert "### ४. मुख्य सामर्थ्य, शुभ योग र आत्म-विकास" in prompt


class TestIntentClassification:
    """Astrological consultation intent classification."""

    def test_natal_identity_intents(self):
        queries = [
            "tell me about myself",
            "who am I?",
            "what is my personality?",
            "what are my strengths and weaknesses?",
            "describe my character",
            "tell me about my chart",
            "what is my soul purpose?",
            "आफ्नो बारेमा भन्नुहोस्",
            "म को हुँ?",
            "मेरो स्वभाव कस्तो छ?",
        ]
        for q in queries:
            assert classify_intent(q) == ConsultationIntent.NATAL_IDENTITY, f"Failed for '{q}'"

    def test_event_prediction_intents(self):
        queries = [
            "When will I get promoted?",
            "when will I get a job?",
            "when will my finances improve?",
            "मेरो जागिर कहिले हुन्छ?",
            "विवाह कहिले हुन्छ?",
        ]
        for q in queries:
            assert classify_intent(q) == ConsultationIntent.EVENT_PREDICTION, f"Failed for '{q}'"

    def test_remedial_intents(self):
        queries = [
            "what remedies should I do for Saturn?",
            "lal kitab upaya for Rahu",
            "which gemstone should I wear?",
            "शान्ति पूजा र उपाय",
        ]
        for q in queries:
            assert classify_intent(q) == ConsultationIntent.REMEDIAL, f"Failed for '{q}'"

    def test_conceptual_intents(self):
        queries = [
            "what is Sade Sati?",
            "explain Gajakesari yoga",
            "meaning of Retrograde Mercury",
            "कालसर्प दोष भनेको के हो?",
        ]
        for q in queries:
            assert classify_intent(q) == ConsultationIntent.CONCEPTUAL, f"Failed for '{q}'"


class TestBirthSummaryEnrichment:
    """Enriched natal summary generation."""

    def test_lagna_lord_and_jaimini_karakas(self):
        chart_data = {
            "ascendant": {"sign": "Capricorn", "degree_in_sign": 21.0, "nakshatra": "Shravana", "pada": 4, "nakshatra_lord": "Moon"},
            "planets": [
                {"name": "Sun", "sign": "Virgo", "house": 9, "degree_in_sign": 27.7, "nakshatra": "Chitra", "pada": 2, "dignity": "neutral"},
                {"name": "Moon", "sign": "Gemini", "house": 6, "degree_in_sign": 13.2, "nakshatra": "Ardra", "pada": 2, "dignity": "neutral"},
                {"name": "Mars", "sign": "Scorpio", "house": 11, "degree_in_sign": 2.3, "nakshatra": "Vishakha", "pada": 4, "dignity": "own"},
                {"name": "Mercury", "sign": "Virgo", "house": 9, "degree_in_sign": 11.4, "nakshatra": "Hasta", "pada": 1, "dignity": "exalted"},
                {"name": "Jupiter", "sign": "Scorpio", "house": 11, "degree_in_sign": 19.1, "nakshatra": "Jyeshtha", "pada": 1, "dignity": "neutral"},
                {"name": "Venus", "sign": "Libra", "house": 10, "degree_in_sign": 12.5, "nakshatra": "Swati", "pada": 2, "dignity": "own"},
                {"name": "Saturn", "sign": "Aquarius", "house": 2, "degree_in_sign": 25.4, "nakshatra": "Purva Bhadrapada", "pada": 2, "retrograde": True, "dignity": "own"},
            ],
            "ashtakavarga": {
                "sarvashtakavarga": [26, 24, 33, 23, 28, 35, 21, 27, 29, 34, 30, 27]
            }
        }
        summary = _format_birth_summary(chart_data)
        assert "Lagna Lord Placement: Saturn sits in House 2 in Aquarius" in summary
        assert "Jaimini Chara Karakas: Atmakaraka (Soul): Sun (27.70°)" in summary
        assert "Amatyakaraka (Career/Action): Saturn (25.40°)" in summary
        assert "Darakaraka (Spouse/Partnership): Mars (2.30°)" in summary
        assert "Sarvashtakavarga (SAV Points by House from Lagna):" in summary
        assert "High Strength Houses (SAV >= 30 bindus):" in summary
        assert "Do NOT recite all 12 signs or scores in a raw list" in summary


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

    def test_formats_natal_identity_results(self):
        results = [_result(verse="1")]
        answer = FallbackSynthesizer().synthesize("tell me about myself", results)
        assert "### 1. Cosmic Blueprint & Ascendant Archetype" in answer.answer
        assert "### 2. Emotional Landscape & Mind (Chandra & Nakshatra)" in answer.answer
        assert "### 3. Soul Purpose & Driving Vitality (Surya & Karakas)" in answer.answer
        assert "### 4. Key Strengths, Yogas & Karmic Evolution" in answer.answer

    def test_formats_remedial_results(self):
        results = [_result(verse="1")]
        answer = FallbackSynthesizer().synthesize("what remedies for Saturn?", results)
        assert "### 1. Core Afflictions & Karmic Imbalances" in answer.answer
        assert "### 2. Primary 43-Day Daytime Lal Kitab Upaya" in answer.answer
        assert "### 3. Creature & Household Seva" in answer.answer
        assert "### 4. Inviolable Savdhani (Strict Behavioral Precautions)" in answer.answer


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

    def test_strip_trailing_references(self):
        from nakshatra.ai.synthesize import _strip_trailing_references

        text = (
            "You have great career potential with 10th lord Moon [1].\n\n"
            "References:\n\n"
            "[1] Phaladeepika Ch. 10 Verse 1\n"
            "[2] Saravali Ch. 32 Verse 2\n"
        )
        cleaned = _strip_trailing_references(text)
        assert cleaned == "You have great career potential with 10th lord Moon [1]."

        text_ne = (
            "तपाईंको वैवाहिक जीवन उत्तम रहनेछ [१]।\n\n"
            "सन्दर्भहरू:\n"
            "[१] फलदीपिका च. १०\n"
        )
        cleaned_ne = _strip_trailing_references(text_ne)
        assert cleaned_ne == "तपाईंको वैवाहिक जीवन उत्तम रहनेछ [१]।"

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
