"""
Nakshatra - Vedic Astrology AI Engine
Core calculation module powered by Swiss Ephemeris (pyswisseph) via mayaastrolib.

Calculations:
- Sidereal planetary positions, true velocities, retrograde motion, and dignities
- Ayanamsas: Lahiri, JHora Traditional Lahiri, Raman, Krishnamurti, Fagan-Bradley
- House systems: Whole Sign, Placidus, Koch, Regiomontanus, Campanus, Equal, Porphyry
- Vimshottari Dasha: Mahadasha, Antardasha, and Pratyantardasha with exact timestamps
- Divisional charts: Shodashavarga (D1 through D60)
- Ashtakavarga: Sarvashtakavarga (337 bindus) and Bhinnashtakavarga for 7 planets
- Shadbala: Sthana, Dig, Kala, Cheshta, Naisargika, and Drik balas with rupas
- Upagrahas: Dhuma, Vyatipata, Parivesha, Indrachapa, and Upaketu
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

import mayaastrolib.vedic.ashtakavarga as vav
import mayaastrolib.vedic.ayanamsa as vaya
import mayaastrolib.vedic.dasha as vdasha
import mayaastrolib.vedic.divisional as vdiv
import mayaastrolib.vedic.nakshatras as vnak
import mayaastrolib.vedic.shadbala as vsb
import mayaastrolib.vedic.upagrahas as vupa
import swisseph
from mayaastrolib import const
from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from nakshatra.transits import TransitReport


class Ayanamsa(str, Enum):
    """Supported ayanamsa systems."""

    LAHIRI = "lahiri"
    JHORA_LAHIRI = "jhora_lahiri"
    RAMAN = "raman"
    KRISHNAMURTI = "krishnamurti"
    FAGAN_BRADLEY = "fagan_bradley"


class HouseSystem(str, Enum):
    """Supported house systems."""

    WHOLE_SIGN = "WholeSign"
    PLACIDUS = "Placidus"
    KOCH = "Koch"
    REGIOMONTANUS = "Regiomontanus"
    CAMPANUS = "Campanus"
    EQUAL = "Equal"
    PORPHYRY = "Porphyry"


class ZodiacSystem(str, Enum):
    """Zodiac systems."""

    TROPICAL = "tropical"
    SIDEREAL = "sidereal"


@dataclass(frozen=True)
class GeoLocation:
    """Geographic location for birth place."""

    latitude: float
    longitude: float
    timezone: str
    place_name: str | None = None


@dataclass(frozen=True)
class BirthData:
    """Birth data input."""

    year: int
    month: int
    day: int
    hour: int
    minute: int
    second: int = 0
    latitude: float = 0.0
    longitude: float = 0.0
    timezone: str = "UTC"
    place_name: str | None = None

    @property
    def datetime_utc(self) -> datetime:
        """Convert to UTC datetime using zoneinfo."""
        dt = datetime(self.year, self.month, self.day, self.hour, self.minute, self.second)
        tz = ZoneInfo(self.timezone)
        dt_local = dt.replace(tzinfo=tz)
        return dt_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)


class PlanetPosition(BaseModel):
    """Single planet position in chart."""

    name: str
    longitude: float
    latitude: float = 0.0
    distance: float = 0.0
    speed: float = 0.0
    sign: str
    sign_lord: str
    degree_in_sign: float
    nakshatra: str | None = None
    nakshatra_lord: str | None = None
    pada: int | None = None
    house: int
    retrograde: bool = False
    dignity: str | None = None


class HouseCusp(BaseModel):
    """House cusp data."""

    house: int
    longitude: float
    sign: str
    sign_lord: str = ""
    degree_in_sign: float


class Aspect(BaseModel):
    """Aspect between two planets."""

    planet1: str
    planet2: str
    aspect_type: str
    orb: float
    applying: bool
    exact_degree: float


class VedicAspect(BaseModel):
    """Parashari Graha Drishti (aspect from a planet to a house and its occupants)."""

    planet: str
    source_house: int
    target_house: int
    aspect_type: str
    target_sign: str = ""
    aspected_planets: list[str] = Field(default_factory=list)
    strength: float = 1.0


class DashaPeriod(BaseModel):
    """Single Dasha period (Mahadasha, Antardasha, or Pratyantardasha)."""

    lord: str
    start: str
    end: str
    level: int = 1
    duration_years: float | None = None
    subs: list[DashaPeriod] | None = None


class VimshottariDasha(BaseModel):
    """Complete Vimshottari Dasha system data."""

    birth_nakshatra: str
    birth_nakshatra_lord: str
    balance_lord: str
    balance_years: float
    current_md: DashaPeriod | None = None
    current_ad: DashaPeriod | None = None
    current_pd: DashaPeriod | None = None
    mahadashas: list[DashaPeriod] = Field(default_factory=list)


class ShadbalaPlanet(BaseModel):
    """Planetary strength metrics from Shadbala."""

    planet: str
    total_rupas: float
    total_virupas: float
    required_rupas: float
    sufficient: bool
    sthana_bala: float
    dig_bala: float
    kala_bala: float
    cheshta_bala: float
    naisargika_bala: float
    drik_bala: float


class AshtakavargaData(BaseModel):
    """Ashtakavarga bindu totals and classical Shodhita reductions."""

    sarvashtakavarga: list[int]
    grand_total: int
    bhinnashtakavarga: dict[str, list[int]]
    shodhita_sarvashtakavarga: list[int] | None = None
    shodhita_bhinnashtakavarga: dict[str, list[int]] | None = None


class UpagrahaPosition(BaseModel):
    """Position of a shadow planet / upagraha."""

    name: str
    longitude: float
    sign: str
    degree_in_sign: float
    house: int


class ChartData(BaseModel):
    """Complete birth chart data."""

    birth_data: BirthData
    calculation_time: str
    zodiac: ZodiacSystem
    ayanamsa: Ayanamsa
    ayanamsa_value: float | None = None
    house_system: HouseSystem
    planets: list[PlanetPosition]
    houses: list[HouseCusp]
    aspects: list[Aspect]
    ascendant: PlanetPosition
    midheaven: PlanetPosition
    rahu: PlanetPosition
    ketu: PlanetPosition
    dashas: VimshottariDasha | None = None
    vargas: dict[str, dict[str, str]] | None = None
    d10_chart: dict | None = None
    ashtakavarga: AshtakavargaData | None = None
    shadbala: dict[str, ShadbalaPlanet] | None = None
    upagrahas: list[UpagrahaPosition] | None = None
    transits: dict | None = None
    panchanga: Any | None = None
    yogas: list[Any] | None = None
    vedic_aspects: list[VedicAspect] = Field(default_factory=list)

    def get_house_aspects_received(self) -> dict[int, list[VedicAspect]]:
        """Map of house number (1-12) to list of Vedic aspects received."""
        mapping: dict[int, list[VedicAspect]] = {h: [] for h in range(1, 13)}
        for asp in self.vedic_aspects:
            if asp.target_house in mapping:
                mapping[asp.target_house].append(asp)
        return mapping

    def get_panchanga(self) -> Any:
        """Get or calculate Vedic Panchanga."""
        if self.panchanga is None:
            from nakshatra.panchanga import calculate_panchanga

            dt_local = datetime(
                self.birth_data.year,
                self.birth_data.month,
                self.birth_data.day,
                self.birth_data.hour,
                self.birth_data.minute,
                self.birth_data.second,
                tzinfo=ZoneInfo(self.birth_data.timezone),
            )
            self.panchanga = calculate_panchanga(
                dt_local,
                self.birth_data.latitude,
                self.birth_data.longitude,
                self.birth_data.timezone,
                ayanamsa=self.ayanamsa,
            )
        return self.panchanga

    def get_yogas(self) -> list[Any]:
        """Get or calculate Vedic Yogas."""
        if self.yogas is None:
            from nakshatra.yogas import detect_yogas

            self.yogas = detect_yogas(self)
        return self.yogas

    def to_json(self) -> str:
        """Export as JSON string."""
        return self.model_dump_json(indent=2)

    def to_dict(self) -> dict:
        """Export as dictionary."""
        return self.model_dump()

    def to_table(self) -> str:
        """Format chart into formatted ASCII tables."""
        from nakshatra.formatters import format_table

        return format_table(self)

    def to_markdown(self) -> str:
        """Format chart into GitHub-flavored Markdown."""
        from nakshatra.formatters import format_markdown

        return format_markdown(self)

    def to_csv(self) -> str:
        """Format chart planetary positions into CSV."""
        from nakshatra.formatters import format_csv

        return format_csv(self)

    def to_diagram(self, varga: str = "D1") -> str:
        """Format chart into ASCII South Indian diagram for given varga (e.g. D1, D9)."""
        from nakshatra.formatters import format_chart_diagram

        return format_chart_diagram(self, varga=varga)

    def get_varga(self, varga: str = "D10") -> dict:
        """
        Get structured divisional chart data (signs and whole-sign houses
        relative to varga Ascendant).
        """
        v_key = varga.upper()
        if not self.vargas or v_key not in self.vargas:
            return {}
        v_data = self.vargas[v_key]
        asc_sign = v_data.get("Ascendant", self.ascendant.sign)
        asc_idx = ZODIAC_SIGNS.index(asc_sign)

        planets_data = {}
        for name in CHART_BODIES:
            sign = v_data.get(name)
            if sign:
                sign_idx = ZODIAC_SIGNS.index(sign)
                house = ((sign_idx - asc_idx) % 12) + 1
                planets_data[name] = {
                    "sign": sign,
                    "house": house,
                    "sign_lord": SIGN_LORDS[sign],
                }

        return {
            "varga": v_key,
            "ascendant": {
                "sign": asc_sign,
                "house": 1,
                "sign_lord": SIGN_LORDS[asc_sign],
            },
            "planets": planets_data,
        }

    def get_transits(
        self,
        transit_date: datetime | None = None,
        transit_latitude: float | None = None,
        transit_longitude: float | None = None,
    ) -> TransitReport:
        """
        Calculate Vedic transits (Gochar) relative to natal chart.
        Returns TransitReport with Sade Sati, Double Transits, and Ashtakavarga weighting.
        """
        from nakshatra.transits import calculate_transits

        return calculate_transits(
            natal_chart=self,
            transit_date=transit_date,
            transit_latitude=transit_latitude,
            transit_longitude=transit_longitude,
        )

    def get_transit_window(
        self,
        start_date: datetime | None = None,
        days: int = 30,
    ) -> Any:
        """Scan monthly transit window for ingresses, retrograde stations, and Chandrashtama."""
        from nakshatra.transits import scan_transit_window

        return scan_transit_window(natal_chart=self, start_date=start_date, days=days)

    def get_predictions(
        self,
        domain: str | None = None,
        transits: TransitReport | None = None,
    ) -> Any:
        """
        Evaluate deterministic 5-step classical Vedic predictions across life domains.
        Returns dict of DomainPredictions or single DomainPrediction if domain specified.
        """
        from nakshatra.predictor import evaluate_all_domains, evaluate_domain

        if domain:
            return evaluate_domain(domain, self, transits=transits)
        return evaluate_all_domains(self, transits=transits)

    def get_remedies(self, transits: TransitReport | None = None) -> Any:
        """
        Calculate dual-system classical remedies (Parashari + Lal Kitab Upayas)
        tailored to natal chart afflictions, dasha lords, and Gochar transits.
        """
        from nakshatra.remedies import calculate_remedies

        return calculate_remedies(self, transits=transits)

    def save(self, filepath: str, format: str | None = None) -> str:
        """
        Save chart data directly to file.
        Infers format from file extension (.json, .md, .csv, .txt) if not provided.
        """
        fmt = format.lower() if format else None
        if not fmt:
            if filepath.endswith(".json"):
                fmt = "json"
            elif filepath.endswith((".md", ".markdown")):
                fmt = "markdown"
            elif filepath.endswith(".csv"):
                fmt = "csv"
            else:
                fmt = "table"

        if fmt == "json":
            content = self.to_json()
        elif fmt == "markdown":
            content = self.to_markdown()
        elif fmt == "csv":
            content = self.to_csv()
        elif fmt == "diagram":
            content = self.to_diagram()
        else:
            content = self.to_table()

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return filepath


# Nakshatra data (27 nakshatras with lords)
NAKSHATRAS = [
    ("Ashwini", "Ketu"),
    ("Bharani", "Venus"),
    ("Krittika", "Sun"),
    ("Rohini", "Moon"),
    ("Mrigashira", "Mars"),
    ("Ardra", "Rahu"),
    ("Punarvasu", "Jupiter"),
    ("Pushya", "Saturn"),
    ("Ashlesha", "Mercury"),
    ("Magha", "Ketu"),
    ("Purva Phalguni", "Venus"),
    ("Uttara Phalguni", "Sun"),
    ("Hasta", "Moon"),
    ("Chitra", "Mars"),
    ("Swati", "Rahu"),
    ("Vishakha", "Jupiter"),
    ("Anuradha", "Saturn"),
    ("Jyeshtha", "Mercury"),
    ("Mula", "Ketu"),
    ("Purva Ashadha", "Venus"),
    ("Uttara Ashadha", "Sun"),
    ("Shravana", "Moon"),
    ("Dhanishta", "Mars"),
    ("Shatabhisha", "Rahu"),
    ("Purva Bhadrapada", "Jupiter"),
    ("Uttara Bhadrapada", "Saturn"),
    ("Revati", "Mercury"),
]

# Zodiac signs in order
ZODIAC_SIGNS = [
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
]

# Sign lords
SIGN_LORDS = {
    "Aries": "Mars",
    "Taurus": "Venus",
    "Gemini": "Mercury",
    "Cancer": "Moon",
    "Leo": "Sun",
    "Virgo": "Mercury",
    "Libra": "Venus",
    "Scorpio": "Mars",
    "Sagittarius": "Jupiter",
    "Capricorn": "Saturn",
    "Aquarius": "Saturn",
    "Pisces": "Jupiter",
}

# 7 Classical Grahas
VEDIC_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

# All chart bodies (7 grahas + lunar nodes)
CHART_BODIES = [
    "Sun",
    "Moon",
    "Mars",
    "Mercury",
    "Jupiter",
    "Venus",
    "Saturn",
    "North Node",
    "South Node",
]

# Mayaastrolib House system mapping
HOUSE_MAP = {
    HouseSystem.WHOLE_SIGN: const.HOUSES_WHOLE_SIGN,
    HouseSystem.PLACIDUS: const.HOUSES_PLACIDUS,
    HouseSystem.KOCH: const.HOUSES_KOCH,
    HouseSystem.REGIOMONTANUS: const.HOUSES_REGIOMONTANUS,
    HouseSystem.CAMPANUS: const.HOUSES_CAMPANUS,
    HouseSystem.EQUAL: const.HOUSES_EQUAL,
    HouseSystem.PORPHYRY: const.HOUSES_PORPHYRIUS,
}

# Swiss Ephemeris body IDs
SWE_BODY_MAP = {
    "Sun": swisseph.SUN,
    "Moon": swisseph.MOON,
    "Mercury": swisseph.MERCURY,
    "Venus": swisseph.VENUS,
    "Mars": swisseph.MARS,
    "Jupiter": swisseph.JUPITER,
    "Saturn": swisseph.SATURN,
    "Rahu": swisseph.MEAN_NODE,
    "North Node": swisseph.MEAN_NODE,
}


def get_nakshatra(longitude: float) -> tuple[str, str, int]:
    """Calculate nakshatra, lord, and pada from sidereal longitude."""
    nakshatra_span = 360.0 / 27.0
    nakshatra_index = int((longitude % 360.0) / nakshatra_span) % 27
    nakshatra_name, lord = NAKSHATRAS[nakshatra_index]

    degree_in_nakshatra = (longitude % 360.0) % nakshatra_span
    pada = int(degree_in_nakshatra / (nakshatra_span / 4.0)) + 1
    return nakshatra_name, lord, min(pada, 4)


def get_sign(longitude: float) -> str:
    """Get zodiac sign from longitude."""
    sign_index = int((longitude % 360.0) / 30.0) % 12
    return ZODIAC_SIGNS[sign_index]


def get_degree_in_sign(longitude: float) -> float:
    """Get degree within sign (0-30)."""
    return (longitude % 360.0) % 30.0


def format_tz_offset(offset_sec: float) -> str:
    """Format total seconds into +/-HH:MM ISO offset string with correct negative rounding."""
    sign = "-" if offset_sec < 0 else "+"
    abs_sec = abs(int(offset_sec))
    offset_h = abs_sec // 3600
    offset_m = (abs_sec % 3600) // 60
    return f"{sign}{offset_h:02d}:{offset_m:02d}"


def calculate_dignity(planet: str, sign: str) -> str:
    """Calculate planetary dignity (simplified classical Vedic)."""
    exaltation = {
        "Sun": "Aries",
        "Moon": "Taurus",
        "Mars": "Capricorn",
        "Mercury": "Virgo",
        "Jupiter": "Cancer",
        "Venus": "Pisces",
        "Saturn": "Libra",
    }
    debilitation = {
        "Sun": "Libra",
        "Moon": "Scorpio",
        "Mars": "Cancer",
        "Mercury": "Pisces",
        "Jupiter": "Capricorn",
        "Venus": "Virgo",
        "Saturn": "Aries",
    }
    own_signs = {
        "Sun": ["Leo"],
        "Moon": ["Cancer"],
        "Mars": ["Aries", "Scorpio"],
        "Mercury": ["Gemini", "Virgo"],
        "Jupiter": ["Sagittarius", "Pisces"],
        "Venus": ["Taurus", "Libra"],
        "Saturn": ["Capricorn", "Aquarius"],
    }

    if sign == exaltation.get(planet):
        return "exalted"
    elif sign == debilitation.get(planet):
        return "debilitated"
    elif sign in own_signs.get(planet, []):
        return "own_sign"
    return "neutral"


def _format_datetime(dt: Datetime) -> str:
    """Format mayaastrolib Datetime to YYYY-MM-DD HH:MM:SS string."""
    pydt = dt.to_pydatetime()
    return pydt.strftime("%Y-%m-%d %H:%M:%S")


def _active_period(period: vdasha.DashaPeriod | None) -> DashaPeriod | None:
    """Convert an optionally-None DashaPeriod without subdivisions."""
    if period is None:
        return None
    return _convert_dasha_period(period, include_subs=False)


def _convert_dasha_period(period: vdasha.DashaPeriod, include_subs: bool = True) -> DashaPeriod:
    """Convert mayaastrolib DashaPeriod to Pydantic model with nested subdivisions."""
    subs_models = None
    if include_subs and period.level == 1:
        # Antardashas
        ads = vdasha.antardashas(period)
        subs_models = []
        for ad in ads:
            # Pratyantardashas
            pds = vdasha.pratyantar_dashas(ad)
            pd_models = [
                DashaPeriod(
                    lord=pd.lord,
                    start=_format_datetime(pd.start),
                    end=_format_datetime(pd.end),
                    level=3,
                )
                for pd in pds
            ]
            has_jd = hasattr(ad.start, "jd") and hasattr(ad.end, "jd")
            dur = round((ad.end.jd - ad.start.jd) / 365.25, 3) if has_jd else None
            subs_models.append(
                DashaPeriod(
                    lord=ad.lord,
                    start=_format_datetime(ad.start),
                    end=_format_datetime(ad.end),
                    level=2,
                    duration_years=dur,
                    subs=pd_models,
                )
            )

    has_jd = hasattr(period.start, "jd") and hasattr(period.end, "jd")
    dur = round((period.end.jd - period.start.jd) / 365.25, 3) if has_jd else None
    return DashaPeriod(
        lord=period.lord,
        start=_format_datetime(period.start),
        end=_format_datetime(period.end),
        level=period.level,
        duration_years=dur,
        subs=subs_models,
    )


VEDIC_ASPECT_OFFSETS: dict[str, list[int]] = {
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

_ASPECT_NAMES: dict[int, str] = {
    3: "3rd",
    4: "4th",
    5: "5th",
    7: "7th",
    8: "8th",
    9: "9th",
    10: "10th",
}


def calculate_vedic_aspects(
    planets: list[PlanetPosition],
    houses: list[HouseCusp] | None = None,
) -> list[VedicAspect]:
    """Calculate classical Parashari Graha Drishti (house-to-house aspects).

    All planets cast full aspect on the 7th house from their position.
    Special aspects (Vishesha Drishti):
    - Mars: 4th, 7th, 8th
    - Jupiter: 5th, 7th, 9th
    - Saturn: 3rd, 7th, 10th
    - Rahu & Ketu: 5th, 7th, 9th
    """
    aspects: list[VedicAspect] = []
    house_signs = {h.house: h.sign for h in houses} if houses else {}

    for p in planets:
        offsets = VEDIC_ASPECT_OFFSETS.get(p.name)
        if not offsets:
            continue
        for offset in offsets:
            target_house = ((p.house - 1 + (offset - 1)) % 12) + 1
            target_sign = house_signs.get(target_house, "")
            aspected_planets = [
                other.name
                for other in planets
                if other.house == target_house and other.name != p.name
            ]
            aspects.append(
                VedicAspect(
                    planet=p.name,
                    source_house=p.house,
                    target_house=target_house,
                    aspect_type=_ASPECT_NAMES.get(offset, f"{offset}th"),
                    target_sign=target_sign,
                    aspected_planets=aspected_planets,
                    strength=1.0,
                )
            )
    return aspects


def calculate_chart(
    birth: BirthData,
    ayanamsa: Ayanamsa = Ayanamsa.JHORA_LAHIRI,
    house_system: HouseSystem = HouseSystem.WHOLE_SIGN,
    target_date: datetime | None = None,
    include_dashas: bool = True,
    include_vargas: bool = True,
    include_ashtakavarga: bool = True,
    include_shadbala: bool = True,
    include_upagrahas: bool = True,
    include_transits: bool = True,
    include_panchanga: bool = True,
    include_yogas: bool = True,
) -> ChartData:
    """
    Calculate complete Vedic birth chart using Swiss Ephemeris / mayaastrolib.

    Args:
        birth: Birth data (date, time, location, timezone)
        ayanamsa: Ayanamsa system (default: Lahiri)
        house_system: House system (default: Whole Sign)
        target_date: Target datetime for current Dasha lookup (default: now)
        include_dashas: Whether to calculate Vimshottari Dashas
        include_vargas: Whether to calculate Shodashavarga charts
        include_ashtakavarga: Whether to calculate Ashtakavarga points
        include_shadbala: Whether to calculate Shadbala strengths
        include_upagrahas: Whether to calculate shadow planets (upagrahas)

    Returns:
        ChartData with planetary positions, houses, aspects, dashas, vargas, etc.
    """
    # 1. Prepare timezone offset string for Datetime
    dt_local = datetime(
        birth.year,
        birth.month,
        birth.day,
        birth.hour,
        birth.minute,
        birth.second,
        tzinfo=ZoneInfo(birth.timezone),
    )
    utc_offset = dt_local.utcoffset()
    offset_sec = utc_offset.total_seconds() if utc_offset is not None else 0.0
    offset_str = format_tz_offset(offset_sec)

    decimal_hour = birth.hour + (birth.minute / 60.0) + (birth.second / 3600.0)
    m_dt = Datetime([birth.year, birth.month, birth.day], decimal_hour, offset_str)
    m_pos = GeoPos(birth.latitude, birth.longitude)

    # 2. Configure Ayanamsa and House system
    is_jhora = ayanamsa == Ayanamsa.JHORA_LAHIRI
    base_ayanamsa = "lahiri" if is_jhora else ayanamsa.value
    # JHora traditional Lahiri is 56.5318 arcseconds smaller than standard IAU Lahiri
    jhora_offset_deg = (56.5318 / 3600.0) if is_jhora else 0.0

    m_hsys = HOUSE_MAP.get(house_system, const.HOUSES_WHOLE_SIGN)

    # Objects to calculate
    objects_list = [
        const.SUN,
        const.MOON,
        const.MARS,
        const.MERCURY,
        const.JUPITER,
        const.VENUS,
        const.SATURN,
        const.NORTH_NODE,
        const.SOUTH_NODE,
    ]

    # Instantiate sidereal chart
    chart = Chart(
        m_dt,
        m_pos,
        IDs=objects_list,
        zodiac=const.ZODIAC_SIDEREAL,
        ayanamsa=base_ayanamsa,
        hsys=m_hsys,
    )

    # Exact ayanamsa value in degrees
    ayanamsa_deg = vaya.get(base_ayanamsa, m_dt) - jhora_offset_deg

    # 3. Ascendant and Midheaven
    asc_angle = chart.getAngle(const.ASC)
    asc_lon = (asc_angle.lon + jhora_offset_deg) % 360.0
    asc_sign = get_sign(asc_lon)
    asc_sign_idx = ZODIAC_SIGNS.index(asc_sign)
    asc_deg_in_sign = get_degree_in_sign(asc_lon)
    asc_nak, asc_lord, asc_pada = get_nakshatra(asc_lon)

    ascendant = PlanetPosition(
        name="Ascendant",
        longitude=round(asc_lon, 6),
        latitude=0.0,
        distance=0.0,
        speed=0.0,
        sign=asc_sign,
        sign_lord=SIGN_LORDS[asc_sign],
        degree_in_sign=round(asc_deg_in_sign, 6),
        nakshatra=asc_nak,
        nakshatra_lord=asc_lord,
        pada=asc_pada,
        house=1,
        retrograde=False,
    )

    mc_angle = chart.getAngle(const.MC)
    mc_lon = (mc_angle.lon + jhora_offset_deg) % 360.0
    mc_sign = get_sign(mc_lon)
    mc_sign_idx = ZODIAC_SIGNS.index(mc_sign)
    mc_deg_in_sign = get_degree_in_sign(mc_lon)

    # In Whole Sign, Midheaven house is determined by sign from Ascendant
    if house_system == HouseSystem.WHOLE_SIGN:
        mc_house = ((mc_sign_idx - asc_sign_idx) % 12) + 1
    else:
        mc_house = 10

    midheaven = PlanetPosition(
        name="Midheaven",
        longitude=round(mc_lon, 6),
        latitude=0.0,
        distance=0.0,
        speed=0.0,
        sign=mc_sign,
        sign_lord=SIGN_LORDS[mc_sign],
        degree_in_sign=round(mc_deg_in_sign, 6),
        nakshatra=None,
        nakshatra_lord=None,
        pada=None,
        house=mc_house,
        retrograde=False,
    )

    # 4. Houses
    houses_list = []
    for i, h in enumerate(chart.houses):
        if house_system == HouseSystem.WHOLE_SIGN:
            h_lon = ((asc_sign_idx + i) % 12) * 30.0
        else:
            h_lon = (h.lon + jhora_offset_deg) % 360.0
        h_sign = get_sign(h_lon)
        houses_list.append(
            HouseCusp(
                house=i + 1,
                longitude=round(h_lon, 6),
                sign=h_sign,
                sign_lord=SIGN_LORDS[h_sign],
                degree_in_sign=round(get_degree_in_sign(h_lon), 6),
            )
        )

    # 5. Planetary positions (7 Grahas) with Swiss Ephemeris true speeds
    planets = []
    swe_mode = vaya._swe_mode_for(base_ayanamsa)
    with vaya._AYANAMSA_LOCK:
        swisseph.set_sid_mode(swe_mode)

    for p_name in VEDIC_PLANETS:
        p_obj = chart.getObject(p_name)
        swe_id = SWE_BODY_MAP[p_name]

        # Calculate exact speed and coordinates from Swiss Ephemeris
        swe_calc, _ = swisseph.calc_ut(m_dt.jd, swe_id, swisseph.FLG_SIDEREAL | swisseph.FLG_SPEED)
        p_lon = (swe_calc[0] + jhora_offset_deg) % 360.0
        p_lat = swe_calc[1]
        p_dist = swe_calc[2]
        p_speed = swe_calc[3]
        p_retro = bool(p_speed < 0)

        p_sign = get_sign(p_lon)
        p_sign_idx = ZODIAC_SIGNS.index(p_sign)
        p_deg_in_sign = get_degree_in_sign(p_lon)
        p_nak, p_nak_lord, p_pada = get_nakshatra(p_lon)

        # House assignment
        if house_system == HouseSystem.WHOLE_SIGN:
            p_house = ((p_sign_idx - asc_sign_idx) % 12) + 1
        else:
            if hasattr(p_obj, "house") and p_obj.house is not None:
                house_num = getattr(p_obj.house, "num", None)
                if house_num is None:
                    house_id = str(getattr(p_obj.house, "id", "1")).replace("House", "")
                    house_num = int(house_id)
                p_house = house_num
            else:
                p_house = ((p_sign_idx - asc_sign_idx) % 12) + 1

        dignity = calculate_dignity(p_name, p_sign)

        planets.append(
            PlanetPosition(
                name=p_name,
                longitude=round(p_lon, 6),
                latitude=round(p_lat, 6),
                distance=round(p_dist, 6),
                speed=round(p_speed, 6),
                sign=p_sign,
                sign_lord=SIGN_LORDS[p_sign],
                degree_in_sign=round(p_deg_in_sign, 6),
                nakshatra=p_nak,
                nakshatra_lord=p_nak_lord,
                pada=p_pada,
                house=p_house,
                retrograde=p_retro,
                dignity=dignity,
            )
        )

    # 6. Rahu & Ketu (Mean Node)
    rahu_calc, _ = swisseph.calc_ut(
        m_dt.jd,
        swisseph.MEAN_NODE,
        swisseph.FLG_SIDEREAL | swisseph.FLG_SPEED,
    )
    rahu_lon = (rahu_calc[0] + jhora_offset_deg) % 360.0
    rahu_speed = rahu_calc[3]
    rahu_sign = get_sign(rahu_lon)
    rahu_sign_idx = ZODIAC_SIGNS.index(rahu_sign)
    rahu_deg = get_degree_in_sign(rahu_lon)
    rahu_nak, rahu_lord, rahu_pada = get_nakshatra(rahu_lon)
    rahu_house = ((rahu_sign_idx - asc_sign_idx) % 12) + 1

    rahu = PlanetPosition(
        name="Rahu",
        longitude=round(rahu_lon, 6),
        latitude=0.0,
        distance=round(rahu_calc[2], 6),
        speed=round(rahu_speed, 6),
        sign=rahu_sign,
        sign_lord=SIGN_LORDS[rahu_sign],
        degree_in_sign=round(rahu_deg, 6),
        nakshatra=rahu_nak,
        nakshatra_lord=rahu_lord,
        pada=rahu_pada,
        house=rahu_house,
        retrograde=True,
    )

    ketu_lon = (rahu_lon + 180.0) % 360.0
    ketu_sign = get_sign(ketu_lon)
    ketu_sign_idx = ZODIAC_SIGNS.index(ketu_sign)
    ketu_deg = get_degree_in_sign(ketu_lon)
    ketu_nak, ketu_lord, ketu_pada = get_nakshatra(ketu_lon)
    ketu_house = ((ketu_sign_idx - asc_sign_idx) % 12) + 1

    ketu = PlanetPosition(
        name="Ketu",
        longitude=round(ketu_lon, 6),
        latitude=0.0,
        distance=round(rahu_calc[2], 6),
        speed=round(rahu_speed, 6),
        sign=ketu_sign,
        sign_lord=SIGN_LORDS[ketu_sign],
        degree_in_sign=round(ketu_deg, 6),
        nakshatra=ketu_nak,
        nakshatra_lord=ketu_lord,
        pada=ketu_pada,
        house=ketu_house,
        retrograde=True,
    )

    # 7. Aspects
    aspects = []
    aspect_bodies = planets + [ascendant, midheaven]
    for i in range(len(aspect_bodies)):
        for j in range(i + 1, len(aspect_bodies)):
            p1, p2 = aspect_bodies[i], aspect_bodies[j]
            # Calculate angular separation
            diff = abs(p1.longitude - p2.longitude)
            angle = min(diff, 360.0 - diff)

            for target_angle, name in [
                (0.0, "conjunction"),
                (60.0, "sextile"),
                (90.0, "square"),
                (120.0, "trine"),
                (180.0, "opposition"),
            ]:
                orb = abs(angle - target_angle)
                if orb <= 8.0:
                    aspects.append(
                        Aspect(
                            planet1=p1.name,
                            planet2=p2.name,
                            aspect_type=name,
                            orb=round(orb, 2),
                            applying=True,
                            exact_degree=round(target_angle, 2),
                        )
                    )

    # 7b. Vedic Graha Drishti (Parashari House Aspects)
    vedic_aspects = calculate_vedic_aspects(planets + [rahu, ketu], houses_list)

    # 8. Vimshottari Dashas
    dashas_data = None
    if include_dashas:
        target_pydt = target_date or datetime.now(ZoneInfo(birth.timezone))
        t_td = target_pydt.utcoffset()
        t_sec = t_td.total_seconds() if t_td is not None else offset_sec
        t_str = format_tz_offset(t_sec)
        target_mdt = Datetime(
            [target_pydt.year, target_pydt.month, target_pydt.day],
            target_pydt.hour + (target_pydt.minute / 60.0) + (target_pydt.second / 3600.0),
            t_str,
        )

        moon_p = next(p for p in planets if p.name == "Moon")
        natal_nak = vnak.of_longitude(moon_p.longitude)
        balance_lord, balance_years = vdasha._birth_balance(natal_nak, moon_p.longitude)
        sequence = vdasha._build_md_sequence(m_dt, balance_lord, balance_years)

        current_md = vdasha._find_active(sequence, target_mdt)
        current_ad = current_pratyantar = None
        if current_md is not None:
            ads = vdasha.antardashas(current_md)
            current_ad = vdasha._find_active(ads, target_mdt)
            if current_ad is not None:
                prs = vdasha.pratyantar_dashas(current_ad)
                current_pratyantar = vdasha._find_active(prs, target_mdt)

        md_models = [_convert_dasha_period(md, include_subs=True) for md in sequence]
        current_md_model = _active_period(current_md)
        current_ad_model = _active_period(current_ad)
        current_pd_model = _active_period(current_pratyantar)

        dashas_data = VimshottariDasha(
            birth_nakshatra=natal_nak.name,
            birth_nakshatra_lord=natal_nak.lord,
            balance_lord=balance_lord,
            balance_years=round(balance_years, 4),
            current_md=current_md_model,
            current_ad=current_ad_model,
            current_pd=current_pd_model,
            mahadashas=md_models,
        )

    # 9. Shodashavarga (Divisional Charts)
    vargas_data = None
    if include_vargas:
        all_objs = {p.name: p.longitude for p in planets}
        all_objs["Ascendant"] = asc_lon
        all_objs["North Node"] = rahu_lon
        all_objs["South Node"] = ketu_lon
        vargas_data = {}
        for v_name, fn in vdiv._VARGA_FUNCTIONS.items():
            vargas_data[v_name] = {p_id: vdiv.SIGN_NAMES[fn(lon)] for p_id, lon in all_objs.items()}

    # 10. Ashtakavarga
    ashtakavarga_data = None
    if include_ashtakavarga:
        av_res = vav.ashtakavarga(chart, ayanamsa=base_ayanamsa)
        shodhita_sav = None
        shodhita_bav = None
        try:
            p_signs_map = {
                p: ZODIAC_SIGNS.index(chart.get(p).sign) for p in vav.ASHTAKAVARGA_PLANETS
            }
            shodhita_res = vav.shodhita_sarvashtakavarga(
                p_signs_map,
                lagna_sign=ZODIAC_SIGNS.index(ascendant.sign),
            )
            shodhita_sav = shodhita_res.get("per_rasi")
            shodhita_bav = shodhita_res.get("by_planet")
        except Exception as e:
            logger.warning("Failed to calculate shodhita ashtakavarga: %s", e)
        ashtakavarga_data = AshtakavargaData(
            sarvashtakavarga=av_res["per_rasi"],
            grand_total=av_res["grand_total"],
            bhinnashtakavarga=av_res["by_planet"],
            shodhita_sarvashtakavarga=shodhita_sav,
            shodhita_bhinnashtakavarga=shodhita_bav,
        )

    # 11. Shadbala
    shadbala_data = None
    if include_shadbala:
        sb_res = vsb.shadbala(chart)
        shadbala_data = {}
        for p_id, p_sb in sb_res.items():
            shadbala_data[p_id] = ShadbalaPlanet(
                planet=p_id,
                total_rupas=round(p_sb["total_rupas"], 2),
                total_virupas=round(p_sb["total_virupas"], 2),
                required_rupas=round(p_sb["required_rupas"], 2),
                sufficient=p_sb["sufficient"],
                sthana_bala=round(p_sb["sthana"]["total"], 2),
                dig_bala=round(p_sb["dig"], 2),
                kala_bala=round(p_sb["kala"]["total"], 2),
                cheshta_bala=round(p_sb["cheshta"], 2),
                naisargika_bala=round(p_sb["naisargika"], 2),
                drik_bala=round(p_sb["drik"], 2),
            )

    # 12. Upagrahas
    upagrahas_data = None
    if include_upagrahas:
        raw_upas = vupa.upagrahas(chart)
        upagrahas_data = []
        for name, up_obj in raw_upas.items():
            up_lon = (up_obj.sidereal_longitude + jhora_offset_deg) % 360.0
            up_sign = get_sign(up_lon)
            up_sign_idx = ZODIAC_SIGNS.index(up_sign)
            up_house = ((up_sign_idx - asc_sign_idx) % 12) + 1
            upagrahas_data.append(
                UpagrahaPosition(
                    name=name,
                    longitude=round(up_lon, 6),
                    sign=up_sign,
                    degree_in_sign=round(get_degree_in_sign(up_lon), 6),
                    house=up_house,
                )
            )

    d10_chart_data = None
    if vargas_data and "D10" in vargas_data:
        d10_v = vargas_data["D10"]
        d10_asc = d10_v.get("Ascendant", ascendant.sign)
        d10_asc_idx = ZODIAC_SIGNS.index(d10_asc)
        d10_planets = {}
        for name in CHART_BODIES:
            if name in d10_v:
                s = d10_v[name]
                s_idx = ZODIAC_SIGNS.index(s)
                h = ((s_idx - d10_asc_idx) % 12) + 1
                d10_planets[name] = {
                    "sign": s,
                    "house": h,
                    "sign_lord": SIGN_LORDS[s],
                }
        d10_chart_data = {
            "varga": "D10",
            "ascendant": {
                "sign": d10_asc,
                "house": 1,
                "sign_lord": SIGN_LORDS[d10_asc],
            },
            "planets": d10_planets,
        }

    res_chart = ChartData(
        birth_data=birth,
        calculation_time=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        zodiac=ZodiacSystem.SIDEREAL,
        ayanamsa=ayanamsa,
        ayanamsa_value=round(ayanamsa_deg, 6),
        house_system=house_system,
        planets=planets,
        houses=houses_list,
        aspects=aspects,
        ascendant=ascendant,
        midheaven=midheaven,
        rahu=rahu,
        ketu=ketu,
        dashas=dashas_data,
        vargas=vargas_data,
        d10_chart=d10_chart_data,
        ashtakavarga=ashtakavarga_data,
        shadbala=shadbala_data,
        upagrahas=upagrahas_data,
        vedic_aspects=vedic_aspects,
    )

    if include_transits:
        try:
            from nakshatra.transits import calculate_transits, scan_transit_window

            transit_report = calculate_transits(res_chart, transit_date=target_date)
            t_dict = transit_report.model_dump()
            transit_win = scan_transit_window(res_chart, start_date=target_date, days=30)
            t_dict["window"] = transit_win.model_dump()
            res_chart.transits = t_dict
        except Exception as e:
            logger.warning("Failed to calculate transits: %s", e)

    if include_panchanga:
        try:
            from nakshatra.panchanga import calculate_panchanga

            res_chart.panchanga = calculate_panchanga(
                dt_local,
                birth.latitude,
                birth.longitude,
                birth.timezone,
                ayanamsa=ayanamsa,
            )
        except Exception as e:
            logger.warning("Failed to calculate panchanga: %s", e)

    if include_yogas:
        try:
            from nakshatra.yogas import detect_yogas

            res_chart.yogas = detect_yogas(res_chart)
        except Exception as e:
            logger.warning("Failed to calculate yogas: %s", e)

    return res_chart
