"""
Nakshatra Legal, Licensing & Classical Corpus Attribution.

Provides transparent disclosures regarding:
1. Swiss Ephemeris engine licensing (Astrodienst AG / pyswisseph dual licensing: AGPL-3.0 / Commercial).
2. Classical Sanskrit scriptural works and English translation copyright statuses.
3. Open-source compliance for developers and enterprise self-hosters.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class EphemerisLicensing(BaseModel):
    engine: str = Field(default="Swiss Ephemeris (Astrodienst AG)")
    python_binding: str = Field(default="pyswisseph")
    dual_license: str = Field(default="GNU AGPL-3.0 / Proprietary Commercial")
    details: str = Field(
        default=(
            "Swiss Ephemeris is copyright © 1997-2026 by Astrodienst AG, Switzerland. "
            "Nakshatra is distributed as open-source software under the GNU Affero General Public License v3.0 (AGPL-3.0). "
            "Any closed-source commercial redistribution requires a commercial license directly from Astrodienst AG."
        )
    )
    astrodienst_url: str = Field(default="https://www.astro.com/swisseph/swephinfo_e.htm")


class CorpusAttribution(BaseModel):
    work: str
    original_author: str
    translator_editor: str
    copyright_status: str
    source_url: str


class LicensingStatement(BaseModel):
    platform_name: str = Field(default="Nakshatra: The Science of Light")
    platform_license: str = Field(default="GNU Affero General Public License v3.0 (AGPL-3.0)")
    ephemeris: EphemerisLicensing
    corpus_works: list[CorpusAttribution]
    compliance_guidelines: list[str]



def get_licensing_statement() -> dict[str, Any]:
    """Return full transparent licensing & corpus rights declaration."""
    statement = LicensingStatement(
        ephemeris=EphemerisLicensing(),
        corpus_works=[
            CorpusAttribution(
                work="Brihat Parashara Hora Shastra (BPHS)",
                original_author="Maharishi Parashara",
                translator_editor="R. Santhanam (1984)",
                copyright_status="Sanskrit root verses in public domain; commentary distributed for non-commercial educational & research study.",
                source_url="https://archive.org/details/BPHSEnglish",
            ),
            CorpusAttribution(
                work="Ancient Hindu Astrology for the Modern Western Astrologer",
                original_author="James T. Braha",
                translator_editor="James T. Braha (1986)",
                copyright_status="Educational analytical excerpt for RAG citation retrieval under Fair Use doctrine.",
                source_url="https://archive.org",
            ),
            CorpusAttribution(
                work="The Hindu Science of the Future",
                original_author="Harihar Majumdar",
                translator_editor="Harihar Majumdar (Calcutta)",
                copyright_status="Classical commentary excerpts indexed for scriptural grounding.",
                source_url="https://archive.org",
            ),
        ],
        compliance_guidelines=[
            "Open Source & Free Services: If you host or modify Nakshatra as a public web service, you must release source modifications under AGPL-3.0.",
            "Commercial Closed-Source SaaS: If building proprietary, closed-source commercial software incorporating pyswisseph, you must obtain a commercial license from Astrodienst AG.",
            "Zero Data Retention: Nakshatra guarantees zero storage or logging of seekers' birth parameters, names, or chat logs.",
        ],
    )
    return statement.model_dump()
