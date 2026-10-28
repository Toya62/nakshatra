"""
Nakshatra - Vedic Astrology AI Engine

High-precision Vedic astrology calculation engine powered by Swiss Ephemeris
via mayaastrolib and pyswisseph.

Features:
- Sidereal birth charts with Lahiri, JHora Lahiri, Raman, KP, and Fagan-Bradley ayanamsas
- Vimshottari Dashas with exact MD, AD, and PD timestamps down to the second
- 120-year visual life timeline and real-time age marker
- Shodashavarga (D1 through D60 divisional charts)
- Complete Ashtakavarga (canonical 337 Sarvashtakavarga and Bhinnashtakavarga)
- Shadbala planetary strength calculations (rupas and virupas)
- Upagrahas (shadow planets: Dhuma, Vyatipata, Parivesha, Indrachapa, Upaketu)
- Gochar transits with Sade Sati, Jupiter Gochar, and Double Transit analysis
- 30-day transit window scanner for ingresses, stations, and Chandrashtama periods
- Panchanga engine with 5 limbs of Vedic time and solar day tracking
- Classical Yogas (Parivartana, Neechabhanga, Raja, Dhana, Mahapurusha)
- Dual-system remedies: Classical Parashari (Mantra, Gem, Dana) and Lal Kitab Upayas
- 36-point Ashtakoota Kundali matching and Kuja Dosha (Manglik) analysis
- Muhurtha timing elections (Choghadiya, Planetary Horas, Abhijit, Rahu Kalam)
- Deterministic hierarchical life domain predictions (Career, Finance, Marriage, Health, Spirituality)
- Scripture-grounded RAG with 3-pillar explainable reason inspector (Pramana, Yukti, Dharma)
- Nepali Bikram Sambat (BS) calendar and Sanskrit Devanagari nomenclature
- Multi-format outputs: North/South Indian diagrams, ASCII tables, Markdown, CSV, JSON
"""

import nakshatra.compatibility as compatibility
import nakshatra.formatters as formatters
import nakshatra.muhurtha as muhurtha
import nakshatra.panchanga as panchanga
import nakshatra.predictor as predictor
import nakshatra.remedies as remedies
import nakshatra.transits as transits
import nakshatra.yogas as yogas
from nakshatra.compatibility import (
    CompatibilityReport,
    KujaDoshaReport,
    calculate_compatibility,
)
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
from nakshatra.muhurtha import (
    MuhurthaReport,
    calculate_muhurtha,
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
from nakshatra.predictor import (
    DomainPrediction,
    PromiseTier,
    evaluate_all_domains,
    evaluate_domain,
)
from nakshatra.remedies import (
    LalKitabUpaya,
    ParashariRemedy,
    PlanetRemedy,
    RemediesReport,
    calculate_remedies,
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
__license__ = "AGPL-3.0"

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
    "calculate_remedies",
    "RemediesReport",
    "PlanetRemedy",
    "ParashariRemedy",
    "LalKitabUpaya",
    "calculate_compatibility",
    "CompatibilityReport",
    "KujaDoshaReport",
    "calculate_muhurtha",
    "MuhurthaReport",
    "evaluate_domain",
    "evaluate_all_domains",
    "DomainPrediction",
    "PromiseTier",
    "formatters",
    "transits",
    "panchanga",
    "yogas",
    "remedies",
    "compatibility",
    "muhurtha",
    "predictor",
]
