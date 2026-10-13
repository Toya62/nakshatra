"""
Nakshatra Text Splitter & Header Tracker
Adapted from Tencent/WeKnora (docreader/splitter).

Provides:
- TextSplitter: recursive character splitting with protected regex preservation (tables, code, math, shlokas).
- HeaderTracker: tracks table headers and markdown section headers across chunks.
- Smart chunk merging with configurable overlap and context preservation.
"""

from __future__ import annotations

import itertools
import logging
import re
from typing import Callable, Generic, Pattern, TypeVar, Union

from pydantic import BaseModel, Field, PrivateAttr

logger = logging.getLogger(__name__)

DEFAULT_CHUNK_SIZE = 512
DEFAULT_CHUNK_OVERLAP = 80

T = TypeVar("T")


def split_text_keep_separator(text: str, separator: str) -> list[str]:
    """Split text by separator, preserving separator at start of subsequent pieces."""
    parts = text.split(separator)
    result = [separator + s if i > 0 else s for i, s in enumerate(parts)]
    return [s for s in result if s]


def split_by_sep(sep: str, keep_sep: bool = True) -> Callable[[str], list[str]]:
    """Create a splitter function for a given separator string."""
    if keep_sep:
        return lambda text: split_text_keep_separator(text, sep)
    return lambda text: text.split(sep)


def split_by_char() -> Callable[[str], list[str]]:
    """Fallback splitter that breaks text into individual characters."""
    return lambda text: list(text)


class HeaderTrackerHook(BaseModel):
    """Configuration for a header pattern hook."""

    start_pattern: Pattern[str] = Field(description="Regex pattern for header start")
    end_pattern: Pattern[str] = Field(description="Regex pattern for header end")
    extract_header_fn: Callable[[re.Match[str]], str] = Field(
        default=lambda m: m.group(0),
        description="Function to extract header string from match",
    )
    priority: int = Field(default=0, description="Priority (higher matched first)")
    case_sensitive: bool = Field(default=True)

    def __init__(
        self,
        start_pattern: Union[str, Pattern[str]],
        end_pattern: Union[str, Pattern[str]],
        **kwargs,
    ):
        flags = 0 if kwargs.get("case_sensitive", True) else re.IGNORECASE
        if isinstance(start_pattern, str):
            start_pattern = re.compile(start_pattern, flags | re.DOTALL)
        if isinstance(end_pattern, str):
            end_pattern = re.compile(end_pattern, flags | re.DOTALL)
        super().__init__(
            start_pattern=start_pattern,
            end_pattern=end_pattern,
            **kwargs,
        )


_TABLE_ROW_PATTERN = re.compile(r"^\s*(?:\|[^|\n]*)+\|\s*$", re.MULTILINE)
_MARKDOWN_TABLE_PRIORITY = 15
_SECTION_HEADER_PRIORITY = 25

DEFAULT_CONFIGS: list[HeaderTrackerHook] = [
    # Markdown table header + divider line
    HeaderTrackerHook(
        start_pattern=r"^\s*(?:\|[^|\n]*)+[\r\n]+\s*(?:\|\s*:?-{3,}:?\s*)+\|?[\r\n]+$",
        end_pattern=r"^\s*$|^\s*[^|\s].*$",
        priority=_MARKDOWN_TABLE_PRIORITY,
        case_sensitive=False,
    ),
    # Markdown H1-H4 heading tracking
    HeaderTrackerHook(
        start_pattern=r"^\s*(#{1,4}\s+[^\r\n]+)[\r\n]*$",
        end_pattern=r"^\s*#{1,4}\s+.*$",
        extract_header_fn=lambda m: m.group(1).strip(),
        priority=_SECTION_HEADER_PRIORITY,
        case_sensitive=True,
    ),
]
DEFAULT_CONFIGS.sort(key=lambda x: -x.priority)


def _is_empty_table_header_row(header: str) -> bool:
    newline = header.find("\n")
    if newline < 0:
        return False
    row = header[:newline].strip()
    return bool(row) and all(ch in "| \t" for ch in row)


def _extract_separator_line(header: str) -> str:
    for line in header.split("\n"):
        if "---" in line:
            return line + "\n"
    return ""


def _table_row_column_count(line: str) -> int:
    line = line.strip()
    if not line.startswith("|"):
        return 0
    parts = line.split("|")
    if parts and parts[0].strip() == "":
        parts = parts[1:]
    if parts and parts[-1].strip() == "":
        parts = parts[:-1]
    return len(parts)


def _first_table_row_column_count(text: str) -> int:
    for line in text.split("\n"):
        line = line.strip()
        if line and _TABLE_ROW_PATTERN.match(line):
            return _table_row_column_count(line)
    return 0


def _header_table_column_count(header: str) -> int:
    for line in header.split("\n"):
        line = line.strip()
        if not line or "---" in line:
            continue
        count = _table_row_column_count(line)
        if count > 0:
            return count
    return 0


def _split_ends_with_paragraph_break(split: str) -> bool:
    trimmed = split.rstrip(" \t\r")
    return trimmed.endswith("\n\n") or trimmed.endswith("\r\n\r\n")


def header_column_mismatch(headers: str, next_unit: str) -> bool:
    header_cols = _header_table_column_count(headers)
    row_cols = _first_table_row_column_count(next_unit)
    return header_cols > 0 and row_cols > 0 and header_cols != row_cols


class HeaderTracker(BaseModel):
    """Tracks active table and section headers during text chunking."""

    header_hook_configs: list[HeaderTrackerHook] = Field(default_factory=lambda: list(DEFAULT_CONFIGS))
    active_headers: dict[int, str] = Field(default_factory=dict)
    ended_headers: set[int] = Field(default_factory=set)
    pending_extend: dict[int, bool] = Field(default_factory=dict)
    pending_table_break: bool = Field(default=False)
    header_ended_this_unit: bool = Field(default=False)

    def _clear_table_header(self) -> None:
        self.ended_headers.add(_MARKDOWN_TABLE_PRIORITY)
        self.active_headers.pop(_MARKDOWN_TABLE_PRIORITY, None)
        self.pending_extend.pop(_MARKDOWN_TABLE_PRIORITY, None)

    def update(self, split: str) -> dict[int, str]:
        """Update tracker state with current split text."""
        new_headers: dict[int, str] = {}
        self.header_ended_this_unit = False

        if self.pending_table_break:
            self.pending_table_break = False
            if _MARKDOWN_TABLE_PRIORITY in self.active_headers:
                if _first_table_row_column_count(split) > 0:
                    self._clear_table_header()
                    self.header_ended_this_unit = True
                else:
                    self._clear_table_header()

        for config in self.header_hook_configs:
            if config.priority in self.active_headers and config.end_pattern.search(split):
                self.ended_headers.add(config.priority)
                del self.active_headers[config.priority]
                self.pending_extend.pop(config.priority, None)

        if (
            _MARKDOWN_TABLE_PRIORITY in self.active_headers
            and not self.pending_extend.get(_MARKDOWN_TABLE_PRIORITY)
        ):
            if _split_ends_with_paragraph_break(split):
                self.pending_table_break = True
            else:
                header = self.active_headers[_MARKDOWN_TABLE_PRIORITY]
                row_cols = _first_table_row_column_count(split)
                header_cols = _header_table_column_count(header)
                if row_cols > 0 and header_cols > 0 and row_cols != header_cols:
                    self._clear_table_header()
                    self.header_ended_this_unit = True

        for priority in list(self.pending_extend.keys()):
            if priority in self.active_headers and _TABLE_ROW_PATTERN.search(split):
                sep = _extract_separator_line(self.active_headers[priority])
                self.active_headers[priority] = split + sep
            self.pending_extend.pop(priority, None)

        for config in self.header_hook_configs:
            if (
                config.priority not in self.active_headers
                and config.priority not in self.ended_headers
            ):
                match = config.start_pattern.search(split)
                if match:
                    header = config.extract_header_fn(match)
                    self.active_headers[config.priority] = header
                    new_headers[config.priority] = header
                    if _is_empty_table_header_row(header):
                        self.pending_extend[config.priority] = True

        if not self.active_headers:
            self.ended_headers.clear()

        return new_headers

    def get_headers(self) -> str:
        """Get concatenated active headers ordered by priority."""
        sorted_headers = sorted(self.active_headers.items(), key=lambda x: -x[0])
        return "\n".join([h for _, h in sorted_headers]) if sorted_headers else ""


DEFAULT_PROTECTED_REGEX: list[str] = [
    # LaTeX math formulas $$...$$
    r"\$\$[\s\S]*?\$\$",
    # Markdown images ![alt](url)
    r"!\[.*?\]\(.*?\)",
    # Markdown links [text](url)
    r"\[.*?\]\(.*?\)",
    # Table header + divider line
    r"[ ]*(?:\|[^|\n]*)+\|[\r\n]+\s*(?:\|\s*:?-{3,}:?\s*)+\|[\r\n]+",
    # Table rows
    r"[ ]*(?:\|[^|\n]*)+\|[\r\n]+",
    # Code blocks ```lang ... ```
    r"```[\s\S]*?```",
    # Sanskrit verse blocks enclosed in double danda ॥...॥
    r"॥[\s\S]*?॥",
]


class TextSplitter(BaseModel, Generic[T]):
    """
    Recursive text splitter with protected regex blocks and header tracking.

    Ensures tables, formulas, code, and shlokas are never sliced across chunk
    boundaries, while maintaining overlap and parent context.
    """

    chunk_size: int = Field(default=DEFAULT_CHUNK_SIZE, description="Max chunk character size")
    chunk_overlap: int = Field(default=DEFAULT_CHUNK_OVERLAP, description="Overlap between chunks")
    separators: list[str] = Field(default_factory=lambda: ["\n\n", "\n", ". ", "। ", " ", ""])
    protected_regex: list[str] = Field(default_factory=lambda: list(DEFAULT_PROTECTED_REGEX))
    len_function: Callable[[str], int] = Field(default=len, exclude=True)
    header_hook: HeaderTracker = Field(default_factory=HeaderTracker, exclude=True)

    _protected_fns: list[Pattern] = PrivateAttr()
    _split_fns: list[Callable] = PrivateAttr()

    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
        separators: list[str] | None = None,
        protected_regex: list[str] | None = None,
        length_function: Callable[[str], int] = len,
    ):
        if chunk_overlap > chunk_size:
            raise ValueError(
                f"chunk_overlap ({chunk_overlap}) cannot exceed chunk_size ({chunk_size})"
            )

        seps = separators if separators is not None else ["\n\n", "\n", ". ", "। ", " ", ""]
        protect = protected_regex if protected_regex is not None else DEFAULT_PROTECTED_REGEX

        super().__init__(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=seps,
            protected_regex=protect,
            len_function=length_function,
        )

        self._protected_fns = [re.compile(reg) for reg in self.protected_regex]
        non_empty_seps = [s for s in self.separators if s]
        self._split_fns = [split_by_sep(s) for s in non_empty_seps] + [split_by_char()]

    def split_text(self, text: str) -> list[tuple[int, int, str]]:
        """Split text into chunks returning [(start_char, end_char, chunk_text), ...]."""
        if not text:
            return []

        splits = self._split(text)
        protect = self._split_protected(text)
        splits = self._join(splits, protect)

        if "".join(splits) != text:
            # Fallback if join integrity drifts
            return [(0, len(text), text)]

        return self._merge(splits)

    def split_pieces(self, text: str) -> list[str]:
        """Split text returning chunk text strings only."""
        return [chunk_text for _, _, chunk_text in self.split_text(text)]

    def _split(self, text: str) -> list[str]:
        if self.len_function(text) <= self.chunk_size:
            return [text]

        splits: list[str] = []
        for split_fn in self._split_fns:
            splits = split_fn(text)
            if len(splits) > 1:
                break

        new_splits: list[str] = []
        for split in splits:
            if self.len_function(split) <= self.chunk_size:
                new_splits.append(split)
            else:
                new_splits.extend(self._split(split))
        return new_splits

    def _split_protected(self, text: str) -> list[tuple[int, str]]:
        matches = [
            (match.start(), match.end())
            for pattern in self._protected_fns
            for match in pattern.finditer(text)
        ]
        matches.sort(key=lambda x: (x[0], -x[1]))

        res: list[tuple[int, str]] = []

        def fold(initial: int, current: tuple[int, int]) -> int:
            if current[0] >= initial:
                if current[1] - current[0] < self.chunk_size:
                    res.append((current[0], text[current[0] : current[1]]))
                else:
                    logger.debug("Protected pattern exceeds chunk size: %s", current)
            return max(initial, current[1])

        list(itertools.accumulate(matches, fold, initial=-1))
        return res

    def _join(self, splits: list[str], protect: list[tuple[int, str]]) -> list[str]:
        j = 0
        point, start = 0, 0
        res: list[str] = []

        for split in splits:
            end = start + len(split)
            cur = split[point - start :]

            while j < len(protect):
                p_start, p_content = protect[j]
                p_end = p_start + len(p_content)

                if end <= p_start:
                    break

                if point < p_start:
                    local_end = p_start - point
                    res.append(cur[:local_end])
                    cur = cur[local_end:]
                    point = p_start

                res.append(p_content)
                j += 1

                if point < p_end:
                    local_start = p_end - point
                    cur = cur[local_start:]
                    point = p_end

                if not cur:
                    break

            if cur:
                res.append(cur)
                point = end

            start = end
        return res

    def _merge(self, splits: list[str]) -> list[tuple[int, int, str]]:
        chunks: list[tuple[int, int, str]] = []
        cur_chunk: list[tuple[int, int, str]] = []
        cur_len = 0
        cur_start, cur_end = 0, 0

        for split in splits:
            cur_end = cur_start + len(split)
            split_len = self.len_function(split)

            self.header_hook.update(split)
            if self.header_hook.header_ended_this_unit and len(cur_chunk) > 0:
                chunks.append((
                    cur_chunk[0][0],
                    cur_chunk[-1][1],
                    "".join([c[2] for c in cur_chunk]),
                ))
                cur_chunk = []
                cur_len = 0

            cur_headers = self.header_hook.get_headers()
            cur_headers_len = self.len_function(cur_headers)

            if cur_headers_len > self.chunk_size:
                cur_headers, cur_headers_len = "", 0

            if cur_len + split_len + cur_headers_len > self.chunk_size:
                if len(cur_chunk) > 0:
                    chunks.append((
                        cur_chunk[0][0],
                        cur_chunk[-1][1],
                        "".join([c[2] for c in cur_chunk]),
                    ))

                while cur_chunk and (
                    cur_len > self.chunk_overlap
                    or cur_len + split_len + cur_headers_len > self.chunk_size
                ):
                    first = cur_chunk.pop(0)
                    cur_len -= self.len_function(first[2])
                    if cur_chunk and first[0] == first[1]:
                        first = cur_chunk.pop(0)
                        cur_len -= self.len_function(first[2])

                if (
                    cur_headers
                    and split_len + cur_headers_len < self.chunk_size
                    and cur_headers not in split
                    and not header_column_mismatch(cur_headers, split)
                ):
                    next_start = cur_chunk[0][0] if cur_chunk else cur_start
                    cur_chunk.insert(0, (next_start, next_start, cur_headers + "\n"))
                    cur_len += cur_headers_len + 1

            cur_chunk.append((cur_start, cur_end, split))
            cur_len += split_len
            cur_start = cur_end

        if cur_chunk:
            chunks.append((
                cur_chunk[0][0],
                cur_chunk[-1][1],
                "".join([c[2] for c in cur_chunk]),
            ))

        return chunks
