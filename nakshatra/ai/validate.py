"""
Post-generation validation of LLM answers against chart ground truth.

Step 1 of Nakshatra Task 13 (AI accuracy). Deterministic and offline:
no LLM calls, no network. The validator checks every chart claim an
answer states — planet house/sign/nakshatra/degree, dasha dates, yoga
presence, Sade Sati phase — against the compact chart context the LLM
itself received, and checks every ``[n]`` citation for range AND for
support by the cited chunk text.

Usage::

    result = validate_answer(answer, chart_context, results)
    answer_text = result.cleaned_answer          # unsupported citations removed
    citations = extract_citations(answer_text, results)  # only kept citations
    result.flags                                # mismatches / dropped citations

Design notes
------------
* A claim is only checked when the answer states it in a form the
  validator can attribute: a planet name near a house/sign/nakshatra
  mention in the same sentence, a date attributed to a named dasha
  period, a "X Yoga is present/absent" statement, or a Sade Sati
  statement. Unattributed dates must still fall inside *some* known
  dasha range (or be a transit-window event date / the birth date).
* A citation is supported when the cited chunk shares a distinctive
  astrological term with the citing sentence (planet / sign /
  nakshatra / yoga / house number) or at least 30% of the sentence's
  content words. Sentences with fewer than 4 content words are too
  generic to judge and count as supported. This is the same rule the
  golden eval (``tests/test_ai_eval.py``) implements independently as
  its scoring instrument.
* The validator never rewrites chart claims: a wrong house/sign/date
  stays in the text and is *flagged*; only unsupported/out-of-range
  citation markers are *dropped* from the text.
* The fallback synthesizer is deliberately NOT validated: it quotes
  classical verses verbatim, and verse text is not a claim about the
  seeker's chart. Validation is wired into ``LLMSynthesizer.synthesize``
  (the live LLM path) only.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Any

from pydantic import BaseModel, Field

from nakshatra.ai.retrieval import SearchResult

__all__ = [
    "ValidationFlag",
    "ValidationResult",
    "validate_answer",
    "chunk_supports_sentence",
]

# ---------------------------------------------------------------------------
# Vocabularies
# ---------------------------------------------------------------------------

PLANETS = [
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
]

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha",
    "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana",
    "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]

# Devanagari names (Nepali answers) mapped to the English canonical names.
DEVANAGARI_PLANETS = {
    "सूर्य": "Sun", "चन्द्र": "Moon", "चन्द्रमा": "Moon", "मङ्गल": "Mars",
    "मंगल": "Mars", "बुध": "Mercury", "बृहस्पति": "Jupiter", "गुरु": "Jupiter",
    "शुक्र": "Venus", "शनि": "Saturn", "राहु": "Rahu", "केतु": "Ketu",
}

DEVANAGARI_SIGNS = {
    "मेष": "Aries", "वृष": "Taurus", "वृषभ": "Taurus", "मिथुन": "Gemini",
    "कर्कट": "Cancer", "कर्क": "Cancer", "सिंह": "Leo", "कन्या": "Virgo",
    "तुला": "Libra", "वृश्चिक": "Scorpio", "धनु": "Sagittarius",
    "मकर": "Capricorn", "कुम्भ": "Aquarius", "मीन": "Pisces",
}

_NODE_NAMES = {"North Node": "Rahu", "South Node": "Ketu"}

_STOPWORDS = {
    "the", "a", "an", "is", "in", "of", "and", "to", "your", "you", "are", "it",
    "this", "that", "with", "for", "from", "on", "as", "at", "by", "be", "has",
    "have", "will", "when", "what", "how", "my", "its", "or", "not", "no",
}

# Distinctive terms for the citation-support judge.
_DISTINCTIVE_TERMS = (
    [p.lower() for p in PLANETS]
    + [s.lower() for s in SIGNS]
    + [n.lower() for n in NAKSHATRAS]
    + ["hamsa", "gaja kesari", "budhaditya", "malavya", "bhadra", "sasa",
       "raja yoga", "dhana yoga", "sade sati", "mahadasha", "antardasha",
       "dasha", "yoga", "upaya", "remedy"]
)

# Degrees stated in an answer are usually rounded; accept this tolerance.
DEGREE_TOLERANCE = 0.6
# A house/sign/nakshatra mention pairs with a planet mention within this
# many characters in the same sentence (or anywhere if it is the only
# planet mentioned in the sentence).
_PAIR_WINDOW = 60


# ---------------------------------------------------------------------------
# Result models
# ---------------------------------------------------------------------------

class ValidationFlag(BaseModel):
    """One problem found in an answer."""

    kind: str = Field(description=(
        "placement_mismatch | date_mismatch | date_unverifiable | "
        "yoga_mismatch | sade_sati_mismatch | citation_out_of_range | "
        "citation_unsupported"))
    message: str
    detail: str = ""


class ValidationResult(BaseModel):
    """Outcome of validating one answer against a chart context."""

    valid: bool
    flags: list[ValidationFlag] = Field(default_factory=list)
    cleaned_answer: str
    citations_kept: list[int] = Field(default_factory=list)
    citations_dropped: list[int] = Field(default_factory=list)
    claims_checked: int = 0
    claims_supported: int = 0
    citations_checked: int = 0
    citations_supported: int = 0
    citation_precision: float | None = None
    date_placement_match_rate: float | None = None


# ---------------------------------------------------------------------------
# Chart facts
# ---------------------------------------------------------------------------

def _parse_iso_date(value: Any) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def _clean_lord(lord: Any) -> str:
    if not isinstance(lord, str):
        return ""
    return _NODE_NAMES.get(lord, lord)


class _ChartFacts:
    """Ground truth extracted from a chart-context dict."""

    def __init__(self, chart: dict[str, Any] | None) -> None:
        self.planets: dict[str, dict[str, Any]] = {}
        self.lagna_sign: str | None = None
        self.dasha_ranges: list[tuple[date, date, str]] = []
        # Attributed periods: (level, lord) -> (start, end); ad/pd keyed
        # with their parent lords so "Mercury-Moon AD" resolves exactly.
        self.md_by_lord: dict[str, tuple[date, date]] = {}
        self.ad_by_lords: dict[tuple[str, str], tuple[date, date]] = {}
        self.pd_by_lords: dict[tuple[str, str, str], tuple[date, date]] = {}
        self.has_dashas = False
        self.yogas: list[str] = []
        self.has_yogas = False
        self.sade_sati_active: bool | None = None
        self.sade_sati_phase: str | None = None
        self.birth_date: date | None = None
        self.transit_event_dates: set[date] = set()
        if not isinstance(chart, dict):
            return
        self._planets(chart)
        self._dashas(chart)
        self._yogas(chart)
        self._transits(chart)
        bdata = chart.get("birth_data")
        if isinstance(bdata, dict):
            try:
                self.birth_date = date(int(bdata["year"]), int(bdata.get("month", 1)),
                                       int(bdata.get("day", 1)))
            except (ValueError, TypeError, KeyError):
                self.birth_date = None

    def _planets(self, chart: dict[str, Any]) -> None:
        bodies: list[dict[str, Any]] = []
        planets = chart.get("planets")
        if isinstance(planets, list):
            bodies.extend(p for p in planets if isinstance(p, dict))
        for key in ("rahu", "ketu"):
            node = chart.get(key)
            if isinstance(node, dict):
                bodies.append(node)
        for p in bodies:
            name = p.get("name")
            if isinstance(name, str):
                self.planets[_NODE_NAMES.get(name, name)] = {
                    "house": p.get("house"),
                    "sign": p.get("sign"),
                    "nakshatra": p.get("nakshatra"),
                    "degree": p.get("degree_in_sign"),
                    "retrograde": bool(p.get("retrograde")),
                }
        asc = chart.get("ascendant")
        if isinstance(asc, dict) and isinstance(asc.get("sign"), str):
            self.lagna_sign = asc["sign"]
        elif isinstance(asc, str):
            self.lagna_sign = asc
        if self.lagna_sign:
            self.planets.setdefault("Lagna", {
                "house": 1, "sign": self.lagna_sign, "nakshatra": None,
                "degree": None, "retrograde": False,
            })

    def _dashas(self, chart: dict[str, Any]) -> None:
        dashas = chart.get("dashas")
        if not isinstance(dashas, dict):
            return
        for key in ("current_md", "current_ad", "current_pd"):
            period = dashas.get(key)
            if isinstance(period, dict):
                self._add_period(period, key)
        for md in dashas.get("mahadashas") or []:
            if not isinstance(md, dict):
                continue
            md_lord = _clean_lord(md.get("lord"))
            md_range = self._add_period(md, "mahadasha")
            for ad in md.get("subs") or []:
                if not isinstance(ad, dict):
                    continue
                ad_lord = _clean_lord(ad.get("lord"))
                ad_range = self._add_period(ad, "antardasha")
                if md_range and ad_range:
                    self.ad_by_lords[(md_lord, ad_lord)] = ad_range
                for pd in ad.get("subs") or []:
                    if not isinstance(pd, dict):
                        continue
                    pd_lord = _clean_lord(pd.get("lord"))
                    pd_range = self._add_period(pd, "pratyantardasha")
                    if md_range and ad_range and pd_range:
                        self.pd_by_lords[(md_lord, ad_lord, pd_lord)] = pd_range

    def _add_period(self, period: dict[str, Any], label: str) -> tuple[date, date] | None:
        start = _parse_iso_date(period.get("start"))
        end = _parse_iso_date(period.get("end"))
        if start is None or end is None:
            return None
        self.has_dashas = True
        lord = _clean_lord(period.get("lord"))
        self.dasha_ranges.append((start, end, f"{lord} {label}"))
        if label in ("current_md", "mahadasha"):
            self.md_by_lord.setdefault(lord, (start, end))
        return (start, end)

    def _yogas(self, chart: dict[str, Any]) -> None:
        yogas = chart.get("yogas")
        if isinstance(yogas, list) and yogas:
            self.has_yogas = True
            for y in yogas:
                if isinstance(y, dict) and y.get("name"):
                    self.yogas.append(str(y["name"]))
                elif isinstance(y, str):
                    self.yogas.append(y)

    def _transits(self, chart: dict[str, Any]) -> None:
        transits = chart.get("transits")
        if not isinstance(transits, dict):
            return
        ss = transits.get("sade_sati")
        if isinstance(ss, dict):
            if isinstance(ss.get("is_active"), bool):
                self.sade_sati_active = ss["is_active"]
            if isinstance(ss.get("phase"), str):
                self.sade_sati_phase = ss["phase"]
        window = transits.get("window")
        if isinstance(window, dict):
            for event in window.get("events") or []:
                if isinstance(event, dict):
                    d = _parse_iso_date(event.get("date"))
                    if d is not None:
                        self.transit_event_dates.add(d)
            for period in window.get("chandrashtama_periods") or []:
                if isinstance(period, dict):
                    s = _parse_iso_date(period.get("start_date"))
                    e = _parse_iso_date(period.get("end_date"))
                    if s is not None and e is not None:
                        self.dasha_ranges.append((s, e, "Chandrashtama"))


# ---------------------------------------------------------------------------
# Sentence / claim extraction
# ---------------------------------------------------------------------------

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?।])\s+|\n+")
_ISO_DATE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
_HOUSE_RE = re.compile(r"house\s+(\d{1,2})\b|(\d{1,2})(?:st|nd|rd|th)\s+house\b",
                       re.IGNORECASE)
_DEGREE_RE = re.compile(r"(\d+(?:\.\d+)?)\s*°")
_YOGA_RE = re.compile(r"([A-Za-z][\w\-]*(?:\s+[A-Za-z][\w\-]*){0,2})\s+Yoga\b")


def _sentences(answer: str) -> list[str]:
    return [s.strip() for s in _SENTENCE_SPLIT.split(answer or "") if s.strip()]


def _find_all(pattern: str, sentence: str) -> list[tuple[int, str]]:
    return [(m.start(), m.group(0)) for m in re.finditer(pattern, sentence)]


def _planet_mentions(sentence: str) -> list[tuple[int, str]]:
    """(position, canonical planet name) for every planet mention."""
    mentions: list[tuple[int, str]] = []
    for planet in PLANETS:
        for m in re.finditer(rf"\b{planet}\b", sentence):
            mentions.append((m.start(), planet))
    for dev, planet in DEVANAGARI_PLANETS.items():
        start = 0
        while True:
            idx = sentence.find(dev, start)
            if idx < 0:
                break
            mentions.append((idx, planet))
            start = idx + len(dev)
    # Lagna / Ascendant as a pseudo-planet (sign claim only, house is 1).
    for m in re.finditer(r"\b(?:Lagna|Ascendant)\b", sentence):
        mentions.append((m.start(), "Lagna"))
    mentions.sort()
    return mentions


def _sign_mentions(sentence: str) -> list[tuple[int, str]]:
    mentions: list[tuple[int, str]] = []
    for sign in SIGNS:
        for m in re.finditer(rf"\b{sign}\b", sentence):
            mentions.append((m.start(), sign))
    for dev, sign in DEVANAGARI_SIGNS.items():
        start = 0
        while True:
            idx = sentence.find(dev, start)
            if idx < 0:
                break
            mentions.append((idx, sign))
            start = idx + len(dev)
    mentions.sort()
    return mentions


def _nakshatra_mentions(sentence: str) -> list[tuple[int, str]]:
    mentions: list[tuple[int, str]] = []
    for nak in NAKSHATRAS:
        for m in re.finditer(rf"\b{nak}\b", sentence):
            mentions.append((m.start(), nak))
    mentions.sort()
    return mentions


def _check_claim(flags: list[ValidationFlag], result: ValidationResult,
                 kind: str, ok: bool, message: str, detail: str = "") -> None:
    result.claims_checked += 1
    if ok:
        result.claims_supported += 1
    else:
        flags.append(ValidationFlag(kind=kind, message=message, detail=detail))


def _check_placements(answer: str, facts: _ChartFacts,
                      flags: list[ValidationFlag], result: ValidationResult) -> None:
    seen: set[tuple[str, str, str]] = set()
    for sentence in _sentences(answer):
        planets = _planet_mentions(sentence)
        if not planets:
            continue
        houses = [(m.start(), int(m.group(1) or m.group(2)))
                  for m in _HOUSE_RE.finditer(sentence)]
        signs = _sign_mentions(sentence)
        nakshatras = _nakshatra_mentions(sentence)
        degrees = [(m.start(), float(m.group(1))) for m in _DEGREE_RE.finditer(sentence)]
        retro_m = re.search(r"\bretrograde\b", sentence.lower())
        direct_m = re.search(r"\bdirect\b", sentence.lower())
        for p_pos, planet in planets:
            truth = facts.planets.get(planet)
            if truth is None:
                continue
            only_planet = len({p for _, p in planets}) == 1

            def _near(q_pos: int) -> bool:
                return only_planet or abs(q_pos - p_pos) <= _PAIR_WINDOW

            for q_pos, house in houses:
                if not _near(q_pos):
                    continue
                key = (planet, "house", str(house))
                if key in seen:
                    continue
                seen.add(key)
                _check_claim(
                    flags, result, "placement_mismatch",
                    truth.get("house") == house,
                    f"{planet} stated in House {house} but chart has House {truth.get('house')}",
                    sentence,
                )
            for q_pos, sign in signs:
                if not _near(q_pos):
                    continue
                key = (planet, "sign", sign)
                if key in seen:
                    continue
                seen.add(key)
                _check_claim(
                    flags, result, "placement_mismatch",
                    truth.get("sign") == sign,
                    f"{planet} stated in {sign} but chart has {truth.get('sign')}",
                    sentence,
                )
            for q_pos, nak in nakshatras:
                if not _near(q_pos):
                    continue
                key = (planet, "nakshatra", nak)
                if key in seen:
                    continue
                seen.add(key)
                _check_claim(
                    flags, result, "placement_mismatch",
                    truth.get("nakshatra") == nak,
                    f"{planet} stated in {nak} nakshatra but chart has {truth.get('nakshatra')}",
                    sentence,
                )
            for q_pos, deg in degrees:
                if not _near(q_pos) or truth.get("degree") is None:
                    continue
                key = (planet, "degree", f"{deg:.1f}")
                if key in seen:
                    continue
                seen.add(key)
                _check_claim(
                    flags, result, "placement_mismatch",
                    abs(deg - float(truth["degree"])) <= DEGREE_TOLERANCE,
                    f"{planet} stated at {deg}° but chart has {truth.get('degree'):.2f}°",
                    sentence,
                )
            if retro_m and _near(retro_m.start()):
                key = (planet, "retrograde", "retrograde")
                if key not in seen:
                    seen.add(key)
                    _check_claim(
                        flags, result, "placement_mismatch",
                        bool(truth.get("retrograde")),
                        f"{planet} stated retrograde but chart has it direct",
                        sentence,
                    )
            if direct_m and _near(direct_m.start()):
                key = (planet, "retrograde", "direct")
                if key not in seen:
                    seen.add(key)
                    _check_claim(
                        flags, result, "placement_mismatch",
                        not truth.get("retrograde"),
                        f"{planet} stated direct but chart has it retrograde",
                        sentence,
                    )


_DASHA_LEVEL_RE = re.compile(
    r"(pratyantardasha|antardasha|mahadasha|dasha"
    r"|प्रत्यन्तर्दशा|अन्तर्दशा|महादशा|दशा)",
    re.IGNORECASE,
)
_DASHA_LEVEL_BY_WORD = {
    "pratyantardasha": "pd", "प्रत्यन्तर्दशा": "pd",
    "antardasha": "ad", "अन्तर्दशा": "ad",
    "mahadasha": "md", "महादशा": "md",
    "dasha": "any", "दशा": "any",
}


def _check_dates(answer: str, facts: _ChartFacts,
                 flags: list[ValidationFlag], result: ValidationResult) -> None:
    for sentence in _sentences(answer):
        parsed_dates = [(m.start(), _parse_iso_date(m.group(0)))
                        for m in _ISO_DATE.finditer(sentence)]
        dates = [(pos, d) for pos, d in parsed_dates if d is not None]
        if not dates:
            continue
        # "X to Y" ranges must not end before they start.
        for m in re.finditer(
                r"(\d{4}-\d{2}-\d{2})\s*(?:to|–|—|-)\s*(\d{4}-\d{2}-\d{2})", sentence):
            start, end = _parse_iso_date(m.group(1)), _parse_iso_date(m.group(2))
            if start is not None and end is not None:
                _check_claim(
                    flags, result, "date_mismatch", end >= start,
                    f"Date range {m.group(1)} to {m.group(2)} ends before it starts",
                    sentence,
                )
        if not facts.has_dashas and not facts.transit_event_dates:
            for _pos, d in dates:
                _check_claim(
                    flags, result, "date_unverifiable", False,
                    f"Date {d.isoformat()} cannot be checked: no dasha data in chart context",
                    sentence,
                )
            continue
        level_marks = [(m.start(), _DASHA_LEVEL_BY_WORD[m.group(1).lower()])
                       for m in _DASHA_LEVEL_RE.finditer(sentence)]
        planets = _planet_mentions(sentence)
        for pos, d in dates:
            # Attribute the date to the nearest dasha-level keyword: the
            # closest one before it, else the first one after it. A sentence
            # may state both an MD and an AD range; per-date attribution
            # keeps the MD dates from being judged against the AD range.
            before = [mark for mark in level_marks if mark[0] < pos]
            after = [mark for mark in level_marks if mark[0] >= pos]
            if before:
                level, anchor = before[-1][1], before[-1][0]
            elif after:
                level, anchor = after[0][1], after[0][0]
            else:
                level, anchor = None, pos
            lords = {p for p_pos, p in planets
                     if abs(p_pos - pos) <= _PAIR_WINDOW
                     or abs(p_pos - anchor) <= 40}
            ok, where = _date_supported(d, lords, level, facts)
            _check_claim(
                flags, result, "date_mismatch", ok,
                f"Date {d.isoformat()} is not inside any known {where}" if not ok else "",
                sentence,
            )


def _date_supported(d: date, lords: set[str], level: str | None,
                    facts: _ChartFacts) -> tuple[bool, str]:
    """Check one stated date against the dasha data it is attributed to."""
    if d == facts.birth_date or d in facts.transit_event_dates:
        return True, "transit window / birth date"
    if level in ("md", "ad", "pd") and not lords:
        # Level named but no lord nearby: fall back to any dasha range.
        level = None
    if level == "md":
        for lord in lords:
            rng = facts.md_by_lord.get(lord)
            if rng and rng[0] <= d <= rng[1]:
                return True, f"{lord} Mahadasha"
        return False, f"{' / '.join(sorted(lords)) or 'the stated'} Mahadasha range"
    if level == "ad":
        for (md_lord, ad_lord), rng in facts.ad_by_lords.items():
            if ad_lord in lords and rng[0] <= d <= rng[1]:
                return True, f"{md_lord}-{ad_lord} Antardasha"
        return False, f"{' / '.join(sorted(lords)) or 'the stated'} Antardasha range"
    if level == "pd":
        for (md_lord, ad_lord, pd_lord), rng in facts.pd_by_lords.items():
            if pd_lord in lords and rng[0] <= d <= rng[1]:
                return True, f"{md_lord}-{ad_lord}-{pd_lord} Pratyantardasha"
        return False, f"{' / '.join(sorted(lords)) or 'the stated'} Pratyantardasha range"
    if level == "any":
        for start, end, _label in facts.dasha_ranges:
            if start <= d <= end:
                return True, "dasha range"
        return False, "dasha range"
    for start, end, _label in facts.dasha_ranges:
        if start <= d <= end:
            return True, "dasha range"
    return False, "dasha range"


def _yoga_base_name(name: str) -> str:
    """Strip parenthetical qualifiers: 'Neechabhanga Raja Yoga (Moon)' -> base."""
    return name.split("(")[0].strip().lower().removesuffix(" yoga")


def _yoga_present(claimed: str, chart_yogas: list[str]) -> bool:
    claimed_tokens = set(_yoga_base_name(claimed).split())
    if not claimed_tokens:
        return False
    for chart_name in chart_yogas:
        chart_tokens = set(_yoga_base_name(chart_name).split())
        if claimed_tokens <= chart_tokens or chart_tokens <= claimed_tokens:
            return True
    return False


def _check_yogas(answer: str, facts: _ChartFacts,
                 flags: list[ValidationFlag], result: ValidationResult) -> None:
    if not facts.has_yogas:
        return
    seen: set[tuple[str, bool]] = set()
    for sentence in _sentences(answer):
        lower = sentence.lower()
        for m in _YOGA_RE.finditer(sentence):
            raw = m.group(1).strip()
            words = raw.split()
            negated = False
            # The regex can swallow up to two words before the yoga name
            # ("has no Hamsa", "The Gaja Kesari"): drop articles and
            # negation words, keeping only the yoga name itself.
            kept: list[str] = []
            for w in words:
                wl = w.lower()
                if wl in ("the", "a", "an"):
                    continue
                if wl in ("no", "not", "without", "never"):
                    negated = True
                    continue
                kept.append(w)
            # Drop non-name lead words (e.g. "has" in "has Gaja Kesari").
            while len(kept) > 2 and kept[0].lower() in (
                    "has", "have", "with", "your", "chart", "is", "shows"):
                kept = kept[1:]
            claimed = " ".join(kept)
            if not claimed:
                continue
            before = lower[max(0, m.start() - 30):m.start()]
            after = lower[m.end():m.end() + 20]
            negated = negated or bool(re.search(r"\b(no|not|without|lacks|never)\b", before)) \
                or "absent" in before or "absent" in after
            key = (claimed.lower(), negated)
            if key in seen:
                continue
            seen.add(key)
            present = _yoga_present(claimed, facts.yogas)
            if negated:
                _check_claim(
                    flags, result, "yoga_mismatch", not present,
                    f"{claimed} Yoga stated absent but it is present in the chart",
                    sentence,
                )
            else:
                _check_claim(
                    flags, result, "yoga_mismatch", present,
                    f"{claimed} Yoga stated present but it is absent from the chart",
                    sentence,
                )


def _check_sade_sati(answer: str, facts: _ChartFacts,
                     flags: list[ValidationFlag], result: ValidationResult) -> None:
    if facts.sade_sati_active is None:
        return
    seen: set[str] = set()
    for sentence in _sentences(answer):
        lower = sentence.lower()
        if "sade sati" not in lower:
            continue
        if "sade sati" in seen:
            continue
        seen.add("sade sati")
        inactive_claim = bool(re.search(
            r"\b(no sade sati|not in sade sati|not active|no longer in|is not in)\b", lower))
        active_claim = (not inactive_claim) and bool(re.search(
            r"\b(active|undergoing|peak|rising|setting|in sade sati|going through)\b", lower))
        if inactive_claim:
            _check_claim(
                flags, result, "sade_sati_mismatch", not facts.sade_sati_active,
                "Sade Sati stated inactive but the chart has it active",
                sentence,
            )
        elif active_claim:
            _check_claim(
                flags, result, "sade_sati_mismatch", bool(facts.sade_sati_active),
                "Sade Sati stated active but the chart has it inactive",
                sentence,
            )
            phase_word = next(
                (w for w in ("peak", "rising", "setting") if w in lower), None)
            if phase_word and facts.sade_sati_active and facts.sade_sati_phase:
                _check_claim(
                    flags, result, "sade_sati_mismatch",
                    phase_word in facts.sade_sati_phase.lower(),
                    f"Sade Sati stated in {phase_word} phase but chart has "
                    f"{facts.sade_sati_phase}",
                    sentence,
                )


# ---------------------------------------------------------------------------
# Citation grounding
# ---------------------------------------------------------------------------

def _content_words(text: str) -> set[str]:
    words = set(re.findall(r"[a-z]+", text.lower()))
    return {w for w in words if w not in _STOPWORDS}


def chunk_supports_sentence(chunk_text: str, sentence: str) -> bool:
    """Does the chunk text support the citing sentence?

    Supported when the chunk shares a distinctive astrological term with
    the sentence (planet / sign / nakshatra / yoga / house number) or at
    least 30% of the sentence's content words. Sentences with fewer than
    4 content words are too generic to judge and count as supported.
    """
    claim_words = _content_words(sentence)
    if len(claim_words) < 4:
        return True
    chunk_lower = (chunk_text or "").lower()
    sentence_lower = sentence.lower()
    for term in _DISTINCTIVE_TERMS:
        if term in sentence_lower and term in chunk_lower:
            return True
    for match in re.finditer(
            r"(\d{1,2})(?:st|nd|rd|th)\s+house|house\s+(\d{1,2})", sentence_lower):
        n = match.group(1) or match.group(2)
        if (f"{n}th house" in chunk_lower or f"house {n}" in chunk_lower
                or re.search(rf"\b{n}(?:st|nd|rd|th)\b", chunk_lower)):
            return True
    chunk_words = _content_words(chunk_text or "")
    overlap = len(claim_words & chunk_words) / max(len(claim_words), 1)
    return overlap >= 0.30


def _validate_citations(answer: str, results: list[SearchResult],
                        flags: list[ValidationFlag],
                        result: ValidationResult) -> str:
    """Drop out-of-range / unsupported [n] markers; return cleaned text."""
    markers = sorted({int(m) for m in re.findall(r"\[(\d+)\]", answer or "")})
    dropped: set[int] = set()
    for number in markers:
        result.citations_checked += 1
        if not 1 <= number <= len(results):
            dropped.add(number)
            flags.append(ValidationFlag(
                kind="citation_out_of_range",
                message=f"Citation [{number}] is out of range ({len(results)} references)",
                detail="",
            ))
            continue
        sentence = ""
        for s in _sentences(answer):
            if f"[{number}]" in s:
                sentence = s
                break
        if chunk_supports_sentence(results[number - 1].chunk.text, sentence):
            result.citations_kept.append(number)
            result.citations_supported += 1
        else:
            dropped.add(number)
            flags.append(ValidationFlag(
                kind="citation_unsupported",
                message=f"Citation [{number}] does not support the claim it is attached to",
                detail=sentence,
            ))
    result.citations_dropped = sorted(dropped)
    if not dropped:
        return answer
    cleaned = re.sub(
        r"\[(\d+)\]",
        lambda m: "" if int(m.group(1)) in dropped else m.group(0),
        answer,
    )
    cleaned = re.sub(r"[ \t]+([.,!?;:])", r"\1", cleaned)
    cleaned = re.sub(r" {2,}", " ", cleaned)
    return cleaned


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def validate_answer(
    answer: str,
    chart_context: dict[str, Any] | None = None,
    results: list[SearchResult] | None = None,
    citations: list[SearchResult] | None = None,
) -> ValidationResult:
    """Validate an LLM answer against the chart context and its references.

    Parameters
    ----------
    answer:
        The generated answer text (may contain ``[n]`` citation markers).
    chart_context:
        The chart dict the LLM received (``calculate_chart(...).model_dump()``
        shape). ``None`` skips the chart-claim checks; citation checks
        still run.
    results:
        Retrieved references, in citation order (``[1]`` is ``results[0]``).
    citations:
        Alias for ``results`` (the references the answer cites), kept so
        the call reads as ``validate_answer(answer, chart_context, citations)``.

    Returns
    -------
    ValidationResult with flags for mismatched placements/dates/yogas/
    Sade Sati and for out-of-range/unsupported citations, plus
    ``cleaned_answer`` with dropped citation markers removed.
    """
    refs = citations if citations is not None else (results or [])
    flags: list[ValidationFlag] = []
    result = ValidationResult(valid=True, cleaned_answer=answer or "")

    facts = _ChartFacts(chart_context)
    if chart_context is not None:
        _check_placements(answer, facts, flags, result)
        _check_dates(answer, facts, flags, result)
        _check_yogas(answer, facts, flags, result)
        _check_sade_sati(answer, facts, flags, result)

    result.cleaned_answer = _validate_citations(answer, refs, flags, result)

    if result.claims_checked:
        result.date_placement_match_rate = (
            result.claims_supported / result.claims_checked)
    if result.citations_checked:
        result.citation_precision = (
            result.citations_supported / result.citations_checked)
    result.flags = flags
    result.valid = not flags
    return result
