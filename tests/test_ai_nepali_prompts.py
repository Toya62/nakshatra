"""Task 13 step 6 — Nepali gaps: NE system prompts for all 7 intents and
Romanized Nepali intent routing.

(a) get_system_prompt("ne", intent) must return a distinct Nepali prompt for
EACH of the 7 intents — the 4 missing ones (remedial, career, relationship,
conceptual) used to fall back silently to SYSTEM_PROMPT_NE_PREDICTION.
Each NE prompt must mirror its EN counterpart rule-for-rule (same 4-section
layout, same ground-truth / no-invention rules) in Devanagari Nepali, and
its 4 section headings must agree with the build_prompt() NE directive for
the same intent.

(b) classify_intent() must route Romanized Nepali questions, mirroring the
ConceptMap concepts in retrieval.py (career, timing, marriage, wealth,
health, children, education, travel, remedies). Children / education /
travel have no dedicated archetype: they route to EVENT_PREDICTION
explicitly (they are life-event timing questions), including when the
question contains a self-reference that the default fallback would send to
natal identity.

No live LLM calls in this file.
"""

import re

from nakshatra.ai.corpus import CorpusChunk
from nakshatra.ai.retrieval import SearchResult
from nakshatra.ai.synthesize import (
    SYSTEM_PROMPT_CAREER,
    SYSTEM_PROMPT_CONCEPTUAL,
    SYSTEM_PROMPT_NE_PREDICTION,
    SYSTEM_PROMPT_RELATIONSHIP,
    SYSTEM_PROMPT_REMEDIAL,
    ConsultationIntent,
    build_prompt,
    classify_intent,
    get_system_prompt,
)

DEVANAGARI = re.compile(r"[\u0900-\u097F]")


def _chunk() -> CorpusChunk:
    return CorpusChunk(
        work="BPHS",
        chapter="1",
        verse="1",
        chunk_id="BPHS-1-1-0",
        text="The Sun in Tanu Bhava",
        topics=["Sun"],
        source_file="test.txt",
        char_start=0,
        char_end=len("The Sun in Tanu Bhava"),
        tier="verse",
    )


def _ne_section_headings(prompt: str) -> list[str]:
    """Section headings of a Nepali prompt: '### १. <heading>' lines,
    heading text up to the first ':' (descriptions follow it)."""
    headings = []
    for line in prompt.splitlines():
        match = re.match(r"### [१२३४]\. ([^:\n]+)", line.strip())
        if match:
            headings.append(match.group(1).strip())
    return headings


class TestNeSystemPromptsAllIntents:
    """(a) One distinct Devanagari NE prompt per intent, no silent fallback."""

    ALL_INTENTS = list(ConsultationIntent)

    def test_ne_prompt_distinct_for_each_intent(self):
        prompts = {intent: get_system_prompt("ne", intent) for intent in self.ALL_INTENTS}
        # All 7 are distinct objects/strings — none falls back to another's.
        assert len(set(prompts.values())) == 7, "NE prompts must be distinct per intent"
        # Only the prediction intent itself is the NE prediction prompt.
        assert prompts[ConsultationIntent.EVENT_PREDICTION] == SYSTEM_PROMPT_NE_PREDICTION
        for intent, prompt in prompts.items():
            if intent is not ConsultationIntent.EVENT_PREDICTION:
                assert prompt != SYSTEM_PROMPT_NE_PREDICTION, intent

    def test_ne_prompts_are_nepali_not_english(self):
        for intent in self.ALL_INTENTS:
            prompt = get_system_prompt("ne", intent)
            assert DEVANAGARI.search(prompt), f"{intent}: no Devanagari text"
            assert "You are a master Astrologer" not in prompt, intent
            # String intent values and the "nepali" alias behave the same.
            assert get_system_prompt("nepali", intent.value) == prompt
            assert get_system_prompt("ne", intent.value) == prompt

    def test_ne_prompts_keep_ground_truth_directive(self):
        # Every NE prompt tells the model the Swiss Ephemeris chart data is
        # immutable ground truth (EN prompts do the same).
        for intent in self.ALL_INTENTS:
            assert "अकाट्य सत्य" in get_system_prompt("ne", intent), intent

    def test_ne_remedial_mirrors_en_remedial(self):
        ne = get_system_prompt("ne", ConsultationIntent.REMEDIAL)
        assert "### १. मुख्य ग्रह पीडा र कर्मगत असन्तुलन" in ne
        assert "४३ दिन" in ne and "सूर्योदयदेखि सूर्यास्त" in ne
        assert "जीव सेवा" in ne
        assert "कडा सावधानी (निषेध)" in ne
        assert "सन्दर्भ सूची नदोहोर्‍याउनुहोस्" in ne
        # EN rule mirrored: no bibliography list at the end.
        assert "### ४. कडा सावधानी (निषेध)" in ne

    def test_ne_career_mirrors_en_career(self):
        ne = get_system_prompt("ne", ConsultationIntent.CAREER_FINANCE)
        assert "दशम भाव" in ne and "दशमेश" in ne and "अमात्यकारक" in ne
        assert "दशमांश" in ne  # D10, as in the EN career prompt
        assert "YYYY-MM-DD" in ne
        assert "नक्कली सन्दर्भ" in ne  # never invent citations
        assert "### ३. यकिन समय-तालिका" in ne

    def test_ne_relationship_mirrors_en_relationship(self):
        ne = get_system_prompt("ne", ConsultationIntent.RELATIONSHIP)
        assert "सप्तम भाव" in ne and "सप्तमेश" in ne and "दाराकारक" in ne
        assert "नवांश" in ne  # D9, as in the EN relationship prompt
        assert "मर्यादापूर्ण" in ne  # dignified spousal analysis
        assert "चन्द्र-चन्द्र" in ne  # Moon-to-Moon harmony
        assert "### ३. सम्बन्ध तथा विवाहको यकिन समय-तालिका" in ne

    def test_ne_conceptual_mirrors_en_conceptual(self):
        ne = get_system_prompt("ne", ConsultationIntent.CONCEPTUAL)
        assert "### १. शास्त्रीय परिभाषा र ग्रन्थको आधार" in ne
        assert "भङ्ग" in ne  # cancellations (bhanga)
        assert "[१], [२]" in ne
        assert "नक्कली सन्दर्भ" in ne  # cite only provided verses
        assert "### ४. सकारात्मक रूपान्तरण र मार्गदर्शन" in ne

    def test_en_prompts_unchanged(self):
        assert get_system_prompt("en", ConsultationIntent.REMEDIAL) == SYSTEM_PROMPT_REMEDIAL
        assert get_system_prompt("en", ConsultationIntent.CAREER_FINANCE) == SYSTEM_PROMPT_CAREER
        assert (
            get_system_prompt("en", ConsultationIntent.RELATIONSHIP) == SYSTEM_PROMPT_RELATIONSHIP
        )
        assert get_system_prompt("en", ConsultationIntent.CONCEPTUAL) == SYSTEM_PROMPT_CONCEPTUAL
        # Unknown intent string still falls back to the prediction prompt.
        assert get_system_prompt("ne", "not-an-intent") == SYSTEM_PROMPT_NE_PREDICTION

    def test_ne_system_and_user_prompts_agree_on_sections(self):
        """For every intent, the 4 section headings in build_prompt(ne)
        must appear in get_system_prompt(ne) — system and user prompts must
        not disagree in NE mode. (Step 6 fixed the remedial directive,
        whose old headings differed from the EN remedial sections.)"""
        results = [SearchResult(chunk=_chunk(), score=0.9)]
        for intent in self.ALL_INTENTS:
            system = get_system_prompt("ne", intent)
            user = build_prompt("q", results, language="ne", intent=intent)
            user_headings = _ne_section_headings(user)
            assert len(user_headings) == 4, (intent, user_headings)
            system_headings = _ne_section_headings(system)
            assert len(system_headings) == 4, (intent, system_headings)
            assert user_headings == system_headings, intent


class TestRomanizedNepaliRouting:
    """(b) Romanized Nepali questions route by keyword, mirroring ConceptMap."""

    def test_career_romanized(self):
        # "meri nokari kahile" is a timing question about a job: timing wins
        # over career, exactly as English "when will I get a job?" routes to
        # event prediction rather than career.
        assert classify_intent("meri nokari kahile") == ConsultationIntent.EVENT_PREDICTION
        assert classify_intent("meri nokari") == ConsultationIntent.CAREER_FINANCE
        for q in ("mero kaam kasto chha", "mero pesha", "mero jaagir", "mero naukri"):
            assert classify_intent(q) == ConsultationIntent.CAREER_FINANCE, q

    def test_marriage_romanized(self):
        assert classify_intent("mero vivah") == ConsultationIntent.RELATIONSHIP
        assert classify_intent("mero bihe") == ConsultationIntent.RELATIONSHIP
        assert classify_intent("meri shrimati") == ConsultationIntent.RELATIONSHIP
        # ... unless it is a timing question, which wins like in English.
        assert classify_intent("mero vivah kahile hunchha") == ConsultationIntent.EVENT_PREDICTION

    def test_health_romanized(self):
        for q in ("mero swasthya kasto chha", "mero rog", "mero bimar", "mero chot", "mero aushadhi"):
            assert classify_intent(q) == ConsultationIntent.HEALTH_WELLNESS, q
        # Health beats timing, as in English ("health prediction in future").
        assert classify_intent("mero rog kahile niko hunchha") == ConsultationIntent.HEALTH_WELLNESS

    def test_wealth_romanized_routes_to_career_finance(self):
        for q in ("mero paisa", "mero dhana", "mero kamai", "mero sampatti", "mero aarthik sthiti"):
            assert classify_intent(q) == ConsultationIntent.CAREER_FINANCE, q

    def test_children_education_travel_romanized(self):
        # No dedicated archetype: these are life-event timing questions and
        # route explicitly to event prediction (not via the default).
        for q in (
            "mero chhora",
            "mero chhori",
            "mero santana",
            "mero padhai",
            "mero shiksha",
            "mero bidesh yatra",
            "mero yatra",
        ):
            assert classify_intent(q) == ConsultationIntent.EVENT_PREDICTION, q

    def test_keta_keti_are_children_not_spouse(self):
        # keti/keta colloquially mean "girl/boy" (son/daughter), not spouse:
        # they must not hijack a question into RELATIONSHIP. They belong to
        # the life-event (children) check, so a question about one's son or
        # daughter routes to event prediction, while a marriage word still
        # routes to relationship.
        assert classify_intent("mero keta ko padhai kasto") == ConsultationIntent.EVENT_PREDICTION
        assert classify_intent("mero keti ko barema") == ConsultationIntent.EVENT_PREDICTION
        assert classify_intent("mero vivah") == ConsultationIntent.RELATIONSHIP

    def test_life_event_keywords_beat_natal_default(self):
        # A self-reference ("my ...") would send an unrecognized question to
        # natal identity via the default fallback; a life-event keyword must
        # win instead — the question is about the child, not the self.
        assert classify_intent("my son ko padhai kasto") == ConsultationIntent.EVENT_PREDICTION
        assert classify_intent("my chhora bidesh kahile janchha") == ConsultationIntent.EVENT_PREDICTION

    def test_remedial_romanized(self):
        assert classify_intent("mero lagi daan japa") == ConsultationIntent.REMEDIAL
        assert classify_intent("shani ko upaya") == ConsultationIntent.REMEDIAL

    def test_devanagari_routing_unchanged(self):
        assert classify_intent("मेरो जागिर कहिले हुन्छ?") == ConsultationIntent.EVENT_PREDICTION
        assert classify_intent("विवाह कहिले हुन्छ?") == ConsultationIntent.EVENT_PREDICTION
        assert classify_intent("मेरो छोराको पढाइ कस्तो हुन्छ?") == ConsultationIntent.EVENT_PREDICTION
        assert classify_intent("मेरो स्वास्थ्य र दीर्घायु कस्तो रहला?") == ConsultationIntent.HEALTH_WELLNESS

    def test_english_routing_unchanged(self):
        assert classify_intent("when will I get a job?") == ConsultationIntent.EVENT_PREDICTION
        assert classify_intent("tell me about myself") == ConsultationIntent.NATAL_IDENTITY
        assert classify_intent("what is Sade Sati?") == ConsultationIntent.CONCEPTUAL
        assert classify_intent("what remedies should I do for Saturn?") == ConsultationIntent.REMEDIAL
        assert classify_intent("tell me about health prediction in future") == ConsultationIntent.HEALTH_WELLNESS
        assert classify_intent("will I get a promotion?") == ConsultationIntent.EVENT_PREDICTION

    def test_romanized_words_do_not_hijack_conceptual(self):
        # "what is ..." questions stay conceptual even when they mention a
        # Romanized career/wealth term — conceptual is checked before career.
        assert classify_intent("what is dhana yoga?") == ConsultationIntent.CONCEPTUAL
        assert classify_intent("what is kam?") == ConsultationIntent.CONCEPTUAL
