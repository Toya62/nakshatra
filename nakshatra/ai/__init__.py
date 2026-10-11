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
from nakshatra.ai.retrieval import (
    BM25Index,
    ConceptMap,
    HybridRetriever,
    tokenize,
)

__all__ = [
    "MAX_CHUNK_CHARS",
    "MIN_CHUNK_CHARS",
    "BM25Index",
    "BaseEmbedder",
    "ConceptMap",
    "CorpusChunk",
    "EmbeddingStore",
    "HashingEmbedder",
    "HybridRetriever",
    "IngestReport",
    "IngestResult",
    "SearchResult",
    "SentenceTransformerEmbedder",
    "WorkMeta",
    "chunk_text",
    "ingest_corpus",
    "tag_topics",
    "tokenize",
]
