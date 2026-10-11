"""
Nakshatra Embeddings - NumPy vector store for corpus chunks.

- BaseEmbedder: embedder interface (dim + embed/embed_query)
- SentenceTransformerEmbedder: adapter over sentence-transformers
  (optional [ai] extra, lazily imported)
- HashingEmbedder: deterministic hash-bag embedder for tests and
  zero-dependency environments
- EmbeddingStore: L2-normalized NumPy dot-product (cosine) store with
  save/load persistence
"""

from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import numpy as np
from pydantic import BaseModel, Field

from nakshatra.ai.corpus import CorpusChunk


class BaseEmbedder(ABC):
    """Interface for text embedders."""

    @property
    @abstractmethod
    def dim(self) -> int:
        """Dimensionality of embedding vectors."""

    @abstractmethod
    def embed(self, texts: list[str]) -> np.ndarray:
        """Embed a batch of texts into a (n, dim) array."""

    def embed_query(self, text: str) -> np.ndarray:
        """Embed a single query string."""
        vector: np.ndarray = self.embed([text])[0]
        return vector


class SentenceTransformerEmbedder(BaseEmbedder):
    """Semantic embedder backed by sentence-transformers.

    Requires the optional [ai] extra: pip install 'nakshatra[ai]'
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as e:
            raise ImportError(
                "sentence-transformers is required for semantic embeddings. "
                "Install it with: pip install 'nakshatra[ai]'"
            ) from e
        self.model_name = model_name
        self._model = SentenceTransformer(model_name)

    @property
    def dim(self) -> int:
        return int(self._model.get_sentence_embedding_dimension())

    def embed(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dim), dtype=np.float32)
        vectors = self._model.encode(
            texts, normalize_embeddings=True, show_progress_bar=False
        )
        return np.asarray(vectors, dtype=np.float32)


class HashingEmbedder(BaseEmbedder):
    """Deterministic hash-bag embedder (tests / zero-dependency fallback).

    Tokens are hashed into a fixed-size bag-of-words vector. Not
    semantically meaningful, but deterministic and dependency-free.
    """

    def __init__(self, dim: int = 256) -> None:
        self._dim = dim

    @property
    def dim(self) -> int:
        return self._dim

    def embed(self, texts: list[str]) -> np.ndarray:
        vectors = np.zeros((len(texts), self._dim), dtype=np.float32)
        for row, text in enumerate(texts):
            for token in text.lower().split():
                digest = hashlib.md5(token.encode("utf-8")).hexdigest()
                index = int(digest, 16) % self._dim
                vectors[row, index] += 1.0
        return vectors


class SearchResult(BaseModel):
    """A retrieved chunk with its similarity score."""

    chunk: CorpusChunk
    score: float = Field(..., description="Cosine similarity in [-1, 1]")


class EmbeddingStore:
    """NumPy dot-product vector store with cosine-similarity search.

    Vectors are L2-normalized on insert, so dot product equals cosine
    similarity. Records are full CorpusChunk dumps, making the store
    self-contained at query time.
    """

    def __init__(self) -> None:
        self._vectors: np.ndarray = np.empty((0, 0), dtype=np.float32)
        self._records: list[dict[str, Any]] = []
        self._dim: int = 0

    def __len__(self) -> int:
        return len(self._records)

    @property
    def dim(self) -> int:
        return self._dim

    def add(self, chunks: list[CorpusChunk], vectors: np.ndarray) -> None:
        """Add chunks with their embedding vectors."""
        if not chunks:
            return
        vectors = np.atleast_2d(np.asarray(vectors, dtype=np.float32))
        if vectors.shape[0] != len(chunks):
            raise ValueError(
                f"Chunk/vector count mismatch: {len(chunks)} chunks, "
                f"{vectors.shape[0]} vectors"
            )
        if self._dim and vectors.shape[1] != self._dim:
            raise ValueError(
                f"Dimension mismatch: store has {self._dim}, "
                f"got {vectors.shape[1]}"
            )
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms = np.where(norms == 0.0, 1.0, norms)
        vectors = vectors / norms
        if self._records:
            self._vectors = np.vstack([self._vectors, vectors])
        else:
            self._vectors = vectors
        self._records.extend(chunk.model_dump() for chunk in chunks)
        self._dim = int(vectors.shape[1])

    def build(
        self,
        chunks: list[CorpusChunk],
        embedder: BaseEmbedder,
        batch_size: int = 32,
    ) -> None:
        """Embed chunk texts and add them to the store."""
        texts = [chunk.text for chunk in chunks]
        for start in range(0, len(texts), batch_size):
            batch = texts[start : start + batch_size]
            vectors = embedder.embed(batch)
            self.add(chunks[start : start + batch_size], vectors)

    def search(self, query: np.ndarray, top_k: int = 5) -> list[SearchResult]:
        """Return the top_k most similar chunks by cosine similarity."""
        if not self._records:
            return []
        query_vec = np.asarray(query, dtype=np.float32).ravel()
        norm = float(np.linalg.norm(query_vec))
        if norm == 0.0:
            return []
        query_vec = query_vec / norm
        scores = self._vectors @ query_vec
        top_indices = np.argsort(-scores)[:top_k]
        return [
            SearchResult(
                chunk=CorpusChunk(**self._records[int(index)]),
                score=float(scores[int(index)]),
            )
            for index in top_indices
        ]

    def save(self, index_dir: str | Path) -> None:
        """Persist the store to index_dir (vectors.npy + records.json)."""
        index_path = Path(index_dir)
        index_path.mkdir(parents=True, exist_ok=True)
        np.save(index_path / "vectors.npy", self._vectors)
        (index_path / "records.json").write_text(
            json.dumps(self._records), encoding="utf-8"
        )

    @classmethod
    def load(cls, index_dir: str | Path) -> EmbeddingStore:
        """Load a store persisted by save()."""
        index_path = Path(index_dir)
        vectors = np.load(index_path / "vectors.npy")
        records = json.loads(
            (index_path / "records.json").read_text(encoding="utf-8")
        )
        store = cls()
        store._vectors = np.atleast_2d(np.asarray(vectors, dtype=np.float32))
        store._records = records
        store._dim = int(vectors.shape[1]) if vectors.size else 0
        return store
