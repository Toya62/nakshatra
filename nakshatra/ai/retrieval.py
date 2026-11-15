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

import json
import re
from collections import defaultdict

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
                "career", "careers", "job", "jobs", "profession", "occupation", "work",
                "jagire", "naukari", "kam", "pesha", "jaagir", "kaam", "nokari",
                "ब्यवसाय", "जागिर", "पेशा", "कर्म"
            ],
            ["House 10", "Sun", "Saturn", "D10", "Dashamsa", "Karma"],
        ),
        "marriage": (
            [
                "marriage", "married", "marry", "spouse", "partner", "wed", "wedding",
                "vivah", "bihe", "bibaha", "keti", "keta", "shrimati", "shriman",
                "विवाह", "बिहे", "दाम्पत्य", "जोडी"
            ],
            ["House 7", "Venus", "Jupiter", "D9", "Navamsa"],
        ),
        "wealth": (
            [
                "wealth", "wealthy", "money", "rich", "fortune", "financial", "riches",
                "dhana", "paisa", "sampatti", "aarthik", "kamai",
                "धन", "पैसा", "सम्पत्ति", "लक्ष्मी", "आर्थिक"
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
                "health", "disease", "illness", "sickness", "healing",
                "swasthya", "rog", "bimar", "chot", "aushadhi",
                "स्वास्थ्य", "रोग", "बिमार", "औषधि"
            ],
            ["Lagna", "Ascendant", "House 6", "House 8", "Mars", "Sun"],
        ),
        "children": (
            [
                "children", "child", "son", "daughter", "offspring",
                "santana", "chhora", "chhori", "bachha", "bachhe",
                "सन्तान", "छोरा", "छोरी", "बालबच्चा"
            ],
            ["House 5", "Jupiter", "Moon", "Putra"],
        ),
        "education": (
            [
                "education", "study", "learning", "school", "degree",
                "padhai", "shiksha", "vidya",
                "पढाइ", "शिक्षा", "विद्या"
            ],
            ["House 4", "House 9", "Mercury", "Jupiter", "Knowledge"],
        ),
        "travel": (
            [
                "travel", "journey", "foreign", "abroad", "migration",
                "bidesh", "yatra", "prabas",
                "बिदेश", "विदेश", "यात्रा", "परदेश"
            ],
            ["House 3", "House 9", "House 12", "Rahu", "Foreign"],
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


class HybridRetriever:
    """Hybrid retriever: BM25 + dense rankings fused with RRF.

    The embedder is optional; without it (or without vectors in the
    store) the retriever degrades to BM25-only lexical search.
    """

    def __init__(
        self,
        store: EmbeddingStore,
        embedder: BaseEmbedder | None = None,
        concept_map: ConceptMap | None = None,
    ) -> None:
        self._chunks = store.chunks
        self._bm25 = BM25Index(self._chunks)
        self._store = store
        self._embedder = embedder
        self._concept_map = concept_map or ConceptMap()

    def __len__(self) -> int:
        return len(self._chunks)

    def search(
        self,
        query: str,
        top_k: int = 5,
        k: int = DEFAULT_RRF_K,
    ) -> list[SearchResult]:
        """Retrieve top_k chunks by RRF-fused BM25 + dense ranking."""
        if not self._chunks:
            return []
        expanded = self._concept_map.expand(query)

        rankings: list[list[int]] = []

        # Lexical (BM25) ranking
        bm25_scores = self._bm25.scores(expanded)
        lexical_order = [
            int(index) for index in np.argsort(-bm25_scores) if bm25_scores[int(index)] > 0
        ]
        rankings.append(lexical_order)

        # Dense (embedding) ranking
        if self._embedder is not None:
            dense_results = self._store.search(
                self._embedder.embed_query(expanded),
                top_k=min(len(self._chunks), top_k * 3),
            )
            index_by_key = {
                json.dumps(chunk.model_dump(), sort_keys=True): index
                for index, chunk in enumerate(self._chunks)
            }
            dense_order = [
                index_by_key[json.dumps(result.chunk.model_dump(), sort_keys=True)]
                for result in dense_results
            ]
            rankings.append(dense_order)

        # Reciprocal Rank Fusion
        fused: dict[int, float] = defaultdict(float)
        for ranking in rankings:
            for rank, index in enumerate(ranking):
                fused[index] += 1.0 / (k + rank + 1)

        ranked = sorted(fused.items(), key=lambda item: (-item[1], item[0]))
        return [
            SearchResult(chunk=self._chunks[index], score=score) for index, score in ranked[:top_k]
        ]
