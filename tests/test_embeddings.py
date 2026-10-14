"""
Tests for the NumPy embedding store and embedder adapters.
"""

from __future__ import annotations

import importlib.util
import math

import numpy as np
import pytest

from nakshatra.ai.corpus import CorpusChunk
from nakshatra.ai.embeddings import (
    EmbeddingStore,
    HashingEmbedder,
    SentenceTransformerEmbedder,
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


class TestHashingEmbedder:
    """Deterministic hash-bag embedder."""

    def test_dim_property(self):
        embedder = HashingEmbedder(dim=64)
        assert embedder.dim == 64

    def test_deterministic(self):
        embedder = HashingEmbedder(dim=128)
        vectors = embedder.embed(["the Sun in the first house"])
        again = embedder.embed(["the Sun in the first house"])
        assert np.array_equal(vectors, again)

    def test_batch_shape(self):
        embedder = HashingEmbedder(dim=64)
        vectors = embedder.embed(["one", "two", "three"])
        assert vectors.shape == (3, 64)

    def test_empty_batch(self):
        embedder = HashingEmbedder(dim=64)
        vectors = embedder.embed([])
        assert vectors.shape == (0, 64)

    def test_different_token_sets_differ(self):
        embedder = HashingEmbedder(dim=256)
        a = embedder.embed(["Sun Moon Mars"])
        b = embedder.embed(["Jupiter Venus Saturn"])
        assert not np.array_equal(a, b)

    def test_bag_of_words_order_independent(self):
        embedder = HashingEmbedder(dim=256)
        a = embedder.embed(["Sun Moon"])
        b = embedder.embed(["Moon Sun"])
        assert np.array_equal(a, b)

    def test_embed_query(self):
        embedder = HashingEmbedder(dim=64)
        vector = embedder.embed_query("The Moon in Rohini.")
        assert vector.shape == (64,)

    def test_cross_process_stable_hash(self):
        # md5-based hashing must not depend on PYTHONHASHSEED
        embedder = HashingEmbedder(dim=256)
        vector = embedder.embed_query("Rohini")
        assert vector.shape == (256,)
        assert float(np.linalg.norm(vector)) > 0.0


class TestEmbeddingStore:
    """NumPy dot-product vector store."""

    def test_add_and_search_ranking(self):
        store = EmbeddingStore()
        chunks = [_chunk(verse="1"), _chunk(verse="2"), _chunk(verse="3")]
        vectors = np.array(
            [
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 0.0, 1.0],
            ]
        )
        store.add(chunks, vectors)
        results = store.search(np.array([1.0, 0.1, 0.0]), top_k=2)
        assert len(results) == 2
        assert results[0].chunk.verse == "1"
        assert results[1].chunk.verse == "2"
        assert results[0].score > results[1].score
        assert results[0].score == pytest.approx(1.0 / math.sqrt(1.01), abs=1e-5)

    def test_identical_direction_scores_one(self):
        store = EmbeddingStore()
        store.add([_chunk()], np.array([[3.0, 4.0]]))
        results = store.search(np.array([30.0, 40.0]))
        assert results[0].score == pytest.approx(1.0)

    def test_orthogonal_scores_zero(self):
        store = EmbeddingStore()
        store.add([_chunk()], np.array([[1.0, 0.0]]))
        results = store.search(np.array([0.0, 5.0]))
        assert results[0].score == pytest.approx(0.0)

    def test_len_and_dim(self):
        store = EmbeddingStore()
        assert len(store) == 0
        assert store.dim == 0
        store.add([_chunk()], np.array([[1.0, 0.0, 0.0]]))
        assert len(store) == 1
        assert store.dim == 3

    def test_incremental_add(self):
        store = EmbeddingStore()
        store.add([_chunk(verse="1")], np.array([[1.0, 0.0]]))
        store.add([_chunk(verse="2")], np.array([[0.0, 1.0]]))
        assert len(store) == 2
        assert store.dim == 2
        results = store.search(np.array([0.0, 1.0]))
        assert results[0].chunk.verse == "2"

    def test_count_mismatch_raises(self):
        store = EmbeddingStore()
        with pytest.raises(ValueError, match="count mismatch"):
            store.add([_chunk(), _chunk()], np.array([[1.0, 0.0]]))

    def test_dimension_mismatch_raises(self):
        store = EmbeddingStore()
        store.add([_chunk()], np.array([[1.0, 0.0]]))
        with pytest.raises(ValueError, match="Dimension mismatch"):
            store.add([_chunk()], np.array([[1.0, 0.0, 0.0]]))

    def test_empty_store_search(self):
        store = EmbeddingStore()
        assert store.search(np.array([1.0, 0.0])) == []

    def test_zero_query_vector(self):
        store = EmbeddingStore()
        store.add([_chunk()], np.array([[1.0, 0.0]]))
        assert store.search(np.array([0.0, 0.0])) == []

    def test_top_k_bounds(self):
        store = EmbeddingStore()
        chunks = [_chunk(verse=str(i)) for i in range(10)]
        vectors = np.eye(10, dtype=np.float32)
        store.add(chunks, vectors)
        assert len(store.search(np.eye(10, dtype=np.float32)[0], top_k=3)) == 3
        assert len(store.search(np.eye(10, dtype=np.float32)[0], top_k=50)) == 10

    def test_build_with_hashing_embedder(self):
        store = EmbeddingStore()
        chunks = [
            _chunk(verse="1", text="The Sun rules the first house"),
            _chunk(verse="2", text="The Moon in Rohini nakshatra"),
            _chunk(verse="3", text="Mars aspects the seventh house"),
        ]
        store.build(chunks, HashingEmbedder(dim=64))
        assert len(store) == 3
        assert store.dim == 64
        results = store.search(HashingEmbedder(dim=64).embed_query("Sun"))
        assert len(results) == 3
        assert all(isinstance(r.score, float) for r in results)

    def test_save_load_roundtrip(self, tmp_path):
        store = EmbeddingStore()
        chunks = [
            _chunk(verse="1", text="The Sun rules the first house"),
            _chunk(verse="2", text="The Moon in Rohini nakshatra"),
        ]
        embedder = HashingEmbedder(dim=64)
        store.build(chunks, embedder)
        store.save(tmp_path)

        loaded = EmbeddingStore.load(tmp_path)
        assert len(loaded) == len(store)
        assert loaded.dim == store.dim
        query = embedder.embed_query("The Sun rules the first house")
        original = store.search(query, top_k=1)
        restored = loaded.search(query, top_k=1)
        assert restored[0].chunk.verse == original[0].chunk.verse
        assert restored[0].score == pytest.approx(original[0].score)
        assert restored[0].chunk.text == original[0].chunk.text

    def test_save_load_empty_store(self, tmp_path):
        store = EmbeddingStore()
        store.save(tmp_path)
        loaded = EmbeddingStore.load(tmp_path)
        assert len(loaded) == 0
        assert loaded.search(np.array([1.0])) == []


class TestSentenceTransformerEmbedder:
    """Semantic embedder adapter (requires [ai] extra)."""

    def test_missing_dependency_raises(self):
        if importlib.util.find_spec("sentence_transformers") is not None:
            pytest.skip("sentence-transformers is installed")
        with pytest.raises(ImportError, match=r"nakshatra\[ai\]"):
            SentenceTransformerEmbedder()
