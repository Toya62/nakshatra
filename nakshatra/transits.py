"""
Nakshatra Transit (Gochar) Engine
High-precision Vedic transit analysis overlaying current/transit planetary positions
onto natal charts, with classical Gochar rules, Ashtakavarga bindus, Sade Sati,
and Double Transit (Jupiter + Saturn) detection.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo
from pydantic import BaseModel, Field

from nakshatra.core import (
    BirthData,
    ChartData,
    Ayanamsa,
    PlanetPosition,
    ZODIAC_SIGNS,
    SIGN_LORDS,
    get_sign,
    get_degree_in_sign,
    get_nakshatra,
)
from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos
import swisseph as swe


# Classical Phaladeepika auspicious transit houses from Natal Moon (Chandra Lagna)
FAVORABLE_GOCHAR_HOUSES: dict[str, list[int]] = {
    "Sun": [3, 6, 10, 11],
    "Moon": [1, 3, 6, 7, 10, 11],
    "Mars": [3, 6, 11],
    "Mercury": [2, 4, 6, 8, 10, 11],
    "Jupiter": [2, 5, 7, 9, 11],
    "Venus": [1, 2, 3, 4, 5, 8, 9, 11, 12],
    "Saturn": [3, 6, 11],
    "Rahu": [3, 6, 10, 11],
    "Ketu": [3, 6, 11],
}

# Vedic full planetary aspects by sign count from planet position
# All planets cast 7th aspect; Mars casts 4th, 7th, 8th; Jupiter casts 5th, 7th, 9th; Saturn casts 3rd, 7th, 10th
VEDIC_ASPECTS: dict[str, list[int]] = {
    "Sun": [7],
    "Moon": [7],
    "Mars": [4, 7, 8],
    "Mercury": [7],
    "Jupiter": [5, 7, 9],
    "Venus": [7],
    "Saturn": [3, 7, 10],
    "Rahu": [5, 7, 9],
    "Ketu": [5, 7, 9],
}


class TransitPlanet(BaseModel):
    """Single planet transit position relative to natal chart."""
    name: str
    sign: str
    sign_lord: str
    longitude: float
    degree_in_sign: float
    nakshatra: str
    pada: int
    retrograde: bool
    speed: float
    house_from_lagna: int = Field(..., description="Transit house relative to natal Ascendant (1-12)")
    house_from_moon: int = Field(..., description="Transit house relative to natal Moon / Chandra Lagna (1-12)")
    sav_bindus: Optional[int] = Field(None, description="Sarvashtakavarga bindus in transited sign (>=28 favorable)")
    bav_bindus: Optional[int] = Field(None, description="Planet's own Bhinnashtakavarga bindus in transited sign (>=4 favorable)")
    is_favorable_gochar: bool = Field(..., description="Whether transit is in an auspicious house from Moon per Phaladeepika")


class SadeSatiInfo(BaseModel):
    """Saturn Sade Sati and special transit affliction status."""
    is_active: bool
    phase: Optional[str] = None  # "Rising (12th from Moon)", "Peak (Janma Shani / 1st from Moon)", "Setting (2nd from Moon)"
    is_ashtama_shani: bool = False  # Saturn in 8th from Moon
    is_kantaka_shani: bool = False  # Saturn in 4th or 10th from Moon
    saturn_sign: str
    natal_moon_sign: str
    house_from_moon: int


class TransitReport(BaseModel):
    """Complete transit analysis relative to natal chart."""
    transit_time: str
    natal_birth_time: str
    natal_lagna_sign: str
    natal_moon_sign: str
    ayanamsa: str
    planets: list[TransitPlanet]
    sade_sati: SadeSatiInfo
    jupiter_gochar: dict
    double_transit_houses: list[int] = Field(default_factory=list, description="Houses simultaneously aspected by Transit Jupiter & Transit Saturn")

    def to_table(self) -> str:
        """Render transit analysis as formatted ASCII table."""
        lines = []
        lines.append("=" * 86)
        lines.append("                         VEDIC TRANSIT (GOCHAR) REPORT")
        lines.append("=" * 86)
        lines.append(f" Transit Timestamp   : {self.transit_time}")
        lines.append(f" Natal Birth Lagna   : {self.natal_lagna_sign} | Natal Moon: {self.natal_moon_sign}")
        lines.append(f" Ayanamsa Used       : {self.ayanamsa.upper()}")
        lines.append("-" * 86)

        # Sade Sati Banner
        ss = self.sade_sati
        if ss.is_active:
            lines.append(f" SADE SATI ALERT     : ACTIVE - {ss.phase} (Saturn in {ss.saturn_sign})")
        elif ss.is_ashtama_shani:
            lines.append(f" ASHTAMA SHANI ALERT : ACTIVE - Saturn in 8th from Moon ({ss.saturn_sign})")
        elif ss.is_kantaka_shani:
            lines.append(f" KANTAKA SHANI ALERT : ACTIVE - Saturn in {ss.house_from_moon}th from Moon ({ss.saturn_sign})")
        else:
            lines.append(f" SADE SATI STATUS    : Inactive (Saturn in {ss.saturn_sign}, {ss.house_from_moon}th from Moon)")

        jg = self.jupiter_gochar
        j_status = "AUSPICIOUS" if jg.get("favorable") else "Neutral / Introspective"
        lines.append(f" JUPITER GOCHAR      : In {jg.get('sign')} ({jg.get('house_from_moon')}th from Moon) -> {j_status}")
        
        if self.double_transit_houses:
            dt_str = ", ".join(f"House {h}" for h in self.double_transit_houses)
            lines.append(f" DOUBLE TRANSIT      : Jupiter + Saturn both aspect {dt_str} (High event manifestation)")
        lines.append("-" * 86)

        # Planetary Transits Table
        lines.append(" TRANSITING GRAHA POSITIONS")
        lines.append("-" * 86)
        lines.append(f"{'Planet':<10} {'Sign':<12} {'Deg':<10} {'From Lagna':<12} {'From Moon':<12} {'SAV/BAV':<9} {'Gochar':<10}")
        lines.append("-" * 86)
        for p in self.planets:
            r_flag = "(R)" if p.retrograde else "   "
            p_name = f"{p.name} {r_flag}"
            h_lagna = f"H{p.house_from_lagna} ({p.sign[:3]})"
            h_moon = f"H{p.house_from_moon} ({p.sign[:3]})"
            sav_bav = f"{p.sav_bindus or '-'}/{p.bav_bindus or '-'}"
            g_eval = "FAVORABLE" if p.is_favorable_gochar else "Challenging"
            deg_str = f"{p.degree_in_sign:05.2f}°"
            lines.append(f"{p_name:<10} {p.sign:<12} {deg_str:<10} {h_lagna:<12} {h_moon:<12} {sav_bav:<9} {g_eval:<10}")
        lines.append("=" * 86)
        return "\n".join(lines)


def calculate_transits(
    natal_chart: ChartData,
    transit_date: Optional[datetime] = None,
    transit_latitude: Optional[float] = None,
    transit_longitude: Optional[float] = None,
) -> TransitReport:
    """
    Calculate Vedic planetary transits overlaying current/specified sky positions on natal chart.
    Uses exact same ayanamsa as natal chart (default: jhora_lahiri).
    """
    b = natal_chart.birth_data
    t_lat = transit_latitude if transit_latitude is not None else b.latitude
    t_lon = transit_longitude if transit_longitude is not None else b.longitude

    if transit_date is None:
        t_dt = datetime.now(ZoneInfo(b.timezone))
    elif transit_date.tzinfo is None:
        t_dt = transit_date.replace(tzinfo=ZoneInfo(b.timezone))
    else:
        t_dt = transit_date

    # Setup mayaastrolib Datetime & GeoPos
    offset_sec = t_dt.utcoffset().total_seconds() if t_dt.tzinfo else 0
    t_h = t_dt.hour + (t_dt.minute / 60.0) + (t_dt.second / 3600.0)
    t_tz_str = f"{int(offset_sec//3600):+03d}:{int((abs(offset_sec)%3600)//60):02d}"

    m_dt = Datetime([t_dt.year, t_dt.month, t_dt.day], t_h, t_tz_str)
    m_pos = GeoPos(t_lat, t_lon)

    # Use natal ayanamsa
    maya_ayanamsa = "lahiri" if natal_chart.ayanamsa == Ayanamsa.JHORA_LAHIRI else natal_chart.ayanamsa.value
    ayan_offset = (56.5318 / 3600.0) if natal_chart.ayanamsa == Ayanamsa.JHORA_LAHIRI else 0.0

    m_chart = Chart(
        m_dt,
        m_pos,
        IDs=["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "North Node"],
        zodiac="sidereal",
        ayanamsa=maya_ayanamsa,
        hsys="Whole Sign",
    )

    t_jd = m_dt.jd
    natal_asc_idx = ZODIAC_SIGNS.index(natal_chart.ascendant.sign)
    natal_moon = next(p for p in natal_chart.planets if p.name == "Moon")
    natal_moon_idx = ZODIAC_SIGNS.index(natal_moon.sign)

    # Process transiting planets
    transit_planets: list[TransitPlanet] = []
    transiting_signs_by_planet: dict[str, int] = {}

    swe_bodies = {
        "Sun": swe.SUN,
        "Moon": swe.MOON,
        "Mars": swe.MARS,
        "Mercury": swe.MERCURY,
        "Jupiter": swe.JUPITER,
        "Venus": swe.VENUS,
        "Saturn": swe.SATURN,
    }

    sav_list = natal_chart.ashtakavarga.sarvashtakavarga if natal_chart.ashtakavarga else None
    bav_dict = natal_chart.ashtakavarga.bhinnashtakavarga if natal_chart.ashtakavarga else {}

    for name in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
        raw = m_chart.get(name)
        lon = (raw.lon - ayan_offset) % 360.0
        sign = get_sign(lon)
        sign_idx = ZODIAC_SIGNS.index(sign)
        transiting_signs_by_planet[name] = sign_idx
        deg_in_sign = get_degree_in_sign(lon)
        nak, lord, pada = get_nakshatra(lon)

        # Speed and retrograde from pyswisseph
        swe_body = swe_bodies[name]
        calc = swe.calc_ut(t_jd, swe_body, swe.FLG_SWIEPH | swe.FLG_SPEED)
        speed = calc[0][3]
        retro = speed < 0

        # Houses from natal Lagna & natal Moon
        h_lagna = ((sign_idx - natal_asc_idx) % 12) + 1
        h_moon = ((sign_idx - natal_moon_idx) % 12) + 1

        sav_val = sav_list[sign_idx] if sav_list else None
        bav_val = bav_dict.get(name, [])[sign_idx] if name in bav_dict else None
        is_fav = h_moon in FAVORABLE_GOCHAR_HOUSES.get(name, [])

        transit_planets.append(
            TransitPlanet(
                name=name,
                sign=sign,
                sign_lord=SIGN_LORDS[sign],
                longitude=round(lon, 6),
                degree_in_sign=round(deg_in_sign, 6),
                nakshatra=nak,
                pada=pada,
                retrograde=retro,
                speed=round(speed, 6),
                house_from_lagna=h_lagna,
                house_from_moon=h_moon,
                sav_bindus=sav_val,
                bav_bindus=bav_val,
                is_favorable_gochar=is_fav,
            )
        )

    # Rahu & Ketu
    rahu_raw = m_chart.get("North Node")
    rahu_lon = (rahu_raw.lon - ayan_offset) % 360.0
    rahu_sign = get_sign(rahu_lon)
    rahu_sign_idx = ZODIAC_SIGNS.index(rahu_sign)
    transiting_signs_by_planet["Rahu"] = rahu_sign_idx
    rahu_nak, _, rahu_pada = get_nakshatra(rahu_lon)
    rahu_h_lagna = ((rahu_sign_idx - natal_asc_idx) % 12) + 1
    rahu_h_moon = ((rahu_sign_idx - natal_moon_idx) % 12) + 1

    transit_planets.append(
        TransitPlanet(
            name="Rahu",
            sign=rahu_sign,
            sign_lord=SIGN_LORDS[rahu_sign],
            longitude=round(rahu_lon, 6),
            degree_in_sign=round(get_degree_in_sign(rahu_lon), 6),
            nakshatra=rahu_nak,
            pada=rahu_pada,
            retrograde=True,
            speed=-0.053,
            house_from_lagna=rahu_h_lagna,
            house_from_moon=rahu_h_moon,
            sav_bindus=sav_list[rahu_sign_idx] if sav_list else None,
            bav_bindus=None,
            is_favorable_gochar=rahu_h_moon in FAVORABLE_GOCHAR_HOUSES["Rahu"],
        )
    )

    ketu_lon = (rahu_lon + 180.0) % 360.0
    ketu_sign = get_sign(ketu_lon)
    ketu_sign_idx = ZODIAC_SIGNS.index(ketu_sign)
    transiting_signs_by_planet["Ketu"] = ketu_sign_idx
    ketu_nak, _, ketu_pada = get_nakshatra(ketu_lon)
    ketu_h_lagna = ((ketu_sign_idx - natal_asc_idx) % 12) + 1
    ketu_h_moon = ((ketu_sign_idx - natal_moon_idx) % 12) + 1

    transit_planets.append(
        TransitPlanet(
            name="Ketu",
            sign=ketu_sign,
            sign_lord=SIGN_LORDS[ketu_sign],
            longitude=round(ketu_lon, 6),
            degree_in_sign=round(get_degree_in_sign(ketu_lon), 6),
            nakshatra=ketu_nak,
            pada=ketu_pada,
            retrograde=True,
            speed=-0.053,
            house_from_lagna=ketu_h_lagna,
            house_from_moon=ketu_h_moon,
            sav_bindus=sav_list[ketu_sign_idx] if sav_list else None,
            bav_bindus=None,
            is_favorable_gochar=ketu_h_moon in FAVORABLE_GOCHAR_HOUSES["Ketu"],
        )
    )

    # 1. Sade Sati Analysis
    saturn_transit = next(p for p in transit_planets if p.name == "Saturn")
    sat_h_moon = saturn_transit.house_from_moon

    sade_sati_active = sat_h_moon in (12, 1, 2)
    sade_sati_phase = None
    if sat_h_moon == 12:
        sade_sati_phase = "Rising (12th from Moon)"
    elif sat_h_moon == 1:
        sade_sati_phase = "Peak / Janma Shani (1st from Moon)"
    elif sat_h_moon == 2:
        sade_sati_phase = "Setting (2nd from Moon)"

    sade_sati_info = SadeSatiInfo(
        is_active=sade_sati_active,
        phase=sade_sati_phase,
        is_ashtama_shani=(sat_h_moon == 8),
        is_kantaka_shani=(sat_h_moon in (4, 10)),
        saturn_sign=saturn_transit.sign,
        natal_moon_sign=natal_moon.sign,
        house_from_moon=sat_h_moon,
    )

    # 2. Jupiter Gochar
    jup_transit = next(p for p in transit_planets if p.name == "Jupiter")
    jupiter_gochar = {
        "sign": jup_transit.sign,
        "house_from_lagna": jup_transit.house_from_lagna,
        "house_from_moon": jup_transit.house_from_moon,
        "favorable": jup_transit.is_favorable_gochar,
        "sav_bindus": jup_transit.sav_bindus,
        "bav_bindus": jup_transit.bav_bindus,
    }

    # 3. Double Transit Detection (Signs aspected by BOTH Saturn and Jupiter)
    sat_sign_idx = transiting_signs_by_planet["Saturn"]
    jup_sign_idx = transiting_signs_by_planet["Jupiter"]

    # Signs aspected by Saturn: its occupied sign + 3rd, 7th, 10th aspects
    sat_aspected_signs = {sat_sign_idx} | {((sat_sign_idx + asp - 1) % 12) for asp in [3, 7, 10]}
    # Signs aspected by Jupiter: its occupied sign + 5th, 7th, 9th aspects
    jup_aspected_signs = {jup_sign_idx} | {((jup_sign_idx + asp - 1) % 12) for asp in [5, 7, 9]}

    double_aspected_signs = sat_aspected_signs & jup_aspected_signs
    # Convert double aspected signs into houses from natal Lagna
    double_transit_houses = sorted([((s_idx - natal_asc_idx) % 12) + 1 for s_idx in double_aspected_signs])

    return TransitReport(
        transit_time=t_dt.strftime("%Y-%m-%d %H:%M:%S"),
        natal_birth_time=f"{b.year:04d}-{b.month:02d}-{b.day:02d} {b.hour:02d}:{b.minute:02d}:{b.second:02d}",
        natal_lagna_sign=natal_chart.ascendant.sign,
        natal_moon_sign=natal_moon.sign,
        ayanamsa=natal_chart.ayanamsa.value,
        planets=transit_planets,
        sade_sati=sade_sati_info,
        jupiter_gochar=jupiter_gochar,
        double_transit_houses=double_transit_houses,
    )
