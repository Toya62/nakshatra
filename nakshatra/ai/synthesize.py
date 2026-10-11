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
from typing import Any

from pydantic import BaseModel, Field

from nakshatra.ai.retrieval import SearchResult

SYSTEM_PROMPT = (
    "You are a learned Vedic astrology consultant. Answer the "
    "question using only the provided classical references. Cite "
    "sources with bracketed numbers like [1]. If the references do "
    "not contain the answer, say so clearly. Never invent "
    "scriptural citations."
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


def _citation_label(index: int, result: SearchResult) -> str:
    """Format '[n] Work, Chapter X, Verse Y' for the prompt."""
    parts = [result.chunk.work]
    if result.chunk.chapter:
        parts.append(f"Chapter {result.chunk.chapter}")
    if result.chunk.verse:
        parts.append(f"Verse {result.chunk.verse}")
    return f"[{index}] {' '.join(parts)}"


def build_prompt(
    question: str,
    results: list[SearchResult],
    birth_context: dict[str, Any] | None = None,
) -> str:
    """Assemble the user prompt with numbered references."""
    lines = ["References:"]
    for index, result in enumerate(results, start=1):
        lines.append(
            f"{_citation_label(index, result)}: {result.chunk.text}"
        )
    lines.append("")
    if birth_context:
        lines.append(f"Birth chart context: {json.dumps(birth_context)}")
        lines.append("")
    lines.append(f"Question: {question}")
    lines.append(
        "Answer the question using only the references above, "
        "citing them with bracketed numbers like [1]."
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
        text = self._complete(prompt)
        return Answer(
            question=question,
            answer=text,
            citations=extract_citations(text, results),
            model=self.model,
        )

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
        response = self._client.models.generate_content(
            model=self.model, contents=prompt
        )
        return str(response.text)


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
