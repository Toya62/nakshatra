"""Task 13 step 7 — relevance floor, token budget, citation offsets,
dense index mapping, and the per-work OCR quality report.

No test here calls a live LLM.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

import pytest

from nakshatra.ai.corpus import (
    CorpusChunk,
    chunk_text,
    clean_corpus_text,
    ingest_corpus,
    ocr_cleaning_report,
)
from nakshatra.ai.embeddings import (
    EmbeddingStore,
    HashingEmbedder,
    SearchResult,
)
from nakshatra.ai.retrieval import (
    DEFAULT_BM25_FLOOR,
    DEFAULT_DENSE_FLOOR,
    HybridRetriever,
)
from nakshatra.ai.service import RAGService
from nakshatra.ai.synthesize import (
    PROMPT_BUDGET_NOTE,
    PROMPT_TOKEN_BUDGET,
    build_prompt,
    estimate_prompt_tokens,
)


def _chunk(
    work: str = "BPHS",
    chapter: str = "1",
    verse: str = "1",
    text: str = "The Sun in the first house.",
) -> CorpusChunk:
    return CorpusChunk(
        work=work,
        chapter=chapter,
        verse=verse,
        text=text,
        topics=["Sun"],
        source_file="test.txt",
        char_start=0,
        char_end=len(text),
        tier="verse",
    )


def _any_text(results, needle: str) -> bool:
    return any(needle.lower() in r.chunk.text.lower() for r in results)


# The 6 golden retrieval queries from tests/test_ai_eval.py
# (GOLDEN_RETRIAL_QUERIES), with the same checks.
GOLDEN_QUERIES: list[tuple[str, object]] = [
    (
        "Sade Sati Saturn transit 12th from Moon difficult period",
        lambda r: _any_text(r, "Sade Sati"),
    ),
    (
        "Gaja Kesari Yoga Moon Jupiter kendra from each other",
        lambda r: _any_text(r, "Gaja Kesari"),
    ),
    (
        "Lal Kitab Saturn upaya remedy afflicted Shani",
        lambda r: "Lal Kitab" in [x.chunk.work for x in r],
    ),
    (
        "Vimshottari dasha balance years Moon nakshatra at birth",
        lambda r: _any_text(r, "Dasha"),
    ),
    (
        "Kuja Dosha Mars Manglik houses marriage delay",
        lambda r: _any_text(r, "Kuja Dosha"),
    ),
    (
        "Rahu Ketu eclipse nodes Chaya Graha shadow planets",
        lambda r: _any_text(r, "Rahu") and _any_text(r, "Ketu"),
    ),
]

# Off-topic probe queries: no astrology content. At the calibrated floor
# the first five return nothing at all; the last three keep only their
# single best chunk (a single rare-word collision: "basil", "share
# market", "car"), down from 5 results each.
OFF_TOPIC_EMPTY = [
    "quantum computing qubit entanglement superposition",
    "football world cup 2026 tickets stadium seating",
    "python django tutorial async views database",
    "weather forecast tomorrow Berlin rain temperature",
    "how to bake sourdough bread starter flour water",
]
OFF_TOPIC_SINGLE = [
    "best pizza recipe tomato mozzarella basil Rome",
    "Tesla share price stock market today forecast",
    "how to fix a leaking car engine oil gasket",
]


class TestRelevanceFloor:
    """The floor keeps golden queries and drops off-topic ones (real index)."""

    def test_floor_threshold_is_calibrated(self):
        assert DEFAULT_BM25_FLOOR == 12.0
        assert DEFAULT_DENSE_FLOOR == 0.20

    def test_golden_queries_keep_all_results(self):
        """0/6 golden queries dropped — every top-5 BM25 score is >= 12.62."""
        retriever = RAGService().load()
        assert len(retriever) >= 3000  # floor engages on the real index
        for query, check in GOLDEN_QUERIES:
            results = retriever.search(query, top_k=5)
            assert len(results) == 5, query
            assert check(results), f"golden retrieval query missed: {query!r}"

    def test_off_topic_queries_return_nothing(self):
        retriever = RAGService().load()
        for query in OFF_TOPIC_EMPTY:
            assert retriever.search(query, top_k=5) == [], query

    def test_off_topic_single_term_collisions_keep_at_most_one(self):
        """Residual single rare-word matches keep one chunk, not five."""
        retriever = RAGService().load()
        for query in OFF_TOPIC_SINGLE:
            results = retriever.search(query, top_k=5)
            assert len(results) <= 1, query

    def test_floor_does_not_engage_on_small_indexes(self):
        """Absolute BM25 scores are corpus-scale dependent: on a 2-chunk
        index even an exact match scores under 1.0, so the floor stays
        off and behaviour is unchanged."""
        chunks = [
            _chunk(verse="1", text="The Sun in the 10th house gives career"),
            _chunk(verse="2", text="The Moon in the 4th house gives comfort"),
        ]
        store = EmbeddingStore()
        store.add_records(chunks)
        retriever = HybridRetriever(store)
        results = retriever.search("career")
        assert results
        assert results[0].chunk.verse == "1"


class TestDenseIndexMapping:
    """Dense hits map by chunk index, not by serialized chunk dump."""

    def test_search_with_indices_distinguishes_identical_chunks(self):
        """Two fully identical chunks get distinct indices."""
        text = "Sun career profession work job"
        chunks = [_chunk(verse="1", text=text), _chunk(verse="1", text=text)]
        store = EmbeddingStore()
        store.build(chunks, HashingEmbedder(dim=64))
        hits = store.search_with_indices(
            HashingEmbedder(dim=64).embed_query("career job"), top_k=2
        )
        assert sorted(index for index, _ in hits) == [0, 1]

    def test_duplicate_chunks_are_not_double_counted_in_rrf(self):
        """Old behaviour keyed dense hits by json.dumps(chunk.model_dump()):
        identical chunks collapsed to one index and that index collected
        both dense RRF contributions (top fused score ~0.0487). With
        index mapping each duplicate gets one contribution (top ~0.0328)."""
        text = "alpha beta gamma delta"
        chunks = [
            _chunk(verse="1", text=text),
            _chunk(verse="2", text="unrelated zeta theta"),
            _chunk(verse="1", text=text),
        ]
        store = EmbeddingStore()
        store.build(chunks, HashingEmbedder(dim=64))
        retriever = HybridRetriever(store, HashingEmbedder(dim=64))
        results = retriever.search("alpha beta gamma", top_k=2)
        assert len(results) == 2
        assert all(r.chunk.text == text for r in results)
        # One BM25 + one dense RRF contribution each (2/61 ~= 0.0328);
        # the double-counted value would be ~0.0487.
        assert results[0].score == pytest.approx(2 / 61, abs=1e-3)
        assert results[0].score < 0.04


def _large_synthetic_store() -> EmbeddingStore:
    """~3005-chunk store (floor engages) with 5 genuine career chunks."""
    rng = random.Random(42)
    filler_words = (
        "river stone mountain cloud forest village harvest market temple road "
        "garden flower season rain winter summer autumn spring bird fish horse cow"
    ).split()
    chunks = []
    for i in range(3000):
        words = [rng.choice(filler_words) for _ in range(40)]
        chunks.append(_chunk(verse=str(i), text=" ".join(words) + "."))
    genuine = (
        "The Sun in the tenth house gives career success. Saturn in House 10 "
        "brings profession and employment. Karma Bhava and Dashamsha show livelihood. "
    )
    for j in range(5):
        chunks.append(_chunk(verse=f"g{j}", text=genuine))
    store = EmbeddingStore()
    store.build(chunks, HashingEmbedder(dim=256))
    return store


class TestFloorOnLargeSyntheticIndex:
    """Both floor channels together on a production-scale synthetic index."""

    def test_genuine_query_kept_off_topic_query_dropped(self):
        store = _large_synthetic_store()
        retriever = HybridRetriever(store, HashingEmbedder(dim=256))
        genuine = retriever.search("career job profession", top_k=5)
        assert len(genuine) == 5
        assert all(r.chunk.verse.startswith("g") for r in genuine)
        off_topic = retriever.search(
            "quantum qubit entanglement superposition", top_k=5
        )
        assert off_topic == []

    def test_dense_floor_drops_zero_cosine_hits(self):
        store = _large_synthetic_store()
        hits = store.search_with_indices(
            HashingEmbedder(dim=256).embed_query("quantum qubit entanglement"),
            top_k=5,
        )
        assert hits
        assert all(result.score == 0.0 for _, result in hits)
        retriever = HybridRetriever(store, HashingEmbedder(dim=256))
        assert (
            retriever.search("quantum qubit entanglement superposition", top_k=5)
            == []
        )


class TestCitationOffsets:
    """chunk_text() gives each piece its own offsets from split_text()."""

    def test_offsets_are_per_piece_and_locate_the_text(self):
        sentence = (
            "The Sun in the tenth house gives career success and fame to the native. "
        )
        raw = (
            "Chapter 1, Verse 1: " + sentence * 12 + "\n"
            "Chapter 1, Verse 2: " + sentence * 3
        )
        sanitized = clean_corpus_text(raw)
        chunks, _stats = chunk_text(raw, work="BPHS", source_file="t.txt")
        assert len(chunks) >= 3
        ranges = [(c.char_start, c.char_end) for c in chunks]
        assert len(set(ranges)) == len(ranges), "pieces must not share offsets"
        for chunk in chunks:
            assert 0 <= chunk.char_start < chunk.char_end
            assert sanitized[chunk.char_start : chunk.char_end] == chunk.text

    def test_short_verse_keeps_single_range(self):
        chunks, _ = chunk_text(
            "Chapter 1, Verse 1: Short verse text for offset testing.",
            work="BPHS",
            source_file="t.txt",
        )
        assert len(chunks) == 1
        assert chunks[0].char_start >= 0
        assert chunks[0].char_end > chunks[0].char_start


class TestTokenBudget:
    """Prompt token budgeting truncates the raw chart JSON first."""

    def test_estimate_prompt_tokens(self):
        assert estimate_prompt_tokens("") == 0
        assert estimate_prompt_tokens("x" * 400) == 100
        assert estimate_prompt_tokens("x" * 401) == 101

    def test_small_prompt_untouched(self):
        result = _result()
        prompt = build_prompt(
            "Q",
            [result],
            birth_context={"ascendant": "Aries", "moon_sign": "Cancer"},
        )
        assert PROMPT_BUDGET_NOTE not in prompt
        assert "__truncated__" not in prompt
        assert '"ascendant": "Aries"' in prompt

    def test_huge_chart_json_is_truncated_and_signalled(self):
        birth_context = {
            "ascendant": {
                "sign": "Aries",
                "degree_in_sign": 29.97,
                "nakshatra": "Krittika",
                "pada": 1,
            },
            "notes": "x" * (PROMPT_TOKEN_BUDGET * 4),
        }
        prompt = build_prompt("Q", [_result()], birth_context=birth_context)
        assert estimate_prompt_tokens(prompt) <= PROMPT_TOKEN_BUDGET
        assert PROMPT_BUDGET_NOTE in prompt
        assert "__truncated__" in prompt
        # The formatted summary and the references survive the truncation.
        assert "Lagna (Ascendant): Aries" in prompt
        assert "[1] BPHS Chapter 1 Verse 1" in prompt
        assert "The Sun in the first house." in prompt
        assert "x" * 1000 not in prompt

    def test_budget_env_override(self, monkeypatch):
        # With a 100-token budget the JSON is emptied, but the prompt
        # still exceeds it: references are never dropped and the summary
        # is never cut, so the budget can only shrink the JSON.
        monkeypatch.setenv("PROMPT_TOKEN_BUDGET", "100")
        prompt = build_prompt(
            "Q",
            [_result()],
            birth_context={"ascendant": "Aries", "notes": "y" * 10000},
        )
        assert PROMPT_BUDGET_NOTE in prompt
        assert "__truncated__" in prompt
        assert "y" * 1000 not in prompt
        assert "[1] BPHS Chapter 1 Verse 1" in prompt


def _result() -> SearchResult:
    return SearchResult(chunk=_chunk(), score=0.9)


class TestOCRReport:
    """Per-work OCR quality report from the cleaning heuristics."""

    def test_report_counts_match_cleaning(self):
        raw = (
            "The Sun in the first house gives career success.\n"
            "12345\n"
            "The Moon in the second house gives wealth.\n"
            "wtwfircl the\n"
            "Jupiter in the fifth house gives children.\n"
            "brvnx\n"
            "\n"
            "Saturn in the tenth house gives profession.\n"
        )
        report = ocr_cleaning_report(raw, work="BPHS")
        assert report.work == "BPHS"
        assert report.total_lines == 7  # blank lines are not counted
        assert report.dropped_lines == 3
        assert report.kept_lines == 4
        assert report.dropped_fraction == pytest.approx(3 / 7)
        assert report.by_reason.get("numbers_punctuation_only") == 1
        assert report.by_reason.get("junk_ocr_word") == 1
        assert report.by_reason.get("consonant_cluster") == 1

    def test_report_empty_text(self):
        report = ocr_cleaning_report("", work="BPHS")
        assert report.total_lines == 0
        assert report.dropped_lines == 0
        assert report.dropped_fraction == 0.0

    def test_ingest_attaches_per_work_ocr_report(self, tmp_path):
        corpus = tmp_path / "corpus"
        work_dir = corpus / "bphs"
        work_dir.mkdir(parents=True)
        (work_dir / "meta.json").write_text(
            json.dumps(
                {"work": "BPHS", "translator": "R. Santhanam", "license": "public domain"}
            ),
            encoding="utf-8",
        )
        (work_dir / "bphs.txt").write_text(
            "Chapter 1, Verse 1: The Sun in the first house gives career success.\n"
            "12345\n"
            "Chapter 1, Verse 2: The Moon in the second house gives wealth.\n",
            encoding="utf-8",
        )
        result = ingest_corpus(corpus, tmp_path / "out")
        assert len(result.reports) == 1
        ocr = result.reports[0].ocr
        assert ocr is not None
        assert ocr.work == "BPHS"
        assert ocr.total_lines == 3
        assert ocr.dropped_lines == 1
        assert ocr.dropped_fraction == pytest.approx(1 / 3)

    def test_real_corpus_drop_rates(self):
        """BPHS drops ~46.8% of lines, ~32.2% overall (thresholds
        untouched); ranges pin the behaviour without freezing exact
        counts to future corpus edits."""
        root = Path("corpus")
        assert (root / "bphs").is_dir()
        total = dropped = 0
        bphs_total = bphs_dropped = 0
        for work_dir in sorted(p for p in root.iterdir() if p.is_dir()):
            text = "".join(
                f.read_text(encoding="utf-8")
                for f in sorted(
                    list(work_dir.glob("*.txt")) + list(work_dir.glob("*.md"))
                )
            )
            meta = json.loads((work_dir / "meta.json").read_text(encoding="utf-8"))
            report = ocr_cleaning_report(text, work=meta["work"])
            total += report.total_lines
            dropped += report.dropped_lines
            if meta["work"] == "BPHS":
                bphs_total = report.total_lines
                bphs_dropped = report.dropped_lines
        assert 0.40 < bphs_dropped / bphs_total < 0.55
        assert 0.28 < dropped / total < 0.38
