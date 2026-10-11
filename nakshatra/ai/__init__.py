"""
Nakshatra AI / RAG modules.

Optional layer (install with `pip install -e ".[ai]"` for semantic
embeddings):
- corpus: two-tier chunker for classical texts with license gate
- embeddings: NumPy vector store with embedder adapters
"""

from nakshatra.ai.corpus import (
    MAX_CHUNK_CHARS,
    MIN_CHUNK_CHARS,
    CorpusChunk,
    IngestReport,
    IngestResult,
    WorkMeta,
    chunk_text,
    ingest_corpus,
    tag_topics,
)
from nakshatra.ai.embeddings import (
    BaseEmbedder,
    EmbeddingStore,
    HashingEmbedder,
    SearchResult,
    SentenceTransformerEmbedder,
)

__all__ = [
    "MAX_CHUNK_CHARS",
    "MIN_CHUNK_CHARS",
    "BaseEmbedder",
    "CorpusChunk",
    "EmbeddingStore",
    "HashingEmbedder",
    "IngestReport",
    "IngestResult",
    "SearchResult",
    "SentenceTransformerEmbedder",
    "WorkMeta",
    "chunk_text",
    "ingest_corpus",
    "tag_topics",
]
