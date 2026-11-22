"""
Task 13 step 8: stop trusting the input silently.

- invalid ``language`` is rejected (400 on /rag/ask and /rag/ask/stream;
  ValueError from get_system_prompt) instead of silently falling back to English
- when transits/predictions/remedies fail while building the chart context,
  the model is told the context is partial (which part is missing) in the
  prompt it receives — tested with a stubbed synthesizer capturing the prompt
- a client-supplied raw ``birth_context`` dict is validated (planets, houses,
  dasha) and malformed ones are rejected (400)
- ``index_dir`` must be under an allowlisted base on /rag/ask, /rag/ask/stream
  and /rag/ingest; /rag/ask and /rag/ask/stream have an opt-in API-key gate
  (RAG_API_KEY) that is off by default so the key-less web frontend keeps working

No live LLM is called in any test.
"""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

import nakshatra.api as api_module
import nakshatra.transits as transits_module
from nakshatra.ai.corpus import CorpusChunk
from nakshatra.ai.embeddings import HashingEmbedder
from nakshatra.ai.retrieval import SearchResult
from nakshatra.ai.service import RAGService, validate_birth_context
from nakshatra.ai.synthesize import (
    Answer,
    BaseSynthesizer,
    build_prompt,
    get_system_prompt,
)
from nakshatra.api import RAGAskRequest, _attach_chart_derived_context, app
from nakshatra.core import BirthData, calculate_chart

BIRTH = dict(
    year=1997,
    month=5,
    day=22,
    hour=4,
    minute=53,
    latitude=27.87,
    longitude=83.48,
    timezone="Asia/Kathmandu",
)


def _result() -> SearchResult:
    text = "The Sun in the first house."
    return SearchResult(
        chunk=CorpusChunk(
            work="BPHS",
            chapter="1",
            verse="1",
            text=text,
            topics=["Sun"],
            source_file="test.txt",
            char_start=0,
            char_end=len(text),
            tier="verse",
        ),
        score=0.9,
    )


class CapturingSynthesizer(BaseSynthesizer):
    """Stub synthesizer: records the prompt build_prompt() would send."""

    def __init__(self) -> None:
        self.prompts: list[str] = []

    def synthesize(self, question, results, birth_context=None, language="en"):
        self.prompts.append(
            build_prompt(question, results, birth_context=birth_context, language=language)
        )
        return Answer(question=question, answer="Stub answer [1].", model="capture")


@pytest.fixture()
def corpus(tmp_path):
    work_dir = tmp_path / "corpus" / "bphs"
    work_dir.mkdir(parents=True)
    (work_dir / "meta.json").write_text(
        json.dumps({"work": "BPHS", "translator": "R. Santhanam", "license": "public domain"}),
        encoding="utf-8",
    )
    (work_dir / "bphs.txt").write_text(
        "Chapter 1, Verse 1: The Sun in the first house gives career success.\n"
        "Chapter 1, Verse 2: The Moon in the second house gives wealth.\n",
        encoding="utf-8",
    )
    return tmp_path / "corpus"


@pytest.fixture()
def rag_client(monkeypatch):
    """TestClient with an isolated RAG service; no RAG_API_KEY by default."""
    monkeypatch.delenv("RAG_API_KEY", raising=False)
    monkeypatch.setattr(
        api_module,
        "_rag_service",
        RAGService(embedder=HashingEmbedder(), synthesizer=CapturingSynthesizer()),
    )
    return TestClient(app)


@pytest.fixture()
def indexed(rag_client, corpus, tmp_path):
    """Ingest the minimal corpus; returns the index dir (under tmp_path)."""
    index_dir = tmp_path / "index"
    resp = rag_client.post(
        "/rag/ingest",
        json={"corpus_dir": str(corpus), "index_dir": str(index_dir)},
    )
    assert resp.status_code == 200, resp.text
    return index_dir


def _full_chart_dict() -> dict:
    return calculate_chart(birth=BirthData(**BIRTH)).model_dump()


class TestInvalidLanguage:
    """An invalid language is rejected, not silently treated as English."""

    def test_rag_ask_request_rejects_invalid_language(self):
        with pytest.raises(ValidationError):
            RAGAskRequest(question="Q", language="fr")
        with pytest.raises(ValidationError):
            RAGAskRequest(question="Q", language="xx")
        assert RAGAskRequest(question="Q", language="ne").language == "ne"
        assert RAGAskRequest(question="Q").language == "en"

    def test_get_system_prompt_rejects_invalid_language(self):
        with pytest.raises(ValueError, match="Unsupported language"):
            get_system_prompt("fr")
        with pytest.raises(ValueError, match="Unsupported language"):
            get_system_prompt("xx")
        # Legacy aliases still resolve to the Nepali prompts (existing behaviour).
        assert get_system_prompt("nepali") == get_system_prompt("ne")
        assert get_system_prompt("nep") == get_system_prompt("ne")

    def test_ask_endpoint_returns_400_for_invalid_language(self, rag_client, indexed):
        response = rag_client.post(
            "/rag/ask",
            json={"question": "Q", "index_dir": str(indexed), "language": "fr"},
        )
        assert response.status_code == 400
        assert "language" in response.json()["detail"].lower()

    def test_ask_stream_endpoint_returns_400_for_invalid_language(self, rag_client, indexed):
        response = rag_client.post(
            "/rag/ask/stream",
            json={"question": "Q", "index_dir": str(indexed), "language": "de"},
        )
        assert response.status_code == 400

    def test_valid_ne_language_still_works(self, rag_client, indexed):
        response = rag_client.post(
            "/rag/ask",
            json={"question": "Q", "index_dir": str(indexed), "language": "ne"},
        )
        assert response.status_code == 200


class TestPartialContextDisclosure:
    """A failed transits/predictions/remedies step must reach the model as a warning."""

    def test_attach_records_missing_parts(self, monkeypatch):
        chart = calculate_chart(birth=BirthData(**BIRTH))
        ctx = chart.model_dump()
        monkeypatch.setattr(
            transits_module,
            "calculate_transits",
            lambda *a, **k: (_ for _ in ()).throw(RuntimeError("ephemeris unavailable")),
        )
        missing = _attach_chart_derived_context(chart, ctx)
        # Predictions/remedies also fail here: with transits unavailable
        # they try to compute transits themselves (core.py logs "Failed
        # to calculate transits"), so all three parts are honestly missing.
        assert missing == ["transits", "predictions", "remedies"]
        assert ctx["partial_context"] == ["transits", "predictions", "remedies"]
        assert "predictions" not in ctx
        assert "remedies" not in ctx

    def test_attach_records_each_failing_part(self, monkeypatch):
        chart = calculate_chart(birth=BirthData(**BIRTH))
        ctx = chart.model_dump()
        monkeypatch.setattr(
            type(chart),
            "get_predictions",
            lambda self, **k: (_ for _ in ()).throw(RuntimeError("predictions failed")),
        )
        monkeypatch.setattr(
            type(chart),
            "get_remedies",
            lambda self, **k: (_ for _ in ()).throw(RuntimeError("remedies failed")),
        )
        missing = _attach_chart_derived_context(chart, ctx)
        assert missing == ["predictions", "remedies"]
        assert ctx["partial_context"] == ["predictions", "remedies"]

    def test_build_prompt_discloses_partial_context(self):
        ctx = _full_chart_dict()
        ctx["partial_context"] = ["transits", "remedies"]
        prompt = build_prompt("When will I marry?", [_result()], birth_context=ctx)
        assert "PARTIAL CONTEXT WARNING" in prompt
        assert "transits" in prompt
        assert "remedies" in prompt
        assert "Do NOT invent" in prompt

    def test_build_prompt_without_partial_context_has_no_warning(self):
        prompt = build_prompt("Q", [_result()], birth_context=_full_chart_dict())
        assert "PARTIAL CONTEXT WARNING" not in prompt

    def test_ask_discloses_failed_transits_in_captured_prompt(
        self, rag_client, indexed, monkeypatch
    ):
        monkeypatch.setattr(
            transits_module,
            "calculate_transits",
            lambda *a, **k: (_ for _ in ()).throw(RuntimeError("ephemeris unavailable")),
        )
        response = rag_client.post(
            "/rag/ask",
            json={
                "question": "When will I get married?",
                "index_dir": str(indexed),
                "birth": BIRTH,
            },
        )
        assert response.status_code == 200, response.text
        assert response.json()["meta"]["partial_context"] == [
            "transits",
            "predictions",
            "remedies",
        ]
        service = api_module._rag_service
        assert isinstance(service._get_synthesizer(), CapturingSynthesizer)
        prompt = service._get_synthesizer().prompts[-1]
        assert "PARTIAL CONTEXT WARNING" in prompt
        assert "transits" in prompt


class TestBirthContextValidation:
    """A client-supplied birth_context must carry planets, houses and dasha."""

    def test_validate_birth_context_unit(self):
        assert validate_birth_context(None) == []
        assert validate_birth_context({}) == [
            "birth_context.planets is missing or empty",
            "birth_context.houses is missing or empty",
            "birth_context.dashas is missing or empty",
        ]
        assert validate_birth_context(_full_chart_dict()) == []
        missing_dasha = _full_chart_dict()
        del missing_dasha["dashas"]
        assert any("dashas" in p for p in validate_birth_context(missing_dasha))
        empty_planets = _full_chart_dict()
        empty_planets["planets"] = []
        assert any("planets" in p for p in validate_birth_context(empty_planets))
        nameless = _full_chart_dict()
        nameless["planets"] = [{"house": 1}]
        assert any("planets" in p for p in validate_birth_context(nameless))
        missing_houses = _full_chart_dict()
        del missing_houses["houses"]
        assert any("houses" in p for p in validate_birth_context(missing_houses))

    @pytest.mark.parametrize("mutate", ["planets", "houses", "dashas"])
    def test_ask_rejects_malformed_birth_context(self, rag_client, indexed, mutate):
        ctx = _full_chart_dict()
        del ctx[mutate]
        response = rag_client.post(
            "/rag/ask",
            json={"question": "Q", "index_dir": str(indexed), "birth_context": ctx},
        )
        assert response.status_code == 400
        assert mutate in response.json()["detail"]

    def test_ask_rejects_empty_planets(self, rag_client, indexed):
        ctx = _full_chart_dict()
        ctx["planets"] = []
        response = rag_client.post(
            "/rag/ask",
            json={"question": "Q", "index_dir": str(indexed), "birth_context": ctx},
        )
        assert response.status_code == 400

    def test_ask_accepts_valid_birth_context(self, rag_client, indexed):
        response = rag_client.post(
            "/rag/ask",
            json={"question": "Q", "index_dir": str(indexed), "birth_context": _full_chart_dict()},
        )
        assert response.status_code == 200, response.text

    def test_ask_stream_rejects_malformed_birth_context(self, rag_client, indexed):
        response = rag_client.post(
            "/rag/ask/stream",
            json={
                "question": "Q",
                "index_dir": str(indexed),
                "birth_context": {"ascendant": "Aries"},
            },
        )
        assert response.status_code == 400


class TestIndexDirAllowlist:
    """index_dir must stay under the working directory, RAG_INDEX_BASE_DIRS or tmp."""

    def test_ask_rejects_absolute_path_outside_bases(self, rag_client, indexed):
        response = rag_client.post(
            "/rag/ask",
            json={"question": "Q", "index_dir": "/home/hatch/elsewhere"},
        )
        assert response.status_code == 400

    def test_ask_rejects_traversal(self, rag_client):
        response = rag_client.post(
            "/rag/ask",
            json={"question": "Q", "index_dir": "../outside"},
        )
        assert response.status_code == 400

    def test_ask_stream_rejects_absolute_path_outside_bases(self, rag_client, indexed):
        response = rag_client.post(
            "/rag/ask/stream",
            json={"question": "Q", "index_dir": "/opt/somewhere"},
        )
        assert response.status_code == 400

    def test_ingest_rejects_absolute_path_outside_bases(self, rag_client, corpus):
        response = rag_client.post(
            "/rag/ingest",
            json={"corpus_dir": str(corpus), "index_dir": "/home/hatch/elsewhere"},
        )
        assert response.status_code == 400

    def test_relative_index_dir_still_allowed(self, rag_client):
        # The session fixture guarantees a real index/ under the working directory.
        response = rag_client.post("/rag/ask", json={"question": "Q", "index_dir": "index"})
        assert response.status_code == 200, response.text

    def test_extra_base_dir_via_env(self, rag_client, monkeypatch, tmp_path):
        monkeypatch.setenv("RAG_INDEX_BASE_DIRS", str(tmp_path))
        response = rag_client.post(
            "/rag/ask", json={"question": "Q", "index_dir": str(tmp_path / "missing")}
        )
        # Passes the allowlist (tmp_path is now a base) and fails as a missing index.
        assert response.status_code == 404


class TestRagAccessGate:
    """The /rag/ask gate is opt-in: open without RAG_API_KEY, keyed when set."""

    def test_open_by_default(self, rag_client, indexed):
        response = rag_client.post("/rag/ask", json={"question": "Q", "index_dir": str(indexed)})
        assert response.status_code == 200

    def test_key_required_when_configured(self, rag_client, indexed, monkeypatch):
        monkeypatch.setenv("RAG_API_KEY", "s3cret")
        no_key = rag_client.post("/rag/ask", json={"question": "Q", "index_dir": str(indexed)})
        assert no_key.status_code == 401
        wrong_key = rag_client.post(
            "/rag/ask",
            json={"question": "Q", "index_dir": str(indexed)},
            headers={"X-API-Key": "wrong"},
        )
        assert wrong_key.status_code == 401
        ok = rag_client.post(
            "/rag/ask",
            json={"question": "Q", "index_dir": str(indexed)},
            headers={"X-API-Key": "s3cret"},
        )
        assert ok.status_code == 200
        admin_ok = rag_client.post(
            "/rag/ask",
            json={"question": "Q", "index_dir": str(indexed)},
            headers={"X-Admin-Key": "s3cret"},
        )
        assert admin_ok.status_code == 200

    def test_stream_gate_when_configured(self, rag_client, indexed, monkeypatch):
        monkeypatch.setenv("RAG_API_KEY", "s3cret")
        response = rag_client.post(
            "/rag/ask/stream", json={"question": "Q", "index_dir": str(indexed)}
        )
        assert response.status_code == 401
