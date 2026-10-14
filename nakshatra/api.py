"""
Nakshatra - Vedic Astrology AI Engine
FastAPI application exposing chart calculation, Vimshottari Dashas, Shodashavarga,
Ashtakavarga, Shadbala, Gochar transits, and RAG corpus consultation as JSON
or formatted text.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, Response, StreamingResponse
from pydantic import BaseModel, Field, field_validator

from nakshatra.ai.corpus import IngestResult
from nakshatra.ai.embeddings import SearchResult
from nakshatra.ai.service import RAGService
from nakshatra.ai.synthesize import Answer
from nakshatra.compatibility import (
    CompatibilityReport,
    calculate_compatibility,
)
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
from nakshatra.muhurtha import (
    MuhurthaReport,
    calculate_muhurtha,
)
from nakshatra.panchanga import PanchangaData, calculate_panchanga
from nakshatra.transits import TransitReport, calculate_transits
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


class RAGAskResponse(BaseModel):
    """Consultation answer with retrieved references."""

    success: bool = True
    data: Answer
    references: list[SearchResult]
    meta: dict = Field(default_factory=dict)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan handler."""
    # Startup: pre-load ephemeris data
    yield
    # Shutdown: cleanup if needed


app = FastAPI(
    title="Nakshatra - Vedic Astrology AI Engine",
    description=(
        "JSON API for Vedic birth charts with Vimshottari Dashas, Vargas, "
        "Ashtakavarga, Shadbala, and Gochar Transits"
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_rag_service = RAGService()


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


def _build_chart(request: ChartRequest | TransitRequest) -> ChartData:
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


@app.get("/geocode/search", response_model=list[PlaceResult], tags=["Geocoding"])
async def geocode_search(
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


@app.post("/rag/ingest", response_model=RAGIngestResponse, tags=["RAG"])
async def rag_ingest(request: RAGIngestRequest) -> RAGIngestResponse:
    """
    Ingest a corpus directory into a searchable index.

    Reads works from corpus_dir (each work directory: meta.json with
    work/translator/license plus .txt/.md files), chunks the text, and
    writes the index to index_dir. Embedding vectors are built when
    sentence-transformers is installed; otherwise the index is BM25-only.
    """
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
        if request.birth is not None:
            chart = _build_chart(request.birth)
            birth_context = chart.model_dump()
            try:
                from nakshatra.transits import calculate_transits

                transits = calculate_transits(chart)
                birth_context["transits"] = transits.model_dump()
            except Exception:
                pass
        answer, references = _rag_service.ask(
            request.question,
            index_dir=request.index_dir,
            top_k=request.top_k,
            birth_context=birth_context,
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
    if request.birth is not None:
        chart = _build_chart(request.birth)
        birth_context = chart.model_dump()
        try:
            from nakshatra.transits import calculate_transits

            transits = calculate_transits(chart)
            birth_context["transits"] = transits.model_dump()
        except Exception:
            pass

    async def event_generator() -> AsyncIterator[str]:
        try:
            stream, references, synthesizer = _rag_service.ask_stream(
                request.question,
                index_dir=request.index_dir,
                top_k=request.top_k,
                birth_context=birth_context,
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
        "description": "Vedic Astrology AI Engine - JSON API for birth charts, panchangas, and yogas",
        "version": "0.1.0",
        "license": "MIT",
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
