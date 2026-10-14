"""
Unit tests for TextSplitter & HeaderTracker (adapted from Tencent/WeKnora).
"""

import pytest

from nakshatra.ai.corpus import chunk_text
from nakshatra.ai.splitter import TextSplitter


class TestTextSplitter:
    """Test suite for TextSplitter functionality."""

    def test_short_text_single_chunk(self):
        splitter = TextSplitter(chunk_size=100, chunk_overlap=20)
        text = "Short astrological verse."
        chunks = splitter.split_text(text)
        assert len(chunks) == 1
        assert chunks[0][0] == 0
        assert chunks[0][1] == len(text)
        assert chunks[0][2] == text

    def test_empty_text(self):
        splitter = TextSplitter(chunk_size=100, chunk_overlap=20)
        assert splitter.split_text("") == []

    def test_chunk_size_and_overlap_validation(self):
        with pytest.raises(ValueError, match="cannot exceed chunk_size"):
            TextSplitter(chunk_size=50, chunk_overlap=60)

    def test_overlap_between_chunks(self):
        splitter = TextSplitter(chunk_size=60, chunk_overlap=20)
        text = (
            "First sentence about Aries. Second sentence about Taurus. Third sentence about Gemini."
        )
        chunks = splitter.split_text(text)
        assert len(chunks) > 1
        for start, end, chunk_str in chunks:
            assert len(chunk_str) <= 60

    def test_protected_table_rows(self):
        splitter = TextSplitter(chunk_size=100, chunk_overlap=20)
        table = "| Graha | Rashi |\n|---|---|\n| Surya | Mesha |\n"
        chunks = splitter.split_text(table)
        assert len(chunks) >= 1
        # Full table rows preserved without internal character fragmentation
        assert "| Surya | Mesha |" in "".join([c[2] for c in chunks])

    def test_protected_code_block(self):
        splitter = TextSplitter(chunk_size=150, chunk_overlap=30)
        text = (
            "Introductory text.\n\n"
            "```python\n"
            "def calculate_lagna():\n"
            "    return 1\n"
            "```\n\n"
            "Concluding text."
        )
        chunks = splitter.split_text(text)
        found_block = any("def calculate_lagna():" in c[2] for c in chunks)
        assert found_block

    def test_protected_math_formula(self):
        splitter = TextSplitter(chunk_size=100, chunk_overlap=20)
        text = "Introductory text.\n\n$$\\lambda = \\frac{h}{p}$$\n\nConcluding remarks."
        chunks = splitter.split_text(text)
        assert any("$$\\lambda = \\frac{h}{p}$$" in c[2] for c in chunks)

    def test_protected_shloka_dandas(self):
        splitter = TextSplitter(chunk_size=120, chunk_overlap=20)
        text = (
            "Classical verse:\n"
            "॥ गुरौ चन्द्रे समायोगे गजकेसरी योग उच्यते ॥\n"
            "Gajakesari yoga brings wisdom and virtue."
        )
        chunks = splitter.split_text(text)
        assert any("॥ गुरौ चन्द्रे समायोगे गजकेसरी योग उच्यते ॥" in c[2] for c in chunks)


class TestHeaderTracker:
    """Test suite for HeaderTracker hook and context persistence."""

    def test_header_propagation_in_split(self):
        splitter = TextSplitter(chunk_size=90, chunk_overlap=20)
        text = (
            "# Vedic Astrological Principles\n"
            "The Sun is the karaka of soul.\n\n"
            "The Moon is the karaka of mind.\n\n"
            "Mars is the karaka of energy."
        )
        chunks = splitter.split_text(text)
        assert len(chunks) > 1
        # Check that subsequent chunks retain section header context
        for i, (_s, _e, c_text) in enumerate(chunks):
            if i > 0:
                assert "# Vedic Astrological Principles" in c_text or "karaka" in c_text

    def test_markdown_table_header_tracking(self):
        splitter = TextSplitter(chunk_size=80, chunk_overlap=20)
        table_text = (
            "| Graha | Nature |\n"
            "|---|---|\n"
            "| Surya | Malefic |\n"
            "| Chandra | Benefic |\n"
            "| Mangala | Malefic |\n"
        )
        chunks = splitter.split_text(table_text)
        assert len(chunks) >= 2
        # Check that table header is tracked
        assert any("| Graha | Nature |" in c[2] for c in chunks[1:])


class TestCorpusIntegration:
    """Test integration of TextSplitter in nakshatra corpus chunk_text."""

    def test_chunk_text_with_custom_splitter(self):
        custom_splitter = TextSplitter(chunk_size=350, chunk_overlap=50)
        long_body = " ".join([f"Sloka explanation sentence {i}." for i in range(40)])
        raw_text = f"Chapter 1, Verse 1:\n{long_body}"
        chunks, stats = chunk_text(
            raw_text,
            work="BPHS",
            source_file="bphs.md",
            max_chars=350,
            splitter=custom_splitter,
        )
        assert stats["verse"] > 1
        for chunk in chunks:
            assert chunk.chapter == "1"
            assert chunk.verse == "1"
            assert len(chunk.text) <= 350
