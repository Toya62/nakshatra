"""
Task 13 step 3: the missing deterministic data reaches the prompt.

Covers, with a stubbed synthesizer that captures the prompt (no live LLM):
- D9/Navamsha status line (and the D10 line beside it)
- full Vimshottari mahadasha ranges, past + future (not just MD/AD/PD)
- Kuja Dosha status/severity/cancellations, and the honest Ashtakoota line
  when no partner chart was provided (a score is rendered only when partner
  data is actually present)
- muhurtha lines for a timing question and none for a non-timing question
- the 30-day transit window surviving /rag/ask (regression: api.py used to
  overwrite ``transits`` with a window-less ``calculate_transits()`` report)

The birth context is a real engine chart (user-1997 birth, fixed target
date 2026-11-22, same as the step-1 golden set) with Kuja Dosha attached
exactly as /rag/ask does.
"""

from __future__ import annotations

import json
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

import nakshatra.api as api_module
from nakshatra.ai.corpus import CorpusChunk
from nakshatra.ai.embeddings import HashingEmbedder
from nakshatra.ai.retrieval import SearchResult
from nakshatra.ai.service import RAGService
from nakshatra.ai.synthesize import (
    Answer,
    BaseSynthesizer,
    _format_birth_summary,
    build_prompt,
)
from nakshatra.api import app
from nakshatra.compatibility import evaluate_chart_kuja_dosha
from nakshatra.core import BirthData, calculate_chart

TARGET_DATE = datetime(2026, 11, 22, 12, 0)
BIRTH = dict(
    year=1997, month=5, day=22, hour=4, minute=53,
    latitude=27.87, longitude=83.48, timezone="Asia/Kathmandu",
)

# Full mahadasha ranges the engine returns for this birth
# (lord, start, end) — past, current, and future.
#
# NOTE: the Sun->Moon boundary (2068-01-22 vs 2068-01-23) is NOT pinned
# exactly. It flips by one day depending on whether calculate_transits()
# has run earlier in the same process: transits mutate global ephemeris
# state, shifting the Moon longitude by ~0.00006 deg, which flips a
# rounding boundary in mayaastrolib's _build_md_sequence 40+ years out.
# Pre-existing engine nondeterminism, out of step-3 scope (step 3 only
# renders what the engine returns); the other eight ranges are stable
# across both states, so they are pinned exactly and the boundary pair
# is asserted start-only below.
EXPECTED_MAHADASHAS = [
    ("Jupiter", "1983-01-22", "1999-01-22"),
    ("Saturn", "1999-01-22", "2018-01-22"),
    ("Mercury", "2018-01-22", "2035-01-22"),
    ("Ketu", "2035-01-22", "2042-01-22"),
    ("Venus", "2042-01-22", "2062-01-22"),
    ("Sun", "2062-01-22", None),
    ("Moon", "2068-01-2", None),
    ("Mars", "2078-01-22", "2085-01-22"),
    ("Rahu", "2085-01-22", "2103-01-23"),
    ("Jupiter", "2103-01-23", "2119-01-23"),
]


def _result() -> SearchResult:
    text = "The Sun in the first house."
    return SearchResult(
        chunk=CorpusChunk(
            work="BPHS", chapter="1", verse="1", text=text,
            topics=["Sun"], source_file="test.txt",
            char_start=0, char_end=len(text), tier="verse",
        ),
        score=0.9,
    )


@pytest.fixture(scope="module")
def chart_dict() -> dict:
    """Real chart dict, enriched the way /rag/ask enriches it."""
    chart = calculate_chart(birth=BirthData(**BIRTH), target_date=TARGET_DATE)
    ctx = chart.model_dump()
    ctx["kuja_dosha"] = evaluate_chart_kuja_dosha(chart).model_dump()
    return ctx


class CapturingSynthesizer(BaseSynthesizer):
    """Stub synthesizer: records the prompt build_prompt() would send."""

    def __init__(self) -> None:
        self.prompts: list[str] = []
        self.contexts: list[dict | None] = []

    def synthesize(self, question, results, birth_context=None, language="en"):
        from nakshatra.ai.synthesize import build_prompt as _build_prompt

        self.prompts.append(
            _build_prompt(question, results, birth_context=birth_context, language=language)
        )
        self.contexts.append(birth_context)
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


class TestStep3PromptData:
    """build_prompt carries the new deterministic data in the summary."""

    def test_timing_prompt_contains_all_step3_data(self, chart_dict):
        prompt = build_prompt("When will I get married?", [_result()], birth_context=chart_dict)

        # (a) transit-window events survive into the prompt
        assert "Upcoming Monthly Transit Triggers (30 Days)" in prompt
        assert "Chandrashtama" in prompt
        # (b) D9 line, in the same style as the D10 line beside it
        assert "Navamsha (D9): Lagna Sagittarius" in prompt
        assert "Mars Scorpio" in prompt  # D9 sign, not the D1 Leo
        assert "Dashamsha (D10): Lagna Capricorn" in prompt
        # (c) full mahadasha ranges: past, current, and future
        for lord, start, end in EXPECTED_MAHADASHAS:
            if end is None:
                # Boundary-flaky pair (see note above): lord + start only.
                assert f"{lord}: {start}" in prompt
            else:
                assert f"{lord}: {start} to {end}" in prompt
        assert "Moon: 2068-01-2" in prompt  # 22 or 23, see note above
        assert "to 2078-01-22" in prompt
        assert "Full Mahadasha Timeline (Vimshottari, past + future)" in prompt
        # (d) Kuja Dosha status from the single chart
        assert "Kuja Dosha: Manglik" in prompt
        assert "severity Low" in prompt
        assert "Mars in friendly sign Leo" in prompt  # cancellation
        assert "dosha cancelled" in prompt
        # Ashtakoota: no partner chart, so an honest line, never a score
        assert "Ashtakoota: no partner chart provided" in prompt
        assert "do not invent one" in prompt
        # (e) muhurtha lines for a timing question
        assert "Muhurtha (Timing, reference moment:" in prompt
        assert "Current Hora:" in prompt
        assert "Current Choghadiya:" in prompt
        assert "Rahu Kalam [AVOID]:" in prompt
        assert "Abhijit Muhurtha:" in prompt
        assert "Muhurtha Score:" in prompt
        assert "at birth place (27.87, 83.48)" in prompt

    def test_non_timing_prompt_has_no_muhurtha(self, chart_dict):
        prompt = build_prompt("tell me about myself", [_result()], birth_context=chart_dict)
        assert "Muhurtha" not in prompt
        assert "Rahu Kalam" not in prompt
        assert "Choghadiya" not in prompt
        # The natal data itself is still present for a non-timing question.
        assert "Navamsha (D9): Lagna Sagittarius" in prompt
        assert "Kuja Dosha: Manglik" in prompt
        assert "Ashtakoota: no partner chart provided" in prompt

    def test_full_mahadasha_timeline_marks_current_and_birth_md(self, chart_dict):
        summary = _format_birth_summary(chart_dict)
        assert "Mercury: 2018-01-22 to 2035-01-22 [CURRENT]" in summary
        assert "Jupiter: 1983-01-22 to 1999-01-22 [IN EFFECT AT BIRTH]" in summary
        # The pre-birth Jupiter MD is the balance period, not a lived range
        # starting at birth — it is listed, not hidden.
        assert "Jupiter: 1983-01-22 to 1999-01-22" in summary

    def test_ashtakoota_rendered_when_partner_data_present(self, chart_dict):
        ctx = dict(chart_dict)
        ctx["ashtakoota"] = {
            "total_score": 24.0,
            "percentage": 66.7,
            "verdict": "Good compatibility",
        }
        prompt = build_prompt("When will I get married?", [_result()], birth_context=ctx)
        assert "Ashtakoota: 24.0/36 (66.7%) — Good compatibility" in prompt
        assert "no partner chart provided" not in prompt

    def test_muhurtha_failure_is_reported_not_invented(self, chart_dict, monkeypatch):
        import nakshatra.muhurtha as muhurtha_module

        monkeypatch.setattr(
            muhurtha_module, "calculate_muhurtha",
            lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("no ephemeris")),
        )
        prompt = build_prompt("When will I get married?", [_result()], birth_context=chart_dict)
        assert "Muhurtha (Timing): could not be calculated" in prompt
        assert "do not invent" in prompt
        assert "Current Hora:" not in prompt

    def test_muhurtha_from_context_is_used_verbatim(self, chart_dict):
        ctx = dict(chart_dict)
        ctx["muhurtha"] = {
            "timestamp": "2026-11-22 12:00:00",
            "timezone": "Asia/Kathmandu",
            "latitude": 27.87,
            "longitude": 83.48,
            "sunrise_time": "06:38:42",
            "sunset_time": "17:15:21",
            "current_hora": {
                "ruling_planet": "Mars",
                "start_time": "11:57:01",
                "end_time": "12:50:05",
                "nature": "Malefic",
            },
            "current_choghadiya": {
                "name": "Kaal",
                "ruler": "Saturn",
                "start_time": "11:57:01",
                "end_time": "13:16:36",
                "nature": "Inauspicious",
                "score": 20,
            },
            "rahu_kalam": {
                "start_time": "15:55:46",
                "end_time": "17:15:21",
                "is_active": False,
            },
            "abhijit_muhurtha": {
                "start_time": "11:35:48",
                "end_time": "12:18:15",
                "is_active": True,
            },
            "muhurtha_score": 30,
            "verdict": "Ashubha (Inauspicious / Afflicted)",
        }
        prompt = build_prompt("When will I get a job?", [_result()], birth_context=ctx)
        assert "Current Hora: Mars Hora (11:57:01 - 12:50:05) [Malefic]" in prompt
        assert "Current Choghadiya: Kaal (Saturn, 11:57:01 - 13:16:36)" in prompt
        assert "Rahu Kalam [AVOID]: 15:55:46 - 17:15:21" in prompt
        assert "Abhijit Muhurtha: 11:35:48 - 12:18:15 [ACTIVE NOW]" in prompt
        assert "Muhurtha Score: 30/100 — Ashubha (Inauspicious / Afflicted)" in prompt

    def test_non_manglik_chart_reports_non_manglik(self):
        # 2001-03-10 08:00 Kathmandu: Pisces lagna, Mars in Scorpio (9th
        # from Lagna, and in no Manglik house from Moon or Venus either).
        chart = calculate_chart(
            birth=BirthData(
                year=2001, month=3, day=10, hour=8, minute=0,
                latitude=27.87, longitude=83.48, timezone="Asia/Kathmandu",
            ),
            target_date=TARGET_DATE,
        )
        ctx = chart.model_dump()
        ctx["kuja_dosha"] = evaluate_chart_kuja_dosha(chart).model_dump()
        summary = _format_birth_summary(ctx)
        assert "Kuja Dosha: Non-Manglik" in summary
        assert "severity None" in summary


class TestRagAskKeepsTransitWindow:
    """Regression: /rag/ask must not drop the 30-day transit window."""

    def test_ask_preserves_window_and_attaches_kuja_dosha(
        self, corpus, tmp_path, monkeypatch
    ):
        capturing = CapturingSynthesizer()
        monkeypatch.setattr(
            api_module,
            "_rag_service",
            RAGService(embedder=HashingEmbedder(), synthesizer=capturing),
        )
        client = TestClient(app)
        index_dir = tmp_path / "index"
        client.post(
            "/rag/ingest",
            json={"corpus_dir": str(corpus), "index_dir": str(index_dir)},
        )
        response = client.post(
            "/rag/ask",
            json={
                "question": "When will I get married?",
                "index_dir": str(index_dir),
                "birth": {
                    "year": 1997,
                    "month": 5,
                    "day": 22,
                    "hour": 4,
                    "minute": 53,
                    "latitude": 27.87,
                    "longitude": 83.48,
                    "timezone": "Asia/Kathmandu",
                },
            },
        )
        assert response.status_code == 200
        assert len(capturing.prompts) == 1
        prompt = capturing.prompts[0]
        # The window the summary reads must actually exist in the context
        # that reached the synthesizer.
        ctx = capturing.contexts[0]
        assert ctx is not None
        window = (ctx.get("transits") or {}).get("window")
        assert isinstance(window, dict)
        assert window.get("days_scanned") == 30
        assert window.get("events"), "transit window has no events"
        assert "Upcoming Monthly Transit Triggers (30 Days)" in prompt
        assert "Navamsha (D9)" in prompt
        assert "Kuja Dosha:" in prompt
        assert "Muhurtha (Timing, reference moment:" in prompt
        # Kuja Dosha attached by the endpoint itself.
        kuja = ctx.get("kuja_dosha") or {}
        assert kuja.get("is_manglik") is True
        assert kuja.get("severity") == "Low"
