"""
Nakshatra - Vedic Astrology AI Engine
Core calculation module using openephem (JPL/NASA ephemeris via Skyfield).
Default ayanamsa: Lahiri (Chitra Paksha).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum
from zoneinfo import ZoneInfo

from openephem import resolve, assemble
from openephem.houses import houses_from_jd
from pydantic import BaseModel, Field, field_validator


class Ayanamsa(str, Enum):
    """Supported ayanamsa systems."""
    LAHIRI = "lahiri"
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
    place_name: Optional[str] = None


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
    place_name: Optional[str] = None

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
    latitude: float
    distance: float
    speed: float
    sign: str
    sign_lord: str
    degree_in_sign: float
    nakshatra: Optional[str] = None
    nakshatra_lord: Optional[str] = None
    pada: Optional[int] = None
    house: int
    retrograde: bool
    dignity: Optional[str] = None


class HouseCusp(BaseModel):
    """House cusp data."""
    house: int
    longitude: float
    sign: str
    degree_in_sign: float


class Aspect(BaseModel):
    """Aspect between two planets."""
    planet1: str
    planet2: str
    aspect_type: str
    orb: float
    applying: bool
    exact_degree: float


class ChartData(BaseModel):
    """Complete birth chart data."""
    birth_data: BirthData
    calculation_time: str
    zodiac: ZodiacSystem
    ayanamsa: Ayanamsa
    house_system: HouseSystem
    planets: list[PlanetPosition]
    houses: list[HouseCusp]
    aspects: list[Aspect]
    ascendant: PlanetPosition
    midheaven: PlanetPosition
    rahu: PlanetPosition
    ketu: PlanetPosition

    def to_json(self) -> str:
        """Export as JSON string."""
        return self.model_dump_json(indent=2)

    def to_dict(self) -> dict:
        """Export as dictionary."""
        return self.model_dump()


# Nakshatra data (27 nakshatras with lords)
NAKSHATRAS = [
    ("Ashwini", "Ketu"), ("Bharani", "Venus"), ("Krittika", "Sun"),
    ("Rohini", "Moon"), ("Mrigashira", "Mars"), ("Ardra", "Rahu"),
    ("Punarvasu", "Jupiter"), ("Pushya", "Saturn"), ("Ashlesha", "Mercury"),
    ("Magha", "Ketu"), ("Purva Phalguni", "Venus"), ("Uttara Phalguni", "Sun"),
    ("Hasta", "Moon"), ("Chitra", "Mars"), ("Swati", "Rahu"),
    ("Vishakha", "Jupiter"), ("Anuradha", "Saturn"), ("Jyeshtha", "Mercury"),
    ("Mula", "Ketu"), ("Purva Ashadha", "Venus"), ("Uttara Ashadha", "Sun"),
    ("Shravana", "Moon"), ("Dhanishta", "Mars"), ("Shatabhisha", "Rahu"),
    ("Purva Bhadrapada", "Jupiter"), ("Uttara Bhadrapada", "Saturn"), ("Revati", "Mercury"),
]

# Sign lords
SIGN_LORDS = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury",
    "Cancer": "Moon", "Leo": "Sun", "Virgo": "Mercury",
    "Libra": "Venus", "Scorpio": "Mars", "Sagittarius": "Jupiter",
    "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter",
}

# Vedic planet names mapping (openephem uses Sanskrit sign names)
VEDIC_PLANET_MAP = {
    "Sun": "Sun",
    "Moon": "Moon", 
    "Mars": "Mars",
    "Mercury": "Mercury",
    "Jupiter": "Jupiter",
    "Venus": "Venus",
    "Saturn": "Saturn",
    "TrueNode": "Rahu",  # Mean node is Rahu
}

# Sanskrit sign names to Western
SANSKRIT_TO_WESTERN = {
    "Mesha": "Aries", "Vrishabha": "Taurus", "Mithuna": "Gemini",
    "Karka": "Cancer", "Simha": "Leo", "Kanya": "Virgo",
    "Tula": "Libra", "Vrishchika": "Scorpio", "Dhanu": "Sagittarius",
    "Makara": "Capricorn", "Kumbha": "Aquarius", "Meena": "Pisces",
}

# Planet order for Vedic
VEDIC_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]


def get_nakshatra(longitude: float) -> tuple[str, str, int]:
    """Calculate nakshatra, lord, and pada from sidereal longitude."""
    nakshatra_span = 360 / 27
    nakshatra_index = int(longitude / nakshatra_span) % 27
    nakshatra_name, lord = NAKSHATRAS[nakshatra_index]
    
    degree_in_nakshatra = longitude % nakshatra_span
    pada = int(degree_in_nakshatra / (nakshatra_span / 4)) + 1
    
    return nakshatra_name, lord, pada


def get_sign(longitude: float) -> str:
    """Get zodiac sign from longitude."""
    signs = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]
    sign_index = int(longitude / 30) % 12
    return signs[sign_index]


def get_degree_in_sign(longitude: float) -> float:
    """Get degree within sign (0-30)."""
    return longitude % 30


def calculate_dignity(planet: str, sign: str) -> str:
    """Calculate planetary dignity (simplified)."""
    exaltation = {
        "Sun": "Aries", "Moon": "Taurus", "Mars": "Capricorn",
        "Mercury": "Virgo", "Jupiter": "Cancer", "Venus": "Pisces",
        "Saturn": "Libra",
    }
    debilitation = {
        "Sun": "Libra", "Moon": "Scorpio", "Mars": "Cancer",
        "Mercury": "Pisces", "Jupiter": "Capricorn", "Venus": "Virgo",
        "Saturn": "Aries",
    }
    own_signs = {
        "Sun": ["Leo"], "Moon": ["Cancer"], "Mars": ["Aries", "Scorpio"],
        "Mercury": ["Gemini", "Virgo"], "Jupiter": ["Sagittarius", "Pisces"],
        "Venus": ["Taurus", "Libra"], "Saturn": ["Capricorn", "Aquarius"],
    }
    
    if sign == exaltation.get(planet):
        return "exalted"
    elif sign == debilitation.get(planet):
        return "debilitated"
    elif sign in own_signs.get(planet, []):
        return "own_sign"
    return "neutral"


def calculate_chart(
    birth: BirthData,
    ayanamsa: Ayanamsa = Ayanamsa.LAHIRI,
    house_system: HouseSystem = HouseSystem.WHOLE_SIGN,
) -> ChartData:
    """
    Calculate complete Vedic birth chart.
    
    Args:
        birth: Birth data (date, time, location)
        ayanamsa: Ayanamsa system (default: Lahiri)
        house_system: House system (default: Whole Sign)
    
    Returns:
        ChartData with all planetary positions, houses, aspects
    """
    # Resolve birth moment to coordinates
    moment = resolve(
        date=(birth.year, birth.month, birth.day),
        time=(birth.hour, birth.minute, birth.second),
        lat=birth.latitude,
        lon=birth.longitude,
        tz=birth.timezone,
    )
    
    # Assemble chart with sidereal zodiac and specified ayanamsa
    chart = assemble(
        moment,
        zodiac="sidereal",
        ayanamsa=ayanamsa.value,
        house_system=house_system.value,
    )
    
    # Use sidereal angles from assemble (already ayanamsa-corrected)
    angles = chart.get("angles", {})
    asc_lon = angles.get("asc", 0.0)
    mc_lon = angles.get("mc", 0.0)
    
    # Compute house cusps for the selected house system
    # For Whole Sign, we derive cusps from sidereal ascendant
    # For other systems, we need tropical houses then convert
    if house_system == HouseSystem.WHOLE_SIGN:
        # Whole Sign: each house = one sign starting from ascendant sign
        asc_sign_idx = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"].index(get_sign(asc_lon))
        cusps = [((asc_sign_idx + i) % 12) * 30 for i in range(12)]
    else:
        # For quadrant systems, use houses_from_jd (tropical) - approximation
        houses_obj = houses_from_jd(chart["jd_ut"], chart["lat"], chart["lon"], house_system.value)
        cusps = houses_obj.cusps
    
    # Extract planet positions from chart["bodies"] (dict)
    # Only the 7 grahas (excluding Rahu/Ketu which are handled separately)
    GRAHAS = {
        "Sun": "Sun",
        "Moon": "Moon", 
        "Mars": "Mars",
        "Mercury": "Mercury",
        "Jupiter": "Jupiter",
        "Venus": "Venus",
        "Saturn": "Saturn",
    }
    
    planets = []
    for ephem_name, vedic_name in GRAHAS.items():
        if ephem_name not in chart["bodies"]:
            continue
            
        body = chart["bodies"][ephem_name]
        lon = body["lon"]
        speed = body.get("speed", 0)
        retro = body.get("retro", False)
        
        # openephem doesn't provide latitude/distance in this format, use defaults
        lat = 0.0
        dist = 1.0
        
        sign = get_sign(lon)
        deg_in_sign = get_degree_in_sign(lon)
        nakshatra, nakshatra_lord, pada = get_nakshatra(lon)
        dignity = calculate_dignity(vedic_name, sign)
        
        # House assignment (will be calculated properly below)
        house = 1
        
        planets.append(PlanetPosition(
            name=vedic_name,
            longitude=round(lon, 6),
            latitude=round(lat, 6),
            distance=round(dist, 6),
            speed=round(speed, 6),
            sign=sign,
            sign_lord=SIGN_LORDS[sign],
            degree_in_sign=round(deg_in_sign, 6),
            nakshatra=nakshatra,
            nakshatra_lord=nakshatra_lord,
            pada=pada,
            house=house,
            retrograde=retro,
            dignity=dignity,
        ))
    
    # Ascendant
    asc_sign = get_sign(asc_lon)
    asc_deg = get_degree_in_sign(asc_lon)
    asc_nak, asc_lord, asc_pada = get_nakshatra(asc_lon)
    
    ascendant = PlanetPosition(
        name="Ascendant",
        longitude=round(asc_lon, 6),
        latitude=0.0,
        distance=0.0,
        speed=0.0,
        sign=asc_sign,
        sign_lord=SIGN_LORDS[asc_sign],
        degree_in_sign=round(asc_deg, 6),
        nakshatra=asc_nak,
        nakshatra_lord=asc_lord,
        pada=asc_pada,
        house=1,
        retrograde=False,
    )
    
    # Midheaven
    mc_sign = get_sign(mc_lon)
    mc_deg = get_degree_in_sign(mc_lon)
    
    midheaven = PlanetPosition(
        name="Midheaven",
        longitude=round(mc_lon, 6),
        latitude=0.0,
        distance=0.0,
        speed=0.0,
        sign=mc_sign,
        sign_lord=SIGN_LORDS[mc_sign],
        degree_in_sign=round(mc_deg, 6),
        nakshatra=None,
        nakshatra_lord=None,
        pada=None,
        house=10,
        retrograde=False,
    )
    
    # Rahu (TrueNode from openephem)
    rahu_lon = chart["bodies"]["TrueNode"]["lon"] if "TrueNode" in chart["bodies"] else 0.0
    ketu_lon = (rahu_lon + 180) % 360
    
    rahu_sign = get_sign(rahu_lon)
    rahu_deg = get_degree_in_sign(rahu_lon)
    rahu_nak, rahu_lord, rahu_pada = get_nakshatra(rahu_lon)
    
    rahu = PlanetPosition(
        name="Rahu",
        longitude=round(rahu_lon, 6),
        latitude=0.0,
        distance=0.0,
        speed=0.0,
        sign=rahu_sign,
        sign_lord=SIGN_LORDS[rahu_sign],
        degree_in_sign=round(rahu_deg, 6),
        nakshatra=rahu_nak,
        nakshatra_lord=rahu_lord,
        pada=rahu_pada,
        house=1,
        retrograde=True,
    )
    
    ketu_sign = get_sign(ketu_lon)
    ketu_deg = get_degree_in_sign(ketu_lon)
    ketu_nak, ketu_lord, ketu_pada = get_nakshatra(ketu_lon)
    
    ketu = PlanetPosition(
        name="Ketu",
        longitude=round(ketu_lon, 6),
        latitude=0.0,
        distance=0.0,
        speed=0.0,
        sign=ketu_sign,
        sign_lord=SIGN_LORDS[ketu_sign],
        degree_in_sign=round(ketu_deg, 6),
        nakshatra=ketu_nak,
        nakshatra_lord=ketu_lord,
        pada=ketu_pada,
        house=1,
        retrograde=True,
    )
    
    # Calculate houses from cusps
    houses_list = []
    signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
             "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
    
    for i, cusp_lon in enumerate(cusps):
        house_sign = get_sign(cusp_lon)
        houses_list.append(HouseCusp(
            house=i + 1,
            longitude=round(cusp_lon, 6),
            sign=house_sign,
            degree_in_sign=round(get_degree_in_sign(cusp_lon), 6),
        ))
    
    # Assign houses to planets based on Whole Sign from Ascendant
    asc_sign_idx = signs.index(asc_sign)
    
    for planet in planets:
        planet_sign_idx = signs.index(planet.sign)
        house_num = ((planet_sign_idx - asc_sign_idx) % 12) + 1
        planet.house = house_num
    
    rahu.house = ((signs.index(rahu.sign) - asc_sign_idx) % 12) + 1
    ketu.house = ((signs.index(ketu.sign) - asc_sign_idx) % 12) + 1
    
    # Calculate aspects from chart["aspects"] (already computed by openephem)
    aspects = []
    for aspect in chart.get("aspects", []):
        # Only include aspects involving Vedic planets + Asc/MC/Rahu/Ketu
        p1, p2 = aspect["a"], aspect["b"]
        aspect_type = aspect["aspect"]
        orb = aspect["orb"]
        applying = aspect["applying"]
        
        # Map openephem aspect names to our format
        aspect_map = {
            "conjunction": "conjunction",
            "sextile": "sextile", 
            "square": "square",
            "trine": "trine",
            "opposition": "opposition",
        }
        
        if aspect_type in aspect_map:
            aspects.append(Aspect(
                planet1=p1,
                planet2=p2,
                aspect_type=aspect_map[aspect_type],
                orb=round(abs(orb), 2),
                applying=applying,
                exact_degree=round(aspect["angle"], 2),
            ))
    
    return ChartData(
        birth_data=birth,
        calculation_time=datetime.utcnow().isoformat() + "Z",
        zodiac=ZodiacSystem.SIDEREAL,
        ayanamsa=ayanamsa,
        house_system=house_system,
        planets=planets,
        houses=houses_list,
        aspects=aspects,
        ascendant=ascendant,
        midheaven=midheaven,
        rahu=rahu,
        ketu=ketu,
    )