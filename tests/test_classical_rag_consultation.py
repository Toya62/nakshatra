"""
Tests for newly integrated classical Vedic works and deep consultation capabilities.
Verifies Phaladeepika, Saravali, Jaimini Upadesha Sutras, and Uttara Kalamrita
ingestion, retrieval precision, concept expansion, and AI answer verification.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from nakshatra.ai.corpus import tag_topics
from nakshatra.ai.retrieval import ConceptMap
from nakshatra.ai.service import RAGService
from nakshatra.ai.synthesize import FallbackSynthesizer, extract_citations


class TestClassicalWorksIngestion:
    """Verify all classical works are present in index and correctly chunked."""

    def test_manifest_contains_classical_shastras(self):
        manifest_path = Path("index/manifest.json")
        assert manifest_path.is_file(), "index/manifest.json missing"
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        works = {r["work"] for r in data.get("reports", [])}

        required_works = {
            "BPHS",
            "Phaladeepika",
            "Saravali",
            "Jaimini Upadesha Sutras",
            "Uttara Kalamrita",
            "Lal Kitab",
        }
        for rw in required_works:
            assert rw in works, f"Classical work {rw} missing from manifest"

    def test_tag_topics_with_jaimini_and_yogas(self):
        topics = tag_topics("The Atmakaraka and Amatyakaraka form a Raja Yoga in Arudha Lagna.")
        assert "Atmakaraka" in topics
        assert "Amatyakaraka" in topics
        assert "Arudha Lagna" in topics
        assert "Raja Yoga" in topics


class TestConceptMapExpansion:
    """Verify expanded concepts for deep astrological consultation."""

    def test_spirituality_concept_expansion(self):
        cm = ConceptMap()
        expanded = cm.expand("What does my chart say about my spiritual journey and moksha?")
        assert "Atmakaraka" in expanded or "Karakamsa" in expanded or "House 9" in expanded

    def test_remedies_concept_expansion(self):
        cm = ConceptMap()
        expanded = cm.expand("What are the best classical remedies and upaya for Saturn?")
        assert "Upaya" in expanded or "Dana" in expanded or "Lal Kitab" in expanded


class TestClassicalRetrievalPrecision:
    """Verify hybrid retriever locates exact classical verses."""

    @pytest.fixture
    def rag_service(self):
        return RAGService()

    def test_retrieve_phaladeepika_hamsa_yoga(self, rag_service):
        retriever = rag_service.load()
        results = retriever.search("Pancha Mahapurusha Hamsa Malavya yoga in Phaladeepika", top_k=5)
        works = [r.chunk.work for r in results]
        assert "Phaladeepika" in works

    def test_retrieve_saravali_budhaditya(self, rag_service):
        retriever = rag_service.load()
        results = retriever.search("Budhaditya conjunction of Sun and Mercury in Saravali", top_k=5)
        works = [r.chunk.work for r in results]
        assert "Saravali" in works

    def test_retrieve_jaimini_chara_karakas(self, rag_service):
        retriever = rag_service.load()
        results = retriever.search("Atmakaraka and Amatyakaraka seven karakas Jaimini", top_k=5)
        works = [r.chunk.work for r in results]
        assert "Jaimini Upadesha Sutras" in works

    def test_retrieve_uttara_kalamrita_retrograde(self, rag_service):
        retriever = rag_service.load()
        results = retriever.search(
            "Retrograde debilitated planet rules in Uttara Kalamrita", top_k=5
        )
        works = [r.chunk.work for r in results]
        assert "Uttara Kalamrita" in works


class TestAnswerCompletenessAndAccuracy:
    """Verify fallback and LLM citation synthesis adheres to standards."""

    def test_fallback_synthesizer_produces_substantial_cited_output(self):
        rag = RAGService(synthesizer=FallbackSynthesizer())
        ans, refs = rag.ask("What are the classical results of Hamsa Yoga?", top_k=2)
        assert len(ans.answer) > 200
        assert len(ans.citations) > 0
        assert "[1]" in ans.answer

    def test_anti_fatalism_and_citations_parsing(self):
        from nakshatra.ai.corpus import CorpusChunk
        from nakshatra.ai.retrieval import SearchResult

        raw_llm_text = (
            "According to Maharishi Parashara and Mantreswara in Phaladeepika [1], "
            "Saturn transiting the 8th house tests mental endurance. With patience and "
            "classical remedies like Dāna and Japa [2], this challenging phase becomes a period "
            "of profound spiritual maturity rather than ruin."
        )
        chunk1 = CorpusChunk(
            work="Phaladeepika",
            chapter="26",
            verse="2",
            text="Ashtama Shani...",
            source_file="phal.txt",
            char_start=0,
            char_end=20,
            tier="verse",
        )
        chunk2 = CorpusChunk(
            work="Lal Kitab",
            chapter="8",
            verse="3",
            text="Upayas for Saturn...",
            source_file="lk.txt",
            char_start=0,
            char_end=20,
            tier="verse",
        )
        citations = extract_citations(
            raw_llm_text,
            [
                SearchResult(chunk=chunk1, score=0.9),
                SearchResult(chunk=chunk2, score=0.8),
            ],
        )
        assert len(citations) == 2
        assert citations[0].work == "Phaladeepika"
        assert citations[1].work == "Lal Kitab"
