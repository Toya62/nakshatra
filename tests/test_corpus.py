"""
Tests for the corpus ingestion two-tier chunker and license gate.
"""

from __future__ import annotations

import json

import pytest

from nakshatra.ai.corpus import (
    MAX_CHUNK_CHARS,
    IngestResult,
    chunk_text,
    ingest_corpus,
    tag_topics,
)


class TestVerseHeaderParsing:
    """Tier 1: strict verse header regex parsing."""

    def test_chapter_verse_header(self):
        text = "Chapter 1, Verse 2:\nThe Sun in the first house gives brilliance."
        chunks, stats = chunk_text(text, work="BPHS", source_file="bphs.txt")
        assert stats["verse"] >= 1
        chunk = chunks[0]
        assert chunk.chapter == "1"
        assert chunk.verse == "2"
        assert chunk.tier == "verse"
        assert "Sun" in chunk.text
        assert "first house" in chunk.text

    def test_chapter_shloka_variant(self):
        text = "Ch. 3, Shloka 5: Mars aspecting the 7th house."
        chunks, _ = chunk_text(text, work="Phaladeepika", source_file="phal.md")
        assert chunks[0].chapter == "3"
        assert chunks[0].verse == "5"
        assert chunks[0].tier == "verse"

    def test_verse_only_header(self):
        text = "Verse 12:\nJupiter in the 5th house blesses one with children."
        chunks, _ = chunk_text(text, work="Brihat Jataka", source_file="bj.txt")
        assert chunks[0].verse == "12"
        assert chunks[0].chapter == ""  # no chapter context yet

    def test_decimal_header(self):
        text = "3.12: Saturn in the 10th house gives authority."
        chunks, _ = chunk_text(text, work="Saravali", source_file="saravali.txt")
        assert chunks[0].chapter == "3"
        assert chunks[0].verse == "12"

    def test_multiple_verses(self):
        text = (
            "Chapter 2, Verse 1: First verse about the Moon.\n"
            "Chapter 2, Verse 2: Second verse about Mars."
        )
        chunks, stats = chunk_text(text, work="BPHS", source_file="bphs.txt")
        assert stats["verse"] == 2
        assert chunks[0].verse == "1"
        assert chunks[1].verse == "2"
        assert chunks[0].chapter == "2"
        assert chunks[1].chapter == "2"

    def test_chapter_only_header_updates_context(self):
        text = (
            "Chapter 4\n"
            "Verse 1: Text in chapter 4.\n"
            "Verse 2: Also in chapter 4."
        )
        chunks, _ = chunk_text(text, work="BPHS", source_file="bphs.txt")
        assert all(c.chapter == "4" for c in chunks)

    def test_sloka_spelling(self):
        text = "Sloka 7: The ascendant lord determines the chart's strength."
        chunks, _ = chunk_text(text, work="Phaladeepika", source_file="phal.txt")
        assert chunks[0].verse == "7"


class TestFallbackParagraphChunking:
    """Tier 2: paragraph chunker for texts without verse numbering."""

    def test_no_headers_produces_paragraph_chunks(self):
        paragraphs = [
            f"Paragraph {i} about planetary positions in the natal chart. "
            "The placement of grahas in bhavas determines the yoga results."
            for i in range(20)
        ]
        text = "\n\n".join(paragraphs)
        chunks, stats = chunk_text(text, work="Crux", source_file="crux.txt")
        assert stats["paragraph"] >= 1
        assert all(c.tier == "paragraph" for c in chunks)
        assert all(c.verse == "" for c in chunks)

    def test_chunk_size_bounds(self):
        paragraphs = [
            f"Paragraph {i} contains classical commentary on the "
            "strength of planets in various houses and signs. "
            "The text discusses benefics and malefics in detail here."
            for i in range(30)
        ]
        text = "\n".join(paragraphs)
        chunks, _ = chunk_text(text, work="Crux", source_file="crux.txt")
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk.text) <= MAX_CHUNK_CHARS

    def test_long_verse_split_at_word_boundary(self):
        long_verse = " ".join(["word"] * 200)  # ~1000 chars
        text = f"Chapter 1, Verse 1:\n{long_verse}"
        chunks, _ = chunk_text(text, work="BPHS", source_file="bphs.txt")
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk.text) <= MAX_CHUNK_CHARS
        assert all(c.verse == "1" for c in chunks)
        assert all(c.chapter == "1" for c in chunks)

    def test_chapter_context_retained_in_fallback(self):
        text = (
            "Chapter 5\n"
            "Some prose text without verse numbering. " * 20
        )
        chunks, _ = chunk_text(text, work="BPHS", source_file="bphs.txt")
        assert len(chunks) >= 1
        assert all(c.chapter == "5" for c in chunks)
        assert all(c.tier == "paragraph" for c in chunks)

    def test_empty_text(self):
        chunks, stats = chunk_text("", work="BPHS", source_file="bphs.txt")
        assert chunks == []
        assert stats == {"verse": 0, "paragraph": 0}

    def test_whitespace_only_text(self):
        chunks, _ = chunk_text("   \n  \n ", work="BPHS", source_file="bphs.txt")
        assert chunks == []


class TestTopicTagging:
    """Topic extraction for BM25 keyword search."""

    def test_planet_topics(self):
        topics = tag_topics("The Sun and Moon are in Aries with Mars.")
        assert "Sun" in topics
        assert "Moon" in topics
        assert "Mars" in topics
        assert "Aries" not in topics  # signs are not topics (nakshatras are)

    def test_nakshatra_topics(self):
        topics = tag_topics("The Moon is in Rohini nakshatra.")
        assert "Rohini" in topics

    def test_house_topics(self):
        topics = tag_topics("The planet in the 5th house is strong.")
        assert "House 5" in topics
        topics = tag_topics("The 10th house lord is exalted.")
        assert "House 10" in topics

    def test_yoga_topics(self):
        topics = tag_topics("This forms Gaja Kesari and Neechabhanga Raja Yoga.")
        assert "Gaja Kesari" in topics
        assert "Neechabhanga" in topics

    def test_lagna_topic(self):
        topics = tag_topics("The Lagna lord is in the Ascendant.")
        assert "Lagna" in topics
        assert "Ascendant" in topics


class TestLicenseGate:
    """meta.json license gate for corpus works."""

    def test_missing_meta_json_fails(self, tmp_path):
        work_dir = tmp_path / "bphs"
        work_dir.mkdir()
        (work_dir / "text.txt").write_text("Chapter 1, Verse 1: Test.")
        with pytest.raises(ValueError, match="License gate"):
            ingest_corpus(tmp_path, tmp_path / "out")

    def test_empty_license_fails(self, tmp_path):
        work_dir = tmp_path / "bphs"
        work_dir.mkdir()
        (work_dir / "meta.json").write_text(
            json.dumps({"work": "BPHS", "translator": "Test", "license": ""})
        )
        (work_dir / "text.txt").write_text("Chapter 1, Verse 1: Test.")
        with pytest.raises(ValueError, match="License gate"):
            ingest_corpus(tmp_path, tmp_path / "out")

    def test_invalid_meta_json_fails(self, tmp_path):
        work_dir = tmp_path / "bphs"
        work_dir.mkdir()
        (work_dir / "meta.json").write_text("not json {{{")
        with pytest.raises(ValueError, match="Invalid meta.json"):
            ingest_corpus(tmp_path, tmp_path / "out")

    def test_missing_required_fields_fail(self, tmp_path):
        work_dir = tmp_path / "bphs"
        work_dir.mkdir()
        (work_dir / "meta.json").write_text(json.dumps({"translator": "Test"}))
        with pytest.raises(ValueError):
            ingest_corpus(tmp_path, tmp_path / "out")


class TestIngestCorpus:
    """Full corpus ingestion pipeline."""

    def _make_work(self, root, name: str, text: str) -> None:
        work_dir = root / name
        work_dir.mkdir(parents=True)
        (work_dir / "meta.json").write_text(json.dumps({
            "work": name.replace("-", " ").title(),
            "translator": "Test Translator",
            "license": "Public Domain",
            "source": "test",
        }))
        (work_dir / "text.txt").write_text(text)

    def test_full_ingestion(self, tmp_path):
        corpus = tmp_path / "corpus"
        corpus.mkdir()
        self._make_work(
            corpus, "bphs",
            "Chapter 1, Verse 1: The Sun in the first house.\n"
            "Chapter 1, Verse 2: The Moon in the second house.",
        )
        self._make_work(
            corpus, "phaladeepika",
            "Prose text about planetary strengths and weaknesses. " * 10,
        )
        out = tmp_path / "index"
        result = ingest_corpus(corpus, out)

        assert isinstance(result, IngestResult)
        assert result.total_files == 2
        assert result.total_chunks > 0
        assert len(result.reports) == 2

        report_by_work = {r.work: r for r in result.reports}
        assert "Bphs" in report_by_work
        assert report_by_work["Bphs"].verse_chunks == 2
        assert report_by_work["Bphs"].license == "Public Domain"
        assert report_by_work["Bphs"].translator == "Test Translator"

        # JSONL output
        jsonl_path = out / "corpus.jsonl"
        assert jsonl_path.exists()
        lines = jsonl_path.read_text().strip().split("\n")
        assert len(lines) == result.total_chunks
        first = json.loads(lines[0])
        assert first["work"] == "Bphs"
        assert first["chapter"] == "1"
        assert first["verse"] == "1"
        assert first["tier"] == "verse"
        assert "Sun" in first["topics"]

        # Manifest
        manifest = json.loads((out / "manifest.json").read_text())
        assert manifest["total_chunks"] == result.total_chunks

    def test_empty_corpus_dir_fails(self, tmp_path):
        with pytest.raises(ValueError, match="Corpus directory not found"):
            ingest_corpus(tmp_path / "nonexistent", tmp_path / "out")

    def test_work_with_no_text_files(self, tmp_path):
        corpus = tmp_path / "corpus"
        corpus.mkdir()
        work_dir = corpus / "empty"
        work_dir.mkdir()
        (work_dir / "meta.json").write_text(json.dumps({
            "work": "Empty", "license": "Public Domain"
        }))
        result = ingest_corpus(corpus, tmp_path / "out")
        assert result.total_chunks == 0
        assert result.total_files == 0
        assert result.reports[0].chunks == 0

    def test_char_offsets_are_approximate(self, tmp_path):
        corpus = tmp_path / "corpus"
        corpus.mkdir()
        self._make_work(
            corpus, "bphs",
            "Chapter 1, Verse 1: Short verse text for offset testing.",
        )
        result = ingest_corpus(corpus, tmp_path / "out")
        assert result.total_chunks >= 1
        lines = (tmp_path / "out" / "corpus.jsonl").read_text().strip().split("\n")
        chunk = json.loads(lines[0])
        assert chunk["char_start"] >= 0
        assert chunk["char_end"] >= chunk["char_start"]
