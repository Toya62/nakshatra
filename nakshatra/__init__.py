"""
Nakshatra - Vedic Astrology AI Engine

High-precision Vedic astrology calculation engine powered by Swiss Ephemeris
via mayaastrolib and pyswisseph.

Features:
- Sidereal birth charts with Lahiri, JHora Lahiri, Raman, KP, and Fagan-Bradley ayanamsas
- Vimshottari Dashas with exact MD, AD, and PD timestamps down to the second
- Shodashavarga (D1 through D60 divisional charts)
- Complete Ashtakavarga (Sarvashtakavarga and Bhinnashtakavarga)
- Shadbala planetary strength calculations (rupas and virupas)
- Upagrahas (shadow planets: Dhuma, Vyatipata, Parivesha, Indrachapa, Upaketu)
"""

from nakshatra.core import (
    BirthData,
    ChartData,
    Ayanamsa,
    HouseSystem,
    ZodiacSystem,
    calculate_chart,
    PlanetPosition,
    HouseCusp,
    Aspect,
    DashaPeriod,
    VimshottariDasha,
    ShadbalaPlanet,
    AshtakavargaData,
    UpagrahaPosition,
)

__version__ = "0.1.0"
__author__ = "Toya"
__license__ = "MIT"

__all__ = [
    "BirthData",
    "ChartData",
    "Ayanamsa",
    "HouseSystem",
    "ZodiacSystem",
    "calculate_chart",
    "PlanetPosition",
    "HouseCusp",
    "Aspect",
    "DashaPeriod",
    "VimshottariDasha",
    "ShadbalaPlanet",
    "AshtakavargaData",
    "UpagrahaPosition",
]