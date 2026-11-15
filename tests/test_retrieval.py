"""
Tests for hybrid BM25 + dense retrieval with RRF fusion
and the Bhava/Karaka concept map.
"""

from __future__ import annotations

from nakshatra.ai.corpus import CorpusChunk
from nakshatra.ai.embeddings import EmbeddingStore, HashingEmbedder
from nakshatra.ai.retrieval import (
    BM25Index,
    ConceptMap,
    HybridRetriever,
    tokenize,
)


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


class TestTokenize:
    """BM25 tokenizer."""

    def test_lowercase_alphanumeric(self):
        assert tokenize("The Sun-in-the 10th House!") == [
            "the",
            "sun",
            "in",
            "the",
            "10",
            "house",
        ]

    def test_ordinal_suffixes_stripped(self):
        assert tokenize("1st 2nd 3rd 10th 21st") == ["1", "2", "3", "10", "21"]

    def test_words_without_ordinals_unchanged(self):
        assert tokenize("with the fourth house") == [
            "with",
            "the",
            "fourth",
            "house",
        ]

    def test_empty_text(self):
        assert tokenize("") == []


class TestBM25Index:
    """Okapi BM25 lexical index."""

    def test_ranks_relevant_chunks(self):
        chunks = [
            _chunk(verse="1", text="The Sun in the 10th house gives career"),
            _chunk(verse="2", text="The Moon in the 4th house gives comfort"),
        ]
        index = BM25Index(chunks)
        hits = index.search("Sun career")
        assert hits
        assert hits[0][0] == 0
        assert hits[0][1] > 0

    def test_ordinal_query_matches_text(self):
        chunks = [
            _chunk(verse="1", text="The planet in the 10th house"),
            _chunk(verse="2", text="The planet in the 7th house"),
        ]
        index = BM25Index(chunks)
        hits = index.search("House 10")
        assert hits[0][0] == 0

    def test_empty_index(self):
        index = BM25Index([])
        assert len(index) == 0
        assert index.search("Sun") == []
        assert index.scores("Sun").size == 0

    def test_no_match_returns_empty(self):
        chunks = [_chunk(text="The Sun in the first house.")]
        index = BM25Index(chunks)
        assert index.search("zzzqqq") == []

    def test_scores_parallel_to_chunks(self):
        chunks = [
            _chunk(verse="1", text="Venus in the 7th house"),
            _chunk(verse="2", text="Mars in the 6th house"),
        ]
        index = BM25Index(chunks)
        scores = index.scores("Venus")
        assert scores.shape == (2,)
        assert scores[0] > scores[1]


class TestConceptMap:
    """Bhava/Karaka concept expansion."""

    def setup_method(self) -> None:
        self.concept_map = ConceptMap()

    def test_career_expansion(self):
        expanded = self.concept_map.expand("What is my career?")
        for term in ["House 10", "Sun", "Saturn", "D10"]:
            assert term in expanded

    def test_marriage_expansion(self):
        expanded = self.concept_map.expand("When will I marry?")
        for term in ["House 7", "Venus", "Jupiter"]:
            assert term in expanded

    def test_wealth_expansion(self):
        expanded = self.concept_map.expand("Will I be wealthy?")
        for term in ["House 2", "House 11", "Dhana Yoga"]:
            assert term in expanded

    def test_health_expansion(self):
        expanded = self.concept_map.expand("Health concerns")
        for term in ["Lagna", "House 6", "House 8"]:
            assert term in expanded

    def test_unrelated_query_unchanged(self):
        query = "tell me about Rohini nakshatra"
        assert self.concept_map.expand(query) == query

    def test_case_insensitive(self):
        assert "House 7" in self.concept_map.expand("MARRIAGE timing")

    def test_trigger_synonym(self):
        assert "House 10" in self.concept_map.expand("my job prospects")

    def test_no_duplicate_terms(self):
        expanded = self.concept_map.expand("career and job")
        assert expanded.count("House 10") == 1
        assert expanded.count("Sun") == 1

    def test_query_preserved_in_expansion(self):
        expanded = self.concept_map.expand("career")
        assert expanded.startswith("career ")


class TestHybridRetriever:
    """Hybrid BM25 + dense retrieval with RRF fusion."""

    def test_bm25_only_retrieval(self):
        chunks = [
            _chunk(verse="1", text="The Sun in the 10th house gives career"),
            _chunk(verse="2", text="The Moon in the 4th house gives comfort"),
        ]
        store = EmbeddingStore()
        store.add_records(chunks)
        retriever = HybridRetriever(store)  # no embedder
        assert len(retriever) == 2
        results = retriever.search("career")
        assert results
        assert results[0].chunk.verse == "1"
        assert results[0].score > 0

    def test_hybrid_retrieval(self):
        chunks = [
            _chunk(verse="1", text="The Sun in the 10th house gives career"),
            _chunk(verse="2", text="The Moon in the 4th house gives comfort"),
            _chunk(verse="3", text="Mars in the 6th house causes disputes"),
        ]
        embedder = HashingEmbedder(dim=64)
        store = EmbeddingStore()
        store.build(chunks, embedder)
        retriever = HybridRetriever(store, embedder)
        results = retriever.search("career", top_k=2)
        assert len(results) == 2
        assert results[0].chunk.verse == "1"
        assert all(isinstance(r.score, float) for r in results)

    def test_concept_expansion_drives_retrieval(self):
        chunks = [
            _chunk(verse="1", text="Saturn in the 10th house makes a leader"),
            _chunk(verse="2", text="The Moon in Rohini is very auspicious"),
        ]
        embedder = HashingEmbedder(dim=128)
        store = EmbeddingStore()
        store.build(chunks, embedder)
        retriever = HybridRetriever(store, embedder)
        # "job" triggers the career concept map (Saturn, House 10)
        results = retriever.search("Will I get a good job?")
        assert results[0].chunk.verse == "1"

    def test_marriage_retrieval(self):
        chunks = [
            _chunk(verse="1", text="Venus in the 7th house blesses marriage"),
            _chunk(verse="2", text="The Sun in the 10th house gives fame"),
        ]
        embedder = HashingEmbedder(dim=128)
        store = EmbeddingStore()
        store.build(chunks, embedder)
        retriever = HybridRetriever(store, embedder)
        results = retriever.search("marriage")
        assert results[0].chunk.verse == "1"

    def test_top_k_bounds(self):
        chunks = [_chunk(verse=str(i), text=f"Verse {i} about the Sun and Moon") for i in range(10)]
        store = EmbeddingStore()
        store.add_records(chunks)
        retriever = HybridRetriever(store)
        assert len(retriever.search("Sun", top_k=3)) == 3
        assert len(retriever.search("Sun", top_k=50)) == 10

    def test_empty_store(self):
        retriever = HybridRetriever(EmbeddingStore())
        assert len(retriever) == 0
        assert retriever.search("career") == []

    def test_results_sorted_by_score(self):
        chunks = [
            _chunk(verse="1", text="The Sun in the 10th house gives career"),
            _chunk(verse="2", text="The Sun in the 4th house"),
        ]
        store = EmbeddingStore()
        store.add_records(chunks)
        retriever = HybridRetriever(store)
        results = retriever.search("career Sun")
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_rrf_fusion_prefers_double_ranked_chunk(self):
        # Chunk 0 is top-ranked by both lexical and dense (via shared
        # hash tokens), chunk 1 only lexically.
        chunks = [
            _chunk(verse="1", text="Sun career profession work job"),
            _chunk(verse="2", text="career work"),
        ]
        embedder = HashingEmbedder(dim=64)
        store = EmbeddingStore()
        store.build(chunks, embedder)
        retriever = HybridRetriever(store, embedder)
        results = retriever.search("career job profession")
        assert results[0].chunk.verse == "1"

    def test_romanized_nepali_and_devanagari_retrieval(self):
        chunks = [
            _chunk(verse="1", text="Venus in House 7 blesses marriage and Navamsa"),
            _chunk(verse="2", text="Sun in House 10 gives career and Karma"),
        ]
        store = EmbeddingStore()
        store.add_records(chunks)
        retriever = HybridRetriever(store)

        # Romanized Nepali query "mero vivah kahile hunchha" triggers marriage concept
        results_roman = retriever.search("mero vivah kahile hunchha")
        assert len(results_roman) > 0
        assert results_roman[0].chunk.verse == "1"

        # Devanagari Nepali query "मेरो बिहे कहिले हुन्छ" triggers marriage concept
        results_ne = retriever.search("मेरो बिहे कहिले हुन्छ")
        assert len(results_ne) > 0
        assert results_ne[0].chunk.verse == "1"
