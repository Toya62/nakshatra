"""
Nakshatra — The Science of Light
FastAPI application exposing high-precision Swiss Ephemeris chart calculation,
120-year Vimshottari Dashas, Shodashavarga (D1-D60), Ashtakavarga (337 SAV),
Shadbala, Gochar transits, 30-day transit scanner, Classical Parashari Yogas,
Dual-System Remedies (Parashari & Lal Kitab), 36-point Ashtakoota compatibility,
Muhurtha election timings, 5-limb Panchanga, Bikram Sambat conversion,
Sanskrit Devanagari nomenclature, and RAG corpus consultation as JSON or formatted text.
"""

from __future__ import annotations

import json
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from calendar import monthrange
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, Response, StreamingResponse
from pydantic import BaseModel, Field, field_validator

from nakshatra.additional_lagnas import (
    SpecialLagnasReport,
)
from nakshatra.ai.corpus import IngestResult
from nakshatra.ai.embeddings import SearchResult
from nakshatra.ai.service import RAGService
from nakshatra.ai.synthesize import Answer
from nakshatra.calendar_bs import (
    DEVANAGARI_NAKSHATRAS,
    DEVANAGARI_PLANETS,
    DEVANAGARI_SIGNS,
    BikramSambatDate,
    GregorianDate,
    ad_to_bs,
    bs_to_ad,
)
from nakshatra.chakra import (
    ChakraReport,
)
from nakshatra.compatibility import (
    CompatibilityReport,
    calculate_compatibility,
    evaluate_chart_kuja_dosha,
)
from nakshatra.config import settings
from nakshatra.core import (
    Ayanamsa,
    BirthData,
    ChartData,
    HouseSystem,
    calculate_chart,
)
from nakshatra.geocoding import (
    PlaceResult,
    TimezoneOffsetInfo,
    resolve_timezone_offset,
    search_places,
)
from nakshatra.kalsarp import (
    KalsarpReport,
)
from nakshatra.licensing import get_licensing_statement
from nakshatra.muhurtha import (
    MuhurthaReport,
    calculate_muhurtha,
)
from nakshatra.panchanga import PanchangaData, calculate_panchanga
from nakshatra.privacy import (
    PrivacyMiddleware,
    get_privacy_statement,
    setup_privacy_logging,
)
from nakshatra.rashi_fal import (
    RashiFalReport,
    calculate_rashi_fal,
)
from nakshatra.rate_limit import RateLimitMiddleware
from nakshatra.transits import (
    TransitReport,
    TransitWindowReport,
    calculate_transits,
    scan_transit_window,
)
from nakshatra.varshaphal import (
    VarshaphalReport,
    calculate_varshaphal,
)
from nakshatra.yogas import (
    YogaResult,
    detect_yogas,
    format_yogas_markdown,
    format_yogas_table,
)

load_dotenv()

SUPPORTED_FORMATS = ("json", "table", "markdown", "csv", "diagram")

FORMAT_CONTENT_TYPES = {
    "json": "application/json",
    "table": "text/plain; charset=utf-8",
    "markdown": "text/markdown; charset=utf-8",
    "csv": "text/csv; charset=utf-8",
    "diagram": "text/plain; charset=utf-8",
}


class ChartRequest(BaseModel):
    """Birth chart calculation request."""

    year: int = Field(..., ge=1, le=3000, description="Birth year")
    month: int = Field(..., ge=1, le=12, description="Birth month")
    day: int = Field(..., ge=1, le=31, description="Birth day")
    hour: int = Field(..., ge=0, le=23, description="Birth hour (24-hour format)")
    minute: int = Field(..., ge=0, le=59, description="Birth minute")
    second: int = Field(0, ge=0, le=59, description="Birth second")
    latitude: float = Field(..., ge=-90, le=90, description="Birth latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Birth longitude")
    timezone: str = Field(
        ..., description="IANA timezone (e.g., 'America/New_York', 'Asia/Kolkata')"
    )
    place_name: str | None = Field(None, description="Place name for reference")

    ayanamsa: Ayanamsa = Field(
        Ayanamsa.JHORA_LAHIRI, description="Ayanamsa system (default: jhora_lahiri)"
    )
    house_system: HouseSystem = Field(
        HouseSystem.WHOLE_SIGN, description="House system (default: WholeSign)"
    )

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v: str) -> str:
        # Basic validation - could use zoneinfo for full validation
        return v


class ChartResponse(BaseModel):
    """Birth chart calculation response."""

    success: bool = True
    data: ChartData
    meta: dict = Field(default_factory=dict)


class TransitRequest(BaseModel):
    """Transit (Gochar) calculation request: natal birth data + optional transit time/place."""

    year: int = Field(..., ge=1, le=3000, description="Natal birth year")
    month: int = Field(..., ge=1, le=12, description="Natal birth month")
    day: int = Field(..., ge=1, le=31, description="Natal birth day")
    hour: int = Field(..., ge=0, le=23, description="Natal birth hour (24-hour format)")
    minute: int = Field(..., ge=0, le=59, description="Natal birth minute")
    second: int = Field(0, ge=0, le=59, description="Natal birth second")
    latitude: float = Field(..., ge=-90, le=90, description="Natal birth latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Natal birth longitude")
    timezone: str = Field(
        ..., description="IANA timezone (e.g., 'America/New_York', 'Asia/Kolkata')"
    )
    place_name: str | None = Field(None, description="Place name for reference")

    ayanamsa: Ayanamsa = Field(
        Ayanamsa.JHORA_LAHIRI, description="Ayanamsa system (default: jhora_lahiri)"
    )
    house_system: HouseSystem = Field(
        HouseSystem.WHOLE_SIGN, description="House system (default: WholeSign)"
    )

    transit_date: datetime | None = Field(
        None, description="Transit datetime (ISO 8601); defaults to now"
    )
    transit_latitude: float | None = Field(
        None, ge=-90, le=90, description="Transit latitude (default: natal)"
    )
    transit_longitude: float | None = Field(
        None, ge=-180, le=180, description="Transit longitude (default: natal)"
    )


class TransitResponse(BaseModel):
    """Transit (Gochar) calculation response."""

    success: bool = True
    data: TransitReport
    meta: dict = Field(default_factory=dict)


class TransitWindowRequest(BaseModel):
    """Monthly transit window scan request."""

    year: int = Field(..., ge=1, le=3000, description="Natal birth year")
    month: int = Field(..., ge=1, le=12, description="Natal birth month")
    day: int = Field(..., ge=1, le=31, description="Natal birth day")
    hour: int = Field(..., ge=0, le=23, description="Natal birth hour (24-hour format)")
    minute: int = Field(..., ge=0, le=59, description="Natal birth minute")
    second: int = Field(0, ge=0, le=59, description="Natal birth second")
    latitude: float = Field(..., ge=-90, le=90, description="Natal birth latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Natal birth longitude")
    timezone: str = Field(..., description="IANA timezone")
    place_name: str | None = Field(None, description="Place name")
    ayanamsa: Ayanamsa = Field(Ayanamsa.JHORA_LAHIRI)
    house_system: HouseSystem = Field(HouseSystem.WHOLE_SIGN)
    start_date: datetime | None = Field(
        None, description="Start datetime of window (defaults to now)"
    )
    days: int = Field(30, ge=1, le=180, description="Number of days to scan (default: 30)")


class TransitWindowResponse(BaseModel):
    """Monthly transit window scan response."""

    success: bool = True
    data: TransitWindowReport
    meta: dict = Field(default_factory=dict)


class PanchangaResponse(BaseModel):
    """Vedic Panchanga calculation response."""

    success: bool = True
    data: PanchangaData
    meta: dict = Field(default_factory=dict)


class YogaResponse(BaseModel):
    """Vedic Yoga detection response."""

    success: bool = True
    total: int
    data: list[YogaResult]
    meta: dict = Field(default_factory=dict)


class CompatibilityRequest(BaseModel):
    """Relationship compatibility request."""

    bride: ChartRequest
    groom: ChartRequest
    bride_name: str | None = Field(None, description="Bride name for report")
    groom_name: str | None = Field(None, description="Groom name for report")


class CompatibilityResponse(BaseModel):
    """Relationship compatibility response."""

    success: bool = True
    data: CompatibilityReport
    meta: dict = Field(default_factory=dict)


class MuhurthaRequest(BaseModel):
    """Vedic Muhurtha election request."""

    year: int = Field(..., ge=1, le=3000, description="Year")
    month: int = Field(..., ge=1, le=12, description="Month")
    day: int = Field(..., ge=1, le=31, description="Day")
    hour: int = Field(..., ge=0, le=23, description="Hour (0-23)")
    minute: int = Field(..., ge=0, le=59, description="Minute")
    second: int = Field(0, ge=0, le=59, description="Second")
    latitude: float = Field(..., ge=-90, le=90, description="Latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude")
    timezone: str = Field(..., description="IANA timezone (e.g. 'Asia/Kolkata')")
    ayanamsa: Ayanamsa = Field(Ayanamsa.JHORA_LAHIRI, description="Ayanamsa system")


class MuhurthaResponse(BaseModel):
    """Vedic Muhurtha election response."""

    success: bool = True
    data: MuhurthaReport
    meta: dict = Field(default_factory=dict)


class PredictRequest(ChartRequest):
    """Hierarchical Vedic prediction request."""

    domain: str | None = Field(
        None,
        description="Domain filter: career, relationship, wealth, spiritual_dharma, health. If omitted, returns all domains.",
    )
    include_transits: bool = Field(
        True,
        description="Whether to overlay astronomical Gochar transits onto prediction.",
    )


class PredictResponse(BaseModel):
    """Hierarchical Vedic prediction response."""

    success: bool = True
    data: dict[str, Any]
    meta: dict = Field(default_factory=dict)


class RemediesRequest(ChartRequest):
    """Dual-system remedies request."""

    include_transits: bool = Field(
        True,
        description="Whether to overlay Gochar transits onto remedy assessment.",
    )


class RemediesResponse(BaseModel):
    """Dual-system remedies calculation response."""

    success: bool = True
    data: dict[str, Any]
    meta: dict = Field(default_factory=dict)


class VarshaphalRequest(ChartRequest):
    """Tajik Varshaphal (annual / Barsha Fal) request."""

    target_year: int | None = Field(
        None,
        ge=1,
        le=3000,
        description="Calendar year for the annual forecast. Defaults to current year.",
    )


class VarshaphalResponse(BaseModel):
    """Tajik Varshaphal calculation response."""

    success: bool = True
    data: VarshaphalReport
    meta: dict = Field(default_factory=dict)


class KalsarpRequest(ChartRequest):
    """Kalsarp Dosha analysis request."""


class SpecialLagnasRequest(ChartRequest):
    """Special (vishesha) lagnas calculation request."""


class ChakraRequest(ChartRequest):
    """Vedic chakra systems calculation request."""


class KalsarpResponse(BaseModel):
    """Kalsarp Dosha calculation response."""

    success: bool = True
    data: KalsarpReport
    meta: dict = Field(default_factory=dict)


class SpecialLagnasResponse(BaseModel):
    """Special lagnas calculation response."""

    success: bool = True
    data: SpecialLagnasReport
    meta: dict = Field(default_factory=dict)


class ChakraResponse(BaseModel):
    """Vedic chakra systems calculation response."""

    success: bool = True
    data: ChakraReport
    meta: dict = Field(default_factory=dict)


class RashiFalRequest(ChartRequest):
    """Rashi Fal (Moon-sign horoscope) request."""

    period: str = Field(
        "daily",
        description="Forecast period: daily, monthly, or yearly.",
    )
    reference_date: str | None = Field(
        None,
        description="Reference date YYYY-MM-DD for the forecast. Defaults to today.",
    )


class RashiFalResponse(BaseModel):
    """Rashi Fal calculation response."""

    success: bool = True
    data: RashiFalReport
    meta: dict = Field(default_factory=dict)


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    version: str = "0.1.0"
    ephemeris: str = "Swiss Ephemeris (pyswisseph) via mayaastrolib"
    default_ayanamsa: str = "jhora_lahiri (Traditional Lahiri, Jagannatha Hora calibrated)"


class RAGIngestRequest(BaseModel):
    """Corpus ingestion request."""

    corpus_dir: str = Field("corpus", description="Corpus directory to ingest")
    index_dir: str = Field("index", description="Index output directory")


class RAGIngestResponse(BaseModel):
    """Corpus ingestion response."""

    success: bool = True
    data: IngestResult
    meta: dict = Field(default_factory=dict)


class RAGAskRequest(BaseModel):
    """Consultation question request."""

    question: str = Field(..., min_length=1, description="Consultation question")
    index_dir: str = Field("index", description="Index directory to query")
    top_k: int = Field(5, ge=1, le=20, description="References to retrieve")
    birth: ChartRequest | None = Field(None, description="Optional natal chart context")
    birth_context: dict[str, Any] | None = Field(
        None, description="Optional precalculated chart dictionary"
    )
    language: str = Field("en", description="Consultation response language ('en' or 'ne')")


class RAGAskResponse(BaseModel):
    """Consultation answer with retrieved references."""

    success: bool = True
    data: Answer
    references: list[SearchResult]
    meta: dict = Field(default_factory=dict)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan handler."""
    # Startup: configure GDPR privacy logging and pre-load ephemeris data
    setup_privacy_logging()
    yield
    # Shutdown: cleanup if needed


app = FastAPI(
    title="Nakshatra — The Science of Light",
    description=(
        "JSON API for Vedic birth charts with Vimshottari Dashas, Vargas, "
        "Ashtakavarga, Shadbala, and Gochar Transits. Compliant with AGPL-3.0 and ephemeral GDPR zero-logging policy."
    ),
    version="0.1.0",
    license_info={
        "name": "GNU Affero General Public License v3.0 (AGPL-3.0)",
        "url": "https://www.gnu.org/licenses/agpl-3.0.en.html",
    },
    terms_of_service="https://toya62-nakshatra.hf.space/privacy",
    lifespan=lifespan,
)

cors_origins_env = os.environ.get("CORS_ORIGINS", "")
if cors_origins_env.strip() == "*":
    cors_origins = ["*"]
    cors_allow_credentials = False
elif cors_origins_env.strip():
    cors_origins = [orig.strip() for orig in cors_origins_env.split(",") if orig.strip()]
    cors_allow_credentials = True
else:
    cors_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://nakshatra-light.duckdns.org",
        "https://toya62-nakshatra.hf.space",
    ]
    cors_allow_credentials = True

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"
    if cors_allow_credentials
    else None,
    allow_credentials=cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(PrivacyMiddleware)
setup_privacy_logging()

_rag_service = RAGService()


@app.get("/privacy", tags=["System"])
async def privacy_policy() -> dict[str, Any]:
    """Return explicit GDPR data handling and zero-log guarantee."""
    return get_privacy_statement()


@app.get("/legal/licensing", tags=["System"])
async def licensing_policy() -> dict[str, Any]:
    """Return Swiss Ephemeris and classical corpus licensing disclosures."""
    return get_licensing_statement()


def _format_chart(chart: ChartData, fmt: str) -> Response:
    """Render a ChartData in the requested output format as a Response."""
    if fmt == "table":
        content = chart.to_table()
    elif fmt == "markdown":
        content = chart.to_markdown()
    elif fmt == "csv":
        content = chart.to_csv()
    elif fmt == "diagram":
        content = chart.to_diagram()
    else:
        content = chart.model_dump_json()
    media_type = FORMAT_CONTENT_TYPES.get(fmt, "text/plain; charset=utf-8")
    return Response(content=content, media_type=media_type)


def _attach_chart_derived_context(chart: ChartData, birth_context: dict) -> None:
    """Attach transits, predictions, remedies, and Kuja Dosha to a chart dict.

    Preserves the 30-day transit window already present in
    ``chart.model_dump()``: a fresh ``calculate_transits()`` report has no
    ``window`` key, so the fresh report is merged over the existing one
    instead of overwriting it — otherwise the transit-window events the
    prompt summary tries to read are silently dropped.
    """
    transits = None
    try:
        from nakshatra.transits import calculate_transits

        transits = calculate_transits(chart)
        t_dict = transits.model_dump()
        existing = birth_context.get("transits")
        if isinstance(existing, dict):
            window = existing.get("window")
            if isinstance(window, dict) and "window" not in t_dict:
                t_dict["window"] = window
        birth_context["transits"] = t_dict
    except Exception:
        pass
    try:
        preds = chart.get_predictions(transits=transits)
        birth_context["predictions"] = {k: v.model_dump() for k, v in preds.items()}
    except Exception:
        pass
    try:
        rem = chart.get_remedies(transits=transits)
        birth_context["remedies"] = rem.model_dump()
    except Exception:
        pass
    try:
        birth_context["kuja_dosha"] = evaluate_chart_kuja_dosha(chart).model_dump()
    except Exception:
        pass


def _build_chart(request: ChartRequest | TransitRequest | TransitWindowRequest) -> ChartData:
    """Calculate a natal chart from a ChartRequest or TransitRequest."""
    birth = BirthData(
        year=request.year,
        month=request.month,
        day=request.day,
        hour=request.hour,
        minute=request.minute,
        second=request.second,
        latitude=request.latitude,
        longitude=request.longitude,
        timezone=request.timezone,
        place_name=request.place_name,
    )
    return calculate_chart(
        birth=birth,
        ayanamsa=request.ayanamsa,
        house_system=request.house_system,
    )


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse()


@app.get("/config/defaults", tags=["System"])
async def get_config_defaults() -> dict[str, Any]:
    """Return default configuration parameters."""
    return {
        "default_lat": settings.default_lat,
        "default_lon": settings.default_lon,
        "default_timezone": settings.default_timezone,
        "default_place_name": settings.default_place_name,
        "default_ayanamsa": settings.default_ayanamsa,
        "default_house_system": settings.default_house_system,
    }


@app.get("/geocode/search", response_model=list[PlaceResult], tags=["Geocoding"])
def geocode_search(
    q: str = Query(..., min_length=1, description="Place or city name to search"),
    limit: int = Query(8, ge=1, le=50, description="Max results"),
) -> list[PlaceResult]:
    """Search places and resolve coordinates + IANA timezone."""
    return search_places(q, limit=limit)


@app.get("/geocode/timezone", response_model=TimezoneOffsetInfo, tags=["Geocoding"])
async def geocode_timezone(
    tz: str = Query(..., description="IANA timezone identifier, e.g. 'Asia/Kathmandu'"),
    year: int = Query(..., ge=1, le=3000),
    month: int = Query(..., ge=1, le=12),
    day: int = Query(..., ge=1, le=31),
    hour: int = Query(12, ge=0, le=23),
    minute: int = Query(0, ge=0, le=59),
) -> TimezoneOffsetInfo:
    """Resolve historical UTC offset and Daylight Saving Time (DST) status for an epoch."""
    try:
        return resolve_timezone_offset(tz, year, month, day, hour, minute)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid timezone or date: {str(e)}")


@app.get("/calendar/bs", response_model=BikramSambatDate, tags=["Calendar"])
async def convert_ad_to_bs(
    year: int = Query(..., ge=1, le=3000),
    month: int = Query(..., ge=1, le=12),
    day: int = Query(..., ge=1, le=31),
) -> BikramSambatDate:
    """Convert Gregorian (AD) calendar date to Nepali Bikram Sambat (BS)."""
    try:
        return ad_to_bs(year, month, day)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/calendar/bs/month", response_model=list[BikramSambatDate], tags=["Calendar"])
async def convert_ad_month_to_bs(
    year: int = Query(..., ge=1, le=3000),
    month: int = Query(..., ge=1, le=12),
) -> list[BikramSambatDate]:
    """Convert every day of a Gregorian month to Bikram Sambat, in order.

    One call for the Calendar month grid, instead of one request per day.
    Each entry is the BS date of the corresponding AD day (index + 1).
    """
    _, days_in_month = monthrange(year, month)
    return [ad_to_bs(year, month, day) for day in range(1, days_in_month + 1)]


@app.get("/calendar/ad", response_model=GregorianDate, tags=["Calendar"])
async def convert_bs_to_ad(
    year: int = Query(..., ge=1900, le=2200),
    month: int = Query(..., ge=1, le=12),
    day: int = Query(..., ge=1, le=32),
) -> GregorianDate:
    """Convert Nepali Bikram Sambat (BS) date to Gregorian (AD) calendar date."""
    try:
        return bs_to_ad(year, month, day)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/calendar/nomenclature", tags=["Calendar"])
async def calendar_nomenclature() -> dict[str, Any]:
    """Return canonical Sanskrit Devanagari nomenclature for Grahas, Rasis, and Nakshatras."""
    return {
        "planets": DEVANAGARI_PLANETS,
        "signs": DEVANAGARI_SIGNS,
        "nakshatras": DEVANAGARI_NAKSHATRAS,
    }


@app.post("/chart", response_model=ChartResponse, tags=["Chart"])
async def create_chart(
    request: ChartRequest, format: str = Query("json")
) -> ChartResponse | Response:
    """
    Calculate Vedic birth chart from birth data.

    Returns complete chart with:
    - Planetary positions (7 grahas + Ascendant + Midheaven + Rahu/Ketu nodes)
    - Sign, degree, nakshatra, pada, house, dignity, retrograde status
    - House cusps (12 houses)
    - Major aspects (conjunction, sextile, square, trine, opposition)
    - Vimshottari Dashas, Shodashavarga, Ashtakavarga, Shadbala, Upagrahas
    - Calculation metadata

    Default ayanamsa: jhora_lahiri (Traditional Lahiri, Jagannatha Hora calibrated)
    Default house system: Whole Sign (traditional Vedic)

    Add `?format=table|markdown|csv|diagram` for human-readable text output
    (default `json` returns the structured ChartResponse).
    """
    if format not in SUPPORTED_FORMATS:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported format '{format}'. Use one of: {', '.join(SUPPORTED_FORMATS)}",
        )
    try:
        chart = _build_chart(request)
        if format == "json":
            return ChartResponse(
                data=chart,
                meta={
                    "ayanamsa_used": request.ayanamsa.value,
                    "house_system_used": request.house_system.value,
                    "zodiac": "sidereal",
                },
            )
        return _format_chart(chart, format)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


@app.get("/chart", response_model=ChartResponse, tags=["Chart"])
async def create_chart_get(
    year: int = Query(..., ge=1, le=3000),
    month: int = Query(..., ge=1, le=12),
    day: int = Query(..., ge=1, le=31),
    hour: int = Query(..., ge=0, le=23),
    minute: int = Query(..., ge=0, le=59),
    second: int = Query(0, ge=0, le=59),
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    timezone: str = Query(...),
    place_name: str | None = Query(None),
    ayanamsa: Ayanamsa = Query(Ayanamsa.JHORA_LAHIRI),
    house_system: HouseSystem = Query(HouseSystem.WHOLE_SIGN),
    format: str = Query("json"),
) -> ChartResponse | Response:
    """GET endpoint for chart calculation (convenience for testing). Supports `format` param."""
    if format not in SUPPORTED_FORMATS:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported format '{format}'. Use one of: {', '.join(SUPPORTED_FORMATS)}",
        )
    request = ChartRequest(
        year=year,
        month=month,
        day=day,
        hour=hour,
        minute=minute,
        second=second,
        latitude=latitude,
        longitude=longitude,
        timezone=timezone,
        place_name=place_name,
        ayanamsa=ayanamsa,
        house_system=house_system,
    )
    return await create_chart(request, format=format)


@app.get("/chart/diagram", tags=["Chart"])
async def chart_diagram(
    year: int = Query(..., ge=1, le=3000),
    month: int = Query(..., ge=1, le=12),
    day: int = Query(..., ge=1, le=31),
    hour: int = Query(..., ge=0, le=23),
    minute: int = Query(..., ge=0, le=59),
    second: int = Query(0, ge=0, le=59),
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    timezone: str = Query(...),
    place_name: str | None = Query(None),
    ayanamsa: Ayanamsa = Query(Ayanamsa.JHORA_LAHIRI),
    house_system: HouseSystem = Query(HouseSystem.WHOLE_SIGN),
    varga: str = Query("D1", description="Divisional chart to render (D1, D9, D10, ...)"),
) -> PlainTextResponse:
    """Render a South Indian ASCII chart diagram for the given varga (e.g., D1, D9, D10)."""
    try:
        request = ChartRequest(
            year=year,
            month=month,
            day=day,
            hour=hour,
            minute=minute,
            second=second,
            latitude=latitude,
            longitude=longitude,
            timezone=timezone,
            place_name=place_name,
            ayanamsa=ayanamsa,
            house_system=house_system,
        )
        chart = _build_chart(request)
        return PlainTextResponse(chart.to_diagram(varga=varga))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


@app.post("/transits", response_model=TransitResponse, tags=["Transits"])
async def create_transits(request: TransitRequest) -> TransitResponse:
    """
    Calculate Vedic transits (Gochar) for a natal chart.

    Provide the natal birth data plus an optional transit datetime and
    transit location (defaults: now, natal location). Returns a TransitReport with:
    - Transiting graha positions with houses from natal Lagna and natal Moon
    - Sade Sati phase (rising/peak/setting), Ashtama Shani, Kantaka Shani
    - Jupiter Gochar with Phaladeepika favorable-house evaluation
    - Double Transit houses (aspected by both Jupiter and Saturn)
    - SAV/BAV bindus for each transit sign

    The transit chart uses the same ayanamsa as the natal chart.
    """
    try:
        natal_chart = _build_chart(request)
        report = calculate_transits(
            natal_chart,
            transit_date=request.transit_date,
            transit_latitude=request.transit_latitude,
            transit_longitude=request.transit_longitude,
        )
        return TransitResponse(
            data=report,
            meta={
                "ayanamsa_used": request.ayanamsa.value,
                "house_system_used": request.house_system.value,
                "zodiac": "sidereal",
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


@app.post("/transits/window", response_model=TransitWindowResponse, tags=["Transits"])
async def scan_transit_window_endpoint(request: TransitWindowRequest) -> TransitWindowResponse:
    """
    Scan upcoming monthly transit window (default 30 days) for a natal chart:
    - Planetary Ingresses (sign changes, e.g. Sun into Libra)
    - Planetary Stations (planets turning Retrograde or Direct)
    - Chandrashtama periods (Moon transiting 8th from natal Moon)
    """
    try:
        natal_chart = _build_chart(request)
        report = scan_transit_window(
            natal_chart=natal_chart,
            start_date=request.start_date,
            days=request.days,
        )
        return TransitWindowResponse(
            data=report,
            meta={
                "ayanamsa_used": request.ayanamsa.value,
                "days_scanned": request.days,
                "zodiac": "sidereal",
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scan error: {str(e)}")


@app.get("/panchanga", response_model=PanchangaResponse, tags=["Panchanga"])
async def get_panchanga_endpoint(
    year: int = Query(..., ge=1, le=3000, description="Year"),
    month: int = Query(..., ge=1, le=12, description="Month"),
    day: int = Query(..., ge=1, le=31, description="Day"),
    hour: int = Query(..., ge=0, le=23, description="Hour (24-hour)"),
    minute: int = Query(..., ge=0, le=59, description="Minute"),
    second: int = Query(0, ge=0, le=59, description="Second"),
    latitude: float = Query(..., ge=-90, le=90, description="Latitude"),
    longitude: float = Query(..., ge=-180, le=180, description="Longitude"),
    timezone: str = Query(..., description="IANA timezone (e.g. 'Asia/Kathmandu')"),
    ayanamsa: Ayanamsa = Query(Ayanamsa.JHORA_LAHIRI, description="Ayanamsa system"),
    format: str = Query("json", description="Output format: json, table"),
) -> PanchangaResponse | Response:
    """Calculate 5-limb Vedic Panchanga (Tithi, Vara, Nakshatra, Yoga, Karana)."""
    try:
        dt = datetime(year, month, day, hour, minute, second)
        p = calculate_panchanga(dt, latitude, longitude, timezone, ayanamsa=ayanamsa)
        if format == "table":
            return Response(content=p.to_table(), media_type="text/plain; charset=utf-8")
        return PanchangaResponse(
            data=p,
            meta={
                "ayanamsa": ayanamsa.value,
                "timezone": timezone,
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


@app.post("/panchanga", response_model=PanchangaResponse, tags=["Panchanga"])
async def create_panchanga_endpoint(
    request: ChartRequest,
    format: str = Query("json", description="Output format: json, table"),
) -> PanchangaResponse | Response:
    """Calculate 5-limb Vedic Panchanga from birth request data."""
    try:
        dt = datetime(
            request.year, request.month, request.day, request.hour, request.minute, request.second
        )
        p = calculate_panchanga(
            dt, request.latitude, request.longitude, request.timezone, ayanamsa=request.ayanamsa
        )
        if format == "table":
            return Response(content=p.to_table(), media_type="text/plain; charset=utf-8")
        return PanchangaResponse(
            data=p,
            meta={
                "ayanamsa": request.ayanamsa.value,
                "timezone": request.timezone,
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


@app.get("/yogas", response_model=YogaResponse, tags=["Yogas"])
async def get_yogas_endpoint(
    year: int = Query(..., ge=1, le=3000),
    month: int = Query(..., ge=1, le=12),
    day: int = Query(..., ge=1, le=31),
    hour: int = Query(..., ge=0, le=23),
    minute: int = Query(..., ge=0, le=59),
    second: int = Query(0, ge=0, le=59),
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    timezone: str = Query(...),
    ayanamsa: Ayanamsa = Query(Ayanamsa.JHORA_LAHIRI),
    house_system: HouseSystem = Query(HouseSystem.WHOLE_SIGN),
    format: str = Query("json", description="Output format: json, table, markdown"),
) -> YogaResponse | Response:
    """Detect classical Vedic Yogas in a birth chart."""
    try:
        birth = BirthData(
            year=year,
            month=month,
            day=day,
            hour=hour,
            minute=minute,
            second=second,
            latitude=latitude,
            longitude=longitude,
            timezone=timezone,
        )
        chart = calculate_chart(birth=birth, ayanamsa=ayanamsa, house_system=house_system)
        yogas_list = detect_yogas(chart)
        if format == "table":
            return Response(
                content=format_yogas_table(yogas_list), media_type="text/plain; charset=utf-8"
            )
        if format == "markdown":
            return Response(
                content=format_yogas_markdown(yogas_list), media_type="text/markdown; charset=utf-8"
            )
        return YogaResponse(
            total=len(yogas_list),
            data=yogas_list,
            meta={
                "ayanamsa": ayanamsa.value,
                "house_system": house_system.value,
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


@app.post("/yogas", response_model=YogaResponse, tags=["Yogas"])
async def create_yogas_endpoint(
    request: ChartRequest,
    format: str = Query("json", description="Output format: json, table, markdown"),
) -> YogaResponse | Response:
    """Detect classical Vedic Yogas from ChartRequest JSON."""
    try:
        chart = _build_chart(request)
        yogas_list = detect_yogas(chart)
        if format == "table":
            return Response(
                content=format_yogas_table(yogas_list), media_type="text/plain; charset=utf-8"
            )
        if format == "markdown":
            return Response(
                content=format_yogas_markdown(yogas_list), media_type="text/markdown; charset=utf-8"
            )
        return YogaResponse(
            total=len(yogas_list),
            data=yogas_list,
            meta={
                "ayanamsa": request.ayanamsa.value,
                "house_system": request.house_system.value,
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


@app.post("/predict", response_model=PredictResponse, tags=["Prediction"])
async def predict_endpoint(request: PredictRequest) -> PredictResponse:
    """
    Deterministic 5-step classical Vedic predictive synthesis across core life domains.
    Evaluates Natal Promise (D1), Varga Confirmations (D9/D10), Vimshottari Dasha triggers,
    astronomical Gochar transits (Double Transits, Sade Sati), and active Yogas.
    """
    try:
        chart = _build_chart(request)
        transits = None
        if request.include_transits:
            try:
                from nakshatra.transits import calculate_transits

                transits = calculate_transits(chart)
            except Exception:
                pass

        if request.domain:
            pred = chart.get_predictions(domain=request.domain, transits=transits)
            data = {request.domain: pred.model_dump()}
        else:
            preds = chart.get_predictions(transits=transits)
            data = {k: v.model_dump() for k, v in preds.items()}

        return PredictResponse(
            data=data,
            meta={
                "ayanamsa": chart.ayanamsa.value,
                "domain": request.domain or "all",
                "transits_included": transits is not None,
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction calculation error: {str(e)}")


@app.post("/remedies", response_model=RemediesResponse, tags=["Remedies"])
async def remedies_endpoint(request: RemediesRequest) -> RemediesResponse:
    """
    Calculate dual-system classical remedies (Parashari + Lal Kitab Upayas)
    for afflicted, debilitated, combust, or dusthana-placed grahas in natal chart.
    """
    try:
        chart = _build_chart(request)
        transits = None
        if request.include_transits:
            try:
                from nakshatra.transits import calculate_transits

                transits = calculate_transits(chart)
            except Exception:
                pass

        report = chart.get_remedies(transits=transits)
        return RemediesResponse(
            data=report.model_dump(),
            meta={
                "ayanamsa": chart.ayanamsa.value,
                "transits_included": transits is not None,
                "total_afflictions": report.total_afflictions,
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Remedies calculation error: {str(e)}")


@app.post("/varshaphal", response_model=VarshaphalResponse, tags=["Varshaphal"])
async def varshaphal_endpoint(request: VarshaphalRequest) -> VarshaphalResponse:
    """
    Tajik Varshaphal (Annual / Barsha Fal) report.

    Casts the solar-return chart for ``target_year`` (Sun returns to its natal
    sidereal longitude) and synthesizes the Muntha, Varsheshwara (Year Lord),
    Sahams (sensitive points), and month-wise lords — the core Tajika annual
    horoscopy used for yearly prediction.
    """
    try:
        birth = BirthData(
            year=request.year,
            month=request.month,
            day=request.day,
            hour=request.hour,
            minute=request.minute,
            second=request.second,
            latitude=request.latitude,
            longitude=request.longitude,
            timezone=request.timezone,
            place_name=request.place_name,
        )
        report = calculate_varshaphal(
            birth,
            target_year=request.target_year,
            ayanamsa=request.ayanamsa,
            house_system=request.house_system,
        )
        return VarshaphalResponse(
            data=report,
            meta={
                "ayanamsa": request.ayanamsa.value,
                "house_system": request.house_system.value,
                "target_year": report.target_year,
                "completed_years": report.completed_years,
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Varshaphal calculation error: {str(e)}")


@app.post("/kalsarp", response_model=KalsarpResponse, tags=["Kalsarp"])
async def kalsarp_endpoint(request: KalsarpRequest) -> KalsarpResponse:
    """
    Kalsarp (Kalasarpa) Dosha analysis.

    Detects whether all seven classical Grahas are hemmed between Rahu and Ketu,
    classifies the dosha as Purna (Complete) or Ardh (Partial), and names one of
    twelve classical Kalsarp types by the Rahu–Ketu house axis.
    """
    try:
        chart = _build_chart(request)
        report = chart.get_kalsarp()
        return KalsarpResponse(
            data=report,
            meta={
                "ayanamsa": chart.ayanamsa.value,
                "house_system": chart.house_system.value,
                "has_kalsarp": report.has_kalsarp,
                "classification": report.classification,
                "kalsarp_type": report.kalsarp_type or "",
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Kalsarp calculation error: {str(e)}")


@app.post("/special-lagnas", response_model=SpecialLagnasResponse, tags=["Special Lagnas"])
async def special_lagnas_endpoint(request: SpecialLagnasRequest) -> SpecialLagnasResponse:
    """
    Special (Vishesha) Lagnas.

    Computes Arudha, Upapada, Indu, Bhrigu, Ghati, Sri and Karakamsha lagnas
    — classical Jaimini/Tajika ascendants used for perception, marriage,
    prosperity, karmic triggers, authority, fortune and soul-direction.
    """
    try:
        chart = _build_chart(request)
        report = chart.get_special_lagnas()
        return SpecialLagnasResponse(
            data=report,
            meta={
                "ayanamsa": chart.ayanamsa.value,
                "house_system": chart.house_system.value,
                "lagnas": [lagna.name for lagna in report.lagnas],
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Special lagnas calculation error: {str(e)}")


@app.post("/chakra", response_model=ChakraResponse, tags=["Chakra"])
async def chakra_endpoint(request: ChakraRequest) -> ChakraResponse:
    """
    Vedic chakra systems.

    Computes the Navatara Chakra (9 tara of each planet from the Janma
    nakshatra), Compound (Panchadha Maitri) relationships for every planet
    pair, and the Ghatchakra wheel — classical support analyses used alongside
    the birth chart.
    """
    try:
        chart = _build_chart(request)
        report = chart.get_chakra()
        return ChakraResponse(
            data=report,
            meta={
                "ayanamsa": chart.ayanamsa.value,
                "house_system": chart.house_system.value,
                "janma_nakshatra": report.janma_nakshatra,
                "navatara_count": len(report.navatara),
                "compound_pairs": len(report.compound_relationships),
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chakra calculation error: {str(e)}")


@app.post("/rashi-fal", response_model=RashiFalResponse, tags=["Rashi Fal"])
async def rashi_fal_endpoint(request: RashiFalRequest) -> RashiFalResponse:
    """
    Rashi Fal (Moon-sign / Chandra Lagna horoscope).

    Daily, monthly or yearly forecast read from transits relative to the
    natal Moon sign treated as House 1, with graha-wise house results,
    Double Transit detection and Sade Sati status.
    """
    try:
        from datetime import datetime

        ref_date = None
        if request.reference_date:
            ref_date = datetime.strptime(request.reference_date, "%Y-%m-%d")
        report = chart_get_rashi_fal_helper(
            request,
            period=request.period,
            reference_date=ref_date,
        )
        return RashiFalResponse(
            data=report,
            meta={
                "period": report.period,
                "reference_date": report.reference_date,
                "moon_sign": report.moon_sign,
                "overall_score": report.overall_score,
                "sade_sati_active": report.sade_sati_active,
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rashi Fal calculation error: {str(e)}")


def chart_get_rashi_fal_helper(
    request: RashiFalRequest,
    period: str,
    reference_date: datetime | None,
) -> RashiFalReport:
    """Build chart and compute Rashi Fal."""
    from nakshatra.core import BirthData

    birth = BirthData(
        year=request.year,
        month=request.month,
        day=request.day,
        hour=request.hour,
        minute=request.minute,
        second=request.second,
        latitude=request.latitude,
        longitude=request.longitude,
        timezone=request.timezone,
        place_name=request.place_name,
    )

    return calculate_rashi_fal(
        birth,
        period=period,
        reference_date=reference_date,
        ayanamsa=request.ayanamsa,
        house_system=request.house_system,
    )


@app.post("/match/compatibility", response_model=CompatibilityResponse, tags=["Compatibility"])
async def calculate_compatibility_endpoint(
    request: CompatibilityRequest,
    format: str = Query("json", description="Output format: json, table"),
) -> CompatibilityResponse | Response:
    """Calculate 36-Point Ashtakoota and Kuja Dosha compatibility between Bride and Groom."""
    try:
        b_chart = _build_chart(request.bride)
        g_chart = _build_chart(request.groom)
        report = calculate_compatibility(
            b_chart,
            g_chart,
            bride_name=request.bride_name,
            groom_name=request.groom_name,
        )
        if format == "table":
            return Response(content=report.to_table(), media_type="text/plain; charset=utf-8")
        return CompatibilityResponse(
            data=report,
            meta={
                "ayanamsa": request.bride.ayanamsa.value,
                "total_score": report.ashtakoota.total_score,
                "verdict": report.ashtakoota.verdict,
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Compatibility calculation error: {str(e)}")


@app.post("/muhurtha", response_model=MuhurthaResponse, tags=["Muhurtha"])
async def calculate_muhurtha_endpoint(
    request: MuhurthaRequest,
    format: str = Query("json", description="Output format: json, table"),
) -> MuhurthaResponse | Response:
    """Calculate Vedic Muhurtha, Horas, Choghadiyas, and Siddhi Yogas for a given time and place."""
    try:
        dt = datetime(
            request.year,
            request.month,
            request.day,
            request.hour,
            request.minute,
            request.second,
        )
        report = calculate_muhurtha(
            dt,
            request.latitude,
            request.longitude,
            request.timezone,
            ayanamsa=request.ayanamsa,
        )
        if format == "table":
            return Response(content=report.to_table(), media_type="text/plain; charset=utf-8")
        return MuhurthaResponse(
            data=report,
            meta={
                "score": report.muhurtha_score,
                "verdict": report.verdict,
                "ayanamsa": request.ayanamsa.value,
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Muhurtha calculation error: {str(e)}")


@app.get("/muhurtha", response_model=MuhurthaResponse, tags=["Muhurtha"])
async def get_muhurtha_endpoint(
    year: int = Query(..., ge=1, le=3000),
    month: int = Query(..., ge=1, le=12),
    day: int = Query(..., ge=1, le=31),
    hour: int = Query(..., ge=0, le=23),
    minute: int = Query(..., ge=0, le=59),
    second: int = Query(0, ge=0, le=59),
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    timezone: str = Query(...),
    ayanamsa: Ayanamsa = Query(Ayanamsa.JHORA_LAHIRI),
    format: str = Query("json", description="Output format: json, table"),
) -> MuhurthaResponse | Response:
    """Calculate Vedic Muhurtha via GET query parameters."""
    req = MuhurthaRequest(
        year=year,
        month=month,
        day=day,
        hour=hour,
        minute=minute,
        second=second,
        latitude=latitude,
        longitude=longitude,
        timezone=timezone,
        ayanamsa=ayanamsa,
    )
    return await calculate_muhurtha_endpoint(req, format=format)


def _validate_safe_path(p: str | Path, name: str = "Path") -> Path:
    raw = str(p).strip()
    if not raw:
        raise HTTPException(status_code=400, detail=f"{name} cannot be empty")
    parts = Path(raw).parts
    if ".." in parts:
        raise HTTPException(status_code=400, detail=f"Path traversal detected in {name}")
    resolved = Path(raw).resolve()
    forbidden_roots = (
        Path("/etc"),
        Path("/proc"),
        Path("/sys"),
        Path("/dev"),
        Path("/root"),
        Path("/boot"),
        Path("/bin"),
        Path("/sbin"),
        Path("/usr"),
    )
    for forbidden in forbidden_roots:
        if resolved == forbidden or forbidden in resolved.parents:
            raise HTTPException(status_code=400, detail=f"Access to system path forbidden: {name}")
    forbidden_names = {".ssh", ".env", ".aws", ".gnupg", "id_rsa", "id_ed25519"}
    if any(part in forbidden_names for part in resolved.parts):
        raise HTTPException(status_code=400, detail=f"Access to sensitive path forbidden: {name}")
    return resolved


@app.post("/rag/ingest", response_model=RAGIngestResponse, tags=["RAG"])
async def rag_ingest(
    request: RAGIngestRequest,
    x_admin_key: str | None = Header(None, alias="X-Admin-Key"),
) -> RAGIngestResponse:
    """
    Ingest a corpus directory into a searchable index.

    Reads works from corpus_dir (each work directory: meta.json with
    work/translator/license plus .txt/.md files), chunks the text, and
    writes the index to index_dir. Embedding vectors are built when
    sentence-transformers is installed; otherwise the index is BM25-only.
    """
    admin_key = os.environ.get("ADMIN_API_KEY") or os.environ.get("NAKSHATRA_ADMIN_KEY")
    is_prod = os.environ.get("ENVIRONMENT", "").lower() in ("production", "prod")

    if admin_key:
        if x_admin_key != admin_key:
            raise HTTPException(
                status_code=401, detail="Unauthorized: Invalid or missing X-Admin-Key"
            )
    elif is_prod:
        raise HTTPException(
            status_code=403,
            detail="Ingestion endpoint disabled in production without ADMIN_API_KEY configured",
        )

    _validate_safe_path(request.corpus_dir, "corpus_dir")
    _validate_safe_path(request.index_dir, "index_dir")

    try:
        result = _rag_service.ingest(request.corpus_dir, request.index_dir)
        return RAGIngestResponse(
            data=result,
            meta={
                "corpus_dir": request.corpus_dir,
                "index_dir": request.index_dir,
                "embeddings": _rag_service.embedder is not None,
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion error: {str(e)}")


@app.post("/rag/ask", response_model=RAGAskResponse, tags=["RAG"])
async def rag_ask(request: RAGAskRequest) -> RAGAskResponse:
    """
    Answer a consultation question from the indexed corpus.

    Retrieves the most relevant corpus chunks (hybrid BM25 + dense
    ranking, RRF-fused, with Bhava/Karaka concept expansion) and
    synthesizes a cited answer. Provide `birth` to include natal
    chart context in the consultation.
    """
    try:
        birth_context = None
        if request.birth_context is not None:
            birth_context = request.birth_context
        elif request.birth is not None:
            chart = _build_chart(request.birth)
            birth_context = chart.model_dump()
            _attach_chart_derived_context(chart, birth_context)
        answer, references = _rag_service.ask(
            request.question,
            index_dir=request.index_dir,
            top_k=request.top_k,
            birth_context=birth_context,
            language=request.language,
        )
        return RAGAskResponse(
            data=answer,
            references=references,
            meta={
                "index_dir": request.index_dir,
                "top_k": request.top_k,
                "model": answer.model,
            },
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG error: {str(e)}")


@app.post("/rag/ask/stream", tags=["RAG"])
async def rag_ask_stream(request: RAGAskRequest) -> StreamingResponse:
    """
    Stream consultation answer token-by-token via Server-Sent Events (SSE).
    """
    birth_context = None
    if request.birth_context is not None:
        birth_context = request.birth_context
    elif request.birth is not None:
        chart = _build_chart(request.birth)
        birth_context = chart.model_dump()
        _attach_chart_derived_context(chart, birth_context)

    async def event_generator() -> AsyncIterator[str]:
        try:
            stream, references, synthesizer = _rag_service.ask_stream(
                request.question,
                index_dir=request.index_dir,
                top_k=request.top_k,
                birth_context=birth_context,
                language=request.language,
            )
            ref_data = [
                {
                    "work": r.chunk.work,
                    "chapter": r.chunk.chapter,
                    "verse": r.chunk.verse,
                    "text": r.chunk.text,
                    "score": r.score,
                }
                for r in references
            ]
            model_name = getattr(synthesizer, "model", "synthesizer")
            init_payload = json.dumps({"type": "init", "model": model_name, "references": ref_data})
            yield f"data: {init_payload}\n\n"

            accumulated_tokens: list[str] = []
            for token in stream:
                accumulated_tokens.append(token)
                token_payload = json.dumps({"type": "token", "token": token})
                yield f"data: {token_payload}\n\n"

            full_text = "".join(accumulated_tokens)
            from nakshatra.ai.synthesize import extract_citations

            citations = extract_citations(full_text, references)
            citation_data = [
                {
                    "work": c.work,
                    "chapter": c.chapter,
                    "verse": c.verse,
                    "text": c.text,
                }
                for c in citations
            ]
            final_model = getattr(synthesizer, "model", model_name)
            done_payload = json.dumps(
                {
                    "type": "done",
                    "citations": citation_data,
                    "model": final_model,
                }
            )
            yield f"data: {done_payload}\n\n"
        except Exception as e:
            err_payload = json.dumps({"type": "error", "error": str(e)})
            yield f"data: {err_payload}\n\n"
            done_payload = json.dumps({"type": "done", "citations": [], "model": "fallback"})
            yield f"data: {done_payload}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/", tags=["System"])
async def root() -> dict:
    """Root endpoint with API info."""
    return {
        "name": "Nakshatra",
        "description": "The Science of Light - JSON API for birth charts, panchangas, and yogas",
        "version": "0.1.0",
        "license": "GNU Affero General Public License v3.0 (AGPL-3.0)",
        "ephemeris": "Swiss Ephemeris via mayaastrolib (pyswisseph)",
        "default_ayanamsa": "jhora_lahiri (Traditional Lahiri, Jagannatha Hora calibrated)",
        "default_house_system": "Whole Sign",
        "endpoints": {
            "POST /chart": (
                "Calculate birth chart (JSON body); ?format=table|markdown|csv|diagram for text"
            ),
            "GET /chart": "Calculate birth chart (query params); supports format param",
            "GET /chart/diagram": "South Indian ASCII chart diagram for a varga (D1, D9, D10, ...)",
            "GET /panchanga": "Calculate 5-limb Panchanga (query params); ?format=json|table",
            "POST /panchanga": "Calculate 5-limb Panchanga (JSON body); ?format=json|table",
            "GET /yogas": "Detect Vedic Yogas (query params); ?format=json|table|markdown",
            "POST /yogas": "Detect Vedic Yogas (JSON body); ?format=json|table|markdown",
            "POST /transits": "Calculate Gochar transits against a natal chart with Ashtakavarga Kakshas (JSON body)",
            "POST /match/compatibility": "Calculate 36-point Ashtakoota and Kuja Dosha relationship matching (JSON body)",
            "POST /muhurtha": "Calculate Vedic Muhurtha, Horas, Choghadiyas, and Siddhi Yogas (JSON body)",
            "GET /muhurtha": "Calculate Vedic Muhurtha (query params)",
            "POST /rag/ingest": "Ingest a corpus directory into a searchable index",
            "POST /rag/ask": "Answer a consultation question with cited corpus references",
            "GET /health": "Health check",
            "GET /docs": "Interactive API docs (Swagger UI)",
        },
    }


def main() -> None:
    """Run Nakshatra API server."""
    import uvicorn

    port = int(os.environ.get("PORT", 8004))
    host = os.environ.get("HOST", "0.0.0.0")
    uvicorn.run("nakshatra.api:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
