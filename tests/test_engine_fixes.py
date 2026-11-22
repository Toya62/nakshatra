"""Regression tests for Nakshatra Task 13, Step 2 — deterministic engine bugs.

One test per bug fixed in step 2 (see PROMPT-TASK-13-AI-ACCURACY.md, step 2):
(a) predictor Samasaptaka dead code, (b) yogas Parivartana-by-lordship +
Kendra-Trikona house 1, (c) Kuja Dosha house-set disagreement, (d) unknown
Moon nakshatra + Stree Deergha boundary, (e) muhurtha polar fabricated
times, (f) calendar_bs silent day clamping, (g) JHora ayanamsa sign,
Rahu/Ketu quadrant houses, transit-lock sidereal mode.
No live LLM calls, no network.
"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
import swisseph as swe
from fastapi.testclient import TestClient

from nakshatra.api import app
from nakshatra.calendar_bs import ad_to_bs, bs_to_ad
from nakshatra.compatibility import (
    calculate_compatibility,
    calculate_extended_kutas,
    calculate_gana,
    calculate_nadi,
    calculate_tara,
    calculate_yoni,
    evaluate_chart_kuja_dosha,
)
from nakshatra.core import (
    SIGN_LORDS,
    Ayanamsa,
    BirthData,
    ChartData,
    HouseCusp,
    HouseSystem,
    PlanetPosition,
    calculate_chart,
)
from nakshatra.muhurtha import calculate_muhurtha
from nakshatra.panchanga import calculate_panchanga
from nakshatra.predictor import dasha_lord_relationship
from nakshatra.remedies import calculate_remedies
from nakshatra.transits import calculate_transits, scan_transit_window
from nakshatra.yogas import _detect_parivartana, _detect_raja_and_dhana


def _tnp_chart() -> ChartData:
    """Reference chart: TNP (Palpa, Nepal — 22 May 1997, 04:53)."""
    return calculate_chart(
        BirthData(1997, 5, 22, 4, 53, 0, 27.8667, 83.4833, "Asia/Kathmandu")
    )


# ---------------------------------------------------------------------------
# (a) Samasaptaka dead code — predictor.py
# ---------------------------------------------------------------------------


def test_samasaptaka_opposition_is_not_sambandha():
    """Opposition (dist=7) must classify Samasaptaka, not Sambandha.

    In the TNP chart Sun is in Taurus (House 2) and Moon in Scorpio
    (House 8): 7 houses apart, so the pair normalises to "7/7", which
    used to fall through to the ("Sambandha", "Moderate") default.
    """
    chart = _tnp_chart()
    assert next(p for p in chart.planets if p.name == "Sun").house == 2
    assert next(p for p in chart.planets if p.name == "Moon").house == 8

    rel = dasha_lord_relationship("Sun", "Moon", chart)
    assert rel["pair"] == "7/7"
    assert "Samasaptaka" in rel["name"]
    assert "Sambandha" not in rel["name"]

    # Opposition is symmetric: the reverse direction must agree.
    rel_rev = dasha_lord_relationship("Moon", "Sun", chart)
    assert rel_rev["pair"] == "7/7"
    assert "Samasaptaka" in rel_rev["name"]


# ---------------------------------------------------------------------------
# (b) Yogas — Parivartana by lordship; Raja/Dhana house 1
# ---------------------------------------------------------------------------

_ZODIAC = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]


def _synthetic_aries_chart(placements: dict[str, tuple[str, int]]) -> ChartData:
    """Minimal Aries-Lagna chart for yoga-detector unit tests.

    ``placements`` maps planet name -> (sign, house). Houses are whole-sign
    Aries Lagna, so house lords follow the sign lords. Built with
    model_construct: the detectors under test only read planets + houses.
    """
    houses = [
        HouseCusp(
            house=i + 1,
            longitude=float(i * 30),
            sign=sign,
            sign_lord=SIGN_LORDS[sign],
            degree_in_sign=0.0,
        )
        for i, sign in enumerate(_ZODIAC)
    ]
    planets = [
        PlanetPosition(
            name=name,
            longitude=float(_ZODIAC.index(sign) * 30 + 5),
            sign=sign,
            sign_lord=SIGN_LORDS[sign],
            degree_in_sign=5.0,
            house=house,
        )
        for name, (sign, house) in placements.items()
    ]
    return ChartData.model_construct(planets=planets, houses=houses)


def test_parivartana_classified_by_lordship_not_placement():
    """Mercury<->Jupiter exchange: placement says Kahala, lordship says Dainya.

    Aries Lagna: Mercury in Sagittarius (House 9) and Jupiter in Gemini
    (House 3) exchange signs. By placement the pair sits in Houses 9/3,
    which the old code read as Kahala (3rd-house involvement). By lordship
    Mercury rules 3 and 6, Jupiter rules 9 and 12 — both rule a Dusthana
    (6th / 12th) — so per the docstring (Phaladeepika ch. 6 / BPHS) this is
    Dainya Parivartana, and the ruled Dusthana houses must be reported.
    """
    chart = _synthetic_aries_chart(
        {
            "Sun": ("Leo", 5),  # own sign: no accidental exchange
            "Moon": ("Cancer", 4),  # own sign
            "Mars": ("Aries", 1),  # own sign
            "Mercury": ("Sagittarius", 9),
            "Jupiter": ("Gemini", 3),
            "Venus": ("Taurus", 2),  # own sign
            "Saturn": ("Capricorn", 10),  # own sign
        }
    )
    yogas = _detect_parivartana(chart)
    assert len(yogas) == 1
    yoga = yogas[0]
    assert "Dainya Parivartana Yoga" in yoga.name
    assert "Kahala" not in yoga.name
    assert set(yoga.planets_involved) == {"Mercury", "Jupiter"}
    # Ruled houses, not placement houses: 6 and 12 (Dusthana) must appear.
    assert 6 in yoga.houses_involved
    assert 12 in yoga.houses_involved


def test_kendra_trikona_raja_yoga_includes_house_1():
    """A 1st lord conjunct a 5th lord forms Kendra-Trikona Raja Yoga.

    Aries Lagna: Mars (1st lord, also a Kendra lord — house 1 is a Kendra)
    conjoined with Sun (5th lord, a Trikona lord) in Leo (House 5). The old
    code checked kendra=[4, 7, 10] / trikona=[5, 9] and missed house 1
    entirely, so this yoga was never detected.
    """
    chart = _synthetic_aries_chart(
        {
            "Sun": ("Leo", 5),
            "Moon": ("Cancer", 4),
            "Mars": ("Leo", 5),  # conjoined with Sun
            "Mercury": ("Virgo", 6),
            "Jupiter": ("Sagittarius", 9),
            "Venus": ("Taurus", 2),
            "Saturn": ("Capricorn", 10),
        }
    )
    yogas = _detect_raja_and_dhana(chart)
    raja = [y for y in yogas if y.name.startswith("Kendra-Trikona Raja Yoga")]
    assert len(raja) == 1
    assert set(raja[0].planets_involved) == {"Mars", "Sun"}
    assert 1 in raja[0].houses_involved
    assert 5 in raja[0].houses_involved


# ---------------------------------------------------------------------------
# (c) Kuja Dosha house-set disagreement — compatibility.py / remedies.py
# ---------------------------------------------------------------------------


def test_kuja_dosha_mars_in_house_2_agrees_in_both_modules():
    """Mars in House 2 must give the same verdict in both modules.

    Chart 15 Feb 1998, 06:00, Kathmandu: Mars is 2nd from Lagna, 6th from
    Moon and 3rd from Venus — so only the Lagna count can flag it, which
    isolates the house-set disagreement (compatibility used {1,2,4,7,8,12},
    remedies used (1,4,7,8,12)).
    """
    chart = calculate_chart(
        BirthData(1998, 2, 15, 6, 0, 0, 27.8667, 83.4833, "Asia/Kathmandu")
    )
    mars = next(p for p in chart.planets if p.name == "Mars")
    assert mars.house == 2

    kuja = evaluate_chart_kuja_dosha(chart)
    assert kuja.is_manglik is True
    assert kuja.afflicted_houses_lagna == [2]

    remedies = calculate_remedies(chart)
    mars_remedies = [r for r in remedies.afflicted_planets if r.planet == "Mars"]
    assert len(mars_remedies) == 1
    assert any("Kuja Dosha" in reason for reason in mars_remedies[0].affliction_reasons)

    # The relationship predictor had a THIRD copy of the old set
    # (predictor.py, Lagna check) — it must agree as well.
    from nakshatra.predictor import evaluate_relationship

    relationship = evaluate_relationship(chart)
    assert "Kuja Dosha indication: Mars in House 2" in relationship.promise_summary


# ---------------------------------------------------------------------------
# (d) Unknown Moon nakshatra + Stree Deergha boundary — compatibility.py
# ---------------------------------------------------------------------------


def test_unknown_moon_nakshatra_returns_unknown_not_keyerror():
    """Yoni/Gana/Nadi must return an 'unknown' score, never raise KeyError."""
    for fn, max_score in (
        (lambda b, g: calculate_yoni(b, g), 4.0),
        (lambda b, g: calculate_gana(b, g), 6.0),
        (lambda b, g: calculate_nadi(b, g), 8.0),
    ):
        result = fn("Ashwini", "NotANakshatra")
        assert result.max_score == max_score
        assert result.obtained_score == 0.0
        assert result.is_favorable is False
        assert "Unknown" in result.notes

    # Empty string (what ChartData carries when the Moon has no nakshatra).
    assert "Unknown" in calculate_yoni("", "Ashwini").notes
    assert "Unknown" in calculate_gana("Ashwini", "").notes
    assert "Unknown" in calculate_nadi("", "").notes


def test_tara_unknown_nakshatra_no_longer_defaults_to_ashwini():
    """Tara must not silently default an unknown nakshatra index to 1 (Ashwini)."""
    result = calculate_tara(None, 5)
    assert result.obtained_score == 0.0
    assert result.is_favorable is False
    assert "Unknown" in result.notes
    assert "Ashwini" not in result.bride_val
    # Known indices still work exactly as before.
    assert calculate_tara(1, 1).obtained_score == 3.0


def test_unknown_moon_nakshatra_full_report_path():
    """The full compatibility report completes with unknown Moon nakshatra.

    Bride's Moon nakshatra is blanked; the report must not crash and must
    not present Ashwini-defaulted Tara/Yoni/Gana/Nadi (or extended-kuta)
    scores as if they were computed.
    """
    bride = _tnp_chart()
    groom = calculate_chart(
        BirthData(1995, 11, 28, 8, 30, 0, 28.6139, 77.2090, "Asia/Kolkata")
    )
    bride_unknown = bride.model_copy(deep=True)
    moon = next(p for p in bride_unknown.planets if p.name == "Moon")
    moon.nakshatra = ""

    report = calculate_compatibility(bride_unknown, groom)
    for kuta in (
        report.ashtakoota.tara,
        report.ashtakoota.yoni,
        report.ashtakoota.gana,
        report.ashtakoota.nadi,
    ):
        assert kuta.obtained_score == 0.0
        assert "Unknown" in kuta.notes
    for kuta in (
        report.extended_kutas.mahendra,
        report.extended_kutas.stree_deergha,
        report.extended_kutas.rajju,
        report.extended_kutas.vedha,
    ):
        assert kuta.obtained_score == 0.0
        assert "Unknown" in kuta.notes
    # The unknown kutas contribute no phantom points to the total.
    assert report.ashtakoota.total_score == (
        report.ashtakoota.varna.obtained_score
        + report.ashtakoota.vashya.obtained_score
        + report.ashtakoota.graha_maitri.obtained_score
        + report.ashtakoota.bhakoot.obtained_score
    )


def test_stree_deergha_boundary_exactly_13_is_not_favourable():
    """Stree Deergha needs the groom's nakshatra MORE THAN 13 away.

    Classical rule: "beyond the 13th" / "more than 13" — so distance 13 is
    not favourable (the old code used >= 13, contradicting its own comment).
    Distance is counted bride -> groom, 1-indexed.
    """
    at_13 = calculate_extended_kutas("Ashwini", "Hasta", 1, 13)
    assert at_13.stree_deergha.obtained_score == 0.0
    assert at_13.stree_deergha.is_favorable is False

    at_14 = calculate_extended_kutas("Ashwini", "Chitra", 1, 14)
    assert at_14.stree_deergha.obtained_score == 1.0
    assert at_14.stree_deergha.is_favorable is True


# ---------------------------------------------------------------------------
# (e) Muhurtha polar latitudes — muhurtha.py
# ---------------------------------------------------------------------------


def test_muhurtha_polar_latitude_never_invents_sunrise_sunset():
    """At 78N in June (midnight sun) there is no sunrise/sunset to report.

    The old code invented sunrise 06:00 / sunset 18:00 (midnight JD + 0.25
    / + 0.75). Now it warns and raises ValueError; no fabricated time may
    appear anywhere in the message.
    """
    dt = datetime(2026, 6, 21, 12, 0, tzinfo=ZoneInfo("Europe/Oslo"))
    with pytest.warns(UserWarning, match="No sunrise/sunset"):
        with pytest.raises(ValueError, match="No sunrise/sunset") as excinfo:
            calculate_muhurtha(dt, 78.0, 16.0, "Europe/Oslo")
    assert "06:00" not in str(excinfo.value)
    assert "18:00" not in str(excinfo.value)


def test_muhurtha_polar_night_never_invents_sunrise_sunset():
    """At 78N in December (polar night) the same rule applies."""
    dt = datetime(2026, 12, 21, 12, 0, tzinfo=ZoneInfo("Europe/Oslo"))
    with pytest.warns(UserWarning, match="No sunrise/sunset"):
        with pytest.raises(ValueError, match="No sunrise/sunset"):
            calculate_muhurtha(dt, 78.0, 16.0, "Europe/Oslo")


# ---------------------------------------------------------------------------
# (f) BS calendar silent clamping — calendar_bs.py
# ---------------------------------------------------------------------------


def test_ad_to_bs_out_of_range_day_31_raises_instead_of_clamping():
    """AD 1800-05-31 used to return BS day 30 (min(day, 30)) silently."""
    with pytest.raises(ValueError, match="cannot be approximated"):
        ad_to_bs(1800, 5, 31)
    # Days the approximation can represent are still approximated (least-
    # breaking behaviour: only the clamping case is refused).
    assert ad_to_bs(1800, 5, 15).day == 15


def test_bs_to_ad_out_of_range_day_raises_instead_of_clamping():
    """BS 1900-01-30 used to return AD day 28 (min(day, 28)) silently."""
    with pytest.raises(ValueError, match="cannot be approximated"):
        bs_to_ad(1900, 1, 30)
    assert bs_to_ad(1900, 1, 15).day == 15


def test_bs_to_ad_invalid_day_for_the_month_raises():
    """Day 32 in Chaitra 2054 (31 days) used to fall through the fallback
    and return a fabricated AD date; day 32 in Jestha 2054 is valid."""
    with pytest.raises(ValueError, match="Invalid BS date"):
        bs_to_ad(2054, 12, 32)
    assert bs_to_ad(2054, 2, 32).formatted == "1997-06-14"


def test_calendar_api_returns_400_for_unclampable_dates():
    """The /calendar endpoints surface the refusal as HTTP 400, not 500."""
    client = TestClient(app)
    assert client.get("/calendar/bs", params={"year": 1800, "month": 5, "day": 31}).status_code == 400
    assert client.get("/calendar/ad", params={"year": 1900, "month": 1, "day": 30}).status_code == 400
    assert client.get("/calendar/bs", params={"year": 1997, "month": 5, "day": 22}).status_code == 200
    assert client.get("/calendar/ad", params={"year": 2054, "month": 2, "day": 9}).status_code == 200


# ---------------------------------------------------------------------------
# (g) Verdict items — JHora sign, Rahu/Ketu houses, transit lock
# ---------------------------------------------------------------------------


def test_jhora_panchanga_sun_matches_core_sun():
    """Panchanga Sun longitude for a JHora chart must match core.py's.

    core.py adds the 56.5318" JHora offset; panchanga.py used to subtract
    it, leaving the two ~113" apart.
    """
    chart = _tnp_chart()  # default ayanamsa is JHora Lahiri
    assert chart.ayanamsa == Ayanamsa.JHORA_LAHIRI
    sun_core = next(p for p in chart.planets if p.name == "Sun")
    panchanga = calculate_panchanga(
        datetime(1997, 5, 22, 4, 53, tzinfo=ZoneInfo("Asia/Kathmandu")),
        27.8667,
        83.4833,
        "Asia/Kathmandu",
    )
    assert abs(panchanga.sun_longitude - sun_core.longitude) < 0.01
    moon_core = next(p for p in chart.planets if p.name == "Moon")
    assert abs(panchanga.moon_longitude - moon_core.longitude) < 0.01


def test_jhora_transit_sun_and_rahu_match_core():
    """Transit longitudes for a JHora chart must match a core.py chart cast
    for the same moment, ayanamsa and place (tolerance 0.01 deg; the old
    sign error was 2 x 56.5318" = 0.031 deg)."""
    natal = calculate_chart(
        BirthData(2000, 1, 1, 12, 0, 0, 23.1765, 75.7885, "Asia/Kolkata")
    )
    assert natal.ayanamsa == Ayanamsa.JHORA_LAHIRI
    transit_dt = datetime(2026, 10, 18, 12, 0, tzinfo=ZoneInfo("Asia/Kolkata"))
    report = calculate_transits(natal, transit_date=transit_dt)
    moment = calculate_chart(
        BirthData(2026, 10, 18, 12, 0, 0, 23.1765, 75.7885, "Asia/Kolkata")
    )
    sun_transit = next(p for p in report.planets if p.name == "Sun")
    sun_moment = next(p for p in moment.planets if p.name == "Sun")
    assert abs(sun_transit.longitude - sun_moment.longitude) < 0.01
    rahu_transit = next(p for p in report.planets if p.name == "Rahu")
    assert abs(rahu_transit.longitude - moment.rahu.longitude) < 0.01


def test_rahu_ketu_houses_follow_placidus_not_whole_sign():
    """Under Placidus the nodes take their quadrant house, not whole-sign.

    TNP chart: Rahu at 151.79 deg Virgo — whole-sign House 6, but Placidus
    House 5 (5th cusp 132.96 deg, 6th cusp 169.14 deg). Ketu at 331.79 deg
    Pisces — whole-sign House 12, Placidus House 11. Whole Sign charts
    must be unchanged.
    """
    placidus = calculate_chart(
        BirthData(1997, 5, 22, 4, 53, 0, 27.8667, 83.4833, "Asia/Kathmandu"),
        house_system=HouseSystem.PLACIDUS,
    )
    assert placidus.rahu.house == 5
    assert placidus.ketu.house == 11

    whole_sign = calculate_chart(
        BirthData(1997, 5, 22, 4, 53, 0, 27.8667, 83.4833, "Asia/Kathmandu"),
        house_system=HouseSystem.WHOLE_SIGN,
    )
    assert whole_sign.rahu.house == 6
    assert whole_sign.ketu.house == 12


def test_scan_transit_window_uses_natal_ayanamsa_and_restores_sidereal_mode(monkeypatch):
    """scan_transit_window must honour a non-Lahiri natal ayanamsa and
    leave the process-global sidereal mode exactly as it found it.

    The global mode is observable through swe.get_ayanamsa_ut (pyswisseph
    exposes no get_sid_mode). The mode is pre-set to Fagan-Bradley; a
    recording wrapper on set_sid_mode proves the scan switched to the natal
    Raman mode mid-call and restored Fagan-Bradley at the end.
    """
    natal_raman = calculate_chart(
        BirthData(2000, 1, 1, 12, 0, 0, 23.1765, 75.7885, "Asia/Kolkata"),
        ayanamsa=Ayanamsa.RAMAN,
    )
    natal_lahiri = calculate_chart(
        BirthData(2000, 1, 1, 12, 0, 0, 23.1765, 75.7885, "Asia/Kolkata"),
        ayanamsa=Ayanamsa.LAHIRI,
    )
    start = datetime(2026, 11, 1, 12, 0, tzinfo=ZoneInfo("Asia/Kolkata"))

    swe.set_sid_mode(swe.SIDM_FAGAN_BRADLEY)
    before = swe.get_ayanamsa_ut(2451545.0)

    real_set_sid_mode = swe.set_sid_mode
    seen_modes: list[int] = []

    def _recording_set_sid_mode(mode, *args, **kwargs):
        seen_modes.append(mode)
        return real_set_sid_mode(mode, *args, **kwargs)

    monkeypatch.setattr(swe, "set_sid_mode", _recording_set_sid_mode)
    try:
        report_raman = scan_transit_window(natal_raman, start_date=start, days=30)
    finally:
        monkeypatch.undo()
    after = swe.get_ayanamsa_ut(2451545.0)

    assert abs(after - before) < 1e-9
    assert swe.SIDM_RAMAN in seen_modes
    assert seen_modes[-1] == swe.SIDM_FAGAN_BRADLEY

    # The natal ayanamsa must actually change the scan: Raman and Lahiri
    # scans of the same window report different ingress dates.
    swe.set_sid_mode(swe.SIDM_FAGAN_BRADLEY)
    report_lahiri = scan_transit_window(natal_lahiri, start_date=start, days=30)
    assert swe.get_ayanamsa_ut(2451545.0) == pytest.approx(before)
    mars_raman = {
        e.date for e in report_raman.events if e.event_type == "ingress" and e.planet == "Mars"
    }
    mars_lahiri = {
        e.date for e in report_lahiri.events if e.event_type == "ingress" and e.planet == "Mars"
    }
    assert mars_raman != mars_lahiri
