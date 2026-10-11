"""
Nakshatra Corpus Ingestion
Two-tier chunker for classical Vedic astrology texts.

Tier 1 (strict): verse header regex ("Chapter X, Verse Y:", "Ch. X, Shloka Y:",
"X.Y:") produces one chunk per verse with precise citation metadata.

Tier 2 (fallback): paragraph chunker with 300-600 character bounds, retaining
chapter context, for texts without machine-readable verse numbering.

License gate: every work directory under the corpus root must contain a
meta.json with work, translator, and license fields; ingestion fails without it.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from pydantic import BaseModel, Field

from nakshatra.core import NAKSHATRAS, VEDIC_PLANETS

MIN_CHUNK_CHARS = 300
MAX_CHUNK_CHARS = 600

# Classical yoga and technical terms for topic tagging
YOGA_TERMS = [
    "Pancha Mahapurusha", "Ruchaka", "Bhadra", "Hamsa", "Malavya", "Sasa",
    "Gaja Kesari", "Kemadruma", "Neechabhanga", "Sunapha", "Anapha",
    "Dhurdhura", "Chandra Mangala", "Adhi Yoga", "Budhaditya", "Vesi Yoga",
    "Vasi Yoga", "Ubhayachari", "Amala Yoga", "Dhana Yoga", "Raja Yoga",
    "Viparita Raja", "Maraka", "Yogakaraka", "Karakamsa", "Bhrigu Bindu",
    "Sade Sati", "Ashtama Shani", "Kantaka Shani", "Chandra Lagna",
]

# Bodies for topic tagging (grahas + nodes + angles)
TOPIC_BODIES = VEDIC_PLANETS + ["Rahu", "Ketu", "Lagna", "Ascendant"]

VERSE_HEADER_PATTERNS: list[re.Pattern[str]] = [
    # "Chapter 3, Verse 12:" / "Ch. 3, Shloka 12:" / "Chapter 3 - Verse 12:"
    re.compile(
        r"^\s*\[?\s*(?:chapter|ch\.?)\s*(?P<chapter>\d+)\s*[,.\-–—]?\s*"
        r"(?:verse|shloka|sloka|sutra|v\.?)\s*(?P<verse>\d+)\s*[:.\-–—]?\s*\]?\s*(?P<text>.*)$",
        re.IGNORECASE,
    ),
    # "Verse 12:" / "Shloka 12:" (chapter from surrounding context)
    re.compile(
        r"^\s*\[?\s*(?:verse|shloka|sloka|sutra)\s*(?P<verse>\d+)\s*[:.\-–—]?\s*\]?\s*(?P<text>.*)$",
        re.IGNORECASE,
    ),
    # "3.12:" decimal chapter.verse numbering (short lines only to avoid
    # false positives on decimals in prose)
    re.compile(
        r"^\s*(?P<chapter>\d+)\.(?P<verse>\d+)\s*[:.\-–—]?\s*(?P<text>\S.*)$",
    ),
]

CHAPTER_HEADER_PATTERN = re.compile(
    r"^\s*(?:#+\s*)?(?:chapter|ch\.?)\s*(?P<chapter>\d+)\s*[:.\-–—]?\s*$",
    re.IGNORECASE,
)


class CorpusChunk(BaseModel):
    """Single retrievable chunk of corpus text with citation metadata."""
    work: str
    chapter: str = Field(default="", description="Chapter number/label")
    verse: str = Field(default="", description="Verse number/label")
    text: str
    topics: list[str] = Field(default_factory=list)
    source_file: str
    char_start: int = Field(..., ge=0, description="Approximate offset in source file")
    char_end: int = Field(..., ge=0)
    tier: str = Field(..., description="'verse' (strict) or 'paragraph' (fallback)")


class WorkMeta(BaseModel):
    """Provenance metadata for a corpus work (license gate)."""
    work: str
    translator: str = ""
    license: str = Field(..., description="License of the translation (e.g. 'Public Domain')")
    source: str = ""


class IngestReport(BaseModel):
    """Per-work ingestion statistics."""
    work: str
    files: int
    chunks: int
    verse_chunks: int
    paragraph_chunks: int
    translator: str = ""
    license: str


class IngestResult(BaseModel):
    """Full corpus ingestion result."""
    reports: list[IngestReport] = Field(default_factory=list)
    total_chunks: int
    total_files: int


def _match_verse_header(line: str) -> re.Match[str] | None:
    """Try verse header patterns; decimal pattern limited to short lines."""
    for i, pattern in enumerate(VERSE_HEADER_PATTERNS):
        if i == 2 and len(line) > 100:
            continue
        match = pattern.match(line)
        if match:
            return match
    return None


def tag_topics(text: str) -> list[str]:
    """Extract topical keywords (grahas, nakshatras, houses, yogas) from text."""
    topics: set[str] = set()
    lower = text.lower()

    for body in TOPIC_BODIES:
        if re.search(rf"\b{re.escape(body.lower())}\b", lower):
            topics.add(body)

    for nakshatra, _lord in NAKSHATRAS:
        if re.search(rf"\b{re.escape(nakshatra.lower())}\b", lower):
            topics.add(nakshatra)

    for match in re.finditer(r"\b(\d{1,2})(?:st|nd|rd|th)\s+house\b", lower):
        topics.add(f"House {match.group(1)}")
    for match in re.finditer(r"\bhouse\s+(\d{1,2})\b", lower):
        topics.add(f"House {match.group(1)}")

    for term in YOGA_TERMS:
        if term.lower() in lower:
            topics.add(term)

    return sorted(topics)


def _split_into_pieces(body: str, min_chars: int = MIN_CHUNK_CHARS,
                       max_chars: int = MAX_CHUNK_CHARS) -> list[str]:
    """Split verse/paragraph text into pieces bounded by min/max characters.

    Greedily merges paragraphs up to max_chars; hard-splits oversized paragraphs
    at word boundaries. Short final pieces are kept intact (citation precision).
    """
    pieces: list[str] = []
    current: list[str] = []
    current_len = 0

    for para in body.split("\n"):
        para = para.strip()
        if not para:
            continue
        if current and current_len + len(para) + 1 > max_chars:
            pieces.append(" ".join(current))
            current = []
            current_len = 0
        if len(para) > max_chars:
            words = para.split()
            while words:
                word_batch: list[str] = []
                batch_len = 0
                while words and batch_len + len(words[0]) + 1 <= max_chars:
                    word = words.pop(0)
                    word_batch.append(word)
                    batch_len += len(word) + 1
                if word_batch:
                    pieces.append(" ".join(word_batch))
            continue
        current.append(para)
        current_len += len(para) + 1

    if current:
        pieces.append(" ".join(current))
    return [p for p in pieces if p]


def chunk_text(
    text: str,
    work: str,
    source_file: str,
    min_chars: int = MIN_CHUNK_CHARS,
    max_chars: int = MAX_CHUNK_CHARS,
) -> tuple[list[CorpusChunk], dict[str, int]]:
    """Chunk a corpus text into citable pieces using the two-tier strategy.

    Returns (chunks, stats) where stats counts verse-tier vs paragraph-tier chunks.
    """
    chunks: list[CorpusChunk] = []
    stats = {"verse": 0, "paragraph": 0}

    chapter_ctx = ""
    verse_ctx = ""
    saw_verse_header = False
    buf: list[str] = []
    buf_start = 0
    offset = 0

    def flush(tier: str) -> None:
        nonlocal buf, buf_start, verse_ctx
        body = "\n".join(buf).strip()
        buf = []
        if not body:
            return
        pieces = _split_into_pieces(body, min_chars, max_chars)
        for piece in pieces:
            chunk = CorpusChunk(
                work=work,
                chapter=chapter_ctx,
                verse=verse_ctx,
                text=piece,
                topics=tag_topics(piece),
                source_file=source_file,
                char_start=buf_start,
                char_end=buf_start + len(body),
                tier=tier,
            )
            chunks.append(chunk)
            stats[tier] += 1

    for line in text.splitlines():
        line_len = len(line) + 1  # +1 for the newline

        chapter_match = CHAPTER_HEADER_PATTERN.match(line)
        if chapter_match:
            flush("verse" if saw_verse_header else "paragraph")
            chapter_ctx = chapter_match.group("chapter")
            offset += line_len
            continue

        verse_match = _match_verse_header(line)
        if verse_match:
            flush("verse" if saw_verse_header else "paragraph")
            saw_verse_header = True
            groups = verse_match.groupdict()
            chapter_ctx = groups.get("chapter") or chapter_ctx
            verse_ctx = groups["verse"]
            trailing = verse_match.group("text").strip()
            buf = [trailing] if trailing else []
            buf_start = offset if trailing else offset + line_len
            offset += line_len
            continue

        buf.append(line)
        offset += line_len

    flush("verse" if saw_verse_header else "paragraph")
    return chunks, stats


def _load_work_meta(work_dir: Path) -> WorkMeta:
    """Load and validate a work's meta.json (license gate)."""
    meta_path = work_dir / "meta.json"
    if not meta_path.is_file():
        raise ValueError(
            f"License gate: missing meta.json in {work_dir}. "
            "Each corpus work directory must contain meta.json with "
            "'work', 'translator', and 'license' fields."
        )
    try:
        data = json.loads(meta_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid meta.json in {work_dir}: {e}") from e
    try:
        meta = WorkMeta(**data)
    except Exception as e:
        raise ValueError(f"Invalid meta.json fields in {work_dir}: {e}") from e
    if not meta.license.strip():
        raise ValueError(f"License gate: empty 'license' in {meta_path}")
    return meta


def ingest_corpus(corpus_dir: str | Path, out_dir: str | Path) -> IngestResult:
    """Ingest all works under corpus_dir into out_dir (JSONL + manifest).

    Directory layout:
        corpus/
          bphs/
            meta.json      # work, translator, license (license gate)
            bphs_text.txt
          phaladeepika/
            meta.json
            phaladeepika.txt

    Output:
        out_dir/corpus.jsonl   # one CorpusChunk per line
        out_dir/manifest.json  # IngestResult summary
    """
    corpus_path = Path(corpus_dir)
    if not corpus_path.is_dir():
        raise ValueError(f"Corpus directory not found: {corpus_path}")

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    reports: list[IngestReport] = []
    all_chunks: list[CorpusChunk] = []
    total_files = 0

    for work_dir in sorted(p for p in corpus_path.iterdir() if p.is_dir()):
        meta = _load_work_meta(work_dir)  # license gate

        work_chunks: list[CorpusChunk] = []
        work_files = 0
        text_files = sorted(
            list(work_dir.glob("*.txt")) + list(work_dir.glob("*.md"))
        )
        for text_file in text_files:
            text = text_file.read_text(encoding="utf-8")
            chunks, _stats = chunk_text(
                text, work=meta.work, source_file=text_file.name
            )
            work_chunks.extend(chunks)
            work_files += 1

        total_files += work_files
        all_chunks.extend(work_chunks)
        reports.append(
            IngestReport(
                work=meta.work,
                files=work_files,
                chunks=len(work_chunks),
                verse_chunks=sum(1 for c in work_chunks if c.tier == "verse"),
                paragraph_chunks=sum(1 for c in work_chunks if c.tier == "paragraph"),
                translator=meta.translator,
                license=meta.license,
            )
        )

    jsonl_path = out_path / "corpus.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as f:
        for chunk in all_chunks:
            f.write(chunk.model_dump_json() + "\n")

    result = IngestResult(
        reports=reports,
        total_chunks=len(all_chunks),
        total_files=total_files,
    )
    (out_path / "manifest.json").write_text(
        json.dumps(result.model_dump(), indent=2), encoding="utf-8"
    )
    return result
