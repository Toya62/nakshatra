"""
Nakshatra Retrieval - hybrid BM25 + dense search with RRF fusion.

- tokenize: BM25 tokenizer (lowercase alphanumeric, ordinal suffixes
  stripped so "10th" matches "House 10" expansions)
- BM25Index: Okapi BM25 lexical index over chunk texts
- ConceptMap: Bhava/Karaka concept expansion (career -> H10/Sun/Saturn/
  D10, marriage -> H7/Venus/Jupiter/D9, wealth -> H2+H11/Dhana Yogas,
  health -> Lagna/H6/H8, etc.)
- HybridRetriever: BM25 and dense rankings fused via Reciprocal
  Rank Fusion (RRF)
"""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

import numpy as np
from rank_bm25 import BM25Okapi

from nakshatra.ai.corpus import CorpusChunk
from nakshatra.ai.embeddings import (
    BaseEmbedder,
    EmbeddingStore,
    SearchResult,
)

DEFAULT_RRF_K = 60
IDF_FLOOR = 0.1

# Task 13 step 7 — relevance floor. A retrieved chunk enters RRF fusion
# only through a channel where it clears that channel's floor: BM25 score
# >= DEFAULT_BM25_FLOOR, or dense cosine similarity >= DEFAULT_DENSE_FLOOR.
# The BM25 number is calibrated on the step-1 eval set against the
# production index (6,690 chunks): every top-5 BM25 score of the 6 golden
# retrieval queries (tests/test_ai_eval.py) and the 4 classical queries
# (tests/test_classical_rag_consultation.py) is >= 12.62, so the floor
# drops none of them, while 5 of 8 off-topic probe queries return nothing
# at all and the other 3 keep only their single best chunk (from 5).
# The dense floor is a conservative default for cosine similarity with
# the production all-MiniLM-L6-v2 embedder (relevant chunks typically
# score well above 0.20); it is NOT calibrated here because
# sentence-transformers is not installed in this environment, so no dense
# measurement on the real index was possible.
DEFAULT_BM25_FLOOR = 12.0
DEFAULT_DENSE_FLOOR = 0.20

# Absolute BM25 scores scale with corpus size (idf grows with log N), so
# a floor calibrated on the 6,690-chunk production index is meaningless
# on a tiny index, where even an exact match scores under 1.0. Measured
# on random subsamples of the production index: at N=100 the golden
# queries top out at 5-15, at N=1000 two of six top out below 12.0, and
# at N=3000 all six top out at >= 13.6. The floor therefore only engages
# at production scale (MIN_CHUNKS_FOR_FLOOR); below that, search behaves
# exactly as before (no floor), so small test corpora keep working.
MIN_CHUNKS_FOR_FLOOR = 3000


def tokenize(text: str) -> list[str]:
    """Tokenize for BM25: lowercase alphanumeric + Devanagari, ordinals stripped."""
    tokens = re.findall(r"[\u0900-\u097Fa-z0-9]+", text.lower())
    return [re.sub(r"(?<=\d)(st|nd|rd|th)$", "", token) for token in tokens]


class BM25Index:
    """Okapi BM25 lexical index over corpus chunks."""

    def __init__(self, chunks: list[CorpusChunk]) -> None:
        self._chunks = chunks
        self._tokenized = [tokenize(chunk.text) for chunk in chunks]
        self._bm25 = BM25Okapi(self._tokenized) if self._tokenized else None
        if self._bm25 is not None:
            # Okapi idf smoothing zeroes terms present in half a small
            # corpus and penalizes terms in all of it; floor both so
            # ranking still works on small works.
            self._bm25.idf = {term: max(score, IDF_FLOOR) for term, score in self._bm25.idf.items()}

    def __len__(self) -> int:
        return len(self._chunks)

    def scores(self, query: str) -> np.ndarray:
        """BM25 score for every chunk (parallel to chunks)."""
        if self._bm25 is None:
            return np.zeros(len(self._chunks), dtype=np.float32)
        return np.asarray(self._bm25.get_scores(tokenize(query)), dtype=np.float32)

    def search(self, query: str, top_k: int = 5) -> list[tuple[int, float]]:
        """Top-k (chunk_index, score) pairs, highest score first."""
        scores = self.scores(query)
        if scores.size == 0:
            return []
        order = np.argsort(-scores)
        return [
            (int(index), float(scores[int(index)]))
            for index in order[:top_k]
            if scores[int(index)] > 0
        ]


class ConceptMap:
    """Bhava/Karaka concept expansion for intent-aware retrieval.

    Maps consultation intents to their classical significators:
    bhavas (houses), karakas (planetary significators), and vargas
    (divisional charts).
    """

    CONCEPTS: dict[str, tuple[list[str], list[str]]] = {
        # concept: (trigger keywords, expansion terms)
        "career": (
            [
                "career",
                "careers",
                "job",
                "jobs",
                "profession",
                "occupation",
                "work",
                "employment",
                "interview",
                "interviews",
                "promotion",
                "promotions",
                "business",
                "service",
                "hiring",
                "hire",
                "naukri",
                "naukeri",
                "naukari",
                "kam",
                "pesha",
                "jaagir",
                "kaam",
                "nokari",
                "livelihood",
                "ब्यवसाय",
                "जागिर",
                "पेशा",
                "कर्म",
                "रोजगार",
                "नोकरी",
            ],
            [
                "House 10",
                "Karma Bhava",
                "House 6",
                "Service",
                "Employment",
                "House 11",
                "House 2",
                "Sun",
                "Saturn",
                "Mercury",
                "D10",
                "Dashamsa",
            ],
        ),
        "timing": (
            [
                "when",
                "timing",
                "date",
                "range",
                "dates",
                "period",
                "timeline",
                "years",
                "year",
                "month",
                "months",
                "future",
                "schedule",
                "when will",
                "exact date",
                "kahile",
                "samaya",
                "kailesamma",
                "कहिले",
                "समय",
                "मिति",
                "अवधि",
                "भविष्य",
            ],
            [
                "Dasha",
                "Mahadasha",
                "Antardasha",
                "Pratyantardasha",
                "Gochara",
                "Transit",
                "Bhukti",
                "Timing of Events",
            ],
        ),
        "marriage": (
            [
                "marriage",
                "married",
                "marry",
                "spouse",
                "partner",
                "wed",
                "wedding",
                "vivah",
                "bihe",
                "bibaha",
                "keti",
                "keta",
                "shrimati",
                "shriman",
                "विवाह",
                "बिहे",
                "दाम्पत्य",
                "जोडी",
                "जीवनसाथी",
                "श्रीमती",
            ],
            ["House 7", "Venus", "Jupiter", "D9", "Navamsa", "Kalatra Bhava", "Kalatra", "Saptama"],
        ),
        "wealth": (
            [
                "wealth",
                "wealthy",
                "money",
                "rich",
                "fortune",
                "financial",
                "riches",
                "dhana",
                "paisa",
                "sampatti",
                "aarthik",
                "kamai",
                "धन",
                "पैसा",
                "सम्पत्ति",
                "लक्ष्मी",
                "आर्थिक",
            ],
            [
                "House 2",
                "House 11",
                "Dhana Yoga",
                "Jupiter",
                "Venus",
                "Lakshmi",
            ],
        ),
        "health": (
            [
                "health",
                "healthy",
                "wellness",
                "disease",
                "diseases",
                "illness",
                "illnesses",
                "sickness",
                "sick",
                "healing",
                "longevity",
                "vitality",
                "immunity",
                "surgery",
                "medical",
                "recovery",
                "ailment",
                "ailments",
                "prakriti",
                "ayurveda",
                "swasthya",
                "rog",
                "roga",
                "ayur",
                "bimar",
                "chot",
                "aushadhi",
                "upachar",
                "hospital",
                "hospitalization",
                "accident",
                "dirghayu",
                "tandurusti",
                "स्वास्थ्य",
                "रोग",
                "बिमार",
                "औषधि",
                "उपचार",
                "आयु",
                "दीर्घायु",
                "तन्दुरुस्ती",
                "निरोगी",
                "अस्पताल",
                "चोटपटक",
            ],
            [
                "Lagna",
                "Ascendant",
                "Tanu Bhava",
                "House 6",
                "Roga Bhava",
                "House 8",
                "Ayur Bhava",
                "Mars",
                "Sun",
                "Saturn",
                "Vitality",
                "Immunity",
                "Longevity",
                "Ayurveda",
                "Prakriti",
            ],
        ),
        "children": (
            [
                "children",
                "child",
                "son",
                "daughter",
                "offspring",
                "santana",
                "chhora",
                "chhori",
                "bachha",
                "bachhe",
                "सन्तान",
                "छोरा",
                "छोरी",
                "बालबच्चा",
            ],
            ["House 5", "Jupiter", "Moon", "Putra"],
        ),
        "education": (
            [
                "education",
                "study",
                "learning",
                "school",
                "degree",
                "padhai",
                "shiksha",
                "vidya",
                "पढाइ",
                "शिक्षा",
                "विद्या",
            ],
            ["House 4", "House 9", "Mercury", "Jupiter", "Knowledge"],
        ),
        "travel": (
            [
                "travel",
                "journey",
                "foreign",
                "abroad",
                "migration",
                "bidesh",
                "yatra",
                "prabas",
                "बिदेश",
                "विदेश",
                "यात्रा",
                "परदेश",
            ],
            ["House 3", "House 9", "House 12", "Rahu", "Foreign"],
        ),
        "spirituality": (
            [
                "spirituality",
                "spiritual",
                "moksha",
                "enlightenment",
                "soul",
                "meditation",
                "dharmic",
                "adhyatma",
                "mukti",
                "liberation",
                "atman",
                "अध्यात्म",
                "मोक्ष",
                "मुक्ति",
                "साधना",
            ],
            ["House 9", "House 12", "Atmakaraka", "Karakamsa", "Jupiter", "Ketu", "Moksha"],
        ),
        "remedies": (
            [
                "remedy",
                "remedies",
                "upaya",
                "solution",
                "totka",
                "dana",
                "daan",
                "japa",
                "mantra",
                "puja",
                "shanti",
                "उपाय",
                "शान्ति",
                "दान",
                "जप",
                "मन्त्र",
            ],
            ["Upaya", "Remedies", "Dana", "Japa", "Lal Kitab"],
        ),
        "identity": (
            [
                "myself",
                "about me",
                "who am i",
                "who i am",
                "personality",
                "nature",
                "temperament",
                "characteristics",
                "character",
                "strengths",
                "weaknesses",
                "soul purpose",
                "life path",
                "my chart",
                "describe me",
                "traits",
                "आफ्नो बारेमा",
                "मेरो बारेमा",
                "म को हुँ",
                "स्वभाव",
                "चरित्र",
                "व्यक्तित्व",
                "गुण",
                "कमजोरी",
            ],
            [
                "Lagna",
                "Tanu Bhava",
                "Ascendant",
                "Atmakaraka",
                "Chandra",
                "Moon",
                "Sun",
                "Nakshatra",
                "Prakriti",
                "Yogas",
            ],
        ),
    }

    def expand(self, query: str) -> str:
        """Expand a query with concept significators when triggered."""
        lower = query.lower()
        expansions: list[str] = []
        for _concept, (triggers, terms) in self.CONCEPTS.items():
            matched = any(
                re.search(rf"\b{re.escape(trigger)}\b", lower)
                if trigger.isascii()
                else trigger in lower
                for trigger in triggers
            )
            if matched:
                expansions.extend(terms)
        if not expansions:
            return query
        return f"{query} {' '.join(dict.fromkeys(expansions))}"


def _is_unsuitable_chunk(text: str) -> bool:
    """Filter out pure mathematical calculation lookup tables, OCR arithmetic, and crude archaic terms."""
    lower = text.lower()
    # 1. Pure lookup tables & calendar arithmetic
    if "speculum of abbreviated ahargana" in lower or "abbreviated ahargana" in lower:
        return True
    if "speculum of ayana bala" in lower or "deg:mn virupa" in lower:
        return True
    if "speculum of horas" in lower and text.count("\n\n") > 8:
        return True
    # 2. Crude, vulgar, or archaic anatomical curse words from uncurated scans
    unsuitable_terms = (
        "harlot",
        "harlots",
        "vagina",
        "private parts",
        "prostitute",
        "prostitutes",
        "adulteress",
        'kiss" the private parts',
    )
    if any(term in lower for term in unsuitable_terms):
        return True
    return False


# Backwards compatibility alias
_is_tabular_noise_chunk = _is_unsuitable_chunk


class HybridRetriever:
    """Hybrid retriever: BM25 + dense rankings fused with RRF.

    The embedder is optional; without it (or without vectors in the
    store) the retriever degrades to BM25-only lexical search.

    A relevance floor (Task 13 step 7) drops chunks whose BM25 score and
    dense cosine similarity are both below their floors, instead of
    presenting top-k chunks when nothing matched. The floor engages only
    on production-scale indexes (>= MIN_CHUNKS_FOR_FLOOR chunks); see the
    constants above for the calibration.
    """

    def __init__(
        self,
        store: EmbeddingStore,
        embedder: BaseEmbedder | None = None,
        concept_map: ConceptMap | None = None,
        bm25_floor: float = DEFAULT_BM25_FLOOR,
        dense_floor: float = DEFAULT_DENSE_FLOOR,
    ) -> None:
        self._chunks = store.chunks
        self._bm25 = BM25Index(self._chunks)
        self._store = store
        self._embedder = embedder
        self._concept_map = concept_map or ConceptMap()
        self._bm25_floor = bm25_floor
        self._dense_floor = dense_floor

    def __len__(self) -> int:
        return len(self._chunks)

    def search(
        self,
        query: str,
        top_k: int = 5,
        k: int = DEFAULT_RRF_K,
        birth_context: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Retrieve top_k chunks by RRF-fused BM25 + dense ranking."""
        if not self._chunks:
            return []
        expanded = self._concept_map.expand(query)
        if birth_context:
            asc = birth_context.get("ascendant")
            lagna_sign = asc.get("sign") if isinstance(asc, dict) else (asc if isinstance(asc, str) else None)
            moon_sign = birth_context.get("moon_sign")
            raw_yogas = birth_context.get("yogas") or []
            yogas = [str(y["name"]) for y in raw_yogas if isinstance(y, dict) and y.get("name")]
            extra_terms: list[str] = []
            if lagna_sign:
                extra_terms.append(f"{lagna_sign} Lagna")
            if moon_sign:
                extra_terms.append(f"{moon_sign} Moon")
            if yogas:
                extra_terms.extend(yogas[:2])
            q_lower = query.lower()
            if extra_terms and any(
                w in q_lower
                for w in [
                    "myself",
                    "about me",
                    "who am i",
                    "personality",
                    "nature",
                    "strengths",
                    "chart",
                    "character",
                    "health",
                    "illness",
                    "disease",
                    "vitality",
                    "immunity",
                    "longevity",
                    "wellness",
                    "आफ्नो",
                    "स्वभाव",
                    "व्यक्तित्व",
                    "स्वास्थ्य",
                    "रोग",
                    "दीर्घायु",
                ]
            ):
                expanded = f"{expanded} {' '.join(extra_terms)}"

        rankings: list[list[int]] = []

        # The relevance floor engages only at production scale (see
        # MIN_CHUNKS_FOR_FLOOR): absolute BM25 scores are not comparable
        # across corpus sizes, so on a small index every chunk is kept,
        # exactly as before this step.
        floor_on = len(self._chunks) >= MIN_CHUNKS_FOR_FLOOR

        # Lexical (BM25) ranking: only chunks clearing the BM25 floor
        # enter fusion when the floor is on; otherwise every chunk with
        # a positive score, as before.
        bm25_scores = self._bm25.scores(expanded)
        lexical_order = [
            int(index)
            for index in np.argsort(-bm25_scores)
            if bm25_scores[int(index)] > 0
            and (not floor_on or bm25_scores[int(index)] >= self._bm25_floor)
        ]
        rankings.append(lexical_order)

        # Dense (embedding) ranking, mapped by chunk index (Task 13
        # step 7): dense hits used to be keyed by the chunk's serialized
        # dump, so duplicate identical chunks collapsed to one index and
        # a hit could return the wrong duplicate. Only chunks clearing
        # the dense cosine floor enter fusion when the floor is on.
        if self._embedder is not None:
            dense_hits = self._store.search_with_indices(
                self._embedder.embed_query(expanded),
                top_k=min(len(self._chunks), top_k * 3),
            )
            dense_order = [
                index
                for index, result in dense_hits
                if not floor_on or result.score >= self._dense_floor
            ]
            rankings.append(dense_order)

        # Reciprocal Rank Fusion
        fused: dict[int, float] = defaultdict(float)
        for ranking in rankings:
            for rank, index in enumerate(ranking):
                fused[index] += 1.0 / (k + rank + 1)

        ranked = sorted(fused.items(), key=lambda item: (-item[1], item[0]))
        results: list[SearchResult] = []
        for index, score in ranked:
            chunk = self._chunks[index]
            if _is_unsuitable_chunk(chunk.text):
                continue
            results.append(SearchResult(chunk=chunk, score=score))
            if len(results) >= top_k:
                break
        return results
