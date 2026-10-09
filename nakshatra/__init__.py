"""
Nakshatra - Vedic Astrology AI Engine

A modern, MIT-licensed Vedic astrology calculation engine
built on NASA JPL ephemeris via Skyfield/openephem.

Default ayanamsa: Lahiri (Chitra Paksha) - official Indian government standard
Default house system: Whole Sign (traditional Vedic)
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
]