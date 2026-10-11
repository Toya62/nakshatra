"""
Tests for the RAG service and /rag API endpoints.
"""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

import nakshatra.api as api_module
from nakshatra.ai.embeddings import HashingEmbedder
from nakshatra.ai.service import RAGService
from nakshatra.ai.synthesize import FallbackSynthesizer
from nakshatra.api import app


@pytest.fixture()
def corpus(tmp_path):
    """A minimal licensed corpus with two verses."""
    work_dir = tmp_path / "corpus" / "bphs"
    work_dir.mkdir(parents=True)
    (work_dir / "meta.json").write_text(
        json.dumps(
            {"work": "BPHS", "translator": "R. Santhanam",
             "license": "public domain"}
        ),
        encoding="utf-8",
    )
    (work_dir / "bphs.txt").write_text(
        "Chapter 1, Verse 1: The Sun in the first house gives career success.\n"
        "Chapter 1, Verse 2: The Moon in the second house gives wealth.\n",
        encoding="utf-8",
    )
    return tmp_path / "corpus"


@pytest.fixture()
def service():
    """Deterministic RAG service (hash embeddings, fallback synthesis)."""
    return RAGService(
        embedder=HashingEmbedder(), synthesizer=FallbackSynthesizer()
    )


@pytest.fixture()
def rag_client(tmp_path, monkeypatch):
    """TestClient with an isolated RAG service instance."""
    monkeypatch.setattr(
        api_module,
        "_rag_service",
        RAGService(
            embedder=HashingEmbedder(), synthesizer=FallbackSynthesizer()
        ),
    )
    return TestClient(app)


class TestRAGService:
    """Service-level ingest/load/ask behavior."""

    def test_ingest_builds_index(self, corpus, tmp_path, service):
        index_dir = tmp_path / "index"
        result = service.ingest(corpus, index_dir)
        assert result.total_chunks == 2
        assert result.total_files == 1
        assert (index_dir / "corpus.jsonl").is_file()
        assert (index_dir / "manifest.json").is_file()
        assert (index_dir / "vectors.npy").is_file()
        assert (index_dir / "records.json").is_file()

    def test_ask_returns_answer_and_references(
        self, corpus, tmp_path, service
    ):
        index_dir = tmp_path / "index"
        service.ingest(corpus, index_dir)
        answer, references = service.ask(
            "What about my career?", index_dir=index_dir
        )
        assert answer.question == "What about my career?"
        assert references
        assert answer.citations

    def test_ask_missing_index_raises(self, tmp_path, service):
        with pytest.raises(FileNotFoundError, match="Run POST /rag/ingest"):
            service.ask("Q", index_dir=tmp_path / "nonexistent")

    def test_ask_with_birth_context(self, corpus, tmp_path, service):
        index_dir = tmp_path / "index"
        service.ingest(corpus, index_dir)
        answer, references = service.ask(
            "Q",
            index_dir=index_dir,
            birth_context={"ascendant": "Aries"},
        )
        assert answer.answer
        assert references

    def test_load_caches_retriever(self, corpus, tmp_path, service):
        index_dir = tmp_path / "index"
        service.ingest(corpus, index_dir)
        assert service.load(index_dir) is service.load(index_dir)

    def test_ingest_invalidates_cache(self, corpus, tmp_path, service):
        index_dir = tmp_path / "index"
        service.ingest(corpus, index_dir)
        first = service.load(index_dir)
        service.ingest(corpus, index_dir)
        assert service.load(index_dir) is not first

    def test_bm25_only_mode(self, corpus, tmp_path):
        """embedder=False forces BM25-only (records, no vectors)."""
        service = RAGService(
            embedder=False, synthesizer=FallbackSynthesizer()
        )
        index_dir = tmp_path / "index"
        result = service.ingest(corpus, index_dir)
        assert result.total_chunks == 2
        assert service.embedder is None
        answer, references = service.ask("career?", index_dir=index_dir)
        assert references
        assert answer.citations

    def test_load_corpus_without_vectors(self, corpus, tmp_path, service):
        """A CLI-ingested corpus.jsonl (no vectors.npy) loads BM25-only."""
        index_dir = tmp_path / "index"
        service.ingest(corpus, index_dir)
        (index_dir / "vectors.npy").unlink()
        (index_dir / "records.json").unlink()
        retriever = service.load(index_dir)
        assert len(retriever) == 2

    def test_default_synthesizer_fallback(self, monkeypatch):
        """Without API keys the default synthesizer is the fallback."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        service = RAGService()
        assert isinstance(service._get_synthesizer(), FallbackSynthesizer)


class TestRAGEndpoints:
    """FastAPI /rag endpoint behavior."""

    def test_ingest_endpoint(self, rag_client, corpus, tmp_path):
        response = rag_client.post(
            "/rag/ingest",
            json={
                "corpus_dir": str(corpus),
                "index_dir": str(tmp_path / "index"),
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["total_chunks"] == 2
        assert body["data"]["total_files"] == 1
        assert body["meta"]["index_dir"] == str(tmp_path / "index")

    def test_ask_endpoint(self, rag_client, corpus, tmp_path):
        index_dir = tmp_path / "index"
        rag_client.post(
            "/rag/ingest",
            json={
                "corpus_dir": str(corpus),
                "index_dir": str(index_dir),
            },
        )
        response = rag_client.post(
            "/rag/ask",
            json={
                "question": "What about my career?",
                "index_dir": str(index_dir),
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["question"] == "What about my career?"
        assert body["data"]["model"] == "fallback"
        assert body["references"]
        assert body["data"]["citations"]

    def test_ask_without_index_returns_404(self, rag_client, tmp_path):
        response = rag_client.post(
            "/rag/ask",
            json={"question": "Q", "index_dir": str(tmp_path / "missing")},
        )
        assert response.status_code == 404

    def test_ingest_missing_corpus_returns_400(
        self, rag_client, tmp_path
    ):
        response = rag_client.post(
            "/rag/ingest",
            json={
                "corpus_dir": str(tmp_path / "missing"),
                "index_dir": "index",
            },
        )
        assert response.status_code == 400

    def test_ask_with_birth_context(self, rag_client, corpus, tmp_path):
        index_dir = tmp_path / "index"
        rag_client.post(
            "/rag/ingest",
            json={
                "corpus_dir": str(corpus),
                "index_dir": str(index_dir),
            },
        )
        response = rag_client.post(
            "/rag/ask",
            json={
                "question": "What about my career?",
                "index_dir": str(index_dir),
                "birth": {
                    "year": 1990,
                    "month": 1,
                    "day": 1,
                    "hour": 6,
                    "minute": 0,
                    "latitude": 28.6,
                    "longitude": 77.2,
                    "timezone": "Asia/Kolkata",
                },
            },
        )
        assert response.status_code == 200
        assert response.json()["references"]

    def test_ask_empty_question_returns_422(self, rag_client):
        response = rag_client.post(
            "/rag/ask", json={"question": "", "index_dir": "index"}
        )
        assert response.status_code == 422

    def test_root_lists_rag_endpoints(self, rag_client):
        body = rag_client.get("/").json()
        assert "POST /rag/ingest" in body["endpoints"]
        assert "POST /rag/ask" in body["endpoints"]
