"""
Nakshatra Synthesis - LLM answer generation over retrieved context.

- build_prompt: assembles the consultation prompt with numbered
  classical references and optional birth chart context
- extract_citations: parses [n] citation markers from model output
- LLMSynthesizer: generates answers via OpenAI-compatible or Google
  GenAI APIs (optional [ai] extra, lazily imported)
- FallbackSynthesizer: deterministic synthesis that formats the
  retrieved references verbatim (no API key required)
"""

from __future__ import annotations

import json
import os
import re
from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import Any

from pydantic import BaseModel, Field

from nakshatra.ai.retrieval import SearchResult

SYSTEM_PROMPT = (
    "You are a revered Vedic Astrologer (Jyotish Acharya) with deep mastery of classical "
    "scriptures (Brihat Parashara Hora Shastra, Phaladeepika, Saravali). "
    "Your consultation combines authentic scriptural grounding (Pramana), practical chart synthesis (Yukti), "
    "and empathetic, actionable counseling.\n\n"
    "Consultation Guidelines:\n"
    "1. Persona: Speak with warm, insightful authority. Avoid sterile disclaimers like "
    "'Based on the provided references...'. Instead, speak naturally as a wise master: "
    "'In the sacred tradition of Maharishi Parashara, the 10th house (Karma Bhava) governs...'.\n"
    "2. Scriptural Evidence: Anchor your astrological principles in the provided classical verses "
    "using bracketed citations like [1] or [2]. Never invent scriptural citations.\n"
    "3. Chart Personalization: When natal chart details are provided, actively examine the seeker's "
    "Lagna, relevant house lords, and active Vimshottari Dasha period to provide personalized insight.\n"
    "4. Remedial Wisdom: Offer constructive, Dharma-aligned life guidance and classical remedial principles.\n"
    "5. Strict Astronomical Grounding: ONLY cite and use the exact house lords, planetary placements, "
    "astronomical transits, and Ashtakavarga bindus explicitly provided in the context below. "
    "NEVER invent or fabricate bindu scores, rekhas, or imaginary planetary positions.\n"
    "6. Concrete Predictive Synthesis: For predictive and timing questions, anchor your judgment in "
    "the operating Mahadasha and Antardasha lords (their specific house rulerships and chart placements) "
    "synthesized with the active Gochara transit houses. Avoid generic fortune-teller generalizations."
)


class Citation(BaseModel):
    """A classical reference cited in an answer."""

    work: str
    chapter: str = ""
    verse: str = ""
    text: str


class Answer(BaseModel):
    """A synthesized consultation answer."""

    question: str
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    model: str = ""


class BaseSynthesizer(ABC):
    """Interface for answer synthesizers."""

    @abstractmethod
    def synthesize(
        self,
        question: str,
        results: list[SearchResult],
        birth_context: dict[str, Any] | None = None,
    ) -> Answer:
        """Generate an answer from retrieved search results."""

    def synthesize_stream(
        self,
        question: str,
        results: list[SearchResult],
        birth_context: dict[str, Any] | None = None,
    ) -> Iterator[str]:
        """Stream answer tokens. Defaults to yielding complete synthesized text."""
        ans = self.synthesize(question, results, birth_context)
        yield ans.answer


def _citation_label(index: int, result: SearchResult) -> str:
    """Format '[n] Work, Chapter X, Verse Y' for the prompt."""
    parts = [result.chunk.work]
    if result.chunk.chapter:
        parts.append(f"Chapter {result.chunk.chapter}")
    if result.chunk.verse:
        parts.append(f"Verse {result.chunk.verse}")
    return f"[{index}] {' '.join(parts)}"


_ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]
_SIGN_LORDS = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury",
    "Cancer": "Moon", "Leo": "Sun", "Virgo": "Mercury",
    "Libra": "Venus", "Scorpio": "Mars", "Sagittarius": "Jupiter",
    "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter",
}


def _format_birth_summary(chart: dict[str, Any]) -> str:
    """Format structured natal chart facts, house lords, ashtakavarga, and transits for synthesis."""
    lines: list[str] = []
    asc = chart.get("ascendant")
    lagna_sign: str | None = None
    if isinstance(asc, dict):
        lagna_sign = asc.get("sign")
        deg = asc.get("degree_in_sign", 0)
        lines.append(
            f"- Lagna (Ascendant): {lagna_sign} at {deg:.2f}° "
            f"(Nakshatra: {asc.get('nakshatra')} Pada {asc.get('pada')}, Lord: {asc.get('nakshatra_lord')})"
        )
    elif isinstance(asc, str):
        lagna_sign = asc
        lines.append(f"- Lagna (Ascendant): {asc}")

    # Explicit 12 House Lords ground truth
    if lagna_sign and lagna_sign in _ZODIAC_SIGNS:
        lagna_idx = _ZODIAC_SIGNS.index(lagna_sign)
        house_lord_parts: list[str] = []
        for h in range(1, 13):
            s_idx = (lagna_idx + h - 1) % 12
            h_sign = _ZODIAC_SIGNS[s_idx]
            h_lord = _SIGN_LORDS[h_sign]
            house_lord_parts.append(f"H{h} ({h_sign}) lord: {h_lord}")
        lines.append("- Exact House Rulerships (Bhaveshas): " + " | ".join(house_lord_parts))

    planets = chart.get("planets")
    if isinstance(planets, list):
        rahu = chart.get("rahu")
        ketu = chart.get("ketu")
        all_bodies = [p for p in planets if isinstance(p, dict)]
        if isinstance(rahu, dict):
            all_bodies.append(rahu)
        if isinstance(ketu, dict):
            all_bodies.append(ketu)

        if all_bodies:
            lines.append("- Natal Planetary Placements (Grahas in Bhavas):")
            for p in all_bodies:
                retro = " (Retrograde)" if p.get("retrograde") else ""
                deg_val = p.get("degree_in_sign", 0)
                lines.append(
                    f"  • {p.get('name')}: House {p.get('house')} in {p.get('sign')} "
                    f"({deg_val:.2f}° {p.get('nakshatra')} Pada {p.get('pada')}){retro}"
                )

    # Real Ashtakavarga Points
    av = chart.get("ashtakavarga")
    if isinstance(av, dict):
        sav = av.get("sarvashtakavarga")
        if isinstance(sav, list) and len(sav) == 12:
            sav_items = [f"{_ZODIAC_SIGNS[i]}: {sav[i]}" for i in range(12)]
            lines.append("- Calculated Sarvashtakavarga (SAV Points per Sign): " + ", ".join(sav_items))

    # Real-Time Astronomical Transits (Gochara)
    transits = chart.get("transits")
    if isinstance(transits, dict):
        t_time = transits.get("transit_time", "Active")
        lines.append(f"- Astronomical Planetary Transits (Gochara as of {t_time}):")
        t_planets = transits.get("planets") or []
        for tp in t_planets:
            if isinstance(tp, dict):
                fav = " [Auspicious from Moon]" if tp.get("is_favorable_gochar") else ""
                bav_str = f", BAV: {tp.get('bav_bindus')}" if tp.get("bav_bindus") is not None else ""
                sav_str = f", SAV: {tp.get('sav_bindus')}" if tp.get("sav_bindus") is not None else ""
                retro = " (Retrograde)" if tp.get("retrograde") else ""
                lines.append(
                    f"  • Transit {tp.get('name')}: {tp.get('sign')} ({tp.get('degree_in_sign', 0):.2f}° {tp.get('nakshatra')}){retro} "
                    f"-> House {tp.get('house_from_lagna')} from Lagna, House {tp.get('house_from_moon')} from Moon"
                    f"{sav_str}{bav_str}{fav}"
                )
        sade_sati = transits.get("sade_sati") or {}
        if sade_sati.get("is_active"):
            lines.append(f"  • Saturn Sade Sati: ACTIVE ({sade_sati.get('phase')})")
        elif sade_sati.get("is_ashtama_shani"):
            lines.append("  • Saturn Ashtama Shani: ACTIVE (8th from Moon)")
        elif sade_sati.get("is_kantaka_shani"):
            lines.append("  • Saturn Kantaka Shani: ACTIVE (4th/10th from Moon)")

        double_tr = transits.get("double_transit_houses") or []
        if double_tr:
            lines.append(f"  • Double Transit Focus (Jupiter + Saturn jointly influencing Bhavas): Houses {', '.join(map(str, double_tr))}")

    dashas = chart.get("dashas")
    if isinstance(dashas, dict):
        curr_md = (dashas.get("current_md") or {}).get("lord")
        curr_ad = (dashas.get("current_ad") or {}).get("lord")
        curr_pd = (dashas.get("current_pd") or {}).get("lord")
        if curr_md or curr_ad:
            lines.append(
                f"- Operating Vimshottari Period: Mahadasha [{curr_md}] -> "
                f"Antardasha [{curr_ad}] -> Pratyantardasha [{curr_pd}]"
            )

    yogas = chart.get("yogas")
    if isinstance(yogas, list):
        yoga_names = [str(y["name"]) for y in yogas if isinstance(y, dict) and y.get("name")]
        if yoga_names:
            lines.append(f"- Active Yogas: {', '.join(yoga_names[:5])}")

    return "\n".join(lines)


def build_prompt(
    question: str,
    results: list[SearchResult],
    birth_context: dict[str, Any] | None = None,
) -> str:
    """Assemble the consultation prompt with classical references and natal context."""
    lines = ["References:"]
    for index, result in enumerate(results, start=1):
        lines.append(
            f"{_citation_label(index, result)}: {result.chunk.text}"
        )
    lines.append("")
    if birth_context:
        lines.append(f"Birth chart context: {json.dumps(birth_context)}")
        summary = _format_birth_summary(birth_context)
        if summary:
            lines.append("\n" + summary)
        lines.append("")
    lines.append(f"Question: {question}")
    lines.append(
        "Answer the question using the references above, citing them with bracketed numbers like [1]. "
        "Synthesize scriptural principles into insightful, actionable astrological guidance."
    )
    return "\n".join(lines)


def extract_citations(
    answer: str, results: list[SearchResult]
) -> list[Citation]:
    """Parse [n] markers from model output into citations."""
    used = sorted({int(match) for match in re.findall(r"\[(\d+)\]", answer)})
    citations: list[Citation] = []
    for number in used:
        if 1 <= number <= len(results):
            chunk = results[number - 1].chunk
            citations.append(
                Citation(
                    work=chunk.work,
                    chapter=chunk.chapter,
                    verse=chunk.verse,
                    text=chunk.text,
                )
            )
    return citations


class LLMSynthesizer(BaseSynthesizer):
    """Generates answers via an LLM provider (optional [ai] extra).

    Providers:
    - "openai": OpenAI-compatible API (also serves local models
      via base_url)
    - "google": Google GenAI API
    """

    def __init__(
        self,
        provider: str = "openai",
        model: str = "gpt-4o-mini",
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.provider = provider
        self.model = model
        self._api_key = api_key
        self._base_url = base_url
        self._client: Any = None

    def synthesize(
        self,
        question: str,
        results: list[SearchResult],
        birth_context: dict[str, Any] | None = None,
    ) -> Answer:
        prompt = build_prompt(question, results, birth_context)
        try:
            text = self._complete(prompt)
            return Answer(
                question=question,
                answer=text,
                citations=extract_citations(text, results),
                model=self.model,
            )
        except Exception as e:
            fb = FallbackSynthesizer()
            ans = fb.synthesize(question, results, birth_context)
            ans.answer = (
                f"*[Notice: Gemini service temporarily unavailable ({e}). "
                "Retrieved classical scriptural citations:]*\n\n" + ans.answer
            )
            return ans

    def _complete(self, prompt: str) -> str:
        if self.provider == "openai":
            return self._complete_openai(prompt)
        if self.provider == "google":
            return self._complete_google(prompt)
        raise ValueError(f"Unknown LLM provider: {self.provider}")

    def _openai_client(self) -> Any:
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError as e:
                raise ImportError(
                    "The openai package is required for the openai "
                    "provider. Install it with: pip install 'nakshatra[ai]'"
                ) from e
            self._client = OpenAI(
                api_key=self._api_key or os.environ.get("OPENAI_API_KEY"),
                base_url=self._base_url,
            )
        return self._client

    def _complete_openai(self, prompt: str) -> str:
        client = self._openai_client()
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )
        return str(response.choices[0].message.content)

    def _complete_google(self, prompt: str) -> str:
        rotation_models = [
            "gemini-3.7-flash",
            "gemini-3.6-flash",
            "gemini-3.5-flash",
            "gemini-3.5-flash-lite",
            "gemini-3.1-flash-lite",
            "gemini-3-flash-preview",
            "gemini-flash-latest",
            "gemini-flash-lite-latest",
        ]
        candidates = [self.model]
        for m in rotation_models:
            if m not in candidates:
                candidates.append(m)

        if self._client is None:
            try:
                from google import genai
            except ImportError as e:
                raise ImportError(
                    "The google-genai package is required for the google "
                    "provider. Install it with: pip install 'nakshatra[ai]'"
                ) from e
            api_key = (
                self._api_key
                or os.environ.get("GOOGLE_API_KEY")
                or os.environ.get("GEMINI_API_KEY")
            )
            self._client = genai.Client(api_key=api_key)

        last_err: Exception | None = None
        for cand in candidates:
            try:
                response = self._client.models.generate_content(
                    model=cand, contents=prompt
                )
                self.model = cand
                return str(response.text)
            except Exception as e:
                last_err = e
                err_str = str(e)
                # Rotate immediately if model hits 429 quota exhaustion or 503 unavailable
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "503" in err_str or "UNAVAILABLE" in err_str:
                    continue
                raise

        if last_err:
            raise last_err
        raise RuntimeError("Google GenAI completion failed without error")

    def synthesize_stream(
        self,
        question: str,
        results: list[SearchResult],
        birth_context: dict[str, Any] | None = None,
    ) -> Iterator[str]:
        prompt = build_prompt(question, results, birth_context)
        if self.provider == "google":
            yield from self._stream_google(prompt)
        elif self.provider == "openai":
            yield from self._stream_openai(prompt)
        else:
            yield self._complete(prompt)

    def _stream_openai(self, prompt: str) -> Iterator[str]:
        client = self._openai_client()
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            stream=True,
        )
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                yield str(chunk.choices[0].delta.content)

    def _stream_google(self, prompt: str) -> Iterator[str]:
        rotation_models = [
            "gemini-3.7-flash",
            "gemini-3.6-flash",
            "gemini-3.5-flash",
            "gemini-3.5-flash-lite",
            "gemini-3.1-flash-lite",
            "gemini-3-flash-preview",
            "gemini-flash-latest",
            "gemini-flash-lite-latest",
        ]
        candidates = [self.model]
        for m in rotation_models:
            if m not in candidates:
                candidates.append(m)

        if self._client is None:
            from google import genai
            api_key = (
                self._api_key
                or os.environ.get("GOOGLE_API_KEY")
                or os.environ.get("GEMINI_API_KEY")
            )
            self._client = genai.Client(api_key=api_key)

        last_err: Exception | None = None
        for cand in candidates:
            try:
                stream_response = self._client.models.generate_content_stream(
                    model=cand, contents=prompt
                )
                self.model = cand
                for chunk in stream_response:
                    if chunk.text:
                        yield str(chunk.text)
                return
            except Exception as e:
                last_err = e
                err_str = str(e)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "503" in err_str or "UNAVAILABLE" in err_str:
                    continue
                raise

        if last_err:
            raise last_err


class FallbackSynthesizer(BaseSynthesizer):
    """Deterministic synthesizer that formats retrieved references verbatim.

    Used when no LLM provider is configured: the answer is the
    numbered reference list, so the pipeline works end-to-end
    without API keys.
    """

    def synthesize(
        self,
        question: str,
        results: list[SearchResult],
        birth_context: dict[str, Any] | None = None,
    ) -> Answer:
        if not results:
            return Answer(
                question=question,
                answer=(
                    "No relevant references were found in the corpus "
                    "for this question."
                ),
                model="fallback",
            )
        lines = [f"Regarding your question '{question}':"]
        for index, result in enumerate(results, start=1):
            lines.append(
                f"{_citation_label(index, result)}: {result.chunk.text}"
            )
        return Answer(
            question=question,
            answer="\n".join(lines),
            citations=[
                Citation(
                    work=result.chunk.work,
                    chapter=result.chunk.chapter,
                    verse=result.chunk.verse,
                    text=result.chunk.text,
                )
                for result in results
            ],
            model="fallback",
        )
