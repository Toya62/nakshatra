"""
Nakshatra AI / RAG modules.

Optional layer (install with `pip install -e ".[ai]"`):
- corpus: two-tier chunker for classical texts with license gate
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

__all__ = [
    "MAX_CHUNK_CHARS",
    "MIN_CHUNK_CHARS",
    "CorpusChunk",
    "IngestReport",
    "IngestResult",
    "WorkMeta",
    "chunk_text",
    "ingest_corpus",
    "tag_topics",
]
