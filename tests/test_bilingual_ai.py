"""Tests for bilingual English/Nepali AI synthesis and consultation."""

from nakshatra.ai.corpus import CorpusChunk
from nakshatra.ai.retrieval import SearchResult
from nakshatra.ai.synthesize import (
    FallbackSynthesizer,
    build_prompt,
    get_system_prompt,
)
from nakshatra.api import RAGAskRequest


def _chunk(work="BPHS", text="The Sun in Tanu Bhava"):
    return CorpusChunk(
        work=work,
        chapter="1",
        verse="1",
        chunk_id=f"{work}-1-1-0",
        text=text,
        topics=["Sun"],
        source_file="test.txt",
        char_start=0,
        char_end=len(text),
        tier="verse",
    )


def test_get_system_prompt_languages():
    en_prompt = get_system_prompt("en")
    assert "You are a revered Vedic Astrologer" in en_prompt
    assert "Maharishi Parashara" in en_prompt

    ne_prompt = get_system_prompt("ne")
    assert "तपाईं एक सिद्ध, पूज्य तथा धर्मनिष्ठ वैदिक ज्योतिषाचार्य हुनुहुन्छ" in ne_prompt
    assert "वृहत् पराशर होरा शास्त्र" in ne_prompt
    assert "१. भाषा र आदरार्थी शैली" in ne_prompt
    assert "९. स्पष्ट कालक्रम तथा फलादेश संश्लेषण" in ne_prompt

    nepali_prompt = get_system_prompt("nepali")
    assert nepali_prompt == ne_prompt


def test_build_prompt_bilingual():
    results = [SearchResult(chunk=_chunk(), score=0.9)]

    en_prompt = build_prompt("Tell me about Sun", results, language="en")
    assert "भाषा निर्देशन" not in en_prompt
    assert "Question: Tell me about Sun" in en_prompt

    ne_prompt = build_prompt("सूर्यको फल भन्नुहोस्", results, language="ne")
    assert "भाषा निर्देशन: सोधकर्ताको भाषा नेपाली भएकाले" in ne_prompt
    assert "Question: सूर्यको फल भन्नुहोस्" in ne_prompt


def test_fallback_synthesizer_bilingual():
    fb = FallbackSynthesizer()
    results = [SearchResult(chunk=_chunk(text="सूर्य लग्नमा हुँदा तेजिलो हुन्छ"), score=0.95)]

    # English fallback
    en_ans = fb.synthesize("Sun in lagna?", results, language="en")
    assert "Regarding your question 'Sun in lagna?':" in en_ans.answer
    assert "[1] BPHS Chapter 1 Verse 1" in en_ans.answer

    # Nepali fallback
    ne_ans = fb.synthesize("सूर्य लग्नमा?", results, language="ne")
    assert "तपाईंको प्रश्न 'सूर्य लग्नमा?' सम्बन्धी शास्त्रीय सन्दर्भहरू:" in ne_ans.answer

    # Empty results
    empty_ne = fb.synthesize("केही छैन", [], language="ne")
    assert "कुनै सान्दर्भिक श्लोक वा सन्दर्भ फेला परेन" in empty_ne.answer


def test_rag_ask_request_language_field():
    req_default = RAGAskRequest(question="Career question")
    assert req_default.language == "en"

    req_ne = RAGAskRequest(question="करियर", language="ne")
    assert req_ne.language == "ne"
