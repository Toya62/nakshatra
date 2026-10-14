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
- Gochar transits with Sade Sati, Jupiter Gochar, and Double Transit analysis
- Multi-format outputs: ASCII tables, South Indian diagram, Markdown, CSV, JSON
"""

import nakshatra.formatters as formatters
import nakshatra.panchanga as panchanga
import nakshatra.transits as transits
import nakshatra.yogas as yogas
from nakshatra.core import (
    AshtakavargaData,
    Aspect,
    Ayanamsa,
    BirthData,
    ChartData,
    DashaPeriod,
    HouseCusp,
    HouseSystem,
    PlanetPosition,
    ShadbalaPlanet,
    UpagrahaPosition,
    VimshottariDasha,
    ZodiacSystem,
    calculate_chart,
)
from nakshatra.formatters import (
    format_chart_diagram,
    format_csv,
    format_markdown,
    format_table,
)
from nakshatra.panchanga import (
    KaranaData,
    NakshatraData,
    PanchangaData,
    TithiData,
    VaraData,
    YogaData,
    calculate_panchanga,
)
from nakshatra.transits import (
    SadeSatiInfo,
    TransitPlanet,
    TransitReport,
    calculate_transits,
)
from nakshatra.yogas import (
    YogaCategory,
    YogaResult,
    detect_yogas,
    format_yogas_markdown,
    format_yogas_table,
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
    "format_table",
    "format_markdown",
    "format_csv",
    "format_chart_diagram",
    "calculate_transits",
    "TransitReport",
    "TransitPlanet",
    "SadeSatiInfo",
    "calculate_panchanga",
    "PanchangaData",
    "TithiData",
    "NakshatraData",
    "YogaData",
    "KaranaData",
    "VaraData",
    "detect_yogas",
    "YogaResult",
    "YogaCategory",
    "format_yogas_table",
    "format_yogas_markdown",
    "formatters",
    "transits",
    "panchanga",
    "yogas",
]
