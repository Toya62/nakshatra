"""
Nakshatra Configuration
Centralized configuration for defaults, paths, and feature flags.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class NakshatraSettings(BaseSettings):
    """Application settings with environment variable support."""

    # Default location (can be overridden by env vars)
    default_lat: float = Field(default=0.0, description="Default latitude")
    default_lon: float = Field(default=0.0, description="Default longitude")
    default_timezone: str = Field(default="UTC", description="Default IANA timezone")
    default_place_name: str | None = Field(default=None, description="Default place name")
    default_ayanamsa: str = Field(default="jhora_lahiri", description="Default ayanamsa")
    default_house_system: str = Field(default="WholeSign", description="Default house system")

    # Geocoding configuration
    geocoding_use_builtin: bool = Field(default=True, description="Use built-in place database")
    geocoding_fallback_online: bool = Field(default=True, description="Fallback to online geocoding")
    nominatim_user_agent: str = Field(
        default="NakshatraVedicAstrologyEngine/0.1.0",
        description="User-Agent for Nominatim requests",
    )

    # Ephemeris configuration
    ephe_path: str = Field(default="", description="Path to Swiss Ephemeris files")

    # API configuration
    api_host: str = Field(default="127.0.0.1", description="API host")
    api_port: int = Field(default=8004, description="API port")
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        description="Allowed CORS origins",
    )

    # Feature flags
    enable_rag: bool = Field(default=True, description="Enable RAG consultation features")
    enable_privacy_middleware: bool = Field(default=True, description="Enable privacy middleware")

    # Data paths
    data_dir: Path = Field(default_factory=lambda: Path(__file__).parent / "data")
    corpus_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "corpus")
    index_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "index")

    model_config = SettingsConfigDict(
        env_prefix="NAKSHATRA_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


# Global settings instance
settings = NakshatraSettings()
