"""
Nakshatra - Vedic Astrology AI Engine
FastAPI application exposing chart calculation, Vimshottari Dashas, Shodashavarga,
Ashtakavarga, Shadbala, and Gochar transits as JSON or formatted text.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, Response
from pydantic import BaseModel, Field, field_validator

from nakshatra.core import (
    Ayanamsa,
    BirthData,
    ChartData,
    HouseSystem,
    calculate_chart,
)
from nakshatra.transits import TransitReport, calculate_transits

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


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str = "0.1.0"
    ephemeris: str = "Swiss Ephemeris (pyswisseph) via mayaastrolib"
    default_ayanamsa: str = "jhora_lahiri (Traditional Lahiri, Jagannatha Hora calibrated)"


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
        year=year, month=month, day=day,
        hour=hour, minute=minute, second=second,
        latitude=latitude, longitude=longitude,
        timezone=timezone, place_name=place_name,
        ayanamsa=ayanamsa, house_system=house_system,
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
            year=year, month=month, day=day,
            hour=hour, minute=minute, second=second,
            latitude=latitude, longitude=longitude,
            timezone=timezone, place_name=place_name,
            ayanamsa=ayanamsa, house_system=house_system,
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


@app.get("/", tags=["System"])
async def root() -> dict:
    """Root endpoint with API info."""
    return {
        "name": "Nakshatra",
        "description": "Vedic Astrology AI Engine - JSON API for birth charts and transits",
        "version": "0.1.0",
        "license": "MIT",
        "ephemeris": "Swiss Ephemeris via mayaastrolib (pyswisseph)",
        "default_ayanamsa": "jhora_lahiri (Traditional Lahiri, Jagannatha Hora calibrated)",
        "default_house_system": "Whole Sign",
        "endpoints": {
            "POST /chart": (
                "Calculate birth chart (JSON body); "
                "?format=table|markdown|csv|diagram for text"
            ),
            "GET /chart": "Calculate birth chart (query params); supports format param",
            "GET /chart/diagram": "South Indian ASCII chart diagram for a varga (D1, D9, D10, ...)",
            "POST /transits": "Calculate Gochar transits against a natal chart (JSON body)",
            "GET /health": "Health check",
            "GET /docs": "Interactive API docs (Swagger UI)",
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
