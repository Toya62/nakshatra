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
from nakshatra.ai.service import (
    DEFAULT_CORPUS_DIR,
    DEFAULT_INDEX_DIR,
    RAGService,
)
from nakshatra.ai.splitter import (
    HeaderTracker,
    TextSplitter,
)
from nakshatra.ai.synthesize import (
    Answer,
    BaseSynthesizer,
    Citation,
    FallbackSynthesizer,
    LLMSynthesizer,
    build_prompt,
    extract_citations,
)

__all__ = [
    "DEFAULT_CORPUS_DIR",
    "DEFAULT_INDEX_DIR",
    "MAX_CHUNK_CHARS",
    "MIN_CHUNK_CHARS",
    "Answer",
    "BM25Index",
    "BaseEmbedder",
    "BaseSynthesizer",
    "Citation",
    "ConceptMap",
    "CorpusChunk",
    "EmbeddingStore",
    "FallbackSynthesizer",
    "HashingEmbedder",
    "HeaderTracker",
    "HybridRetriever",
    "IngestReport",
    "IngestResult",
    "LLMSynthesizer",
    "RAGService",
    "SearchResult",
    "SentenceTransformerEmbedder",
    "TextSplitter",
    "WorkMeta",
    "build_prompt",
    "chunk_text",
    "extract_citations",
    "ingest_corpus",
    "tag_topics",
    "tokenize",
]
