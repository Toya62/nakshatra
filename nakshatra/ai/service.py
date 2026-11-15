"""
Nakshatra RAG Service - stateful retrieval + synthesis pipeline.

RAGService ties together corpus ingestion, the embedding store,
hybrid BM25/dense retrieval, and cited answer synthesis. The
FastAPI app keeps one module-level instance; embedder and
synthesizer can be injected for tests or alternative backends.
"""

from __future__ import annotations

import importlib.util
import os
from collections.abc import Iterator
from pathlib import Path
from typing import Literal

from nakshatra.ai.corpus import CorpusChunk, IngestResult, ingest_corpus
from nakshatra.ai.embeddings import (
    BaseEmbedder,
    EmbeddingStore,
    SentenceTransformerEmbedder,
)
from nakshatra.ai.retrieval import HybridRetriever, SearchResult
from nakshatra.ai.synthesize import (
    Answer,
    BaseSynthesizer,
    FallbackSynthesizer,
    LLMSynthesizer,
    OllamaSynthesizer,
)

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

DEFAULT_CORPUS_DIR = "corpus"
DEFAULT_INDEX_DIR = "index"


def _module_available(name: str) -> bool:
    """Check importability without triggering parent-package errors."""
    try:
        return importlib.util.find_spec(name) is not None
    except ImportError:
        return False


def _default_embedder() -> BaseEmbedder | None:
    """Semantic embedder when sentence-transformers is installed."""
    if _module_available("sentence_transformers"):
        return SentenceTransformerEmbedder()
    return None


def _default_synthesizer() -> BaseSynthesizer:
    """LLM synthesizer priority: explicit AI_PROVIDER -> Gemini -> Router/OpenAI -> Ollama -> Fallback."""
    ai_provider = (os.environ.get("AI_PROVIDER") or "").lower()
    google_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    openai_base_url = os.environ.get("OPENAI_BASE_URL")

    # If explicitly set to google, or if Google API key is available and provider is not forced to openai
    if (ai_provider == "google" or (google_key and ai_provider != "openai" and not (ai_provider == "router"))) and _module_available("google.genai"):
        if google_key:
            return LLMSynthesizer(provider="google", model="gemini-3.8-flash", api_key=google_key)

    if (openai_base_url or ai_provider in ("openai", "router", "9router")) and _module_available("openai"):
        model = os.environ.get("OPENAI_MODEL", "ag/gemini-3.8-flash")
        api_key = os.environ.get("OPENAI_API_KEY")
        return LLMSynthesizer(provider="openai", model=model, api_key=api_key, base_url=openai_base_url)

    if google_key and _module_available("google.genai"):
        return LLMSynthesizer(provider="google", model="gemini-3.8-flash", api_key=google_key)

    if os.environ.get("OPENAI_API_KEY") and _module_available("openai"):
        model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        return LLMSynthesizer(provider="openai", model=model)

    if (
        os.environ.get("USE_OLLAMA")
        or os.environ.get("OLLAMA_HOST")
        or os.environ.get("OLLAMA_MODEL")
    ) and _module_available("openai"):
        return OllamaSynthesizer(
            model=os.environ.get("OLLAMA_MODEL", "qwen2.5:3b"),
            base_url=os.environ.get("OLLAMA_HOST", "http://localhost:11434/v1"),
        )

    return FallbackSynthesizer()


def _read_corpus_chunks(index_dir: str | Path) -> list[CorpusChunk]:
    """Read chunks from a persisted corpus.jsonl index."""
    path = Path(index_dir) / "corpus.jsonl"
    if not path.is_file():
        return []
    chunks: list[CorpusChunk] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            chunks.append(CorpusChunk.model_validate_json(line))
    return chunks


class RAGService:
    """Stateful RAG pipeline: ingest, load, ask.

    Parameters
    ----------
    embedder:
        Embedder for dense retrieval. ``None`` (default)
        auto-detects sentence-transformers; ``False`` forces
        BM25-only mode; an instance is used as given.
    synthesizer:
        Answer synthesizer. ``None`` (default) auto-detects
        an LLM provider from API keys, falling back to
        verbatim reference synthesis.
    """

    def __init__(
        self,
        embedder: BaseEmbedder | None | Literal[False] = None,
        synthesizer: BaseSynthesizer | None = None,
    ) -> None:
        self._embedder = embedder
        self._synthesizer = synthesizer
        self._retrievers: dict[str, HybridRetriever] = {}

    def _get_embedder(self) -> BaseEmbedder | None:
        if self._embedder is None:
            self._embedder = _default_embedder()
        if self._embedder is False:
            return None
        return self._embedder

    def _get_synthesizer(self) -> BaseSynthesizer:
        if self._synthesizer is None:
            self._synthesizer = _default_synthesizer()
        return self._synthesizer

    @property
    def embedder(self) -> BaseEmbedder | None:
        """The active embedder (None in BM25-only mode)."""
        return self._get_embedder()

    def ingest(
        self,
        corpus_dir: str | Path = DEFAULT_CORPUS_DIR,
        index_dir: str | Path = DEFAULT_INDEX_DIR,
    ) -> IngestResult:
        """Ingest a corpus directory and (re)build the index.

        Writes corpus.jsonl + manifest.json via ingest_corpus,
        then persists an EmbeddingStore (with vectors when an
        embedder is available, records-only otherwise).
        """
        result = ingest_corpus(corpus_dir, index_dir)
        chunks = _read_corpus_chunks(index_dir)
        if chunks:
            store = EmbeddingStore()
            embedder = self._get_embedder()
            if embedder is not None:
                store.build(chunks, embedder)
            else:
                store.add_records(chunks)
            store.save(index_dir)
        self._retrievers.pop(str(Path(index_dir).resolve()), None)
        return result

    def load(self, index_dir: str | Path = DEFAULT_INDEX_DIR) -> HybridRetriever:
        """Load (and cache) a retrieval index from disk."""
        key = str(Path(index_dir).resolve())
        if key not in self._retrievers:
            index_path = Path(index_dir)
            if (index_path / "vectors.npy").is_file():
                store = EmbeddingStore.load(index_dir)
            else:
                # CLI-ingested corpus without vectors: BM25-only
                chunks = _read_corpus_chunks(index_dir)
                if not chunks:
                    raise FileNotFoundError(
                        f"No index found at {index_dir}. Run POST /rag/ingest first."
                    )
                store = EmbeddingStore()
                store.add_records(chunks)
            self._retrievers[key] = HybridRetriever(store, embedder=self._get_embedder())
        return self._retrievers[key]

    def ask(
        self,
        question: str,
        index_dir: str | Path = DEFAULT_INDEX_DIR,
        top_k: int = 5,
        birth_context: dict | None = None,
        language: str = "en",
    ) -> tuple[Answer, list[SearchResult]]:
        """Retrieve references and synthesize a cited answer."""
        retriever = self.load(index_dir)
        results = retriever.search(question, top_k=top_k)
        answer = self._get_synthesizer().synthesize(
            question, results, birth_context=birth_context, language=language
        )
        return answer, results

    def ask_stream(
        self,
        question: str,
        index_dir: str | Path = DEFAULT_INDEX_DIR,
        top_k: int = 5,
        birth_context: dict | None = None,
        language: str = "en",
    ) -> tuple[Iterator[str], list[SearchResult], BaseSynthesizer]:
        """Retrieve references and stream synthesized answer tokens."""
        retriever = self.load(index_dir)
        results = retriever.search(question, top_k=top_k)
        synthesizer = self._get_synthesizer()
        stream = synthesizer.synthesize_stream(
            question, results, birth_context=birth_context, language=language
        )
        return stream, results, synthesizer
