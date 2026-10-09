"""
Nakshatra - Vedic Astrology AI Engine
FastAPI application exposing chart calculation as JSON API.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from nakshatra.core import (
    BirthData,
    Ayanamsa,
    HouseSystem,
    ZodiacSystem,
    calculate_chart,
    ChartData,
)


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
    timezone: str = Field(..., description="IANA timezone (e.g., 'America/New_York', 'Asia/Kolkata')")
    place_name: Optional[str] = Field(None, description="Place name for reference")
    
    ayanamsa: Ayanamsa = Field(Ayanamsa.LAHIRI, description="Ayanamsa system (default: Lahiri)")
    house_system: HouseSystem = Field(HouseSystem.WHOLE_SIGN, description="House system (default: Whole Sign)")
    
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


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str = "0.1.0"
    ephemeris: str = "Swiss Ephemeris (pyswisseph) via mayaastrolib"
    default_ayanamsa: str = "Lahiri (Chitra Paksha)"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup: pre-load ephemeris data
    yield
    # Shutdown: cleanup if needed


app = FastAPI(
    title="Nakshatra - Vedic Astrology AI Engine",
    description="JSON API for Vedic birth charts with Vimshottari Dashas, Vargas, Ashtakavarga, and Shadbala",
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


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Health check endpoint."""
    return HealthResponse()


@app.post("/chart", response_model=ChartResponse, tags=["Chart"])
async def create_chart(request: ChartRequest):
    """
    Calculate Vedic birth chart from birth data.
    
    Returns complete chart with:
    - Planetary positions (9 grahas + Ascendant + Midheaven + Rahu/Ketu)
    - Sign, degree, nakshatra, pada, house, dignity, retrograde status
    - House cusps (12 houses)
    - Major aspects (conjunction, sextile, square, trine, opposition)
    - Calculation metadata
    
    Default ayanamsa: Lahiri (Chitra Paksha) - official Indian standard
    Default house system: Whole Sign (traditional Vedic)
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
        
        chart = calculate_chart(
            birth=birth,
            ayanamsa=request.ayanamsa,
            house_system=request.house_system,
        )
        
        return ChartResponse(
            data=chart,
            meta={
                "ayanamsa_used": request.ayanamsa.value,
                "house_system_used": request.house_system.value,
                "zodiac": "sidereal",
            }
        )
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
    place_name: Optional[str] = Query(None),
    ayanamsa: Ayanamsa = Query(Ayanamsa.LAHIRI),
    house_system: HouseSystem = Query(HouseSystem.WHOLE_SIGN),
):
    """GET endpoint for chart calculation (convenience for testing)."""
    request = ChartRequest(
        year=year, month=month, day=day,
        hour=hour, minute=minute, second=second,
        latitude=latitude, longitude=longitude,
        timezone=timezone, place_name=place_name,
        ayanamsa=ayanamsa, house_system=house_system,
    )
    return await create_chart(request)


@app.get("/", tags=["System"])
async def root():
    """Root endpoint with API info."""
    return {
        "name": "Nakshatra",
        "description": "Vedic Astrology AI Engine - JSON API for birth charts",
        "version": "0.1.0",
        "license": "MIT",
        "ephemeris": "Swiss Ephemeris via mayaastrolib",
        "default_ayanamsa": "Lahiri (Chitra Paksha)",
        "default_house_system": "Whole Sign",
        "endpoints": {
            "POST /chart": "Calculate birth chart (JSON body)",
            "GET /chart": "Calculate birth chart (query params)",
            "GET /health": "Health check",
            "GET /docs": "Interactive API docs (Swagger UI)",
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)