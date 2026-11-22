"""
Golden Q&A eval for Nakshatra Task 13, step 1.

Offline eval set: known charts (facts hard-coded from the deterministic
engine output, verified by ``test_golden_chart_facts_match_engine``),
stub LLM answers (correct + deliberately corrupted, mimicking real
hallucination modes), and golden retrieval queries.

Scores reported (see :func:`evaluate_golden_set`):
- citation precision = supported cited claims / all cited claims
- date/placement match rate = stated dates/positions matching the chart
  / all stated dates/positions
- detection rate = incorrect claims flagged / all incorrect claims

"before" mode simulates the pre-validator pipeline: raw stub answers
plus ``extract_citations`` (range check only, unsupported citations pass
through, nothing is flagged). "after" mode runs
``nakshatra.ai.validate.validate_answer`` and re-scores the cleaned
output. No live LLM is ever called; every case runs on stubs.

Measured 2026-11-22 (before validator, pre-validator code):
  citation precision (before) = 0.865 (32/37)
  date/placement match rate (before) = 0.919 (102/111)
  detection rate (before) = 0.000 (0/9 incorrect claims flagged)
  retrieval hit rate (before) = 1.000 (6/6)
After validator (see test_eval_after_score):
  citation precision (after) = 1.000 (32/32 kept citations)
  date/placement match rate among unflagged claims (after) = 1.000 (91/91)
  detection rate (after) = 1.000 (9/9 incorrect claims flagged)
  dropped citations (after) = 6 (5 unsupported + 1 out of range)
  (raw date/placement match rate is unchanged at 0.919 — the validator
  flags wrong claims, it does not rewrite them.)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime

import pytest

from nakshatra.ai.corpus import CorpusChunk
from nakshatra.ai.retrieval import SearchResult
from nakshatra.ai.synthesize import extract_citations
from nakshatra.core import BirthData, calculate_chart
from nakshatra.transits import calculate_transits

# Fixed "today" so current dasha / Sade Sati are reproducible.
GOLDEN_TARGET_DATE = datetime(2026, 11, 22, 12, 0)

# ---------------------------------------------------------------------------
# Golden charts. Facts below are the deterministic engine's own output for
# each birth (lagna, planets, dasha ranges, yogas, Sade Sati at the fixed
# target date) — transcribed from a probe run and guarded by
# test_golden_chart_facts_match_engine. The validator's job is to check an
# answer against the chart context the LLM receives, so the engine's values
# are the ground truth here, not any external chart file.
# planets: name -> (house, sign, nakshatra)
# md/ad/pd: (lord, start YYYY-MM-DD, end YYYY-MM-DD) as the engine returns
#   them ("North Node"/"South Node" are the engine's lord spellings).
# ---------------------------------------------------------------------------
GOLDEN_CHARTS: dict[str, dict] = {
    "user-1997": {
        "birth": dict(year=1997, month=5, day=22, hour=4, minute=53,
                      latitude=27.87, longitude=83.48, timezone="Asia/Kathmandu"),
        "lagna": "Aries",
        "planets": {
            "Sun": (2, "Taurus", "Krittika"), "Moon": (8, "Scorpio", "Vishakha"),
            "Mars": (5, "Leo", "Purva Phalguni"), "Mercury": (1, "Aries", "Ashwini"),
            "Jupiter": (10, "Capricorn", "Dhanishta"), "Venus": (2, "Taurus", "Rohini"),
            "Saturn": (12, "Pisces", "Revati"), "Rahu": (6, "Virgo", "Uttara Phalguni"),
            "Ketu": (12, "Pisces", "Purva Bhadrapada"),
        },
        "md": ("Mercury", "2018-01-22", "2035-01-22"),
        "ad": ("Mars", "2026-07-24", "2027-07-21"),
        "pd": ("Jupiter", "2026-10-07", "2026-11-24"),
        "yogas": ["Kemadruma Bhanga Yoga (Cancelled Kemadruma)",
                  "Neechabhanga Raja Yoga (Moon)", "Neechabhanga Raja Yoga (Jupiter)",
                  "Chandradhi Yoga", "Vasi Yoga", "Amala Yoga (from Lagna)",
                  "Dhana Yoga (Wealth Axis)", "Kendra-Trikona Raja Yoga (Venus & Sun)",
                  "Dainya Parivartana Yoga (Jupiter & Saturn)"],
        "sade_sati": {"active": False, "phase": None, "moon_sign": "Scorpio"},
    },
    "berlin-1990": {
        "birth": dict(year=1990, month=1, day=15, hour=10, minute=30,
                      latitude=52.52, longitude=13.40, timezone="Europe/Berlin"),
        "lagna": "Pisces",
        "planets": {
            "Sun": (11, "Capricorn", "Uttara Ashadha"), "Moon": (6, "Leo", "Purva Phalguni"),
            "Mars": (9, "Scorpio", "Jyeshtha"), "Mercury": (10, "Sagittarius", "Purva Ashadha"),
            "Jupiter": (4, "Gemini", "Ardra"), "Venus": (11, "Capricorn", "Uttara Ashadha"),
            "Saturn": (10, "Sagittarius", "Purva Ashadha"), "Rahu": (11, "Capricorn", "Dhanishta"),
            "Ketu": (5, "Cancer", "Ashlesha"),
        },
        "md": ("North Node", "2019-04-21", "2037-04-20"),
        "ad": ("Saturn", "2024-05-26", "2027-04-02"),
        "pd": ("Jupiter", "2026-11-15", "2027-04-02"),
        "yogas": ["Kemadruma Bhanga Yoga (Cancelled Kemadruma)", "Vasi Yoga",
                  "Amala Yoga (from Lagna)", "Maha Parivartana Yoga (Mercury & Jupiter)"],
        "sade_sati": {"active": False, "phase": None, "moon_sign": "Leo"},
    },
    "nyc-1985": {
        "birth": dict(year=1985, month=7, day=4, hour=18, minute=0,
                      latitude=40.71, longitude=-74.01, timezone="America/New_York"),
        "lagna": "Scorpio",
        "planets": {
            "Sun": (8, "Gemini", "Ardra"), "Moon": (3, "Capricorn", "Shravana"),
            "Mars": (8, "Gemini", "Punarvasu"), "Mercury": (9, "Cancer", "Pushya"),
            "Jupiter": (3, "Capricorn", "Shravana"), "Venus": (7, "Taurus", "Krittika"),
            "Saturn": (12, "Libra", "Vishakha"), "Rahu": (6, "Aries", "Bharani"),
            "Ketu": (12, "Libra", "Vishakha"),
        },
        "md": ("Jupiter", "2012-11-25", "2028-11-25"),
        "ad": ("North Node", "2026-07-02", "2028-11-25"),
        "pd": ("Jupiter", "2026-11-11", "2027-03-08"),
        "yogas": ["Malavya Yoga", "Gaja Kesari Yoga",
                  "Kemadruma Bhanga Yoga (Cancelled Kemadruma)",
                  "Neechabhanga Raja Yoga (Jupiter)", "Ubhayachari Yoga",
                  "Harsha Yoga (Viparita Raja Yoga)"],
        "sade_sati": {"active": False, "phase": None, "moon_sign": "Capricorn"},
    },
    "ktm-2000": {
        "birth": dict(year=2000, month=12, day=25, hour=6, minute=15,
                      latitude=27.70, longitude=85.32, timezone="Asia/Kathmandu"),
        "lagna": "Sagittarius",
        "planets": {
            "Sun": (1, "Sagittarius", "Mula"), "Moon": (1, "Sagittarius", "Mula"),
            "Mars": (11, "Libra", "Swati"), "Mercury": (1, "Sagittarius", "Mula"),
            "Jupiter": (6, "Taurus", "Krittika"), "Venus": (2, "Capricorn", "Dhanishta"),
            "Saturn": (6, "Taurus", "Krittika"), "Rahu": (7, "Gemini", "Punarvasu"),
            "Ketu": (1, "Sagittarius", "Purva Ashadha"),
        },
        "md": ("Venus", "2006-12-20", "2026-12-20"),
        "ad": ("South Node", "2025-10-19", "2026-12-20"),
        "pd": ("Mercury", "2026-10-20", "2026-12-20"),
        "yogas": ["Sunapha Yoga", "Budhaditya Yoga", "Vesi Yoga",
                  "Dhana Yoga (Wealth Axis)", "Kendra-Trikona Raja Yoga (Mercury & Sun)",
                  "Dainya Parivartana Yoga (Venus & Saturn)"],
        "sade_sati": {"active": False, "phase": None, "moon_sign": "Sagittarius"},
    },
    "london-1978": {
        "birth": dict(year=1978, month=3, day=8, hour=12, minute=0,
                      latitude=51.50, longitude=-0.12, timezone="Europe/London"),
        "lagna": "Gemini",
        "planets": {
            "Sun": (9, "Aquarius", "Purva Bhadrapada"), "Moon": (9, "Aquarius", "Shatabhisha"),
            "Mars": (1, "Gemini", "Punarvasu"), "Mercury": (10, "Pisces", "Purva Bhadrapada"),
            "Jupiter": (1, "Gemini", "Mrigashira"), "Venus": (10, "Pisces", "Uttara Bhadrapada"),
            "Saturn": (3, "Leo", "Magha"), "Rahu": (4, "Virgo", "Hasta"),
            "Ketu": (10, "Pisces", "Uttara Bhadrapada"),
        },
        "md": ("Mercury", "2018-06-22", "2035-06-23"),
        "ad": ("Moon", "2025-07-23", "2026-12-22"),
        "pd": ("Venus", "2026-09-01", "2026-11-26"),
        "yogas": ["Malavya Yoga", "Neechabhanga Raja Yoga (Mercury)", "Sunapha Yoga",
                  "Vesi Yoga", "Amala Yoga (from Lagna)",
                  "Kendra-Trikona Raja Yoga (Mercury & Venus)",
                  "Kahala Parivartana Yoga (Sun & Saturn)",
                  "Maha Parivartana Yoga (Mercury & Jupiter)"],
        "sade_sati": {"active": True, "phase": "Setting (2nd from Moon)", "moon_sign": "Aquarius"},
    },
    "mumbai-1995": {
        "birth": dict(year=1995, month=9, day=19, hour=23, minute=45,
                      latitude=19.08, longitude=72.88, timezone="Asia/Kolkata"),
        "lagna": "Gemini",
        "planets": {
            "Sun": (4, "Virgo", "Uttara Phalguni"), "Moon": (2, "Cancer", "Pushya"),
            "Mars": (5, "Libra", "Swati"), "Mercury": (4, "Virgo", "Chitra"),
            "Jupiter": (6, "Scorpio", "Anuradha"), "Venus": (4, "Virgo", "Hasta"),
            "Saturn": (9, "Aquarius", "Purva Bhadrapada"), "Rahu": (5, "Libra", "Chitra"),
            "Ketu": (11, "Aries", "Ashwini"),
        },
        "md": ("Mercury", "2013-07-21", "2030-07-21"),
        "ad": ("Jupiter", "2025-08-05", "2027-11-11"),
        "pd": ("Venus", "2026-09-16", "2027-02-01"),
        "yogas": ["Bhadra Yoga", "Kemadruma Bhanga Yoga (Cancelled Kemadruma)",
                  "Neechabhanga Raja Yoga (Venus)", "Budhaditya Yoga", "Vesi Yoga",
                  "Dhana Yoga (Wealth Axis)", "Kendra-Trikona Raja Yoga (Mercury & Venus)"],
        "sade_sati": {"active": False, "phase": None, "moon_sign": "Cancer"},
    },
    "sydney-1988": {
        "birth": dict(year=1988, month=6, day=21, hour=4, minute=20,
                      latitude=-33.87, longitude=151.21, timezone="Australia/Sydney"),
        "lagna": "Taurus",
        "planets": {
            "Sun": (2, "Gemini", "Mrigashira"), "Moon": (4, "Leo", "Purva Phalguni"),
            "Mars": (10, "Aquarius", "Purva Bhadrapada"), "Mercury": (1, "Taurus", "Mrigashira"),
            "Jupiter": (1, "Taurus", "Krittika"), "Venus": (1, "Taurus", "Mrigashira"),
            "Saturn": (8, "Sagittarius", "Mula"), "Rahu": (10, "Aquarius", "Purva Bhadrapada"),
            "Ketu": (4, "Leo", "Purva Phalguni"),
        },
        "md": ("North Node", "2024-10-28", "2042-10-29"),
        "ad": ("North Node", "2024-10-28", "2027-07-12"),
        "pd": ("Venus", "2026-07-23", "2027-01-04"),
        "yogas": ["Malavya Yoga", "Gaja Kesari Yoga",
                  "Kemadruma Bhanga Yoga (Cancelled Kemadruma)", "Vasi Yoga",
                  "Amala Yoga (from Moon)", "Maha Dhana Yoga (2nd & 11th Lords Conjunction)"],
        "sade_sati": {"active": False, "phase": None, "moon_sign": "Leo"},
    },
    "berlin-2003": {
        "birth": dict(year=2003, month=2, day=14, hour=9, minute=0,
                      latitude=52.52, longitude=13.40, timezone="Europe/Berlin"),
        "lagna": "Pisces",
        "planets": {
            "Sun": (12, "Aquarius", "Dhanishta"), "Moon": (4, "Gemini", "Punarvasu"),
            "Mars": (9, "Scorpio", "Jyeshtha"), "Mercury": (11, "Capricorn", "Uttara Ashadha"),
            "Jupiter": (5, "Cancer", "Ashlesha"), "Venus": (10, "Sagittarius", "Purva Ashadha"),
            "Saturn": (3, "Taurus", "Mrigashira"), "Rahu": (3, "Taurus", "Rohini"),
            "Ketu": (9, "Scorpio", "Anuradha"),
        },
        "md": ("Saturn", "2010-08-14", "2029-08-14"),
        "ad": ("North Node", "2024-03-26", "2027-01-31"),
        "pd": ("Moon", "2026-09-06", "2026-12-02"),
        "yogas": ["Dhurdhura Yoga", "Chandradhi Yoga", "Vasi Yoga",
                  "Harsha Yoga (Viparita Raja Yoga)", "Amala Yoga (from Lagna)"],
        "sade_sati": {"active": False, "phase": None, "moon_sign": "Gemini"},
    },
    "toronto-1970": {
        "birth": dict(year=1970, month=11, day=30, hour=15, minute=30,
                      latitude=43.65, longitude=-79.38, timezone="America/Toronto"),
        "lagna": "Aries",
        "planets": {
            "Sun": (8, "Scorpio", "Anuradha"), "Moon": (9, "Sagittarius", "Mula"),
            "Mars": (7, "Libra", "Chitra"), "Mercury": (9, "Sagittarius", "Mula"),
            "Jupiter": (7, "Libra", "Vishakha"), "Venus": (7, "Libra", "Swati"),
            "Saturn": (1, "Aries", "Bharani"), "Rahu": (11, "Aquarius", "Dhanishta"),
            "Ketu": (5, "Leo", "Magha"),
        },
        "md": ("North Node", "2015-11-01", "2033-10-31"),
        "ad": ("South Node", "2026-05-02", "2027-05-21"),
        "pd": ("North Node", "2026-10-09", "2026-12-05"),
        "yogas": ["Malavya Yoga", "Kemadruma Bhanga Yoga (Cancelled Kemadruma)",
                  "Neechabhanga Raja Yoga (Saturn)", "Ubhayachari Yoga",
                  "Kendra-Trikona Raja Yoga (Venus & Jupiter)"],
        "sade_sati": {"active": False, "phase": None, "moon_sign": "Sagittarius"},
    },
    "ktm-2010": {
        "birth": dict(year=2010, month=5, day=5, hour=8, minute=0,
                      latitude=27.70, longitude=85.32, timezone="Asia/Kathmandu"),
        "lagna": "Gemini",
        "planets": {
            "Sun": (11, "Aries", "Bharani"), "Moon": (8, "Capricorn", "Uttara Ashadha"),
            "Mars": (2, "Cancer", "Ashlesha"), "Mercury": (11, "Aries", "Ashwini"),
            "Jupiter": (10, "Pisces", "Purva Bhadrapada"), "Venus": (12, "Taurus", "Rohini"),
            "Saturn": (4, "Virgo", "Uttara Phalguni"), "Rahu": (7, "Sagittarius", "Purva Ashadha"),
            "Ketu": (1, "Gemini", "Punarvasu"),
        },
        "md": ("Mars", "2020-12-05", "2027-12-06"),
        "ad": ("Venus", "2025-10-30", "2026-12-30"),
        "pd": ("Mercury", "2026-10-06", "2026-12-05"),
        "yogas": ["Hamsa Yoga", "Kemadruma Bhanga Yoga (Cancelled Kemadruma)",
                  "Neechabhanga Raja Yoga (Mars)", "Budhaditya Yoga", "Ubhayachari Yoga",
                  "Vimala Yoga (Viparita Raja Yoga)", "Amala Yoga (from Lagna)",
                  "Dhana Yoga (Wealth Axis)"],
        "sade_sati": {"active": False, "phase": None, "moon_sign": "Capricorn"},
    },
    "delhi-1992": {
        "birth": dict(year=1992, month=4, day=10, hour=7, minute=10,
                      latitude=28.61, longitude=77.21, timezone="Asia/Kolkata"),
        "lagna": "Aries",
        "planets": {
            "Sun": (12, "Pisces", "Revati"), "Moon": (3, "Gemini", "Punarvasu"),
            "Mars": (11, "Aquarius", "Shatabhisha"), "Mercury": (12, "Pisces", "Uttara Bhadrapada"),
            "Jupiter": (5, "Leo", "Magha"), "Venus": (12, "Pisces", "Uttara Bhadrapada"),
            "Saturn": (10, "Capricorn", "Shravana"), "Rahu": (9, "Sagittarius", "Mula"),
            "Ketu": (3, "Gemini", "Ardra"),
        },
        "md": ("Mercury", "2024-09-22", "2041-09-22"),
        "ad": ("Mercury", "2024-09-22", "2027-02-18"),
        "pd": ("Saturn", "2026-10-02", "2027-02-18"),
        "yogas": ["Sasa Yoga", "Kemadruma Bhanga Yoga (Cancelled Kemadruma)",
                  "Neechabhanga Raja Yoga (Mercury)", "Budhaditya Yoga", "Vasi Yoga",
                  "Harsha Yoga (Viparita Raja Yoga)", "Amala Yoga (from Moon)",
                  "Kendra-Trikona Raja Yoga (Venus & Sun)",
                  "Dainya Parivartana Yoga (Sun & Jupiter)"],
        "sade_sati": {"active": False, "phase": None, "moon_sign": "Gemini"},
    },
    "pokhara-1999": {
        "birth": dict(year=1999, month=8, day=30, hour=21, minute=40,
                      latitude=28.21, longitude=83.99, timezone="Asia/Kathmandu"),
        "lagna": "Aries",
        "planets": {
            "Sun": (5, "Leo", "Magha"), "Moon": (12, "Pisces", "Revati"),
            "Mars": (8, "Scorpio", "Anuradha"), "Mercury": (5, "Leo", "Magha"),
            "Jupiter": (1, "Aries", "Ashwini"), "Venus": (4, "Cancer", "Ashlesha"),
            "Saturn": (1, "Aries", "Bharani"), "Rahu": (4, "Cancer", "Ashlesha"),
            "Ketu": (10, "Capricorn", "Shravana"),
        },
        "md": ("Sun", "2026-11-10", "2032-11-10"),
        "ad": ("Sun", "2026-11-10", "2027-02-28"),
        "pd": ("Moon", "2026-11-16", "2026-11-25"),
        "yogas": ["Neechabhanga Raja Yoga (Saturn)", "Sunapha Yoga", "Budhaditya Yoga",
                  "Vasi Yoga", "Sarala Yoga (Viparita Raja Yoga)",
                  "Kendra-Trikona Raja Yoga (Saturn & Jupiter)"],
        "sade_sati": {"active": True, "phase": "Peak / Janma Shani (1st from Moon)",
                      "moon_sign": "Pisces"},
    },
}


def _node_name(lord: str) -> str:
    """Engine spells the nodes 'North Node'/'South Node'; display names are Rahu/Ketu."""
    return {"North Node": "Rahu", "South Node": "Ketu"}.get(lord, lord)


_CONTEXT_CACHE: dict[str, dict] = {}


def build_golden_context(chart_id: str) -> dict:
    """Deterministic chart context for a golden chart (fixed target date)."""
    if chart_id not in _CONTEXT_CACHE:
        spec = GOLDEN_CHARTS[chart_id]
        birth = BirthData(second=0, **spec["birth"])
        chart = calculate_chart(birth=birth, target_date=GOLDEN_TARGET_DATE)
        ctx = chart.model_dump()
        # calculate_chart computes transits for "now"; pin them to the fixed date.
        ctx["transits"] = calculate_transits(
            chart, transit_date=GOLDEN_TARGET_DATE
        ).model_dump()
        _CONTEXT_CACHE[chart_id] = ctx
    return _CONTEXT_CACHE[chart_id]


def test_golden_chart_facts_match_engine():
    """Guard: the hard-coded golden facts really are what the engine returns."""
    for chart_id, spec in GOLDEN_CHARTS.items():
        ctx = build_golden_context(chart_id)
        assert ctx["ascendant"]["sign"] == spec["lagna"], chart_id
        by_name = {p["name"]: p for p in ctx["planets"]}
        by_name["Rahu"] = ctx["rahu"]
        by_name["Ketu"] = ctx["ketu"]
        for name, (house, sign, nak) in spec["planets"].items():
            p = by_name[name]
            assert p["house"] == house, (chart_id, name, "house")
            assert p["sign"] == sign, (chart_id, name, "sign")
            assert p["nakshatra"] == nak, (chart_id, name, "nakshatra")
        dashas = ctx["dashas"]
        for key, expected in (("current_md", spec["md"]), ("current_ad", spec["ad"]),
                              ("current_pd", spec["pd"])):
            got = dashas[key]
            assert got["lord"] == expected[0], (chart_id, key, "lord")
            assert got["start"][:10] == expected[1], (chart_id, key, "start")
            assert got["end"][:10] == expected[2], (chart_id, key, "end")
        assert {y["name"] for y in ctx["yogas"]} == set(spec["yogas"]), chart_id
        ss = ctx["transits"]["sade_sati"]
        assert ss["is_active"] == spec["sade_sati"]["active"], chart_id
        assert ss["phase"] == spec["sade_sati"]["phase"], chart_id
        assert ss["natal_moon_sign"] == spec["sade_sati"]["moon_sign"], chart_id


# ---------------------------------------------------------------------------
# Stub answers. Each case is a stub "LLM answer" plus the claims it states,
# labelled correct/incorrect against the golden chart, and the retrieved
# chunks it cites. The eval never calls a live LLM.
# ---------------------------------------------------------------------------

def _chunk(work: str, text: str, chapter: str = "1", verse: str = "1") -> SearchResult:
    return SearchResult(
        chunk=CorpusChunk(
            work=work, chapter=chapter, verse=verse, text=text,
            source_file="golden.txt", char_start=0, char_end=len(text), tier="verse",
        ),
        score=0.9,
    )


def _ordinal(n: int) -> str:
    return {1: "1st", 2: "2nd", 3: "3rd"}.get(n, f"{n}th")


def _correct_answer(spec: dict) -> tuple[str, list[tuple[str, bool]]]:
    """Build a fully correct stub answer from the hard-coded golden facts."""
    moon_h, moon_s, moon_n = spec["planets"]["Moon"]
    sat_h, sat_s, _sat_n = spec["planets"]["Saturn"]
    md_lord, md_s, md_e = spec["md"]
    ad_lord, ad_s, ad_e = spec["ad"]
    md_name, ad_name = _node_name(md_lord), _node_name(ad_lord)
    answer = (
        f"Your Moon is in the {moon_h}{_ordinal(moon_h)[-2:]} house in {moon_s} "
        f"({moon_n}). Saturn is in the {sat_h}{_ordinal(sat_h)[-2:]} house in {sat_s} [1]. "
        f"Your {md_name} Mahadasha runs from {md_s} to {md_e}, and the current "
        f"{ad_name} Antardasha runs from {ad_s} to {ad_e} [2]."
    )
    claims = [
        (f"Moon house {moon_h}", True),
        (f"Moon sign {moon_s}", True),
        (f"Moon nakshatra {moon_n}", True),
        (f"Saturn house {sat_h}", True),
        (f"Saturn sign {sat_s}", True),
        (f"{md_name} MD {md_s} to {md_e}", True),
        (f"{ad_name} AD {ad_s} to {ad_e}", True),
    ]
    return answer, claims


def _correct_results(spec: dict) -> list[SearchResult]:
    moon_h, moon_s, moon_n = spec["planets"]["Moon"]
    sat_h, sat_s, _sat_n = spec["planets"]["Saturn"]
    md_lord, _md_s, _md_e = spec["md"]
    return [
        _chunk("BPHS",
               f"The Moon in the {_ordinal(moon_h)} house in {moon_s} ({moon_n}) "
               f"and Saturn in the {_ordinal(sat_h)} house in {sat_s} shape the "
               "native's mind and discipline."),
        _chunk("Phaladeepika",
               f"The {_node_name(md_lord)} Mahadasha and its Antardasha periods "
               "govern the timing of events in Vimshottari Dasha."),
    ]


@dataclass
class GoldenCase:
    """One stub-answer eval case."""

    case_id: str
    chart_id: str
    question: str
    language: str
    answer: str
    results: list[SearchResult]
    # (claim label, is the claim correct against the golden chart?)
    claims: list[tuple[str, bool]]
    # flag kinds the validator is expected to raise for this case (after-mode)
    expected_flags: list[str] = field(default_factory=list)


def build_golden_cases() -> list[GoldenCase]:
    """Assemble the golden QA cases: correct + corrupted stub answers."""
    cases: list[GoldenCase] = []
    # 1. One fully correct answer per golden chart (12 cases).
    for chart_id, spec in GOLDEN_CHARTS.items():
        answer, claims = _correct_answer(spec)
        cases.append(GoldenCase(
            case_id=f"correct-{chart_id}",
            chart_id=chart_id,
            question="Tell me about my Moon, Saturn and current dasha.",
            language="en",
            answer=answer,
            results=_correct_results(spec),
            claims=claims,
        ))

    # 2. Wrong house: user-1997 Moon is in the 8th, not the 3rd.
    spec = GOLDEN_CHARTS["user-1997"]
    cases.append(GoldenCase(
        case_id="wrong-house-moon",
        chart_id="user-1997",
        question="Where is my Moon placed?",
        language="en",
        answer=("Your Moon is in the 3rd house in Scorpio (Vishakha). "
                "Saturn is in the 12th house in Pisces [1]."),
        results=_correct_results(spec),
        claims=[("Moon house 3", False), ("Moon sign Scorpio", True),
                ("Saturn house 12", True)],
        expected_flags=["placement_mismatch"],
    ))

    # 3. Wrong sign: ktm-2000 Sun is in Sagittarius, not Capricorn.
    spec = GOLDEN_CHARTS["ktm-2000"]
    cases.append(GoldenCase(
        case_id="wrong-sign-sun",
        chart_id="ktm-2000",
        question="Where is my Sun placed?",
        language="en",
        answer=("Your Sun is in the 1st house in Capricorn (Mula). "
                "Budhaditya Yoga is present in your chart [1]."),
        results=_correct_results(spec),
        claims=[("Sun house 1", True), ("Sun sign Capricorn", False),
                ("Budhaditya Yoga present", True)],
        # The [1] on the yoga sentence is also unsupported: chunk [1] is
        # about Moon/Saturn placements, not Budhaditya Yoga.
        expected_flags=["placement_mismatch", "citation_unsupported"],
    ))

    # 4. Wrong dasha date, attributed: london-1978 Moon AD ends 2026-12-22.
    spec = GOLDEN_CHARTS["london-1978"]
    cases.append(GoldenCase(
        case_id="wrong-dasha-date",
        chart_id="london-1978",
        question="When does my current antardasha end?",
        language="en",
        answer=("Your Mercury-Moon Antardasha runs until 2027-06-01, "
                "and your Mercury Mahadasha runs from 2018-06-22 to 2035-06-23 [1]."),
        results=_correct_results(spec),
        claims=[("Moon AD ends 2027-06-01", False),
                ("Mercury MD 2018-06-22 to 2035-06-23", True)],
        expected_flags=["date_mismatch"],
    ))

    # 5. Impossible date: outside every dasha range of the chart.
    cases.append(GoldenCase(
        case_id="impossible-date",
        chart_id="london-1978",
        question="When will my career peak?",
        language="en",
        answer=("Your peak career window is 1970-05-05 to 1970-06-05, "
                "under Mercury Mahadasha [1]."),
        results=_correct_results(spec),
        claims=[("window 1970-05-05 to 1970-06-05", False)],
        # The [1] on the dasha sentence is also unsupported: chunk [1] is
        # about Moon/Saturn placements, not dasha timing.
        expected_flags=["date_mismatch", "citation_unsupported"],
    ))

    # 6. Yoga claimed present but absent: nyc-1985 has no Hamsa Yoga.
    spec = GOLDEN_CHARTS["nyc-1985"]
    cases.append(GoldenCase(
        case_id="yoga-false-present",
        chart_id="nyc-1985",
        question="Do I have Hamsa Yoga?",
        language="en",
        answer=("Yes, Hamsa Yoga is present in your chart and gives great fortune [1]. "
                "Gaja Kesari Yoga is also present."),
        results=[
            _chunk("Phaladeepika",
                   "Hamsa Yoga is formed when Jupiter is in a Kendra in its own or "
                   "exaltation sign. Gaja Kesari Yoga is formed when Jupiter is in "
                   "a Kendra from the Moon."),
        ],
        claims=[("Hamsa Yoga present", False), ("Gaja Kesari Yoga present", True)],
        expected_flags=["yoga_mismatch"],
    ))

    # 7. Yoga claimed absent but present: ktm-2010 HAS Hamsa Yoga.
    spec = GOLDEN_CHARTS["ktm-2010"]
    cases.append(GoldenCase(
        case_id="yoga-false-absent",
        chart_id="ktm-2010",
        question="Do I have Hamsa Yoga?",
        language="en",
        answer=("No, Hamsa Yoga is absent from your chart. "
                "Budhaditya Yoga is present [1]."),
        results=[
            _chunk("Phaladeepika",
                   "Hamsa Yoga is formed when Jupiter is in a Kendra in its own or "
                   "exaltation sign. Budhaditya Yoga is formed by the conjunction "
                   "of Sun and Mercury."),
        ],
        claims=[("Hamsa Yoga absent", False), ("Budhaditya Yoga present", True)],
        expected_flags=["yoga_mismatch"],
    ))

    # 8. Wrong Sade Sati phase: london-1978 is Setting, not Peak.
    spec = GOLDEN_CHARTS["london-1978"]
    cases.append(GoldenCase(
        case_id="sade-sati-wrong-phase",
        chart_id="london-1978",
        question="Am I in Sade Sati?",
        language="en",
        answer=("Yes, you are in Sade Sati and it is in its Peak phase [1]. "
                "Your Moon is in the 9th house in Aquarius."),
        results=_correct_results(spec),
        claims=[("Sade Sati active", True), ("Sade Sati Peak phase", False),
                ("Moon house 9", True)],
        # The [1] on the Sade Sati sentence is also unsupported: chunk [1]
        # never mentions Sade Sati.
        expected_flags=["sade_sati_mismatch", "citation_unsupported"],
    ))

    # 9. Sade Sati denied while active: pokhara-1999 is in Peak Sade Sati.
    spec = GOLDEN_CHARTS["pokhara-1999"]
    cases.append(GoldenCase(
        case_id="sade-sati-false-absent",
        chart_id="pokhara-1999",
        question="Am I in Sade Sati?",
        language="en",
        answer=("No, there is no Sade Sati active for you now [1]. "
                "Your Moon is in the 12th house in Pisces."),
        results=_correct_results(spec),
        claims=[("Sade Sati inactive", False), ("Moon house 12", True)],
        # The [1] on the Sade Sati sentence is also unsupported: chunk [1]
        # never mentions Sade Sati.
        expected_flags=["sade_sati_mismatch", "citation_unsupported"],
    ))

    # 10. Out-of-range citation: [9] with only 2 results.
    spec = GOLDEN_CHARTS["user-1997"]
    cases.append(GoldenCase(
        case_id="citation-out-of-range",
        chart_id="user-1997",
        question="Tell me about my chart.",
        language="en",
        answer=("Your Moon is in the 8th house in Scorpio [9]. "
                "Saturn is in the 12th house in Pisces [1]."),
        results=_correct_results(spec),
        claims=[("Moon house 8", True), ("Saturn house 12", True)],
        expected_flags=["citation_out_of_range"],
    ))

    # 11. Unsupported citation: a Saturn-remedy claim cited to a Hamsa Yoga chunk.
    cases.append(GoldenCase(
        case_id="citation-unsupported",
        chart_id="user-1997",
        question="What remedy helps my Saturn?",
        language="en",
        answer=("Saturn in the 12th house in Pisces needs a 43-day daytime upaya "
                "of feeding crows and donating sesame [1]. "
                "Your Moon is in the 8th house in Scorpio [2]."),
        results=[
            _chunk("Phaladeepika",
                   "Hamsa Yoga is formed when Jupiter is in a Kendra in its own or "
                   "exaltation sign, giving the native great fortune and fame."),
            _chunk("BPHS",
                   "The Moon in the 8th house in Scorpio (Vishakha) shapes the "
                   "native's mind and emotional depth."),
        ],
        claims=[("Saturn house 12", True), ("Moon house 8", True)],
        expected_flags=["citation_unsupported"],
    ))

    # 12. Nepali question, correct answer (Devanagari planet/sign names).
    cases.append(GoldenCase(
        case_id="nepali-correct",
        chart_id="user-1997",
        question="मेरो बुध महादशा कहिले सकिन्छ?",
        language="ne",
        answer=("तपाईंको बुध महादशा 2018-01-22 देखि 2035-01-22 सम्म चल्छ। "
                "शनि 12th house मा मीन राशिमा छ [1]।"),
        results=[
            _chunk("BPHS",
                   "Saturn in the 12th house in Pisces and the Mercury Mahadasha "
                   "from 2018-01-22 to 2035-01-22 shape the native's timing."),
        ],
        claims=[("Mercury MD 2018-01-22 to 2035-01-22", True),
                ("Saturn house 12", True), ("Saturn sign Pisces", True)],
        expected_flags=[],
    ))

    # 13. Nepali question, corrupted answer (wrong house for Saturn).
    cases.append(GoldenCase(
        case_id="nepali-wrong-house",
        chart_id="user-1997",
        question="मेरो शनि कहाँ छ?",
        language="ne",
        answer=("शनि 8th house मा मीन राशिमा छ [1]।"),
        results=[
            _chunk("BPHS",
                   "Saturn in the 12th house in Pisces shapes the native's discipline."),
        ],
        claims=[("Saturn house 8", False), ("Saturn sign Pisces", True)],
        expected_flags=["placement_mismatch"],
    ))

    return cases


# ---------------------------------------------------------------------------
# Independent scoring instrument (does NOT import the validator): the
# citation-support judge used to score both the before and after runs.
# Rule: a cited sentence is supported when the chunk shares a distinctive
# astrological term (planet / sign / nakshatra / yoga / house number) or at
# least 30% of the sentence's content words. Sentences with fewer than 4
# content words are too generic to judge and count as supported.
# ---------------------------------------------------------------------------
_STOPWORDS = {
    "the", "a", "an", "is", "in", "of", "and", "to", "your", "you", "are", "it",
    "this", "that", "with", "for", "from", "on", "as", "at", "by", "be", "has",
    "have", "will", "when", "what", "how", "my", "its", "or", "not", "no",
}

_DISTINCTIVE_TERMS = [
    "sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu",
    "aries", "taurus", "gemini", "cancer", "leo", "virgo", "libra", "scorpio",
    "sagittarius", "capricorn", "aquarius", "pisces",
    "ashwini", "bharani", "krittika", "rohini", "mrigashira", "ardra",
    "punarvasu", "pushya", "ashlesha", "magha", "purva phalguni",
    "uttara phalguni", "hasta", "chitra", "swati", "vishakha", "anuradha",
    "jyeshtha", "mula", "purva ashadha", "uttara ashadha", "shravana",
    "dhanishta", "shatabhisha", "purva bhadrapada", "uttara bhadrapada", "revati",
    "hamsa", "gaja kesari", "budhaditya", "malavya", "bhadra", "ruchiaka",
    "sasa", "raja yoga", "dhana yoga", "sade sati", "mahadasha", "antardasha",
    "dasha", "yoga", "upaya", "remedy",
]


def _content_words(text: str) -> set[str]:
    words = set(re.findall(r"[a-z]+", text.lower()))
    return {w for w in words if w not in _STOPWORDS}


def _sentence_with_marker(answer: str, number: int) -> str:
    """First sentence containing the [n] marker (markers are sentence-final)."""
    for sentence in re.split(r"(?<=[.!?])\s+|\n+", answer):
        if f"[{number}]" in sentence:
            return sentence
    return ""


def chunk_supports_sentence(chunk_text: str, sentence: str) -> bool:
    """Independent support judge: does the chunk text support the sentence?"""
    claim_words = _content_words(sentence)
    if len(claim_words) < 4:
        return True
    chunk_lower = chunk_text.lower()
    for term in _DISTINCTIVE_TERMS:
        if term in sentence.lower() and term in chunk_lower:
            return True
    for match in re.finditer(r"(\d{1,2})(?:st|nd|rd|th)\s+house|house\s+(\d{1,2})",
                             sentence.lower()):
        n = match.group(1) or match.group(2)
        if (f"{n}th house" in chunk_lower or f"house {n}" in chunk_lower
                or re.search(rf"\b{n}(?:st|nd|rd|th)\b", chunk_lower)):
            return True
    chunk_words = _content_words(chunk_text)
    overlap = len(claim_words & chunk_words) / max(len(claim_words), 1)
    return overlap >= 0.30


@dataclass
class EvalReport:
    """Aggregate scores for one eval run."""

    mode: str
    citation_precision: float | None
    date_placement_match_rate: float | None
    detection_rate: float | None
    citations_checked: int = 0
    citations_supported: int = 0
    claims_checked: int = 0
    claims_correct: int = 0
    claims_flagged: int = 0
    incorrect_claims: int = 0
    incorrect_flagged: int = 0
    retrieval_hit_rate: float | None = None
    # After-mode only: claims in answers the validator did not flag with a
    # chart-claim kind, and how many of those are correct.
    unflagged_claims: int = 0
    unflagged_correct: int = 0
    unflagged_match_rate: float | None = None
    citations_dropped: int = 0

    def summary(self) -> str:
        def pct(v: float | None) -> str:
            return f"{v:.3f}" if v is not None else "n/a"
        return (
            f"eval[{self.mode}] citation_precision={pct(self.citation_precision)} "
            f"({self.citations_supported}/{self.citations_checked}) "
            f"date_placement_match={pct(self.date_placement_match_rate)} "
            f"({self.claims_correct}/{self.claims_checked}) "
            f"unflagged_match={pct(self.unflagged_match_rate)} "
            f"({self.unflagged_correct}/{self.unflagged_claims}) "
            f"detection={pct(self.detection_rate)} "
            f"({self.incorrect_flagged}/{self.incorrect_claims}) "
            f"dropped_citations={self.citations_dropped} "
            f"retrieval_hit={pct(self.retrieval_hit_rate)}"
        )


_CHART_CLAIM_KINDS = {
    "placement_mismatch", "date_mismatch", "date_unverifiable",
    "yoga_mismatch", "sade_sati_mismatch",
}


def evaluate_golden_set(mode: str = "before") -> EvalReport:
    """Score the golden set in ``before`` or ``after`` mode.

    Before mode: the delivered answer is the raw stub text, citations are
    whatever ``extract_citations`` returns (range check only), and nothing
    is ever flagged. After mode: each stub answer is run through
    ``validate_answer`` and the cleaned output is re-scored; a claim
    counts as detected when its case raises the expected flag kind.
    """
    assert mode in ("before", "after")
    report = EvalReport(mode=mode, citation_precision=None,
                        date_placement_match_rate=None, detection_rate=0.0)
    if mode == "after":
        from nakshatra.ai.validate import validate_answer

    for case in build_golden_cases():
        if mode == "before":
            # Before behaviour: citations are whatever extract_citations
            # returns (range check only); judge each one for support with
            # the independent instrument.
            kept_numbers = [
                n for n in sorted({int(m) for m in re.findall(r"\[(\d+)\]", case.answer)})
                if 1 <= n <= len(case.results)
            ]
            for number in kept_numbers:
                report.citations_checked += 1
                sentence = _sentence_with_marker(case.answer, number)
                if chunk_supports_sentence(case.results[number - 1].chunk.text, sentence):
                    report.citations_supported += 1
            report.claims_checked += len(case.claims)
            report.claims_correct += sum(1 for _label, ok in case.claims if ok)
            report.incorrect_claims += sum(1 for _label, ok in case.claims if not ok)
            # Before: nothing is flagged, so every claim is "unflagged".
            report.unflagged_claims += len(case.claims)
            report.unflagged_correct += sum(1 for _label, ok in case.claims if ok)
        else:
            ctx = build_golden_context(case.chart_id)
            result = validate_answer(case.answer, ctx, case.results)
            report.citations_dropped += len(result.citations_dropped)
            # Citation precision after validation: the independent
            # instrument judges only the citations the validator kept.
            for number in result.citations_kept:
                report.citations_checked += 1
                sentence = _sentence_with_marker(case.answer, number)
                if chunk_supports_sentence(case.results[number - 1].chunk.text, sentence):
                    report.citations_supported += 1
            report.claims_checked += len(case.claims)
            report.claims_correct += sum(1 for _label, ok in case.claims if ok)
            report.incorrect_claims += sum(1 for _label, ok in case.claims if not ok)
            chart_kinds = {f.kind for f in result.flags if f.kind in _CHART_CLAIM_KINDS}
            if chart_kinds:
                report.claims_flagged += len(case.claims)
                if any(not ok for _label, ok in case.claims):
                    report.incorrect_flagged += sum(
                        1 for _label, ok in case.claims if not ok)
            else:
                report.unflagged_claims += len(case.claims)
                report.unflagged_correct += sum(1 for _label, ok in case.claims if ok)
    if report.citations_checked:
        report.citation_precision = report.citations_supported / report.citations_checked
    if report.claims_checked:
        report.date_placement_match_rate = report.claims_correct / report.claims_checked
    if report.unflagged_claims:
        report.unflagged_match_rate = report.unflagged_correct / report.unflagged_claims
    if report.incorrect_claims:
        report.detection_rate = report.incorrect_flagged / report.incorrect_claims
    report.retrieval_hit_rate = _retrieval_hit_rate()
    return report


def _retrieval_hit_rate() -> float:
    from nakshatra.ai.service import RAGService

    retriever = RAGService().load()
    hits = 0
    for query, check in GOLDEN_RETRIAL_QUERIES:
        results = retriever.search(query, top_k=5)
        if check(results):
            hits += 1
    return hits / len(GOLDEN_RETRIAL_QUERIES)


# ---------------------------------------------------------------------------
# Golden retrieval queries — 6 NEW queries extending the 4 in
# tests/test_classical_rag_consultation.py (Hamsa/Phaladeepika, Budhaditya/
# Saravali, Jaimini karakas, Uttara Kalamrita retrograde). Verified by probe
# against the real index on 2026-11-22.
# ---------------------------------------------------------------------------
def _any_text(results, needle: str) -> bool:
    return any(needle.lower() in r.chunk.text.lower() for r in results)


GOLDEN_RETRIAL_QUERIES: list[tuple[str, object]] = [
    ("Sade Sati Saturn transit 12th from Moon difficult period",
     lambda r: _any_text(r, "Sade Sati")),
    ("Gaja Kesari Yoga Moon Jupiter kendra from each other",
     lambda r: _any_text(r, "Gaja Kesari")),
    ("Lal Kitab Saturn upaya remedy afflicted Shani",
     lambda r: "Lal Kitab" in [x.chunk.work for x in r]),
    ("Vimshottari dasha balance years Moon nakshatra at birth",
     lambda r: _any_text(r, "Dasha")),
    ("Kuja Dosha Mars Manglik houses marriage delay",
     lambda r: _any_text(r, "Kuja Dosha")),
    ("Rahu Ketu eclipse nodes Chaya Graha shadow planets",
     lambda r: _any_text(r, "Rahu") and _any_text(r, "Ketu")),
]


def test_golden_retrieval_queries():
    """The 6 new golden retrieval queries hit the expected classical content."""
    from nakshatra.ai.service import RAGService

    retriever = RAGService().load()
    for query, check in GOLDEN_RETRIAL_QUERIES:
        results = retriever.search(query, top_k=5)
        assert len(results) > 0, query
        assert check(results), f"golden retrieval query missed: {query!r}"


def test_eval_before_score():
    """BEFORE score (pre-validator pipeline): unsupported citations pass,
    wrong dates/positions are delivered unflagged."""
    report = evaluate_golden_set(mode="before")
    print("\n" + report.summary(), flush=True)
    assert report.citation_precision is not None and report.citation_precision < 1.0
    assert report.date_placement_match_rate is not None
    assert report.date_placement_match_rate < 1.0
    assert report.detection_rate == 0.0
    assert report.retrieval_hit_rate == 1.0

# ---------------------------------------------------------------------------
# AFTER mode: validator behaviour on the golden set.
# ---------------------------------------------------------------------------

def test_eval_after_score():
    """AFTER score (validator wired in): unsupported citations are dropped,
    every incorrect chart claim is flagged, and no correct claim is."""
    report = evaluate_golden_set(mode="after")
    print("\n" + report.summary(), flush=True)
    assert report.citation_precision == 1.0
    assert report.unflagged_match_rate == 1.0
    assert report.detection_rate == 1.0
    assert report.citations_dropped > 0
    assert report.retrieval_hit_rate == 1.0


def test_eval_after_flags_match_expected_kinds():
    """Per case: the validator raises exactly the expected flag kinds —
    no missing flags on corrupted answers, no false flags on correct ones."""
    from nakshatra.ai.validate import validate_answer

    for case in build_golden_cases():
        ctx = build_golden_context(case.chart_id)
        result = validate_answer(case.answer, ctx, case.results)
        got = sorted({f.kind for f in result.flags})
        assert got == sorted(set(case.expected_flags)), (
            f"{case.case_id}: got {got}, expected {sorted(set(case.expected_flags))}; "
            f"flags={[f.message for f in result.flags]}"
        )
        if not case.expected_flags:
            assert result.valid
            assert result.cleaned_answer == case.answer


def test_eval_before_after_comparison():
    """The validator strictly improves both headline scores."""
    before = evaluate_golden_set(mode="before")
    after = evaluate_golden_set(mode="after")
    assert after.citation_precision > before.citation_precision
    assert after.unflagged_match_rate > before.unflagged_match_rate
    assert after.detection_rate > before.detection_rate
    print(f"\nbefore: {before.summary()}\nafter:  {after.summary()}", flush=True)


# ---------------------------------------------------------------------------
# Validator unit tests (synthetic minimal chart contexts).
# ---------------------------------------------------------------------------

def _mini_context() -> dict:
    return {
        "ascendant": {"sign": "Aries"},
        "planets": [
            {"name": "Sun", "house": 2, "sign": "Taurus", "nakshatra": "Krittika",
             "degree_in_sign": 7.11, "retrograde": False},
            {"name": "Moon", "house": 8, "sign": "Scorpio", "nakshatra": "Vishakha",
             "degree_in_sign": 1.94, "retrograde": False},
            {"name": "Saturn", "house": 12, "sign": "Pisces", "nakshatra": "Revati",
             "degree_in_sign": 22.55, "retrograde": True},
        ],
        "rahu": {"name": "Rahu", "house": 6, "sign": "Virgo",
                 "nakshatra": "Uttara Phalguni", "degree_in_sign": 1.79,
                 "retrograde": True},
        "dashas": {
            "current_md": {"lord": "Mercury", "start": "2018-01-22", "end": "2035-01-22"},
            "current_ad": {"lord": "Mars", "start": "2026-07-24", "end": "2027-07-21"},
            "current_pd": {"lord": "Jupiter", "start": "2026-10-07", "end": "2026-11-24"},
            "mahadashas": [
                {"lord": "Mercury", "start": "2018-01-22", "end": "2035-01-22",
                 "subs": [
                     {"lord": "Mars", "start": "2026-07-24", "end": "2027-07-21",
                      "subs": [
                          {"lord": "Jupiter", "start": "2026-10-07", "end": "2026-11-24"},
                      ]},
                 ]},
            ],
        },
        "yogas": [{"name": "Budhaditya Yoga"}, {"name": "Gaja Kesari Yoga"}],
        "transits": {"sade_sati": {"is_active": False, "phase": None}},
        "birth_data": {"year": 1997, "month": 5, "day": 22},
    }


def test_validate_correct_answer_is_clean():
    from nakshatra.ai.validate import validate_answer

    result = validate_answer(
        "Your Moon is in the 8th house in Scorpio (Vishakha). "
        "Saturn is retrograde in the 12th house in Pisces [1]. "
        "Your Mercury Mahadasha runs from 2018-01-22 to 2035-01-22.",
        _mini_context(),
        [_chunk("BPHS", "The Moon in the 8th house in Scorpio and Saturn retrograde "
                        "in the 12th house in Pisces.")],
    )
    assert result.valid, [f.message for f in result.flags]
    assert result.date_placement_match_rate == 1.0
    assert result.citation_precision == 1.0


def test_validate_degree_tolerance():
    from nakshatra.ai.validate import validate_answer

    ctx = _mini_context()
    # 1.9° vs true 1.94° (rounding) passes; 3.0° does not.
    ok = validate_answer("Moon is at 1.9° in Scorpio.", ctx, [])
    assert ok.valid, [f.message for f in ok.flags]
    bad = validate_answer("Moon is at 3.0° in Scorpio.", ctx, [])
    assert any(f.kind == "placement_mismatch" for f in bad.flags)


def test_validate_no_chart_context_skips_chart_checks():
    from nakshatra.ai.validate import validate_answer

    result = validate_answer(
        "Saturn is in the 12th house in Pisces [1].",
        None,
        [_chunk("BPHS", "Saturn in the 12th house in Pisces governs discipline.")],
    )
    assert result.valid
    assert result.date_placement_match_rate is None


def test_validate_empty_answer_and_no_results():
    from nakshatra.ai.validate import validate_answer

    result = validate_answer("", _mini_context(), [])
    assert result.valid
    assert result.cleaned_answer == ""
    result = validate_answer("See [1] and [2].", _mini_context(), [])
    assert {f.kind for f in result.flags} == {"citation_out_of_range"}
    assert result.citations_dropped == [1, 2]
    assert "[1]" not in result.cleaned_answer and "[2]" not in result.cleaned_answer


def test_validate_reversed_date_range():
    from nakshatra.ai.validate import validate_answer

    result = validate_answer(
        "Window 1: 2027-07-21 to 2026-07-24.", _mini_context(), [])
    assert any(f.kind == "date_mismatch" for f in result.flags)


def test_validate_citations_kwarg_alias():
    from nakshatra.ai.validate import validate_answer

    result = validate_answer(
        "Moon in the 8th house [5].", _mini_context(),
        citations=[_chunk("BPHS", "Moon in the 8th house.")],
    )
    assert result.citations_dropped == [5]


# ---------------------------------------------------------------------------
# Wiring: LLMSynthesizer validates live answers, drops bad citations.
# ---------------------------------------------------------------------------

def test_llm_synthesizer_validates_and_drops_citations():
    from nakshatra.ai.synthesize import Answer, BaseSynthesizer, LLMSynthesizer

    class StubLLM(LLMSynthesizer):
        def _complete(self, prompt, system_prompt=None):
            return (
                "Your Moon is in the 3rd house in Scorpio [1]. "
                "Saturn in the 12th house in Pisces needs a 43-day upaya [2]."
            )

    results = [
        _chunk("BPHS", "The Moon in the 8th house in Scorpio shapes the mind."),
        _chunk("Phaladeepika", "Hamsa Yoga is formed when Jupiter is in a Kendra."),
    ]
    synth = StubLLM(provider="openai", model="stub-model")
    answer: Answer = synth.synthesize(
        "Where is my Moon?", results,
        birth_context=build_golden_context("user-1997"), language="en",
    )
    assert answer.model == "stub-model"
    # Wrong house flagged; unsupported [2] dropped from text and citations.
    assert answer.validation is not None
    assert any(f.kind == "placement_mismatch" for f in answer.validation.flags)
    assert any(f.kind == "citation_unsupported" for f in answer.validation.flags)
    assert "[2]" not in answer.answer
    assert "[1]" in answer.answer
    assert len(answer.citations) == 1
    assert answer.citations[0].work == "BPHS"
