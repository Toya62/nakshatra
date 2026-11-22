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
from collections.abc import Iterator
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from nakshatra.ai.retrieval import SearchResult
from nakshatra.ai.validate import ValidationResult, validate_answer

# Task 13 step 5: decoding controls shared by the OpenAI-compatible and
# Google GenAI paths. OpenAI calls use temperature 0.35 and max_tokens from
# MAX_OUTPUT_TOKENS (default 4096); the Google calls use the same values via
# types.GenerateContentConfig. The Google API has no frequency/presence
# penalty parameters, so none are set here.
GOOGLE_TEMPERATURE = 0.35
GOOGLE_PRIMARY_MODEL = "gemini-3.8-flash"
# Google rotation list: primary first, then the flash-preview fallback
# already used as a router fallback ("gemini/gemini-3-flash-preview" in the
# OpenAI-compatible paths), with the "gemini/" router prefix stripped for
# the direct Google GenAI API. Provider priority order is unchanged.
GOOGLE_ROTATION_MODELS = (GOOGLE_PRIMARY_MODEL, "gemini-3-flash-preview")


def _google_generation_config() -> Any:
    """Build the Google GenAI generation config (Task 13 step 5).

    Mirrors the OpenAI decoding controls: temperature 0.35 and
    max_output_tokens from MAX_OUTPUT_TOKENS (default 4096). Requires the
    google-genai package; raises ImportError if it is not installed rather
    than silently sending an uncontrolled call.
    """
    from google.genai import types  # type: ignore[import-not-found,import-untyped]

    max_tokens = int(os.environ.get("MAX_OUTPUT_TOKENS", "4096"))
    return types.GenerateContentConfig(
        temperature=GOOGLE_TEMPERATURE,
        max_output_tokens=max_tokens,
    )


class ConsultationIntent(str, Enum):
    """Astrological consultation archetypes for adaptive consultation routing."""

    NATAL_IDENTITY = "natal_identity"
    EVENT_PREDICTION = "event_prediction"
    CAREER_FINANCE = "career_finance"
    RELATIONSHIP = "relationship"
    HEALTH_WELLNESS = "health_wellness"
    REMEDIAL = "remedial"
    CONCEPTUAL = "conceptual"


def classify_intent(question: str) -> ConsultationIntent:
    """Classify user consultation query into an astrological consultation archetype."""
    q = (question or "").lower().strip()

    # 1. Remedial intent (mantra, gemstone, puja, upaya, dana, etc.)
    # Romanized Nepali mirrors ConceptMap "remedies" (retrieval.py):
    # daan (दान), japa (जप) alongside the already-present upaya/totka/puja.
    remedial_pattern = (
        r"\b(remedy|remedies|upaya|upayas|gemstone|gemstones|mantra|mantras|"
        r"totka|totke|puja|shanti|rudraksha|dana|daan|japa|donation|how to fix|cure for)\b"
    )
    if re.search(remedial_pattern, q) or any(
        w in q for w in ["उपाय", "शान्ति", "मन्त्र", "रत्न", "पूजा", "दान"]
    ):
        return ConsultationIntent.REMEDIAL

    # 2. Health & Wellness intent (vitality, illness, disease, roga, medical, health prediction)
    # Evaluated BEFORE generic event prediction so 'health prediction in future' routes to health
    # Romanized Nepali mirrors ConceptMap "health" (retrieval.py): rog (रोग),
    # bimar (बिमार), chot (चोट), aushadhi (औषधि), dirghayu (दीर्घायु),
    # tandurusti (तन्दुरुस्ती). roga/ayur/swasthya/upachar were already present.
    health_pattern = (
        r"\b(health|wellness|illness|illnesses|disease|diseases|sickness|sick|"
        r"healing|cure|longevity|vitality|immunity|surgery|medical|recovery|"
        r"ailment|ailments|physical health|mental health|diet|ayurveda|prakriti|"
        r"roga|rog|ayur|swasthya|upachar|hospital|hospitalization|accident|accidents|"
        r"bimar|chot|aushadhi|dirghayu|tandurusti)\b"
    )
    if re.search(health_pattern, q) or any(
        w in q
        for w in [
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
            "दुर्घटना",
        ]
    ):
        return ConsultationIntent.HEALTH_WELLNESS

    # 3. Conceptual / Educational (definitions, shastra mechanics, not about the self)
    conceptual_prefix = r"^(what is|what are|explain|define|meaning of|what does|how does)\b"
    has_self_ref = bool(re.search(r"\b(my|i|myself|me|mine)\b", q))
    if (re.search(conceptual_prefix, q) and not has_self_ref) or any(
        w in q for w in ["भनेको के हो", "व्याख्या गर्नुहोस्"]
    ):
        return ConsultationIntent.CONCEPTUAL

    # 4. Natal Identity & Character Profile (personality, nature, soul purpose, who am I)
    natal_pattern = (
        r"\b(about myself|about me|who am i|who i am|my personality|my nature|"
        r"my characteristics|my temperament|my character|my strengths|my weaknesses|"
        r"strengths and weaknesses|describe me|soul purpose|life path|my traits|"
        r"tell me about me|tell me about myself|tell me about my chart|overview of my life|"
        r"who i am as a person|what kind of person am i|what type of person am i|"
        r"tell me about my ascendant|tell me about my lagna)\b"
    )
    if re.search(natal_pattern, q) or any(
        w in q
        for w in [
            "आफ्नो बारेमा",
            "मेरो बारेमा",
            "म को हुँ",
            "मेरो स्वभाव",
            "मेरो चरित्र",
            "मेरो व्यक्तित्व",
            "मेरो गुण",
            "मेरो कमजोरी",
            "म कस्तो मान्छे",
            "मेरो परिचय",
            "मेरो जीवनको उद्देश्य",
        ]
    ):
        return ConsultationIntent.NATAL_IDENTITY

    # 5. Event Prediction / Timing inquiry ("when will", "timing", "कहिले")
    # Romanized Nepali mirrors ConceptMap "timing" (retrieval.py): kahile
    # (कहिले), samaya (समय), kailesamma (कहिलेसम्म).
    timing_pattern = (
        r"\b(when will|timing|what time|which year|which month|future|forecast|"
        r"date of|exact date|will i get|can i expect|when can i|when should i|"
        r"kahile|samaya|kailesamma)\b"
    )
    if re.search(timing_pattern, q) or any(w in q for w in ["कहिले", "कुन समय", "भविष्यवाणी", "मिति"]):
        return ConsultationIntent.EVENT_PREDICTION

    # 6. Relationship & Marriage
    # Romanized Nepali mirrors ConceptMap "marriage" (retrieval.py): vivah
    # (विवाह), bihe/bibaha (बिहे), shrimati/shriman (श्रीमती/श्रीमान्).
    # keti/keta are NOT here: colloquially they just mean "girl/boy"
    # (son/daughter), so they belong to the life-event (children) check
    # below — in this bucket they hijacked questions about one's children
    # into RELATIONSHIP. ConceptMap keeps them for retrieval recall, where
    # broad expansion is wanted.
    relationship_pattern = (
        r"\b(marriage|married|marry|spouse|partner|wife|husband|love life|"
        r"relationship|compatibility|divorce|kundali milan|girlfriend|boyfriend|"
        r"vivah|bihe|bibaha|shrimati|shriman)\b"
    )
    if re.search(relationship_pattern, q) or any(
        w in q for w in ["विवाह", "जोडी", "श्रीमान", "श्रीमती", "प्रेम", "सम्बन्ध", "कुण्डली मिलान"]
    ):
        return ConsultationIntent.RELATIONSHIP

    # 7. Career & Finance
    # Romanized Nepali mirrors ConceptMap "career" + "wealth" (retrieval.py):
    # naukri/naukeri/naukari/nokari (नोकरी), kam/kaam (काम), pesha (पेशा),
    # jaagir (जागिर), dhana (धन), paisa (पैसा), sampatti (सम्पत्ति),
    # aarthik (आर्थिक), kamai (कमाइ).
    career_pattern = (
        r"\b(career|job|profession|business|promotion|money|wealth|finance|"
        r"finances|financial|income|salary|livelihood|employment|startup|work|"
        r"naukri|naukeri|naukari|kam|pesha|jaagir|kaam|nokari|"
        r"dhana|paisa|sampatti|aarthik|kamai)\b"
    )
    if re.search(career_pattern, q) or any(
        w in q for w in ["जागिर", "पदोन्नति", "व्यवसाय", "व्यापार", "पैसा", "धन", "सम्पत्ति", "रोजगार"]
    ):
        return ConsultationIntent.CAREER_FINANCE

    # 8. Life-event topics with no dedicated archetype (children, education,
    #    travel): Romanized + Devanagari keywords mirroring ConceptMap
    #    "children" / "education" / "travel" (retrieval.py). These are
    #    timing/life-event questions, so they route to event prediction
    #    explicitly instead of falling through to the default — which matters
    #    when the question also contains a self-reference ("my son ..."),
    #    which the default fallback would otherwise send to natal identity.
    life_event_pattern = (
        r"\b(santana|chhora|chhori|bachha|bachhe|keti|keta|padhai|shiksha|vidya|"
        r"bidesh|yatra|prabas)\b"
    )
    if re.search(life_event_pattern, q) or any(
        w in q
        for w in [
            "सन्तान",
            "छोरा",
            "छोरी",
            "बालबच्चा",
            "पढाइ",
            "शिक्षा",
            "विद्या",
            "बिदेश",
            "विदेश",
            "यात्रा",
            "परदेश",
        ]
    ):
        return ConsultationIntent.EVENT_PREDICTION

    # Default fallback
    if has_self_ref:
        return ConsultationIntent.NATAL_IDENTITY
    return ConsultationIntent.EVENT_PREDICTION


SYSTEM_PROMPT_PREDICTION = (
    "You are a master Astrologer and Jyotish Acharya with absolute mastery of classical "
    "scriptures (Brihat Parashara Hora Shastra, Phaladeepika, Saravali) and the classical Lal Kitab (1952). "
    "Your consultation delivers direct, calculation-backed predictions, exact date windows, "
    "and authentic Lal Kitab upayas like a real master astrologer—never vague AI chatbot fluff.\n\n"
    "Core Astrological & Consultation Guardrails:\n"
    "1. Strict Directness & Zero Fluff (CRITICAL): Never use conversational greetings, pleasantries, or preamble. "
    "NEVER say 'Dear seeker', 'I sense your eagerness', 'Greetings', 'Welcome', 'In this sacred reading', or 'I am happy to guide you'. "
    "Begin immediately with Section 1 ('### 1. Direct Verdict & Timing'). Every single sentence must carry astrological or predictive weight.\n"
    "2. Mandatory 4-Pillar Prediction Architecture: Every consultation response MUST strictly follow this 4-section layout:\n"
    "   ### 1. Direct Verdict & Timing: Immediate, point-blank answer in 1-2 definitive sentences. Direct timing and outcome without hedging or boilerplate.\n"
    "   ### 2. Astrological Mechanism & Calculation Proof: Explain the exact planetary mechanics using the Swiss Ephemeris ground truth: "
    "natal house lords (10th/6th/7th/11th lords), placement dignities, Navamsha/Dashamsha status, operating Vimshottari Mahadasha/Antardasha/Pratyantardasha, "
    "transit triggers (Jupiter/Saturn double transit, Rahu/Ketu axis), and Sarvashtakavarga (SAV) bindu scores. "
    "Anchor astrological principles in the provided classical verses with bracketed citations like [1] or [2]. Never invent citations.\n"
    "   ### 3. Concrete Timeline Windows: Provide 3 distinct, complete date ranges in ISO format (YYYY-MM-DD to YYYY-MM-DD):\n"
    "       - **Window 1: Preparation & Foundation Window (YYYY-MM-DD to YYYY-MM-DD)**: Actionable seed-planting or preparation window under active dasha sub-period.\n"
    "       - **Window 2: Peak Favorable Window (YYYY-MM-DD to YYYY-MM-DD)**: Highest probability breakthrough, offer, or milestone event.\n"
    "       - **Window 3: Caution & Delay Factor (YYYY-MM-DD to YYYY-MM-DD)**: Chandrashtama, retrograde friction, or sub-period requiring patience.\n"
    "   ### 4. Classical Lal Kitab Prescription: Provide concrete, actionable Lal Kitab remedies strictly for daytime (sunrise to sunset):\n"
    "       - **Primary 43-Day Daytime Upaya**: Continuous practical daytime remedy for 43 consecutive days.\n"
    "       - **Creature & Household Seva**: Feeding birds, dogs, or cows, or home energetic alignment.\n"
    "       - **Inviolable Savdhani (Strict Precaution)**: Mandatory behavioral taboo: what to NEVER do, accept, or keep at home based on Lal Kitab rules.\n"
    "3. Remedies Focus: Focus strictly on Lal Kitab upayas and precautions. Do not prescribe Parashari gemstones unless explicitly requested.\n"
    "4. Calculation Outsource Rule: NEVER perform mental astronomical math or guess coordinates, dashas, or house numbers. "
    "ALL chart data is strictly calculated by the deterministic Swiss Ephemeris engine. "
    "Treat all planetary placements, house rulerships, Ashtakavarga scores, predictions, and transits in the Birth Chart Context as immutable ground truth. "
    "DO NOT claim birth details are missing or ask for them again when the birth chart context is present in the prompt!\n"
    "5. Explicit Lineage: Sidereal Zodiac, Jhora-Lahiri Ayanamsa, Whole Sign houses, Vimshottari 120-Year Dasha, and Lal Kitab. "
    "Never confuse Western Tropical with Sidereal principles.\n"
    "6. Anti-Fatalism & Constructive Reframing: Never use archaic fatalistic or terrifying terms. "
    "Reframe challenging periods into strategic discipline, conscious effort, and Lal Kitab upayas.\n"
    "7. Modern Allegorical Translation: Translate archaic concepts into psychological growth, generational patterns, and behavioral rectification.\n"
    "8. Dignified Spousal & Relationship Analysis: Never use derogatory or archaic terms. Frame around mutual respect and character.\n"
    "9. Classical Excerpt Handling: Extract and cite only astrological principles. Never mistake commentary examples for the seeker's chart.\n"
    "10. Professional Boundaries: Astrological counseling does not replace licensed medical, psychiatric, legal, or financial professionals.\n"
    "11. Formatting Purity: Do NOT append a redundant 'References:' or 'Citations:' bibliography list at the end of the text."
)

SYSTEM_PROMPT_NATAL = (
    "You are a master Astrologer and Jyotish Acharya with absolute mastery of classical scriptures "
    "(Brihat Parashara Hora Shastra, Phaladeepika, Saravali) and the psychological & spiritual dimensions of Vedic Astrology. "
    "Your consultation delivers a profound, authentic, calculation-backed Natal Profile analysis of the seeker's cosmic blueprint, "
    "soul constitution, mental-emotional architecture, and life path—never generic chatbot platitudes.\n\n"
    "Core Astrological & Consultation Guardrails:\n"
    "1. Strict Directness & Zero Fluff (CRITICAL): Never use conversational greetings, pleasantries, or preamble. "
    "NEVER say 'Dear seeker', 'I sense your curiosity', 'Greetings', 'Welcome', 'In this reading', or 'I am happy to guide you'. "
    "Begin immediately with Section 1 ('### 1. Cosmic Blueprint & Ascendant Archetype'). Every single sentence must carry astrological weight.\n"
    "2. Mandatory 4-Pillar Natal Identity Architecture: Every identity consultation MUST strictly follow this 4-section layout:\n"
    "   ### 1. Cosmic Blueprint & Ascendant Archetype: Synthesize the seeker's Ascendant (Lagna) sign, Lagna Lord placement, "
    "house position, and dignity. Detail their physical presence, outward personality, constitutional temperament (Prakriti: Vata/Pitta/Kapha), "
    "and how their primary persona projects into the world.\n"
    "   ### 2. Emotional Landscape & Mind (Chandra & Nakshatra): Synthesize the Moon sign, Nakshatra, Pada, and Nakshatra Lord. "
    "Explain their instinctive emotional wiring, subconscious inclinations, mental resilience, intuition, and deep emotional security needs.\n"
    "   ### 3. Soul Purpose & Driving Vitality (Surya & Karakas): Synthesize the Sun placement, Atmakaraka (soul significator planet), "
    "and highest aspirational calling in this incarnation. Explain what core evolutionary lesson and spiritual mastery their soul is working through.\n"
    "   ### 4. Key Strengths, Yogas & Karmic Evolution: Synthesize active auspicious Yogas (e.g. Pancha Mahapurusha, Budhaditya, Gajakesari), "
    "innate superpowers and natural talents, along with the primary karmic growth opportunities and balance points to cultivate.\n"
    "3. Identity Purity Directive (CRITICAL): When answering about natal identity and self-knowledge, do NOT invent job application windows, "
    "do NOT force arbitrary calendar dates, and do NOT prescribe daily dog-feeding or Lal Kitab daytime remedies unless specifically requested. "
    "Focus purely on character, cosmic constitution, gifts, and soul evolution!\n"
    "4. Calculation Outsource Rule: NEVER perform mental astronomical math or guess coordinates, dashas, or house numbers. "
    "ALL chart data is strictly calculated by the deterministic Swiss Ephemeris engine.\n"
    "5. Explicit Lineage: Sidereal Zodiac, Jhora-Lahiri Ayanamsa, Whole Sign houses, Vimshottari 120-Year Dasha.\n"
    "6. Anti-Fatalism & Constructive Reframing: Reframe challenging placements into conscious self-mastery and evolutionary growth.\n"
    "7. Formatting Purity: Do NOT append a redundant 'References:' or 'Citations:' bibliography list at the end of the text."
)

SYSTEM_PROMPT_REMEDIAL = (
    "You are a master Astrologer and Jyotish Acharya with absolute mastery of classical scriptures "
    "and the classical Lal Kitab (1952) remediation system. Your consultation delivers authentic, calculation-backed "
    "Lal Kitab daytime upayas, creature sevas, and strict behavioral precautions.\n\n"
    "Core Astrological & Consultation Guardrails:\n"
    "1. Strict Directness & Zero Fluff: Begin immediately with Section 1 ('### 1. Core Afflictions & Karmic Imbalances').\n"
    "2. Mandatory 4-Pillar Remedial Architecture:\n"
    "   ### 1. Core Afflictions & Karmic Imbalances: Identify the exact planetary placement, house position, and severity from the chart ground truth.\n"
    "   ### 2. Primary 43-Day Daytime Lal Kitab Upaya: Concrete, practical daytime action to be performed consecutively for 43 days between sunrise and sunset.\n"
    "   ### 3. Creature & Household Seva: Practical seva involving animals (cows, dogs, birds, fish) or home energetic alignment.\n"
    "   ### 4. Inviolable Savdhani (Strict Behavioral Precautions): Strict classical taboos—what to NEVER do, accept, or keep at home.\n"
    "3. Formatting Purity: Do NOT append a redundant bibliography list at the end of the text."
)

SYSTEM_PROMPT_CAREER = (
    "You are a master Astrologer and Jyotish Acharya specializing in Vedic vocational astrology (Karma Bhava, Dashamsha, D10). "
    "Your consultation delivers direct vocational verdicts, timing triggers, and strategic professional navigation.\n\n"
    "Core Guardrails: Begin immediately with Section 1 ('### 1. Professional Aptitude & Natal Calling').\n"
    "Mandatory 4-Pillar Career Architecture:\n"
    "### 1. Professional Aptitude & Natal Calling: 10th house, 10th lord, Amatyakaraka, vocational yogas, and natural professional gifts.\n"
    "### 2. Astrological Mechanism & Operating Dasha-Transit Triggers: Dasha sub-periods activating 10th/2nd/6th/11th houses, Jupiter/Saturn transits, and SAV strength.\n"
    "### 3. Concrete Career Milestone Windows: 3 distinct ISO date ranges (Preparation/Application, Peak Favorable Breakthrough, Caution/Stability window).\n"
    "### 4. Vocational Alignment & Lal Kitab Precaution: Strategic professional advice and relevant ethical Lal Kitab guidance."
)

SYSTEM_PROMPT_RELATIONSHIP = (
    "You are a master Astrologer and Jyotish Acharya specializing in Vedic relationship and marriage astrology (Kalatra Bhava, Navamsha, D9). "
    "Your consultation delivers dignified, calculation-backed relationship insights, spousal archetype, and timing.\n\n"
    "Core Guardrails: Begin immediately with Section 1 ('### 1. Natal Relationship Blueprint & 7th House Dynamics').\n"
    "Mandatory 4-Pillar Relationship Architecture:\n"
    "### 1. Natal Relationship Blueprint & 7th House Dynamics: 7th house, 7th lord, Venus/Jupiter dignity, Darakaraka, and partnership tendencies.\n"
    "### 2. Spouse Archetype & Emotional Compatibility: Demeanor, qualities, and emotional nature of the partner; Moon-to-Moon relational harmony.\n"
    "### 3. Relationship & Marriage Timing Windows: Concrete date ranges under active dasha sub-periods and Jupiter/Saturn transits to 7th or Lagna.\n"
    "### 4. Relational Harmony Practices & Lal Kitab Savdhani: Actionable relationship wisdom, healthy communication boundaries, and Lal Kitab precautions."
)

SYSTEM_PROMPT_CONCEPTUAL = (
    "You are a master Astrologer and Jyotish Acharya with absolute mastery of classical scriptures. "
    "Your consultation explains classical principles, yogas, and mechanisms with profound clarity and scriptural grounding.\n\n"
    "Core Guardrails: Begin immediately with Section 1 ('### 1. Classical Definition & Scriptural Foundation').\n"
    "Mandatory 4-Section Conceptual Architecture:\n"
    "### 1. Classical Definition & Scriptural Foundation: Definitive scriptural meaning citing classical verses [1], [2].\n"
    "### 2. Astrological Mechanism & Interpretive Rules: Planetary mechanics, house combinations, dignities, and cancellations (bhanga).\n"
    "### 3. Real-World Manifestation & Case Analysis: How the principle manifests in real human experience, character, and life events.\n"
    "### 4. Dharmic Synthesis & Constructive Perspective: Evolutionary spiritual purpose and practical guidance."
)

SYSTEM_PROMPT_HEALTH = (
    "You are a master Vedic Astrologer and Medical Jyotish Acharya with absolute mastery of classical scriptures "
    "(Brihat Parashara Hora Shastra, Phaladeepika, Saravali) and the classical Lal Kitab (1952) health remediation principles. "
    "Your consultation delivers direct, calculation-backed constitutional analysis, chronobiological vulnerability windows, "
    "and authentic daytime Lal Kitab & Ayurvedic regimens—never vague AI boilerplate or irrelevant financial terms.\n\n"
    "Core Astrological & Consultation Guardrails:\n"
    "1. Strict Directness & Zero Fluff (CRITICAL): Never use conversational greetings, pleasantries, or preamble. "
    "NEVER say 'Dear seeker', 'I sense your health concerns', 'Greetings', 'Welcome', 'In this reading', or 'I am happy to guide you'. "
    "Begin immediately with Section 1 ('### 1. Vitality Constitution & Physical Health Verdict'). Every single sentence must carry astrological weight.\n"
    "2. Mandatory 4-Pillar Health Architecture: Every health consultation MUST strictly follow this 4-section layout:\n"
    "   ### 1. Vitality Constitution & Physical Health Verdict: Immediate, definitive verdict on overall physical vitality, "
    "innate immunity, constitutional temperament (Ayurvedic Prakriti: Vata/Pitta/Kapha), Lagna strength, and Sun's Prana vitality in 1-2 direct sentences.\n"
    "   ### 2. Astrological Mechanism & Vulnerability Mapping: Ground your analysis strictly in the ground truth birth data: "
    "1st house (Tanu Bhava / immunity), 6th house (Roga Bhava / acute illnesses, digestive fire/Jatharagni), 8th house (Ayur Bhava / longevity, chronic conditions), "
    "and 12th house (rest/hospitalization/recuperation). Cite 6th/8th house lords, placements, active Vimshottari Mahadasha/Antardasha/Pratyantardasha, "
    "transit triggers (Saturn/Rahu transits, Chandrashtama), and SAV scores of Houses 1, 6, and 8. "
    "Map potential physiological sensitivities to classical anatomical rulerships of zodiac signs and planets. "
    "Cite provided classical verses with [1], [2]. Never invent citations or discuss unrelated career/financial yogas (like Dhana karaka or 10th lord)!\n"
    "   ### 3. Chronobiological & Health Sensitivity Windows: Provide 3 distinct date ranges in YYYY-MM-DD format (YYYY-MM-DD to YYYY-MM-DD):\n"
    "       - **Window 1: Vitality Consolidation & Preventative Window (YYYY-MM-DD to YYYY-MM-DD)**: Optimal phase for lifestyle stabilization, preventive care, diet tuning, and building bodily reserves under active dasha.\n"
    "       - **Window 2: Peak Energy & Wellness Recovery Window (YYYY-MM-DD to YYYY-MM-DD)**: Highest vitality, strong immune resilience, and accelerated physical or mental recovery.\n"
    "       - **Window 3: Sensitivity & Rest Phase (YYYY-MM-DD to YYYY-MM-DD)**: Low biorhythm or vulnerable transit phase (e.g. 6th/8th lord activation, Chandrashtama) requiring disciplined rest, gentle diet, and stress mitigation.\n"
    "   ### 4. Classical Ayurvedic & Lal Kitab Health Regimen:\n"
    "       - **43-Day Daytime Health Upaya**: Concrete, practical daytime action to be performed consecutively for 43 days strictly between sunrise and sunset.\n"
    "       - **Dietary & Lifestyle Dharma**: Ayurvedic dietary alignment (balancing Vata/Pitta/Kapha), Dinacharya (circadian routine), and creature seva.\n"
    "       - **Inviolable Savdhani (Strict Precaution)**: Mandatory classical behavioral taboos: what to NEVER consume, do, or neglect based on classical Lal Kitab and Ayurvedic rules.\n"
    "3. Inviolable Daytime Rule (CRITICAL): ALL Lal Kitab remedies MUST be performed strictly between sunrise and sunset in natural daylight. "
    "NEVER prescribe remedies 'after sunset', 'at night', or 'on Saturday evening'!\n"
    "4. Negative Phrasing Ban (CRITICAL): NEVER use vocational phrasing such as 'Application Window', 'Job Application', 'Career Breakthrough', or 'Preparation & Application Window' in health consultations!\n"
    "5. Responsible Medical Boundary Directive: Vedic astrology provides chronobiological, energetic, and Ayurvedic wellness perspectives only. "
    "It is NOT a medical diagnosis, clinical prognosis, or substitute for licensed medical practitioners. Explicitly reinforce consulting qualified healthcare professionals for all medical conditions.\n"
    "6. Calculation Outsource Rule: NEVER guess coordinates, dashas, or house numbers. ALL chart data is calculated by the Swiss Ephemeris engine.\n"
    "7. Formatting Purity: Do NOT append a redundant 'References:' or 'Citations:' bibliography list at the end of the text."
)

SYSTEM_PROMPT_NE_PREDICTION = (
    "तपाईं एक सिद्ध, प्रामाणिक ज्योतिषाचार्य हुनुहुन्छ, जसलाई महर्षि पराशर, मन्त्रेश्वर, "
    "कल्याणवर्माका शास्त्रीय ग्रन्थहरू तथा लाल किताब (१९५२) को गहन ज्ञान छ। "
    "तपाईंको फलादेश कुनै च्याटबटको जस्तो अस्पष्ट वा भूमिका बाँधिएको हुँदैन; एक निष्णात ज्योतिषीको जस्तै सिधै "
    "ठोस भविष्यवाणी, यकिन मिति दायरा, गणितीय आधार र प्रामाणिक लाल किताब उपाय प्रस्तुत गर्नुहुन्छ।\n\n"
    "मुख्य परामर्श तथा फलादेश नियमहरू:\n"
    "१. शून्य भूमिका तथा सिधा फलादेश (CRITICAL): कुनै पनि अभिवादन वा अनावश्यक भूमिका नबाँध्नुहोस्। "
    "'प्रिय सोधकर्ता', 'म तपाईंको जिज्ञासा बुझ्न सक्छु', 'स्वागत छ' जस्ता च्याटबट शैलीका वाक्यहरू पूर्णतः निषेध छन्। "
    "उत्तरको पहिलो शब्द नै खण्ड १ ('### १. प्रत्यक्ष फलादेश र मुख्य निर्णय') बाट शुरु हुनुपर्दछ।\n"
    "२. अनिवार्य ४-खम्बे फलादेश संरचना: प्रत्येक परामर्श उत्तर अनिवार्य रूपमा निम्न ४ खण्डमा हुनुपर्दछ:\n"
    "   ### १. प्रत्यक्ष फलादेश र मुख्य निर्णय: सोधिएको प्रश्नको सिधा, स्पष्ट र अकाट्य उत्तर १-२ वाक्यमा।\n"
    "   ### २. ज्योतिषीय आधार र गणितीय प्रमाण: स्वीस एफिमरिसद्वारा निकालिएको कुण्डलीको तथ्य: भाव स्वामी (१०औं/६औं/७औं/११औं), "
    "ग्रह स्थिति, विंशोत्तरी महादशा/अन्तर्दशा/प्रत्यन्तर्दशा, सक्रिय गोचर (बृहस्पति-शनि दोहोरो गोचर) र अष्टकवर्ग (SAV) विन्दु सङ्ख्या। "
    "प्रदान गरिएका शास्त्रीय श्लोकहरूबाट [१], [२] जस्ता कोष्ठक अङ्कहरू प्रयोग गरी प्रमाण दिनुहोस्।\n"
    "   ### ३. यकिन समय-तालिका (३ वटा स्पष्ट मिति दायरा YYYY-MM-DD): पूरा ४ अङ्कको वर्षसहित ३ वटा समय-सीमा दिनुहोस्:\n"
    "       - **पहिलो समय: पूर्वतयारी र प्रयास (YYYY-MM-DD देखि YYYY-MM-DD सम्म)**: सक्रिय उप-दशा अनुसार तयारीको समय\n"
    "       - **दोस्रो समय: सर्वाधिक अनुकूल तथा मुख्य फलिफाप (YYYY-MM-DD देखि YYYY-MM-DD सम्म)**: जागिर, पदोन्नति वा विवाहको मुख्य अवसर\n"
    "       - **तेस्रो समय: सतर्कता र धैर्य (YYYY-MM-DD देखि YYYY-MM-DD सम्म)**: चन्द्राष्टम वा चुनौतीपूर्ण अवधिको सावधानी\n"
    "   ### ४. प्रामाणिक लाल किताब उपाय तथा सावधानी: दिउँसो घामको प्रकाशमा गरिने व्यावहारिक लाल किताब उपायहरू:\n"
    "       - **४३ दिने मुख्य उपाय**: लगातार ४३ दिन दिउँसो गरिने ठोस व्यावहारिक उपाय\n"
    "       - **जीव सेवा तथा पारिवारिक नियम**: काग, कुकुर, गाईलाई आहार वा घरको व्यवस्थापन\n"
    "       - **कडा सावधानी (निषेध)**: लाल किताब अनुसार के कहिल्यै नगर्ने वा घरमा नराख्ने\n"
    "३. उपायहरूमा ध्यान: केवल लाल किताबका सहज तथा गहिरा उपायहरूमा जोड दिनुहोस्।\n"
    "४. गणितीय शुद्धता तथा बाह्य गणना नियम: कुण्डलीका ग्रह स्थिति, अंश, भाव, महादशा कहिल्यै अनुमान नगर्नुहोस्। "
    "स्वीस एफिमरिस इन्जिनको तथ्याङ्कलाई अकाट्य सत्य मानी विश्लेषण गर्नुहोस्। कुण्डली उपलब्ध भइसकेपछि फेरि जन्म विवरण नमाग्नुहोस्।\n"
    "५. परम्परा: निरयण राशि चक्र, जोरा-लाहिरी अयनांश, सम्पूर्ण भाव (Whole Sign), विंशोत्तरी दशा र लाल किताब।\n"
    "६. सकारात्मक तथा धर्म-केन्द्रित रूपान्तरण: कहिल्यै त्रासमय वा घातक शब्द प्रयोग नगर्नुहोस्। साढे साती वा राहु दशालाई अनुशासन र लाल किताब उपायद्वारा समाधान दिनुहोस्।\n"
    "७. आधुनिक प्रतीकात्मक रूपान्तरण: प्राचीन श्रापका कुरा अक्षरशः नदोहोर्‍याउनुहोस्; तिनलाई पारिवारिक संस्कार र आचरण सुधारका रूपमा सम्झाउनुहोस्।\n"
    "८. मर्यादापूर्ण वैवाहिक विश्लेषण: कुनै पनि अशिष्ट वा अपमानजनक शब्द प्रयोग नगर्नुहोस्। सम्बन्धको विश्लेषण आदर, समझदारी र संस्कारमा केन्द्रित गर्नुहोस्।\n"
    "९. प्राचीन अंकगणित निषेध: ग्रन्थका प्राचीन नमुना जोडघटाउ वा अंक तालिका नसुनाउनुहोस्, केवल फलित सिद्धान्त लिनुहोस्।\n"
    "१०. व्यावसायिक मर्यादा: चिकित्सा, कानुनी वा वित्तीय मामिलामा सम्बन्धित आधिकारिक विशेषज्ञको सल्लाह लिन भन्नुहोस्।\n"
    "११. अन्त्यमा सन्दर्भ सूची नदोहोर्‍याउनुहोस्: इन्टरफेसले छुट्टै कार्ड देखाउने भएकाले उत्तरको अन्त्यमा 'References' वा 'सन्दर्भहरू' नदोहोर्‍याउनुहोस्।"
)

SYSTEM_PROMPT_NE_NATAL = (
    "तपाईं एक सिद्ध, प्रामाणिक ज्योतिषाचार्य हुनुहुन्छ, जसलाई महर्षि पराशर, मन्त्रेश्वर, र कल्याणवर्माका शास्त्रीय ग्रन्थहरूको गहन ज्ञान छ। "
    "तपाईंको फलादेशले सोधकर्ताको आत्म-स्वरूप, कुण्डलीको मौलिक संरचना, मानसिक-भावनात्मक स्वभाव र जीवनमार्गको गहन, शास्त्रीय तथा मनोवैज्ञानिक विश्लेषण प्रस्तुत गर्दछ।\n\n"
    "मुख्य परामर्श नियमहरू:\n"
    "१. शून्य भूमिका तथा सिधा विश्लेषण (CRITICAL): कुनै पनि अभिवादन वा अनावश्यक भूमिका नबाँध्नुहोस्। उत्तरको पहिलो शब्द नै खण्ड १ ('### १. कुण्डलीको मूल संरचना र लग्न स्वरूप') बाट शुरु हुनुपर्दछ।\n"
    "२. अनिवार्य ४-खम्बे आत्म-परिचय संरचना:\n"
    "   ### १. कुण्डलीको मूल संरचना र लग्न स्वरूप: लग्न राशि, लग्नेशको स्थिति र बल, बाह्य व्यक्तित्व, शारीरिक ऊर्जा, त्रिदोष (वात/पित्त/कफ) प्रकृति र संसारमा व्यक्त हुने स्वरूप।\n"
    "   ### २. मानसिक-भावनात्मक धरातल र चन्द्र-नक्षत्र: चन्द्र राशि, जन्म नक्षत्र, पाउ, र नक्षत्र स्वामी। भित्री मानसिक प्रवृत्ति, संवेगात्मक आवश्यकता, धैर्यता र भावनात्मक शक्ति।\n"
    "   ### ३. आत्मिक उद्देश्य र आत्मकारक ग्रह (सूर्य र आत्मकारक): सूर्यको स्थिति, आत्मकारक ग्रह, र यस जन्मको मूल आत्मिक लक्ष्य तथा चेतनाको दिशा।\n"
    "   ### ४. मुख्य सामर्थ्य, शुभ योग र आत्म-विकास: सक्रिय शुभ योगहरू, जन्मजात प्रतिभा, र जीवनमा सन्तुलन तथा उन्नतिको लागि ध्यान दिनुपर्ने पक्षहरू।\n"
    "३. शुद्धता निर्देशन: आत्म-परिचयको प्रश्नमा अनावश्यक जागिरको फारम भर्ने मिति वा कुकुरलाई रोटी खुवाउने जस्ता असान्दर्भिक कुरा नथोपर्नुहोस्।\n"
    "४. गणितीय शुद्धता तथा बाह्य गणना नियम: कुण्डलीका ग्रह स्थिति, भाव वा दशा कहिल्यै अनुमान नगर्नुहोस्। "
    "स्वीस एफिमरिस इन्जिनको तथ्याङ्कलाई अकाट्य सत्य मानी विश्लेषण गर्नुहोस्।\n"
    "५. अन्त्यमा सन्दर्भ सूची नदोहोर्‍याउनुहोस्।"
)

SYSTEM_PROMPT_NE_HEALTH = (
    "तपाईं एक सिद्ध, प्रामाणिक वैदिक तथा मेडिकल ज्योतिषाचार्य हुनुहुन्छ, जसलाई महर्षि पराशर, "
    "चरक संहिता, सुश्रुत संहिता तथा लाल किताब (१९५२) को स्वास्थ्य तथा आयुर्वेद फलादेशको पूर्ण ज्ञान छ। "
    "तपाईंको फलादेश कुनै च्याटबटको जस्तो अस्पष्ट वा भूमिका बाँधिएको हुँदैन; एक निष्णात ज्योतिषीको जस्तै सिधै "
    "शारीरिक धातु-प्रकृति, रोग भाव (६औं भाव), आयु भाव (८औं भाव), यकिन स्वास्थ्य समय-तालिका र प्रामाणिक दिउँसो गरिने लाल किताब उपाय प्रस्तुत गर्नुहुन्छ।\n\n"
    "मुख्य स्वास्थ्य परामर्श नियमहरू:\n"
    "१. शून्य भूमिका तथा सिधा फलादेश (CRITICAL): कुनै पनि अभिवादन वा अनावश्यक भूमिका नबाँध्नुहोस्। "
    "उत्तरको पहिलो शब्द नै खण्ड १ ('### १. शारीरिक प्रकृति, रोग प्रतिरोधात्मक क्षमता र मुख्य फलादेश') बाट शुरु हुनुपर्दछ।\n"
    "२. अनिवार्य ४-खम्बे स्वास्थ्य संरचना:\n"
    "   ### १. शारीरिक प्रकृति, रोग प्रतिरोधात्मक क्षमता र मुख्य फलादेश: १-२ वाक्यमा सिधै शारीरिक स्वास्थ्य, त्रिदोष (वात/पित्त/कफ) धातु सन्तुलन, लग्न र सूर्यको जीवनी शक्ति (प्राण) को स्पष्ट निर्णय।\n"
    "   ### २. ज्योतिषीय आधार र संवेदनशील अङ्ग विश्लेषण: लग्न (तनु भाव), ६औं (रोग भाव), र ८औं (आयु भाव) का स्वामी, ग्रह स्थिति, विंशोत्तरी दशा, गोचर (शनि/राहु/चन्द्राष्टम), र अष्टकवर्ग (SAV)। धन वा जागिरका असान्दर्भिक योग नल्याउनुहोस्। ग्रन्थका सन्दर्भहरूलाई [१], [२] ले प्रमाणित गर्नुहोस्।\n"
    "   ### ३. स्वास्थ्य समय-तालिका (३ वटा स्पष्ट मिति दायरा YYYY-MM-DD):\n"
    "       - **पहिलो समय: स्वास्थ्य संरक्षण तथा पूर्वतयारी (YYYY-MM-DD देखि YYYY-MM-DD सम्म)**: जीवनशैली सुधार, आहार सन्तुलन र रोग प्रतिरोधात्मक क्षमता बढाउने समय\n"
    "       - **दोस्रो समय: उच्च ऊर्जा तथा स्वास्थ्य लाभ (YYYY-MM-DD देखि YYYY-MM-DD सम्म)**: शारीरिक तन्दुरुस्ती, ऊर्जा र छिटो स्वास्थ्य लाभ हुने समय\n"
    "       - **तेस्रो समय: संवेदनशीलता, विश्राम र सावधानी (YYYY-MM-DD देखि YYYY-MM-DD सम्म)**: न्यून ऊर्जा वा संवेदनशील गोचर (जस्तै चन्द्राष्टम), जसमा खानपान, तनाव र आराममा विशेष ध्यान दिनुपर्ने समय\n"
    "   ### ४. शास्त्रीय आयुर्वेदिक दिनचर्या र लाल किताब उपाय:\n"
    "       - **४३ दिने मुख्य स्वास्थ्य उपाय**: लगातार ४३ दिन दिउँसो घामको प्रकाशमा गरिने ठोस व्यावहारिक उपाय (सूर्यास्त पछि कहिल्यै होइन)\n"
    "       - **आयुर्वेदिक आहार तथा जीव सेवा**: त्रिदोष सन्तुलन गर्ने आहार, दिनचर्या, र चराचुरुङ्गी वा गाईलाई आहार\n"
    "       - **कडा सावधानी (निषेध)**: स्वास्थ्य रक्षाका लागि लाल किताब र आयुर्वेद अनुसार कहिल्यै गर्न नहुने कुरा वा खानपानको परहेज\n"
    "३. दिउँसोको कडा नियम (CRITICAL): सम्पूर्ण लाल किताब उपायहरू अनिवार्य रूपमा सूर्योदयदेखि सूर्यास्तको बीचमा मात्र गर्नुपर्दछ। सूर्यास्त पछि वा राति कुनै उपाय नगर्नुहोस्।\n"
    "४. निषेधित शब्दावली: स्वास्थ्य परामर्शमा जागिर, फारम भर्ने मिति वा 'Application Window' जस्ता शब्द पूर्णतः निषेध छन्।\n"
    "५. चिकित्सा मर्यादा: ज्योतिषीय परामर्श आयुर्वेदिक तथा ऊर्जा विश्लेषण मात्र हो; यो चिकित्सकको जाँच वा औषधोपचारको विकल्प होइन। गम्भीर समस्यामा अनिवार्य रूपमा विशेषज्ञ चिकित्सकको सल्लाह लिनुपर्छ।\n"
    "६. गणितीय शुद्धता तथा बाह्य गणना नियम: कुण्डलीका ग्रह स्थिति, भाव वा दशा कहिल्यै अनुमान नगर्नुहोस्। "
    "स्वीस एफिमरिस इन्जिनको तथ्याङ्कलाई अकाट्य सत्य मानी विश्लेषण गर्नुहोस्।\n"
    "७. अन्त्यमा सन्दर्भ सूची नदोहोर्‍याउनुहोस्।"
)

SYSTEM_PROMPT_NE_REMEDIAL = (
    "तपाईं एक सिद्ध, प्रामाणिक ज्योतिषाचार्य हुनुहुन्छ, जसलाई महर्षि पराशरका शास्त्रीय ग्रन्थहरू तथा "
    "लाल किताब (१९५२) को उपाय प्रणालीको गहन ज्ञान छ। "
    "तपाईंको परामर्शले गणनामा आधारित प्रामाणिक लाल किताब दिउँसो उपायहरू, जीव सेवा र कडा व्यवहारिक सावधानीहरू प्रस्तुत गर्दछ।\n\n"
    "मुख्य परामर्श नियमहरू:\n"
    "१. शून्य भूमिका तथा सिधा परामर्श: सिधै खण्ड १ ('### १. मुख्य ग्रह पीडा र कर्मगत असन्तुलन') बाट शुरु गर्नुहोस्।\n"
    "२. अनिवार्य ४-खम्बे उपाय संरचना: प्रत्येक उपाय परामर्श अनिवार्य रूपमा निम्न ४ खण्डमा हुनुपर्दछ:\n"
    "   ### १. मुख्य ग्रह पीडा र कर्मगत असन्तुलन: कुण्डलीको तथ्याङ्कबाट पीडित ग्रहको यकिन भाव स्थिति, घर र गम्भीरता पहिचान गर्नुहोस्।\n"
    "   ### २. ४३ दिने मुख्य दिउँसो लाल किताब उपाय: सूर्योदयदेखि सूर्यास्तको बीचमा लगातार ४३ दिन गरिने ठोस, व्यावहारिक दिउँसो उपाय।\n"
    "   ### ३. जीव सेवा तथा घरेलु व्यवस्था: गाई, कुकुर, चरा वा माछालाई आहार दिने व्यावहारिक सेवा वा घरको ऊर्जा व्यवस्थापन।\n"
    "   ### ४. कडा सावधानी (निषेध): शास्त्रीय लाल किताब निषेधहरू — के कहिल्यै नगर्ने, नलिने वा घरमा नराख्ने।\n"
    "३. गणितीय शुद्धता तथा बाह्य गणना नियम: कुण्डलीका ग्रह स्थिति, भाव वा दशा कहिल्यै अनुमान नगर्नुहोस्। "
    "स्वीस एफिमरिस इन्जिनको तथ्याङ्कलाई अकाट्य सत्य मानी विश्लेषण गर्नुहोस्।\n"
    "४. अन्त्यमा सन्दर्भ सूची नदोहोर्‍याउनुहोस्।"
)

SYSTEM_PROMPT_NE_CAREER = (
    "तपाईं एक सिद्ध, प्रामाणिक ज्योतिषाचार्य हुनुहुन्छ, जो वैदिक व्यावसायिक ज्योतिष (कर्म भाव, दशमांश D10) मा विशेषज्ञ हुनुहुन्छ। "
    "तपाईंको परामर्शले सिधा व्यावसायिक फलादेश, समय प्रेरक र रणनीतिक व्यावसायिक मार्गदर्शन प्रस्तुत गर्दछ।\n\n"
    "मुख्य परामर्श नियमहरू:\n"
    "१. शून्य भूमिका तथा सिधा परामर्श: सिधै खण्ड १ ('### १. व्यावसायिक क्षमता र कर्म क्षेत्र') बाट शुरु गर्नुहोस्।\n"
    "२. अनिवार्य ४-खम्बे पेशा संरचना: प्रत्येक पेशा परामर्श अनिवार्य रूपमा निम्न ४ खण्डमा हुनुपर्दछ:\n"
    "   ### १. व्यावसायिक क्षमता र कर्म क्षेत्र: दशम भाव, दशमेश, अमात्यकारक ग्रह, व्यावसायिक योग र स्वाभाविक पेशागत क्षमता।\n"
    "   ### २. ज्योतिषीय आधार र समय चक्र: दशम/द्वितीय/षष्ठ/एकादश भावलाई सक्रिय पार्ने दशा उप-अवधि, बृहस्पति-शनि गोचर र अष्टकवर्ग (SAV) बल।\n"
    "   ### ३. यकिन समय-तालिका (३ वटा स्पष्ट मिति दायरा YYYY-MM-DD): तयारीको समय, मुख्य उन्नतिको समय र सतर्कताको समय।\n"
    "   ### ४. व्यावसायिक उन्नति र लाल किताब सावधानी: रणनीतिक व्यावसायिक सल्लाह र सान्दर्भिक नैतिक लाल किताब मार्गदर्शन।\n"
    "३. गणितीय शुद्धता तथा बाह्य गणना नियम: कुण्डलीका ग्रह स्थिति, भाव, दशा वा मिति कहिल्यै अनुमान नगर्नुहोस्। "
    "स्वीस एफिमरिस इन्जिनको तथ्याङ्क र विंशोत्तरी दशा दायरालाई अकाट्य सत्य मानी विश्लेषण गर्नुहोस्। शास्त्रीय श्लोकहरूलाई [१], [२] ले प्रमाणित गर्नुहोस्; कहिल्यै नक्कली सन्दर्भ नबनाउनुहोस्।\n"
    "४. अन्त्यमा सन्दर्भ सूची नदोहोर्‍याउनुहोस्।"
)

SYSTEM_PROMPT_NE_RELATIONSHIP = (
    "तपाईं एक सिद्ध, प्रामाणिक ज्योतिषाचार्य हुनुहुन्छ, जो वैदिक वैवाहिक तथा सम्बन्ध ज्योतिष (कलत्र भाव, नवांश D9) मा विशेषज्ञ हुनुहुन्छ। "
    "तपाईंको परामर्शले मर्यादापूर्ण, गणनामा आधारित सम्बन्ध विश्लेषण, जीवनसाथीको स्वरूप र समय प्रस्तुत गर्दछ।\n\n"
    "मुख्य परामर्श नियमहरू:\n"
    "१. शून्य भूमिका तथा सिधा परामर्श: सिधै खण्ड १ ('### १. वैवाहिक स्वरूप र सप्तम भाव विश्लेषण') बाट शुरु गर्नुहोस्।\n"
    "२. अनिवार्य ४-खम्बे सम्बन्ध संरचना: प्रत्येक सम्बन्ध परामर्श अनिवार्य रूपमा निम्न ४ खण्डमा हुनुपर्दछ:\n"
    "   ### १. वैवाहिक स्वरूप र सप्तम भाव विश्लेषण: सप्तम भाव, सप्तमेश, शुक्र/बृहस्पतिको स्थिति र बल, दाराकारक ग्रह र साझेदारी प्रवृत्ति।\n"
    "   ### २. जीवनसाथीको स्वभाव र भावनात्मक सामन्जस्य: जीवनसाथीको आचरण, गुण र भावनात्मक स्वभाव; चन्द्र-चन्द्र सम्बन्ध सामन्जस्य।\n"
    "   ### ३. सम्बन्ध तथा विवाहको यकिन समय-तालिका (YYYY-MM-DD): सक्रिय दशा उप-अवधि र सप्तम वा लग्नमा बृहस्पति/शनि गोचर अनुसार विवाह वा सम्बन्धका स्पष्ट समय दायरा।\n"
    "   ### ४. पारिवारिक सुख र लाल किताब सावधानी: व्यावहारिक सम्बन्ध ज्ञान, स्वस्थ संवाद सीमा र लाल किताब सावधानीहरू।\n"
    "३. मर्यादापूर्ण वैवाहिक विश्लेषण: कुनै पनि अशिष्ट वा अपमानजनक शब्द प्रयोग नगर्नुहोस्। सम्बन्धको विश्लेषण आदर, समझदारी र संस्कारमा केन्द्रित गर्नुहोस्।\n"
    "४. गणितीय शुद्धता तथा बाह्य गणना नियम: कुण्डलीका ग्रह स्थिति, भाव वा दशा कहिल्यै अनुमान नगर्नुहोस्। "
    "स्वीस एफिमरिस इन्जिनको तथ्याङ्कलाई अकाट्य सत्य मानी विश्लेषण गर्नुहोस्।\n"
    "५. अन्त्यमा सन्दर्भ सूची नदोहोर्‍याउनुहोस्।"
)

SYSTEM_PROMPT_NE_CONCEPTUAL = (
    "तपाईं एक सिद्ध, प्रामाणिक ज्योतिषाचार्य हुनुहुन्छ, जसलाई शास्त्रीय ग्रन्थहरूको पूर्ण ज्ञान छ। "
    "तपाईंको परामर्शले शास्त्रीय सिद्धान्त, योग र ज्योतिषीय संयन्त्रलाई गहन स्पष्टता र शास्त्रीय आधारसहित व्याख्या गर्दछ।\n\n"
    "मुख्य परामर्श नियमहरू:\n"
    "१. शून्य भूमिका तथा सिधा व्याख्या: सिधै खण्ड १ ('### १. शास्त्रीय परिभाषा र ग्रन्थको आधार') बाट शुरु गर्नुहोस्।\n"
    "२. अनिवार्य ४-खम्बे शास्त्रीय संरचना: प्रत्येक शास्त्रीय व्याख्या अनिवार्य रूपमा निम्न ४ खण्डमा हुनुपर्दछ:\n"
    "   ### १. शास्त्रीय परिभाषा र ग्रन्थको आधार: शास्त्रीय ग्रन्थ अनुसारको निश्चित परिभाषा, प्रदान गरिएका श्लोकहरूबाट [१], [२] प्रमाणसहित।\n"
    "   ### २. ज्योतिषीय आधार र निर्माण नियम: ग्रह संयन्त्र, भाव संयोग, ग्रह बल र भङ्ग (रद्द हुने) नियमहरू।\n"
    "   ### ३. व्यावहारिक जीवनमा प्रभाव र लक्षण: यो सिद्धान्त मानव जीवन, चरित्र र घटनाक्रममा कसरी प्रकट हुन्छ।\n"
    "   ### ४. सकारात्मक रूपान्तरण र मार्गदर्शन: यस शास्त्रीय सिद्धान्तको आध्यात्मिक उद्देश्य र व्यावहारिक मार्गदर्शन।\n"
    "३. गणितीय शुद्धता तथा बाह्य गणना नियम: कुण्डली सन्दर्भ दिइएको अवस्थामा ग्रह स्थिति, भाव वा दशा कहिल्यै अनुमान नगर्नुहोस्; "
    "स्वीस एफिमरिस इन्जिनको तथ्याङ्कलाई अकाट्य सत्य मान्नुहोस्। प्रदान गरिएका श्लोकहरू मात्र उद्धृत गर्नुहोस्; कहिल्यै नक्कली सन्दर्भ नबनाउनुहोस्।\n"
    "४. अन्त्यमा सन्दर्भ सूची नदोहोर्‍याउनुहोस्।"
)

# Backwards compatibility globals
SYSTEM_PROMPT = SYSTEM_PROMPT_PREDICTION
SYSTEM_PROMPT_NE = SYSTEM_PROMPT_NE_PREDICTION


def get_system_prompt(
    language: str = "en",
    intent: ConsultationIntent | str | None = None,
) -> str:
    """Return language and intent-specific system prompt."""
    lang = (language or "en").lower().strip()
    is_ne = lang in ("ne", "nepali", "nep")

    if intent is None:
        intent_val = ConsultationIntent.EVENT_PREDICTION
    elif isinstance(intent, ConsultationIntent):
        intent_val = intent
    else:
        try:
            intent_val = ConsultationIntent(str(intent).lower().strip())
        except ValueError:
            intent_val = ConsultationIntent.EVENT_PREDICTION

    if is_ne:
        if intent_val == ConsultationIntent.NATAL_IDENTITY:
            return SYSTEM_PROMPT_NE_NATAL
        if intent_val == ConsultationIntent.HEALTH_WELLNESS:
            return SYSTEM_PROMPT_NE_HEALTH
        if intent_val == ConsultationIntent.REMEDIAL:
            return SYSTEM_PROMPT_NE_REMEDIAL
        if intent_val == ConsultationIntent.CAREER_FINANCE:
            return SYSTEM_PROMPT_NE_CAREER
        if intent_val == ConsultationIntent.RELATIONSHIP:
            return SYSTEM_PROMPT_NE_RELATIONSHIP
        if intent_val == ConsultationIntent.CONCEPTUAL:
            return SYSTEM_PROMPT_NE_CONCEPTUAL
        return SYSTEM_PROMPT_NE_PREDICTION

    if intent_val == ConsultationIntent.NATAL_IDENTITY:
        return SYSTEM_PROMPT_NATAL
    if intent_val == ConsultationIntent.HEALTH_WELLNESS:
        return SYSTEM_PROMPT_HEALTH
    if intent_val == ConsultationIntent.REMEDIAL:
        return SYSTEM_PROMPT_REMEDIAL
    if intent_val == ConsultationIntent.CAREER_FINANCE:
        return SYSTEM_PROMPT_CAREER
    if intent_val == ConsultationIntent.RELATIONSHIP:
        return SYSTEM_PROMPT_RELATIONSHIP
    if intent_val == ConsultationIntent.CONCEPTUAL:
        return SYSTEM_PROMPT_CONCEPTUAL
    return SYSTEM_PROMPT_PREDICTION


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
    # Post-generation validation (Task 13 step 1): flags for chart claims
    # that do not match the chart context and for dropped citations.
    # None for answers that were not LLM-validated (e.g. fallback).
    validation: ValidationResult | None = None


class BaseSynthesizer(ABC):
    """Interface for answer synthesizers."""

    @abstractmethod
    def synthesize(
        self,
        question: str,
        results: list[SearchResult],
        birth_context: dict[str, Any] | None = None,
        language: str = "en",
    ) -> Answer:
        """Generate an answer from retrieved search results."""

    def synthesize_stream(
        self,
        question: str,
        results: list[SearchResult],
        birth_context: dict[str, Any] | None = None,
        language: str = "en",
    ) -> Iterator[str]:
        """Stream answer tokens. Defaults to yielding complete synthesized text."""
        ans = self.synthesize(question, results, birth_context, language=language)
        yield ans.answer


def _citation_label(index: int, result: SearchResult) -> str:
    """Format '[n] Work, Chapter X, Verse Y' for the prompt."""
    parts = [result.chunk.work]
    if result.chunk.chapter:
        parts.append(f"Chapter {result.chunk.chapter}")
    if result.chunk.verse:
        parts.append(f"Verse {result.chunk.verse}")
    return f"[{index}] {' '.join(parts)}"


_ZODIAC_SIGNS = [
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
]
_SIGN_LORDS = {
    "Aries": "Mars",
    "Taurus": "Venus",
    "Gemini": "Mercury",
    "Cancer": "Moon",
    "Leo": "Sun",
    "Virgo": "Mercury",
    "Libra": "Venus",
    "Scorpio": "Mars",
    "Sagittarius": "Jupiter",
    "Capricorn": "Saturn",
    "Aquarius": "Saturn",
    "Pisces": "Jupiter",
}


def _clean_node_name(name: str | None) -> str:
    """Display name for a dasha lord ('North Node' -> 'Rahu')."""
    if not name:
        return "Unknown"
    if name == "North Node":
        return "Rahu"
    if name == "South Node":
        return "Ketu"
    return name


def _format_muhurtha_lines(muh: dict[str, Any], reference: str) -> list[str]:
    """Render a MuhurthaReport dict as bounded summary lines.

    Never invents times: a missing sunrise (polar day/night) is reported as
    such, and a missing/incomplete report yields an explicit unavailable
    line instead of fabricated hora/choghadiya windows.
    """
    lines = [f"- Muhurtha (Timing, reference moment: {reference}):"]
    sunrise = muh.get("sunrise_time")
    sunset = muh.get("sunset_time")
    if sunrise is None and sunset is None:
        lines.append(
            "  • No sunrise/sunset on this day at this place (polar day/night); "
            "muhurtha windows are unavailable — do not invent times."
        )
        return lines
    if sunrise:
        lines.append(f"  • Sunrise {sunrise} | Sunset {sunset or '—'}")
    hora = muh.get("current_hora") or {}
    if isinstance(hora, dict) and hora.get("ruling_planet"):
        lines.append(
            f"  • Current Hora: {hora.get('ruling_planet')} Hora "
            f"({hora.get('start_time')} - {hora.get('end_time')}) [{hora.get('nature')}]"
        )
    chog = muh.get("current_choghadiya") or {}
    if isinstance(chog, dict) and chog.get("name"):
        lines.append(
            f"  • Current Choghadiya: {chog.get('name')} ({chog.get('ruler')}, "
            f"{chog.get('start_time')} - {chog.get('end_time')}) "
            f"[{chog.get('nature')} | Score: {chog.get('score')}]"
        )
    rahu_kalam = muh.get("rahu_kalam") or {}
    if isinstance(rahu_kalam, dict) and rahu_kalam.get("start_time"):
        active = " [ACTIVE NOW — avoid new beginnings]" if rahu_kalam.get("is_active") else ""
        lines.append(
            f"  • Rahu Kalam [AVOID]: {rahu_kalam.get('start_time')} - "
            f"{rahu_kalam.get('end_time')}{active}"
        )
    abhijit = muh.get("abhijit_muhurtha") or {}
    if isinstance(abhijit, dict) and abhijit.get("start_time"):
        active = " [ACTIVE NOW]" if abhijit.get("is_active") else ""
        lines.append(
            f"  • Abhijit Muhurtha: {abhijit.get('start_time')} - "
            f"{abhijit.get('end_time')}{active}"
        )
    score = muh.get("muhurtha_score")
    verdict = muh.get("verdict")
    if score is not None or verdict:
        lines.append(
            f"  • Muhurtha Score: {score}/100 — {verdict or ''}".rstrip(" —")
        )
    return lines


def _format_birth_summary(
    chart: dict[str, Any], include_muhurtha: bool = False
) -> str:
    """Format structured natal chart facts, house lords, ashtakavarga, and transits for synthesis.

    ``include_muhurtha`` is True only for timing questions (Event Prediction
    intent, decided by :func:`build_prompt`): the muhurtha lines describe the
    query moment at the birth place, and are omitted otherwise.
    """
    lines: list[str] = []

    # Explicit Seeker Birth Details (Ground Truth)
    bdata = chart.get("birth_data")
    if isinstance(bdata, dict) and bdata.get("year"):
        lines.append(
            f"### SEEKER BIRTH DETAILS (GROUND TRUTH):\n"
            f"- Birth Date & Time: {bdata.get('year'):04d}-{bdata.get('month', 1):02d}-{bdata.get('day', 1):02d} "
            f"{bdata.get('hour', 0):02d}:{bdata.get('minute', 0):02d} ({bdata.get('timezone', 'UTC')})\n"
            f"- Coordinates: Lat {bdata.get('latitude', 0):.2f}°, Lon {bdata.get('longitude', 0):.2f}°"
        )

    asc = chart.get("ascendant")
    lagna_sign: str | None = None
    if isinstance(asc, dict):
        lagna_sign = asc.get("sign")
        deg = asc.get("degree_in_sign", 0)
        lines.append(
            f"- Lagna (Ascendant): {lagna_sign} at {deg:.2f}° "
            f"(Nakshatra: {asc.get('nakshatra')} Pada {asc.get('pada')}, Lord: {asc.get('nakshatra_lord')})"
        )
    elif isinstance(asc, str):
        lagna_sign = asc
        lines.append(f"- Lagna (Ascendant): {asc}")

    # Explicit 12 House Lords ground truth
    if lagna_sign and lagna_sign in _ZODIAC_SIGNS:
        lagna_idx = _ZODIAC_SIGNS.index(lagna_sign)
        house_lord_parts: list[str] = []
        for h in range(1, 13):
            s_idx = (lagna_idx + h - 1) % 12
            h_sign = _ZODIAC_SIGNS[s_idx]
            h_lord = _SIGN_LORDS[h_sign]
            house_lord_parts.append(f"H{h} ({h_sign}) lord: {h_lord}")
        lines.append("- Exact House Rulerships (Bhaveshas): " + " | ".join(house_lord_parts))

        # Health & Vitality Significators (Tanu, Roga, Ayur Bhavas)
        h1_sign = _ZODIAC_SIGNS[lagna_idx]
        h6_sign = _ZODIAC_SIGNS[(lagna_idx + 5) % 12]
        h8_sign = _ZODIAC_SIGNS[(lagna_idx + 7) % 12]
        h1_lord = _SIGN_LORDS[h1_sign]
        h6_lord = _SIGN_LORDS[h6_sign]
        h8_lord = _SIGN_LORDS[h8_sign]
        lines.append(
            f"- Vitality & Health Signposts: Tanu Bhava (1st House - Constitution/Immunity): {h1_sign} (Lord: {h1_lord}) | "
            f"Roga Bhava (6th House - Acute Ailments/Agni): {h6_sign} (Lord: {h6_lord}) | "
            f"Ayur Bhava (8th House - Longevity/Chronic Vulnerabilities): {h8_sign} (Lord: {h8_lord})"
        )

    planets = chart.get("planets")
    if isinstance(planets, list):
        rahu = chart.get("rahu")
        ketu = chart.get("ketu")
        all_bodies = [p for p in planets if isinstance(p, dict)]
        if isinstance(rahu, dict):
            all_bodies.append(rahu)
        if isinstance(ketu, dict):
            all_bodies.append(ketu)

        if all_bodies:
            lines.append("- Natal Planetary Placements (Grahas in Bhavas):")
            for p in all_bodies:
                retro = " (Retrograde)" if p.get("retrograde") else ""
                deg_val = p.get("degree_in_sign", 0)
                dignity_val = p.get("dignity")
                dignity_str = f" [{str(dignity_val).capitalize()}]" if dignity_val else ""
                lines.append(
                    f"  • {p.get('name')}: House {p.get('house')} in {p.get('sign')} "
                    f"({deg_val:.2f}° {p.get('nakshatra')} Pada {p.get('pada')}){retro}{dignity_str}"
                )

            # Synthesize Lagna Lord Placement
            if lagna_sign:
                lagna_lord_name = _SIGN_LORDS.get(lagna_sign)
                lagna_lord_body = next(
                    (b for b in all_bodies if b.get("name") == lagna_lord_name), None
                )
                if lagna_lord_body:
                    ll_retro = " (Retrograde)" if lagna_lord_body.get("retrograde") else ""
                    ll_deg = lagna_lord_body.get("degree_in_sign", 0)
                    lines.append(
                        f"- Lagna Lord Placement: {lagna_lord_name} sits in House {lagna_lord_body.get('house')} "
                        f"in {lagna_lord_body.get('sign')} ({ll_deg:.2f}° {lagna_lord_body.get('nakshatra')}){ll_retro}"
                    )

            # Jaimini 7 Chara Karakas (Soul, Career, Spouse Indicators)
            traditional_7 = [
                b
                for b in planets
                if isinstance(b, dict)
                and b.get("name")
                in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
            ]
            if len(traditional_7) == 7:
                sorted_by_deg = sorted(
                    traditional_7,
                    key=lambda b: float(b.get("degree_in_sign", 0)),
                    reverse=True,
                )
                ak = sorted_by_deg[0]  # Atmakaraka (Soul)
                amk = sorted_by_deg[1]  # Amatyakaraka (Career/Action)
                dk = sorted_by_deg[6]  # Darakaraka (Spouse/Partnership)
                lines.append(
                    f"- Jaimini Chara Karakas: Atmakaraka (Soul): {ak.get('name')} ({ak.get('degree_in_sign', 0):.2f}°), "
                    f"Amatyakaraka (Career/Action): {amk.get('name')} ({amk.get('degree_in_sign', 0):.2f}°), "
                    f"Darakaraka (Spouse/Partnership): {dk.get('name')} ({dk.get('degree_in_sign', 0):.2f}°)"
                )

            # Health & Longevity Karakas (Surya Vitality, Shani Longevity)
            sun_body = next((b for b in all_bodies if b.get("name") == "Sun"), None)
            sat_body = next((b for b in all_bodies if b.get("name") == "Saturn"), None)
            if sun_body and sat_body:
                lines.append(
                    f"- Vitality & Longevity Karakas: Sun (Prana/Vitality): House {sun_body.get('house')} in {sun_body.get('sign')} | "
                    f"Saturn (Ayushkaraka/Longevity): House {sat_body.get('house')} in {sat_body.get('sign')}"
                )

    # Divisional charts: Navamsha (D9, spouse/dharma/fortune) and Dashamsha
    # (D10, career) status as one bounded line each — signs only, never the
    # 16-varga dump. Vargottama = planet in the same sign in D1 and D9.
    vargas = chart.get("vargas")
    if isinstance(vargas, dict):
        d1_signs: dict[str, str] = {}
        if isinstance(planets, list):
            for p in planets:
                if isinstance(p, dict) and p.get("name") and p.get("sign"):
                    d1_signs[str(p["name"])] = str(p["sign"])
        rahu_d = chart.get("rahu")
        ketu_d = chart.get("ketu")
        if isinstance(rahu_d, dict) and rahu_d.get("sign"):
            d1_signs["North Node"] = str(rahu_d["sign"])
        if isinstance(ketu_d, dict) and ketu_d.get("sign"):
            d1_signs["South Node"] = str(ketu_d["sign"])

        def _varga_line(v_key: str, label: str) -> str | None:
            v_data = vargas.get(v_key)
            if not isinstance(v_data, dict) or not v_data:
                return None
            order = [
                "Sun",
                "Moon",
                "Mars",
                "Mercury",
                "Jupiter",
                "Venus",
                "Saturn",
                "North Node",
                "South Node",
            ]
            parts: list[str] = []
            for name in order:
                sign = v_data.get(name)
                if not sign:
                    continue
                disp = (
                    "Rahu"
                    if name == "North Node"
                    else "Ketu"
                    if name == "South Node"
                    else name
                )
                parts.append(f"{disp} {sign}")
            if not parts:
                return None
            asc_sign = v_data.get("Ascendant")
            line = f"- {label}: "
            if asc_sign:
                line += f"Lagna {asc_sign}; "
            line += ", ".join(parts)
            if v_key == "D9":
                vargottama = [
                    ("Rahu" if n == "North Node" else "Ketu" if n == "South Node" else n)
                    for n in order
                    if d1_signs.get(n) and d1_signs.get(n) == v_data.get(n)
                ]
                if vargottama:
                    line += f" [Vargottama (same sign in D1 and D9): {', '.join(vargottama)}]"
            return line

        d9_line = _varga_line("D9", "Navamsha (D9)")
        if d9_line:
            lines.append(d9_line)
        d10_line = _varga_line("D10", "Dashamsha (D10)")
        if d10_line:
            # Prefer the precomputed D10 chart (houses) when present.
            d10_chart = chart.get("d10_chart")
            if isinstance(d10_chart, dict):
                d10_asc = (d10_chart.get("ascendant") or {}).get("sign")
                d10_planets = d10_chart.get("planets") or {}
                if d10_asc and isinstance(d10_planets, dict) and d10_planets:
                    d10_parts = []
                    for name in [
                        "Sun",
                        "Moon",
                        "Mars",
                        "Mercury",
                        "Jupiter",
                        "Venus",
                        "Saturn",
                        "North Node",
                        "South Node",
                    ]:
                        entry = d10_planets.get(name)
                        if isinstance(entry, dict) and entry.get("sign"):
                            disp = (
                                "Rahu"
                                if name == "North Node"
                                else "Ketu"
                                if name == "South Node"
                                else name
                            )
                            d10_parts.append(
                                f"{disp} {entry['sign']} (H{entry.get('house')})"
                            )
                    if d10_parts:
                        d10_line = (
                            f"- Dashamsha (D10): Lagna {d10_asc}; "
                            + ", ".join(d10_parts)
                        )
            lines.append(d10_line)

    # Real Ashtakavarga Points: Grouped cleanly by house strength rather than a raw dump of 12 signs
    av = chart.get("ashtakavarga")
    if isinstance(av, dict):
        sav = av.get("sarvashtakavarga")
        if isinstance(sav, list) and len(sav) == 12:
            if lagna_sign and lagna_sign in _ZODIAC_SIGNS:
                lagna_idx = _ZODIAC_SIGNS.index(lagna_sign)
                house_scores: list[tuple[int, str, int]] = []
                for h in range(1, 13):
                    s_idx = (lagna_idx + h - 1) % 12
                    h_sign = _ZODIAC_SIGNS[s_idx]
                    pts = sav[s_idx]
                    house_scores.append((h, h_sign, pts))

                strong = [
                    f"House {h} ({sign}: {pts})" for h, sign, pts in house_scores if pts >= 30
                ]
                moderate = [
                    f"House {h} ({sign}: {pts})" for h, sign, pts in house_scores if 25 <= pts < 30
                ]
                sensitive = [
                    f"House {h} ({sign}: {pts})" for h, sign, pts in house_scores if pts < 25
                ]

                lines.append("- Sarvashtakavarga (SAV Points by House from Lagna):")
                if strong:
                    lines.append(f"  • High Strength Houses (SAV >= 30 bindus): {', '.join(strong)}")
                if moderate:
                    lines.append(
                        f"  • Moderate Strength Houses (SAV 25-29 bindus): {', '.join(moderate)}"
                    )
                if sensitive:
                    lines.append(
                        f"  • Sensitive Effort Houses (SAV < 25 bindus): {', '.join(sensitive)}"
                    )
                lines.append(
                    "  [SAV DIRECTIVE: Do NOT recite all 12 signs or scores in a raw list. Mention only the specific house relevant to the query; >28 bindus = natural strength and endurance, <28 bindus = requires conscious focus.]"
                )
            else:
                sav_items = [f"{_ZODIAC_SIGNS[i]}: {sav[i]}" for i in range(12)]
                lines.append(
                    "- Calculated Sarvashtakavarga (SAV Points per Sign): " + ", ".join(sav_items)
                )

    # Real-Time Astronomical Transits (Gochara)
    transits = chart.get("transits")
    if isinstance(transits, dict):
        t_time = transits.get("transit_time", "Active")
        lines.append(f"- Astronomical Planetary Transits (Gochara as of {t_time}):")
        t_planets = transits.get("planets") or []
        for tp in t_planets:
            if isinstance(tp, dict):
                fav = " [Auspicious from Moon]" if tp.get("is_favorable_gochar") else ""
                bav_str = (
                    f", BAV: {tp.get('bav_bindus')}" if tp.get("bav_bindus") is not None else ""
                )
                sav_str = (
                    f", SAV: {tp.get('sav_bindus')}" if tp.get("sav_bindus") is not None else ""
                )
                retro = " (Retrograde)" if tp.get("retrograde") else ""
                lines.append(
                    f"  • Transit {tp.get('name')}: {tp.get('sign')} ({tp.get('degree_in_sign', 0):.2f}° {tp.get('nakshatra')}){retro} "
                    f"-> House {tp.get('house_from_lagna')} from Lagna, House {tp.get('house_from_moon')} from Moon"
                    f"{sav_str}{bav_str}{fav}"
                )
        sade_sati = transits.get("sade_sati") or {}
        if sade_sati.get("is_active"):
            lines.append(f"  • Saturn Sade Sati: ACTIVE ({sade_sati.get('phase')})")
        elif sade_sati.get("is_ashtama_shani"):
            lines.append("  • Saturn Ashtama Shani: ACTIVE (8th from Moon)")
        elif sade_sati.get("is_kantaka_shani"):
            lines.append("  • Saturn Kantaka Shani: ACTIVE (4th/10th from Moon)")

        double_tr = transits.get("double_transit_houses") or []
        if double_tr:
            lines.append(
                f"  • Double Transit Focus (Jupiter + Saturn jointly influencing Bhavas): Houses {', '.join(map(str, double_tr))}"
            )

        tr_win = transits.get("window") or chart.get("transit_window")
        if isinstance(tr_win, dict):
            w_events = tr_win.get("events") or []
            if w_events:
                e_lines = [
                    f"{e.get('date')}: {e.get('description')}"
                    for e in w_events[:6]
                    if isinstance(e, dict) and e.get("description")
                ]
                lines.append(
                    f"  • Upcoming Monthly Transit Triggers ({tr_win.get('days_scanned', 30)} Days):\n    - "
                    + "\n    - ".join(e_lines)
                )
            c_periods = tr_win.get("chandrashtama_periods") or []
            if c_periods:
                c_strs = [
                    f"{cp.get('start_date')} to {cp.get('end_date')}"
                    for cp in c_periods
                    if isinstance(cp, dict)
                ]
                lines.append(
                    f"  • Chandrashtama Sensitive Windows (Moon in 8th from Natal Moon - Caution for speculation/disputes): {'; '.join(c_strs)}"
                )

    dashas = chart.get("dashas")
    if isinstance(dashas, dict):
        curr_md = dashas.get("current_md") or {}
        curr_ad = dashas.get("current_ad") or {}
        curr_pd = dashas.get("current_pd") or {}

        md_lord = _clean_node_name(curr_md.get("lord"))
        ad_lord = _clean_node_name(curr_ad.get("lord"))
        pd_lord = _clean_node_name(curr_pd.get("lord"))

        md_s = (curr_md.get("start") or "")[:10]
        md_e = (curr_md.get("end") or "")[:10]
        ad_s = (curr_ad.get("start") or "")[:10]
        ad_e = (curr_ad.get("end") or "")[:10]
        pd_s = (curr_pd.get("start") or "")[:10]
        pd_e = (curr_pd.get("end") or "")[:10]

        lines.append("- Operating Vimshottari Dasha Hierarchy (Deterministic Timing Ground Truth):")
        lines.append(f"  • Current Mahadasha: [{md_lord}] from {md_s} to {md_e}")
        lines.append(f"  • Current Antardasha: [{ad_lord}] from {ad_s} to {ad_e} [ACTIVE NOW]")
        lines.append(f"  • Current Pratyantardasha: [{pd_lord}] from {pd_s} to {pd_e} [ACTIVE NOW]")

        # Full Mahadasha ranges, past + future (bounded summary lines, not the
        # full dasha tree): the LLM must ground any "when" answer in these
        # ranges, not only in the current MD/AD/PD above.
        all_mds = dashas.get("mahadashas") or []
        if all_mds:
            birth_date_str = ""
            if isinstance(bdata, dict) and bdata.get("year"):
                birth_date_str = (
                    f"{bdata.get('year'):04d}-{bdata.get('month', 1):02d}-"
                    f"{bdata.get('day', 1):02d}"
                )
            md_lines = []
            for md in all_mds:
                if not isinstance(md, dict):
                    continue
                lord = _clean_node_name(md.get("lord"))
                s_date = (md.get("start") or "")[:10]
                e_date = (md.get("end") or "")[:10]
                tag = " [CURRENT]" if lord == md_lord else ""
                if birth_date_str and s_date <= birth_date_str <= e_date:
                    tag += " [IN EFFECT AT BIRTH]"
                md_lines.append(f"{lord}: {s_date} to {e_date}{tag}")
            if md_lines:
                lines.append(
                    "  • Full Mahadasha Timeline (Vimshottari, past + future):\n    - "
                    + "\n    - ".join(md_lines)
                )

        mahadashas = dashas.get("mahadashas") or []
        for md in mahadashas:
            if isinstance(md, dict) and _clean_node_name(md.get("lord")) == md_lord:
                ad_subs = md.get("subs") or []
                if ad_subs:
                    ad_lines = []
                    for ad in ad_subs:
                        s_date = (ad.get("start") or "")[:10]
                        e_date = (ad.get("end") or "")[:10]
                        lord_name = _clean_node_name(ad.get("lord"))
                        is_active = lord_name == ad_lord and s_date == ad_s
                        tag = " [ACTIVE NOW]" if is_active else ""
                        ad_lines.append(f"{md_lord}/{lord_name}: {s_date} to {e_date}{tag}")
                    lines.append(
                        f"  • Full Antardasha Timeline ({md_lord} Mahadasha):\n    - "
                        + "\n    - ".join(ad_lines)
                    )

                for ad in ad_subs:
                    if (
                        _clean_node_name(ad.get("lord")) == ad_lord
                        and (ad.get("start") or "")[:10] == ad_s
                    ):
                        pd_subs = ad.get("subs") or []
                        if pd_subs:
                            pd_lines = []
                            for pd in pd_subs:
                                s_date = (pd.get("start") or "")[:10]
                                e_date = (pd.get("end") or "")[:10]
                                lord_name = _clean_node_name(pd.get("lord"))
                                is_active = lord_name == pd_lord and s_date == pd_s
                                tag = " [ACTIVE NOW]" if is_active else ""
                                pd_lines.append(
                                    f"{md_lord}/{ad_lord}/{lord_name}: {s_date} to {e_date}{tag}"
                                )
                            lines.append(
                                f"  • Active Pratyantardasha Micro-Windows ({md_lord}/{ad_lord}):\n    - "
                                + "\n    - ".join(pd_lines)
                            )
                        break
                break

    # Parashari Graha Drishti (House Aspects Received)
    v_aspects = chart.get("vedic_aspects")
    if isinstance(v_aspects, list) and v_aspects:
        aspects_by_house: dict[int, list[str]] = {}
        for va in v_aspects:
            if isinstance(va, dict):
                th = va.get("target_house")
                pl = va.get("planet")
                at = va.get("aspect_type")
                if th and pl:
                    aspects_by_house.setdefault(int(th), []).append(f"{pl} ({at})")
        if aspects_by_house:
            asp_strs = [
                f"House {h}: aspected by {', '.join(aspects_by_house[h])}"
                for h in sorted(aspects_by_house.keys())
            ]
            lines.append(
                "- Graha Drishti (Classical House Aspects Received):\n  • "
                + "\n  • ".join(asp_strs)
            )

    yogas = chart.get("yogas")
    if isinstance(yogas, list):
        yoga_names = [str(y["name"]) for y in yogas if isinstance(y, dict) and y.get("name")]
        if yoga_names:
            lines.append(f"- Active Yogas: {', '.join(yoga_names[:5])}")

    # Compatibility: Kuja Dosha is single-chart, so it is always rendered when
    # the chart context carries it (api.py attaches it from ChartData).
    # Ashtakoota needs TWO charts, and /rag/ask has only one: render the
    # score only when partner data is actually present in the context,
    # otherwise say so honestly — never invent a score.
    kuja = chart.get("kuja_dosha")
    compat = chart.get("compatibility")
    if not isinstance(kuja, dict) and isinstance(compat, dict):
        kuja = compat.get("kuja_dosha")
    ashtakoota = chart.get("ashtakoota")
    if not isinstance(ashtakoota, dict) and isinstance(compat, dict):
        ashtakoota = compat.get("ashtakoota")
    lines.append("- Compatibility & Kuja Dosha (Marriage Matching Ground Truth):")
    if isinstance(kuja, dict) and kuja:
        status = "Manglik" if kuja.get("is_manglik") else "Non-Manglik"
        severity = kuja.get("severity") or "None"
        score = kuja.get("score")
        score_str = f", score {score}" if score is not None else ""
        afflicted: list[str] = []
        for ref, key in (
            ("Lagna", "afflicted_houses_lagna"),
            ("Moon", "afflicted_houses_moon"),
            ("Venus", "afflicted_houses_venus"),
        ):
            houses = kuja.get(key) or []
            if houses:
                afflicted.append(f"Mars in {', '.join(str(h) for h in houses)} from {ref}")
        afflicted_str = (
            f"; afflicted: {'; '.join(afflicted)}" if afflicted else "; Mars in no Manglik house"
        )
        cancellations = kuja.get("cancellations") or []
        cancel_str = (
            f"; cancellations: {'; '.join(str(c) for c in cancellations)}"
            + (" (dosha cancelled)" if kuja.get("is_cancelled") else "")
            if cancellations
            else ""
        )
        lines.append(
            f"  • Kuja Dosha: {status} — severity {severity}{score_str}"
            f"{afflicted_str}{cancel_str}"
        )
    else:
        lines.append(
            "  • Kuja Dosha: not evaluated in the chart context provided; "
            "do not assume Manglik status."
        )
    if isinstance(ashtakoota, dict) and ashtakoota.get("total_score") is not None:
        total = ashtakoota.get("total_score")
        pct = ashtakoota.get("percentage")
        verdict = ashtakoota.get("verdict") or ""
        pct_str = f" ({pct}%)" if pct is not None else ""
        verdict_str = f" — {verdict}" if verdict else ""
        lines.append(f"  • Ashtakoota: {total}/36{pct_str}{verdict_str}")
    else:
        lines.append(
            "  • Ashtakoota: no partner chart provided — no compatibility "
            "score calculated; do not invent one."
        )

    predictions = chart.get("predictions")
    if isinstance(predictions, dict):
        lines.append("- Classical Hierarchical Predictions (Deterministic Engine Ground Truth):")
        for dom_key, pred in predictions.items():
            if isinstance(pred, dict):
                dom_label = str(pred.get("domain", dom_key)).upper()
                tier = pred.get("promise_tier", "Evaluated")
                verdict = pred.get("key_verdict", "")
                p_sum = pred.get("promise_summary", "")
                d_tim = pred.get("dasha_timing", "")
                tr = ", ".join(pred.get("active_transits", []))
                yo = ", ".join(pred.get("active_yogas", []))
                lines.append(
                    f"  • {dom_label} [{tier}]: {verdict}\n"
                    f"    - Natal Promise: {p_sum}\n"
                    f"    - Dasha Trigger: {d_tim}\n"
                    f"    - Active Transits: {tr}\n"
                    f"    - Active Yogas: {yo or 'Standard classical influence'}"
                )

    remedies = chart.get("remedies")
    if isinstance(remedies, dict):
        afflicted = remedies.get("afflicted_planets") or []
        if afflicted:
            lines.append("- Classical Lal Kitab 108 Upayas & Inviolable Precautions (Ground Truth):")
            for p_rem in afflicted[:4]:
                if isinstance(p_rem, dict):
                    pl = p_rem.get("planet", "")
                    h = p_rem.get("house", "")
                    sev = str(p_rem.get("severity", "mild")).upper()
                    lk = p_rem.get("lal_kitab") or {}
                    h_rem = lk.get("household_remedy", "")
                    sym = lk.get("symbolic_action", "")
                    forb = lk.get("forbidden_actions") or []
                    creature = lk.get("creature_service", "")
                    lines.append(
                        f"  • {pl} in House {h} [{sev} AFFLICTION]:\n"
                        f"    - 43-Day Daytime Upaya: {sym or h_rem}\n"
                        f"    - Creature / Household Seva: {creature or h_rem}\n"
                        f"    - Inviolable Savdhani (Strict Precaution): {'; '.join(forb[:2]) if forb else 'Maintain clean ethical conduct'}"
                    )

    # Muhurtha — timing questions only (see build_prompt). The reference
    # moment is the query moment at the birth place, stated in the line so
    # the model never mistakes it for a birth-time muhurtha. If the
    # calculation fails, say so; never invent hora/choghadiya times.
    if include_muhurtha:
        muh = chart.get("muhurtha")
        if isinstance(muh, dict) and muh:
            reference = str(
                muh.get("timestamp") or ""
            )
            if muh.get("timezone"):
                reference += f" ({muh.get('timezone')})"
            if muh.get("latitude") is not None and muh.get("longitude") is not None:
                reference += (
                    f", at birth place "
                    f"({muh.get('latitude'):.2f}, {muh.get('longitude'):.2f})"
                )
            lines.extend(_format_muhurtha_lines(muh, reference or "query moment"))
        elif isinstance(bdata, dict) and bdata.get("year"):
            tz_name = str(bdata.get("timezone") or "UTC")
            lat = float(bdata.get("latitude") or 0)
            lon = float(bdata.get("longitude") or 0)
            try:
                from datetime import datetime as _dt
                from zoneinfo import ZoneInfo as _ZoneInfo

                from nakshatra.muhurtha import calculate_muhurtha

                now_local = _dt.now(_ZoneInfo(tz_name))
                report = calculate_muhurtha(now_local, lat, lon, tz_name)
                reference = (
                    f"{report.timestamp} ({report.timezone}), "
                    f"at birth place ({lat:.2f}, {lon:.2f})"
                )
                lines.extend(_format_muhurtha_lines(report.model_dump(), reference))
            except Exception as exc:  # noqa: BLE001 - report, never invent
                lines.append(
                    "- Muhurtha (Timing): could not be calculated for the "
                    f"query moment at the birth place ({exc}); do not invent "
                    "hora, choghadiya, or Rahu Kalam times."
                )
        else:
            lines.append(
                "- Muhurtha (Timing): no birth place/time in the chart context, "
                "so no muhurtha could be calculated; do not invent times."
            )

    return "\n".join(lines)


def _compact_birth_context(chart: dict[str, Any]) -> dict[str, Any]:
    """Prune massive raw subtrees (e.g. 120kb dasha tree, 16 vargas) to prevent prompt overflow."""
    excluded = {
        "dashas",
        "vargas",
        "aspects",
        "vedic_aspects",
        "predictions",
        "transits",
        "shadbala",
        "ashtakavarga",
        "upagrahas",
        "remedies",
    }
    compact: dict[str, Any] = {k: v for k, v in chart.items() if k not in excluded}
    if "dashas" in chart and isinstance(chart["dashas"], dict):
        compact["current_dasha"] = {
            "current_md": chart["dashas"].get("current_md"),
            "current_ad": chart["dashas"].get("current_ad"),
            "current_pd": chart["dashas"].get("current_pd"),
        }
    return compact


# Task 13 step 7 — prompt token budget. The budget counts the whole
# assembled prompt; when it is exceeded, the raw compact chart JSON is
# shortened first (the formatted summary already carries the facts),
# the summary is never cut, and references are never silently dropped.
# Overridable with the PROMPT_TOKEN_BUDGET environment variable.
PROMPT_TOKEN_BUDGET = 16000
PROMPT_BUDGET_NOTE = (
    "[Note: the raw birth chart JSON below was shortened to fit the "
    "prompt token budget; the formatted summary below carries the full "
    "facts. Do not treat the shortened JSON as the complete chart.]"
)


def _prompt_token_budget() -> int:
    """Effective prompt token budget (env override, default 16000)."""
    try:
        return int(os.environ.get("PROMPT_TOKEN_BUDGET", str(PROMPT_TOKEN_BUDGET)))
    except ValueError:
        return PROMPT_TOKEN_BUDGET


def estimate_prompt_tokens(text: str) -> int:
    """Rough prompt-token estimate: ~4 characters per token.

    tiktoken is not installed, so this is the standard rough heuristic
    for English text — a soft budget that prevents gross context
    overflow, not an exact tokenizer count. (Devanagari text tokenizes
    denser than 4 chars/token, so the estimate is optimistic for
    Nepali prompts; the budget still bounds the worst case.)
    """
    return (len(text) + 3) // 4


def _apply_prompt_token_budget(prompt: str) -> str:
    """Shorten the raw compact chart JSON until the prompt fits the budget.

    Drops the largest top-level keys of the ``Birth chart context:``
    JSON first, then the whole JSON if still over budget, and signals
    the shortening in the prompt itself (note line + ``"__truncated__"``
    marker in the JSON). The formatted summary and the numbered
    references are left untouched. Prompts without a birth chart
    context, and prompts already within budget, are returned as-is.
    """
    budget = _prompt_token_budget()
    if estimate_prompt_tokens(prompt) <= budget:
        return prompt
    lines = prompt.split("\n")
    for index, line in enumerate(lines):
        if not line.startswith("Birth chart context: "):
            continue
        try:
            ctx = json.loads(line[len("Birth chart context: ") :])
        except json.JSONDecodeError:
            break
        if not isinstance(ctx, dict):
            break
        while ctx and estimate_prompt_tokens("\n".join(lines)) > budget:
            largest = max(ctx, key=lambda key: len(json.dumps(ctx[key], default=str)))
            del ctx[largest]
            lines[index] = "Birth chart context: " + json.dumps(ctx)
        ctx["__truncated__"] = True
        lines[index] = "Birth chart context: " + json.dumps(ctx)
        lines.insert(index, PROMPT_BUDGET_NOTE)
        break
    return "\n".join(lines)


def build_prompt(
    question: str,
    results: list[SearchResult],
    birth_context: dict[str, Any] | None = None,
    language: str = "en",
    intent: ConsultationIntent | str | None = None,
) -> str:
    """Assemble the consultation prompt with classical references and natal context."""
    if intent is None:
        intent = classify_intent(question)
    elif not isinstance(intent, ConsultationIntent):
        try:
            intent = ConsultationIntent(str(intent).lower().strip())
        except ValueError:
            intent = classify_intent(question)

    is_ne = (language or "").lower().strip() in ("ne", "nepali", "nep")
    lines = ["References:"]
    for index, result in enumerate(results, start=1):
        lines.append(f"{_citation_label(index, result)}: {result.chunk.text}")
    lines.append("")
    if birth_context:
        ayanamsa = birth_context.get("ayanamsa", "jhora_lahiri")
        zodiac = birth_context.get("zodiac", "sidereal")
        house_sys = birth_context.get("house_system", "WholeSign")
        lines.append(
            f"[Lineage: {zodiac.capitalize()} Zodiac | Ayanamsa: {ayanamsa} | "
            f"Houses: {house_sys} | Engine: Swiss Ephemeris]"
        )
        compact_ctx = _compact_birth_context(birth_context)
        lines.append(f"Birth chart context: {json.dumps(compact_ctx)}")
        # Muhurtha lines only for timing questions (Event Prediction intent):
        # they describe the query moment, not the birth moment.
        summary = _format_birth_summary(
            birth_context,
            include_muhurtha=(intent == ConsultationIntent.EVENT_PREDICTION),
        )
        if summary:
            lines.append("\n" + summary)
        lines.append("")
        lines.append(
            "CRITICAL DIRECTIVE: The seeker's birth chart, planetary placements, and exact Dasha date ranges "
            "are ALREADY PROVIDED above. DO NOT claim that birth details are missing or ask the seeker for their birth data. "
            "Directly answer their question using the specific placements, house lords, active transits, and exact dasha date ranges."
        )
    else:
        lines.append(
            "[Note: No birth chart context provided for this query. Answer using classical Jyotish principles directly. "
            "Explain the interpretive framework clearly, and guide the seeker to provide their exact birth date, "
            "time, and location to calculate personalized date ranges down to specific months and weeks.]\n"
        )
    lines.append(f"Question: {question}")

    if intent == ConsultationIntent.NATAL_IDENTITY:
        if is_ne:
            lines.append(
                "आत्म-स्वरूप तथा कुण्डली परिचय निर्देशन (अनिवार्य):\n"
                "कुनै पनि भूमिका वा अनावश्यक सम्बोधन नगरी सिधै निम्न ४ भागमा प्रामाणिक उत्तर दिनुहोस्:\n"
                "### १. कुण्डलीको मूल संरचना र लग्न स्वरूप\n"
                "लग्न राशि, लग्नेशको स्थिति र बल, बाह्य व्यक्तित्व, शारीरिक ऊर्जा, त्रिदोष (वात/पित्त/कफ) प्रकृति र संसारमा व्यक्त हुने स्वरूप।\n\n"
                "### २. मानसिक-भावनात्मक धरातल र चन्द्र-नक्षत्र\n"
                "चन्द्र राशि, जन्म नक्षत्र, पाउ, र नक्षत्र स्वामी। भित्री मानसिक प्रवृत्ति, संवेगात्मक आवश्यकता, धैर्यता र भावनात्मक शक्ति।\n\n"
                "### ३. आत्मिक उद्देश्य र आत्मकारक ग्रह (सूर्य र आत्मकारक)\n"
                "सूर्यको स्थिति, आत्मकारक ग्रह, र यस जन्मको मूल आत्मिक लक्ष्य तथा चेतनाको दिशा।\n\n"
                "### ४. मुख्य सामर्थ्य, शुभ योग र आत्म-विकास\n"
                "सक्रिय शुभ योगहरू, जन्मजात प्रतिभा, र जीवनमा सन्तुलन तथा उन्नतिको लागि ध्यान दिनुपर्ने पक्षहरू।\n\n"
                "कडा सावधानी:\n"
                "- आत्म-परिचयको प्रश्नमा अनावश्यक जागिरको फारम भर्ने मिति वा कुकुरलाई रोटी खुवाउने जस्ता असान्दर्भिक कुरा नथोपर्नुहोस्।\n"
                "- अष्टकवर्गका सबै १२ राशिका अङ्कहरू फोन नम्बर जस्तै नसुनाउनुहोस्।\n"
                "- अन्त्यमा सन्दर्भ सूची नदोहोर्‍याउनुहोस्।"
            )
        else:
            lines.append(
                "NATAL IDENTITY & COSMIC PROFILE DIRECTIVE (MANDATORY):\n"
                "Deliver a profound, calculation-backed natal character, psychological, and soul analysis like a master Jyotishi. "
                "Zero conversational fluff, zero greetings (NO 'Dear seeker', NO pleasantries). "
                "Synthesize your classical mastery with the provided scriptural excerpts, citing them with bracketed numbers like [1] or [2]. "
                "Structure your response strictly into these 4 sections:\n"
                "### 1. Cosmic Blueprint & Ascendant Archetype\n"
                "Synthesize the seeker's Ascendant (Lagna) sign, Lagna Lord placement and dignity, outward personality, physical vitality, "
                "primary temperament (Prakriti: Vata/Pitta/Kapha), and how they project their persona into the world.\n\n"
                "### 2. Emotional Landscape & Mind (Chandra & Nakshatra)\n"
                "Synthesize the Moon sign, Nakshatra, Pada, and Nakshatra Lord. Explain the instinctive emotional wiring, subconscious inclinations, "
                "mental resilience, intuition, and core emotional security needs.\n\n"
                "### 3. Soul Purpose & Driving Vitality (Surya & Karakas)\n"
                "Synthesize the Sun placement, Atmakaraka (soul significator planet), and highest aspirational calling in this incarnation. "
                "What core lesson and mastery does their soul seek?\n\n"
                "### 4. Key Strengths, Yogas & Karmic Evolution\n"
                "Synthesize active auspicious Yogas (e.g. Pancha Mahapurusha, Budhaditya, Ruchaka), innate superpowers and natural talents, "
                "along with the primary karmic growth opportunities to cultivate.\n\n"
                "CRITICAL GUARDRAILS:\n"
                "- Do NOT invent job application windows, do NOT force calendar dates, and do NOT prescribe daily dog-feeding or Lal Kitab daytime remedies when answering about natal identity and self-knowledge!\n"
                "- Do NOT recite telephone-directory lists of all 12 signs' Ashtakavarga numbers.\n"
                "- Do NOT append a redundant 'References:' or 'Citations:' bibliography list at the end of your response, as the platform interface automatically renders dedicated interactive citation cards below your answer."
            )
    elif intent == ConsultationIntent.REMEDIAL:
        if is_ne:
            # Task 13 step 6: aligned with SYSTEM_PROMPT_NE_REMEDIAL — the
            # old directive used different section headings (verdict / sutra /
            # timing guidance) from the EN remedial system prompt, so system
            # and user prompts disagreed in NE mode. These 4 sections now
            # match the NE system prompt exactly, as the EN directive does.
            lines.append(
                "प्रामाणिक लाल किताब तथा वैदिक उपाय निर्देशन (अनिवार्य):\n"
                "सिधै निम्न ४ भागमा प्रामाणिक उत्तर दिनुहोस्:\n"
                "### १. मुख्य ग्रह पीडा र कर्मगत असन्तुलन\n"
                "कुण्डलीमा देखिएको मुख्य ग्रह पीडा, त्यसको यकिन भाव स्थिति, घर र गम्भीरता तथा शास्त्रीय कारण [१], [२]।\n\n"
                "### २. ४३ दिने मुख्य दिउँसो लाल किताब उपाय\n"
                "सूर्योदयदेखि सूर्यास्तको बीचमा लगातार ४३ दिन गरिने ठोस, व्यावहारिक दिउँसो उपाय।\n\n"
                "### ३. जीव सेवा तथा घरेलु व्यवस्था\n"
                "गाई, कुकुर, चरा वा माछालाई आहार दिने व्यावहारिक सेवा वा घरको ऊर्जा व्यवस्थापन।\n\n"
                "### ४. कडा सावधानी (निषेध)\n"
                "लाल किताब अनुसार कहिल्यै गर्न नहुने काम, नलिने कुरा वा घरमा नराख्ने कुरा — कडा शास्त्रीय निषेधहरू।"
            )
        else:
            lines.append(
                "REMEDIAL & UPAAYA DIRECTIVE (MANDATORY):\n"
                "Structure your response strictly into these 4 sections:\n"
                "### 1. Core Afflictions & Karmic Imbalances\n"
                "Identify the afflicted planet, house placement, severity, and root karmic cause. Cite relevant classical verses with [1], [2].\n\n"
                "### 2. Primary 43-Day Daytime Lal Kitab Upaya\n"
                "Exact practical daytime remedy to be performed consecutively for 43 days between sunrise and sunset.\n\n"
                "### 3. Creature & Household Seva\n"
                "Specific animal feeding (cows, dogs, birds, fish) or home energetic rectification.\n\n"
                "### 4. Inviolable Savdhani (Strict Behavioral Precautions)\n"
                "Strict classical Lal Kitab taboos: what to NEVER accept, do, or keep at home."
            )
    elif intent == ConsultationIntent.CAREER_FINANCE:
        if is_ne:
            lines.append(
                "पेशा तथा आर्थिक परामर्श निर्देशन (अनिवार्य):\n"
                "सिधै निम्न ४ भागमा प्रामाणिक उत्तर दिनुहोस्:\n"
                "### १. व्यावसायिक क्षमता र कर्म क्षेत्र\n"
                "दशम भाव, दशमेश, अमात्यकारक ग्रह र स्वाभाविक कर्म क्षमता।\n\n"
                "### २. ज्योतिषीय आधार र समय चक्र\n"
                "सक्रिय महादशा/अन्तर्दशा, गोचर र अष्टकवर्गको अनुकूलता।\n\n"
                "### ३. यकिन समय-तालिका (३ वटा स्पष्ट मिति दायरा YYYY-MM-DD)\n"
                "तयारीको समय, मुख्य उन्नतिको समय, र सतर्कताको समय।\n\n"
                "### ४. व्यावसायिक उन्नति र लाल किताब सावधानी\n"
                "व्यावसायिक वृद्धिका लागि नैतिक आचरण र लाल किताबका नियमहरू।"
            )
        else:
            lines.append(
                "CAREER & FINANCIAL CONSULTATION DIRECTIVE (MANDATORY):\n"
                "Structure your response strictly into these 4 sections:\n"
                "### 1. Professional Aptitude & Natal Calling\n"
                "10th house, 10th lord, Amatyakaraka, vocational yogas, and natural professional gifts.\n\n"
                "### 2. Astrological Mechanism & Operating Dasha-Transit Triggers\n"
                "Operating dasha sub-periods activating 10th/2nd/6th/11th houses, Jupiter/Saturn transits, and SAV strength. Cite classical verses with [1], [2].\n\n"
                "### 3. Concrete Career Milestone Windows\n"
                "Provide 3 distinct ISO date ranges:\n"
                "- **Window 1: Preparation & Application Window (YYYY-MM-DD to YYYY-MM-DD)**\n"
                "- **Window 2: Peak Favorable Window (YYYY-MM-DD to YYYY-MM-DD)**\n"
                "- **Window 3: Caution & Delay Factor (YYYY-MM-DD to YYYY-MM-DD)**\n\n"
                "### 4. Vocational Alignment & Lal Kitab Precaution\n"
                "Strategic professional advice and relevant ethical Lal Kitab guidance."
            )
    elif intent == ConsultationIntent.RELATIONSHIP:
        if is_ne:
            lines.append(
                "वैवाहिक तथा सम्बन्ध परामर्श निर्देशन (अनिवार्य):\n"
                "सिधै निम्न ४ भागमा प्रामाणिक उत्तर दिनुहोस्:\n"
                "### १. वैवाहिक स्वरूप र सप्तम भाव विश्लेषण\n"
                "सप्तम भाव, सप्तमेश, शुक्र/बृहस्पतिको स्थिति र दम्पती सम्बन्ध।\n\n"
                "### २. जीवनसाथीको स्वभाव र भावनात्मक सामन्जस्य\n"
                "जीवनसाथीको चरित्र, स्वभाव र चन्द्र राशिको तालमेल।\n\n"
                "### ३. सम्बन्ध तथा विवाहको यकिन समय-तालिका (YYYY-MM-DD)\n"
                "सक्रिय दशा र गोचर अनुसार विवाह वा सम्बन्ध सुधारका स्पष्ट समय दायरा।\n\n"
                "### ४. पारिवारिक सुख र लाल किताब सावधानी\n"
                "दाम्पत्य सुखका लागि व्यावहारिक नियम र लाल किताब निषेधहरू।"
            )
        else:
            lines.append(
                "RELATIONSHIP & MARRIAGE CONSULTATION DIRECTIVE (MANDATORY):\n"
                "Structure your response strictly into these 4 sections:\n"
                "### 1. Natal Relationship Blueprint & 7th House Dynamics\n"
                "7th house, 7th lord, Venus/Jupiter dignity, Darakaraka, and partnership tendencies.\n\n"
                "### 2. Spouse Archetype & Emotional Compatibility\n"
                "Demeanor, qualities, and emotional nature of the partner; Moon-to-Moon relational harmony. Cite classical verses with [1], [2].\n\n"
                "### 3. Relationship & Marriage Timing Windows\n"
                "Concrete date ranges under active dasha sub-periods and Jupiter/Saturn transits to 7th or Lagna।\n\n"
                "### 4. Relational Harmony Practices & Lal Kitab Savdhani\n"
                "Actionable relationship wisdom, healthy communication boundaries, and Lal Kitab precautions."
            )
    elif intent == ConsultationIntent.HEALTH_WELLNESS:
        if is_ne:
            lines.append(
                "स्वास्थ्य तथा कल्याण परामर्श निर्देशन (अनिवार्य):\n"
                "कुनै पनि भूमिका वा अनावश्यक सम्बोधन नगरी सिधै निम्न ४ भागमा प्रामाणिक उत्तर दिनुहोस्:\n"
                "### १. शारीरिक प्रकृति, रोग प्रतिरोधात्मक क्षमता र मुख्य फलादेश\n"
                "शारीरिक स्वास्थ्य, त्रिदोष (वात/पित्त/कफ) धातु सन्तुलन, लग्न र सूर्यको जीवनी शक्ति (प्राण) को स्पष्ट निर्णय।\n\n"
                "### २. ज्योतिषीय आधार र संवेदनशील अङ्ग विश्लेषण\n"
                "लग्न (तनु भाव), ६औं (रोग भाव), र ८औं (आयु भाव) का स्वामी, ग्रह स्थिति, विंशोत्तरी दशा, गोचर (शनि/राहु/चन्द्राष्टम), र अष्टकवर्ग (SAV)। ग्रन्थका सन्दर्भहरूलाई [१], [२] ले प्रमाणित गर्नुहोस्।\n\n"
                "### ३. स्वास्थ्य समय-तालिका (३ वटा स्पष्ट मिति दायरा YYYY-MM-DD)\n"
                "- **पहिलो समय: स्वास्थ्य संरक्षण तथा पूर्वतयारी (YYYY-MM-DD देखि YYYY-MM-DD सम्म)**\n"
                "- **दोस्रो समय: उच्च ऊर्जा तथा स्वास्थ्य लाभ (YYYY-MM-DD देखि YYYY-MM-DD सम्म)**\n"
                "- **तेस्रो समय: संवेदनशीलता, विश्राम र सावधानी (YYYY-MM-DD देखि YYYY-MM-DD सम्म)**\n\n"
                "### ४. शास्त्रीय आयुर्वेदिक दिनचर्या र लाल किताब उपाय\n"
                "- **४३ दिने मुख्य स्वास्थ्य उपाय**: [लगातार ४३ दिन दिउँसो घामको प्रकाशमा गरिने उपाय - सूर्यास्त पछि कहिल्यै होइन]\n"
                "- **आयुर्वेदिक आहार तथा जीव सेवा**: [त्रिदोष सन्तुलन गर्ने आहार, दिनचर्या, र जीव सेवा]\n"
                "- **कडा सावधानी (निषेध)**: [स्वास्थ्य रक्षाका लागि लाल किताब र आयुर्वेद अनुसार निषेध]\n\n"
                "कडा सावधानी:\n"
                "- स्वास्थ्य परामर्शमा जागिर वा 'Application Window' जस्ता असान्दर्भिक शब्द कहिल्यै प्रयोग नगर्नुहोस्।\n"
                "- लाल किताबका सम्पूर्ण उपायहरू सूर्योदय र सूर्यास्तको बीचमा मात्र गरिनुपर्छ (सूर्यास्त पछि कहिल्यै होइन)।\n"
                "- ज्योतिषीय परामर्श चिकित्सा उपचारको विकल्प होइन; चिकित्सकको सल्लाह लिन स्पष्ट निर्देशन दिनुहोस्।\n"
                "- अन्त्यमा सन्दर्भ सूची नदोहोर्‍याउनुहोस्।"
            )
        else:
            lines.append(
                "HEALTH & WELLNESS CONSULTATION DIRECTIVE (MANDATORY):\n"
                "Deliver a direct, calculation-backed health, vitality, and chronobiological analysis like a master Medical Jyotishi. "
                "Zero conversational fluff, zero greetings (NO 'Dear seeker', NO pleasantries). "
                "Synthesize your classical mastery with the provided scriptural excerpts, citing them with bracketed numbers like [1] or [2]. "
                "Structure your response strictly into these 4 sections:\n"
                "### 1. Vitality Constitution & Physical Health Verdict\n"
                "Immediate, definitive verdict on physical vitality, constitutional temperament (Ayurvedic Prakriti: Vata/Pitta/Kapha), "
                "Lagna immunity, and Sun's Prana in 1-2 definitive sentences.\n\n"
                "### 2. Astrological Mechanism & Vulnerability Mapping\n"
                "Ground your analysis in the calculated 1st house (Tanu/vitality), 6th house (Roga/acute ailments & digestive fire), "
                "8th house (Ayur/chronic vulnerabilities & longevity), their lords, operating Dasha periods, and transits (Saturn/Rahu/Chandrashtama). "
                "Map physiological vulnerabilities to classical sign/planet rulerships. Cite classical verses with [1], [2]. "
                "Do NOT mention unrelated financial significators (such as 2nd lord or Dhana karaka)!\n\n"
                "### 3. Chronobiological & Health Sensitivity Windows\n"
                "Provide 3 distinct date ranges in YYYY-MM-DD format:\n"
                "- **Window 1: Vitality Consolidation & Preventative Window (YYYY-MM-DD to YYYY-MM-DD)**\n"
                "- **Window 2: Peak Energy & Wellness Recovery Window (YYYY-MM-DD to YYYY-MM-DD)**\n"
                "- **Window 3: Sensitivity & Rest Phase (YYYY-MM-DD to YYYY-MM-DD)**\n\n"
                "### 4. Classical Ayurvedic & Lal Kitab Health Regimen\n"
                "- **43-Day Daytime Health Upaya**: [Continuous daytime action performed strictly between sunrise and sunset]\n"
                "- **Dietary & Lifestyle Dharma**: [Ayurvedic dietary balance for Vata/Pitta/Kapha, circadian routine, creature seva]\n"
                "- **Inviolable Savdhani (Strict Precaution)**: [Mandatory taboo: what to NEVER consume, do, or neglect]\n\n"
                "CRITICAL GUARDRAILS:\n"
                "- NEVER use vocational phrasing such as 'Application Window', 'Job Application', or 'Career' in a health consultation!\n"
                "- INVIOLABLE DAYTIME RULE: ALL Lal Kitab remedies MUST be performed strictly between sunrise and sunset in natural daylight. NEVER prescribe remedies 'after sunset', 'at night', or 'on Saturday evening'!\n"
                "- RESPONSIBLE MEDICAL BOUNDARY: Explicitly note that astrological wellness analysis does not replace professional medical diagnosis or treatment from licensed physicians.\n"
                "- Do NOT append a redundant 'References:' or 'Citations:' bibliography list at the end of your response."
            )
    elif intent == ConsultationIntent.CONCEPTUAL:
        if is_ne:
            lines.append(
                "शास्त्रीय अवधारणा निर्देशन (अनिवार्य):\n"
                "सिधै निम्न ४ भागमा प्रामाणिक व्याख्या दिनुहोस्:\n"
                "### १. शास्त्रीय परिभाषा र ग्रन्थको आधार\n"
                "महर्षि पराशर वा शास्त्रीय ग्रन्थ अनुसारको स्पष्ट परिभाषा र श्लोक सन्दर्भ [१]।\n\n"
                "### २. ज्योतिषीय आधार र निर्माण नियम\n"
                "ग्रहको स्थिति, भाव गणना, योगका सर्तहरू तथा भङ्गका नियम।\n\n"
                "### ३. व्यावहारिक जीवनमा प्रभाव र लक्षण\n"
                "मानव जीवन, चरित्र र घटनाक्रममा यसको प्रत्यक्ष अभिव्यक्ति।\n\n"
                "### ४. सकारात्मक रूपान्तरण र मार्गदर्शन\n"
                "यस शास्त्रीय सिद्धान्तलाई जीवन निर्माणमा कसरी सकारात्मक रूपमा प्रयोग गर्ने।"
            )
        else:
            lines.append(
                "CONCEPTUAL JYOTISH INSTRUCTION DIRECTIVE (MANDATORY):\n"
                "Structure your response strictly into these 4 sections:\n"
                "### 1. Classical Definition & Scriptural Foundation\n"
                "Definitive scriptural meaning citing classical verses [1], [2].\n\n"
                "### 2. Astrological Mechanism & Interpretive Rules\n"
                "Planetary mechanics, house combinations, dignities, and cancellations (bhanga).\n\n"
                "### 3. Real-World Manifestation & Case Analysis\n"
                "How the principle manifests in real human experience, character, and life events.\n\n"
                "### 4. Dharmic Synthesis & Constructive Perspective\n"
                "Evolutionary spiritual purpose and practical guidance."
            )
    else:
        # Default: Event Prediction (4-Pillar Timing Layout)
        if is_ne:
            lines.append(
                "\nभाषा निर्देशन: सोधकर्ताको भाषा नेपाली भएकाले सम्पूर्ण परामर्श, विश्लेषण तथा उपायहरू "
                "अत्यन्त शुद्ध, आदरार्थी, स्पष्ट तथा शास्त्रीय नेपाली भाषामा प्रस्तुत गर्नुहोस्।\n"
                "अनिवार्य संरचना निर्देशन:\n"
                "कुनै पनि भूमिका वा अनावश्यक सम्बोधन नगरी सिधै निम्न ४ भागमा प्रामाणिक उत्तर दिनुहोस्:\n"
                "### १. प्रत्यक्ष फलादेश र मुख्य निर्णय\n"
                "### २. ज्योतिषीय आधार र गणितीय प्रमाण\n"
                "### ३. यकिन समय-तालिका (३ वटा स्पष्ट मिति दायरा YYYY-MM-DD)\n"
                "### ४. प्रामाणिक लाल किताब उपाय तथा सावधानी\n"
                "- **४३ दिने मुख्य उपाय**: [कुण्डली सन्दर्भबाट लगातार ४३ दिन दिउँसो गरिने ठोस उपाय]\n"
                "- **जीव सेवा / पारिवारिक नियम**: [गाई, कुकुर, वा चराचुरुङ्गीलाई आहार]\n"
                "- **कडा सावधानी (निषेध)**: [लाल किताब अनुसार कहिल्यै गर्न नहुने काम वा निषेध]\n\n"
                "कुनै पनि खण्डमा एउटै वाक्य नदोहोर्‍याउनुहोस्; प्रत्येक खण्डमा फरक र ठोस विषयवस्तु दिनुहोस्।\n"
                "अन्त्यमा सन्दर्भ सूची नदोहोर्‍याउनुहोस्।"
            )
        else:
            lines.append(
                "PREDICTION ARCHITECTURE DIRECTIVE (MANDATORY):\n"
                "Deliver a direct, calculation-backed prediction like a seasoned master astrologer. "
                "Zero conversational fluff, zero greetings (NO 'Dear seeker', NO pleasantries). "
                "Synthesize your classical mastery with the provided scriptural excerpts, citing them with bracketed numbers like [1] or [2]. "
                "Structure your response strictly into these 4 sections:\n"
                "### 1. Direct Verdict & Timing\n"
                "Immediate point-blank answer and direct outcome in 1-2 definitive sentences.\n\n"
                "### 2. Astrological Mechanism & Calculation Proof\n"
                "Cite the exact calculated planetary placements, house rulerships, active Mahadasha/Antardasha/Pratyantardasha periods, "
                "transits, and Sarvashtakavarga (SAV) bindu scores from the context. Cite relevant classical verses with [1], [2].\n\n"
                "### 3. Concrete Timeline Windows\n"
                "Provide 3 distinct date ranges in YYYY-MM-DD format:\n"
                "- **Window 1: Preparation & Foundation Window (YYYY-MM-DD to YYYY-MM-DD)**\n"
                "- **Window 2: Peak Favorable Window (YYYY-MM-DD to YYYY-MM-DD)**\n"
                "- **Window 3: Caution & Delay Factor (YYYY-MM-DD to YYYY-MM-DD)**\n\n"
                "### 4. Classical Lal Kitab Prescription\n"
                "- **43-Day Daytime Upaya**: [Continuous daytime action from the context]\n"
                "- **Creature / Household Seva**: [Specific animal feeding or household alignment]\n"
                "- **Inviolable Savdhani (Strict Precaution)**: [Mandatory taboo: what to NEVER do or keep at home]\n\n"
                "Do NOT repeat sentences across sections; every section must contain unique, concrete substance.\n"
                "Never recite ancient mathematical calculation algorithms, table numbers, or worked-out arithmetic examples from the commentary texts. "
                "Do NOT append a redundant 'References:' or 'Citations:' bibliography list at the end of your response, as the platform interface automatically renders dedicated interactive citation cards below your answer."
            )
    return _apply_prompt_token_budget("\n".join(lines))


def extract_citations(answer: str, results: list[SearchResult]) -> list[Citation]:
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


def _clean_repeated_phrases(text: str) -> str:
    """Detect and truncate degenerative LLM repetition loops (e.g. phrase repeated 3+ times)."""
    pattern = re.compile(r"([^\n\r]{3,40}?)(?:\s*[:\-–]?\s*\1){2,}", re.IGNORECASE)
    return pattern.sub(r"\1", text)


def _strip_trailing_references(text: str) -> str:
    """Strip redundant trailing References/Citations section from LLM output.

    The frontend UI renders dedicated interactive citation cards from structured
    metadata, so a raw text bibliography at the bottom of the answer creates
    duplicate visual display.
    """
    cleaned = _clean_repeated_phrases(text)
    pattern = (
        r"(?i)\n+(?:###?\s*)?(?:references|citations|classical citations|shloka citations|"
        r"सन्दर्भहरू?|उद्धरणहरू?)\s*:?\s*\n+.*$"
    )
    return re.sub(pattern, "", cleaned, flags=re.DOTALL).rstrip()


class LLMSynthesizer(BaseSynthesizer):
    """Generates answers via an LLM provider (optional [ai] extra).

    Providers:
    - "openai": OpenAI-compatible API (also serves local models via base_url)
    - "google": Google GenAI API
    - "ollama": Local offline inference via Ollama (OpenAI-compatible)
    """

    def __init__(
        self,
        provider: str = "openai",
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.provider = provider
        if model is None:
            if provider == "ollama":
                model = os.environ.get("OLLAMA_MODEL", "qwen2.5:3b")
            elif provider == "google":
                model = GOOGLE_PRIMARY_MODEL
            else:
                model = "gpt-4o-mini"
        self.model = model
        self._api_key = api_key
        self._base_url = base_url
        self._client: Any = None

    def synthesize(
        self,
        question: str,
        results: list[SearchResult],
        birth_context: dict[str, Any] | None = None,
        language: str = "en",
    ) -> Answer:
        intent = classify_intent(question)
        prompt = build_prompt(
            question, results, birth_context, language=language, intent=intent
        )
        sys_prompt = get_system_prompt(language, intent=intent)
        try:
            try:
                text = self._complete(prompt, system_prompt=sys_prompt)
            except TypeError:
                text = self._complete(prompt)
            clean_answer = _strip_trailing_references(text)
            # Task 13 step 1: validate the LLM answer against the chart
            # context it was given; drop unsupported/out-of-range citations
            # and flag any placement/date/yoga/Sade Sati mismatch.
            validation = validate_answer(clean_answer, birth_context, results)
            return Answer(
                question=question,
                answer=validation.cleaned_answer,
                citations=extract_citations(validation.cleaned_answer, results),
                model=self.model,
                validation=validation,
            )
        except Exception as e:
            fb = FallbackSynthesizer()
            ans = fb.synthesize(question, results, birth_context, language=language)
            notice_prefix = (
                "9router"
                if (self._base_url and "20128" in self._base_url)
                else (
                    "Ollama"
                    if self.provider == "ollama"
                    else ("OpenAI" if self.provider == "openai" else "Gemini")
                )
            )
            ans.answer = (
                f"*[Notice: {notice_prefix} service temporarily unavailable ({e}). "
                "Retrieved classical scriptural citations:]*\n\n" + ans.answer
            )
            return ans

    def _complete(self, prompt: str, system_prompt: str = SYSTEM_PROMPT) -> str:
        if self.provider in ("openai", "ollama"):
            try:
                return self._complete_openai(prompt, system_prompt=system_prompt)
            except Exception as e:
                google_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
                if google_key:
                    try:
                        return self._complete_google(prompt, system_prompt=system_prompt)
                    except Exception:
                        pass
                raise e
        if self.provider == "google":
            return self._complete_google(prompt, system_prompt=system_prompt)
        raise ValueError(f"Unknown LLM provider: {self.provider}")

    def _openai_client(self) -> Any:
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError as e:
                raise ImportError(
                    "The openai package is required for the openai/ollama "
                    "provider. Install it with: pip install 'nakshatra[ai]'"
                ) from e
            base_url: str | None
            api_key: str | None
            if self.provider == "ollama":
                base_url = (
                    self._base_url
                    or os.environ.get("OLLAMA_BASE_URL")
                    or os.environ.get("OLLAMA_HOST")
                    or "http://localhost:11434/v1"
                )
                if not base_url.endswith("/v1"):
                    base_url = f"{base_url.rstrip('/')}/v1"
                api_key = self._api_key or os.environ.get("OLLAMA_API_KEY") or "ollama"
            else:
                base_url = self._base_url or os.environ.get("OPENAI_BASE_URL")
                api_key = self._api_key or os.environ.get("OPENAI_API_KEY")
            self._client = OpenAI(
                api_key=api_key,
                base_url=base_url,
                timeout=30.0,
            )
        return self._client

    def _complete_openai(self, prompt: str, system_prompt: str = SYSTEM_PROMPT) -> str:
        client = self._openai_client()
        max_tokens = int(os.environ.get("MAX_OUTPUT_TOKENS", "4096"))
        candidates = [self.model]
        for fallback in ("gemini/gemini-3.5-flash-lite", "gemini/gemini-3-flash-preview"):
            if fallback not in candidates:
                candidates.append(fallback)

        last_err: Exception | None = None
        for cand in candidates:
            try:
                kwargs: dict[str, Any] = {
                    "model": cand,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.35,
                    "frequency_penalty": 0.3,
                    "presence_penalty": 0.2,
                    "timeout": 30.0,
                    "max_tokens": max_tokens,
                }
                response = client.chat.completions.create(**kwargs)
                self.model = cand
                return str(response.choices[0].message.content)
            except Exception as e:
                last_err = e
                continue
        if last_err:
            raise last_err
        raise RuntimeError("OpenAI completion failed")

    def _complete_google(self, prompt: str, system_prompt: str = SYSTEM_PROMPT) -> str:
        rotation_models = list(GOOGLE_ROTATION_MODELS)
        candidates = [self.model]
        for m in rotation_models:
            if m not in candidates:
                candidates.append(m)

        if self._client is None:
            try:
                from google import genai  # type: ignore[import-not-found,import-untyped]
                from google.genai import types  # type: ignore[import-not-found,import-untyped]
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
            # Guard against invalid tokens and enforce strict timeout
            if api_key and api_key.startswith("AQ."):
                raise ValueError(
                    "GOOGLE_API_KEY is an Antigravity token, not a Google AI Studio key."
                )
            http_options = (
                types.HttpOptions(timeout=15000) if hasattr(types, "HttpOptions") else None
            )
            if http_options:
                self._client = genai.Client(api_key=api_key, http_options=http_options)
            else:
                self._client = genai.Client(api_key=api_key)

        last_err: Exception | None = None
        full_contents = f"{system_prompt}\n\n{prompt}"
        # Task 13 step 5: same decoding controls as the OpenAI calls.
        config = _google_generation_config()
        for cand in candidates:
            try:
                response = self._client.models.generate_content(
                    model=cand, contents=full_contents, config=config
                )
                self.model = cand
                return str(response.text)
            except Exception as e:
                last_err = e
                err_str = str(e)
                # Rotate immediately if model hits 429 quota exhaustion or 503 unavailable
                if (
                    "429" in err_str
                    or "RESOURCE_EXHAUSTED" in err_str
                    or "503" in err_str
                    or "UNAVAILABLE" in err_str
                    or "404" in err_str
                    or "NOT_FOUND" in err_str
                ):
                    continue
                raise

        if last_err:
            raise last_err
        raise RuntimeError("Google GenAI completion failed without error")

    def synthesize_stream(
        self,
        question: str,
        results: list[SearchResult],
        birth_context: dict[str, Any] | None = None,
        language: str = "en",
    ) -> Iterator[str]:
        intent = classify_intent(question)
        prompt = build_prompt(
            question, results, birth_context, language=language, intent=intent
        )
        sys_prompt = get_system_prompt(language, intent=intent)
        notice_prefix = (
            "9router"
            if (self._base_url and "20128" in self._base_url)
            else (
                "Ollama"
                if self.provider == "ollama"
                else ("OpenAI" if self.provider == "openai" else "Gemini")
            )
        )
        # Task 13 step 4: never append a second (fallback) answer after
        # partial LLM tokens. Buffer the count: the fallback may only be
        # yielded when ZERO tokens were produced; otherwise end the stream
        # with a short interruption notice and no second answer.
        yielded = 0
        try:
            if self.provider == "google":
                inner = self._stream_google(prompt, system_prompt=sys_prompt)
            elif self.provider in ("openai", "ollama"):
                inner = self._stream_openai(prompt, system_prompt=sys_prompt)
            else:
                try:
                    inner = iter([self._complete(prompt, system_prompt=sys_prompt)])
                except TypeError:
                    inner = iter([self._complete(prompt)])
            for token in inner:
                yielded += 1
                yield token
        except Exception as e:
            if yielded > 0:
                yield (
                    "\n\n*[Notice: "
                    f"{notice_prefix} stream interrupted ({e}) — "
                    "the answer above is incomplete. Please try again.]*"
                )
                return
            fb = FallbackSynthesizer()
            yield f"*[Notice: {notice_prefix} service temporarily unavailable ({e}). Retrieved classical scriptural citations:]*\n\n"
            yield from fb.synthesize_stream(question, results, birth_context, language=language)

    def _stream_openai(self, prompt: str, system_prompt: str = SYSTEM_PROMPT) -> Iterator[str]:
        client = self._openai_client()
        max_tokens = int(os.environ.get("MAX_OUTPUT_TOKENS", "4096"))
        candidates = [self.model]
        for fallback in ("gemini/gemini-3.5-flash-lite", "gemini/gemini-3-flash-preview"):
            if fallback not in candidates:
                candidates.append(fallback)

        last_err: Exception | None = None
        for cand in candidates:
            try:
                kwargs: dict[str, Any] = {
                    "model": cand,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.35,
                    "frequency_penalty": 0.3,
                    "presence_penalty": 0.2,
                    "stream": True,
                    "timeout": 30.0,
                    "max_tokens": max_tokens,
                }
                response = client.chat.completions.create(**kwargs)
                had_content = False
                for chunk in response:
                    if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                        had_content = True
                        yield str(chunk.choices[0].delta.content)
                if had_content:
                    self.model = cand
                    return
            except Exception as e:
                # Task 13 step 4: if this candidate already yielded tokens,
                # do NOT try the next candidate — that would stream a second
                # complete answer after the partial one. Fail instead; the
                # caller ends the stream with an interruption notice.
                if had_content:
                    raise
                last_err = e
                continue
        if last_err:
            raise last_err

    def _stream_google(self, prompt: str, system_prompt: str = SYSTEM_PROMPT) -> Iterator[str]:
        rotation_models = list(GOOGLE_ROTATION_MODELS)
        candidates = [self.model]
        for m in rotation_models:
            if m not in candidates:
                candidates.append(m)

        if self._client is None:
            from google import genai  # type: ignore[import-not-found,import-untyped]
            from google.genai import types  # type: ignore[import-not-found,import-untyped]

            api_key = (
                self._api_key
                or os.environ.get("GOOGLE_API_KEY")
                or os.environ.get("GEMINI_API_KEY")
            )
            if api_key and api_key.startswith("AQ."):
                raise ValueError(
                    "GOOGLE_API_KEY is an Antigravity token, not a Google AI Studio key."
                )
            http_options = (
                types.HttpOptions(timeout=15000) if hasattr(types, "HttpOptions") else None
            )
            if http_options:
                self._client = genai.Client(api_key=api_key, http_options=http_options)
            else:
                self._client = genai.Client(api_key=api_key)

        last_err: Exception | None = None
        full_contents = f"{system_prompt}\n\n{prompt}"
        # Task 13 step 5: same decoding controls as the OpenAI calls.
        config = _google_generation_config()
        yielded_any = False
        for cand in candidates:
            try:
                stream_response = self._client.models.generate_content_stream(
                    model=cand, contents=full_contents, config=config
                )
                self.model = cand
                for chunk in stream_response:
                    if chunk.text:
                        yielded_any = True
                        yield str(chunk.text)
                return
            except Exception as e:
                last_err = e
                err_str = str(e)
                # Task 13 step 4: if any tokens were already yielded, do NOT
                # continue to the next model — that would append a second
                # complete answer after the partial one. Fail instead; the
                # caller ends the stream with an interruption notice.
                if yielded_any:
                    raise
                if (
                    "429" in err_str
                    or "RESOURCE_EXHAUSTED" in err_str
                    or "503" in err_str
                    or "UNAVAILABLE" in err_str
                    or "404" in err_str
                    or "NOT_FOUND" in err_str
                ):
                    continue
                raise

        if last_err:
            raise last_err


class OllamaSynthesizer(LLMSynthesizer):
    """Local offline LLM synthesis via Ollama (qwen2.5:3b)."""

    def __init__(
        self,
        model: str = "qwen2.5:3b",
        base_url: str = "http://localhost:11434/v1",
        api_key: str = "ollama",
    ) -> None:
        super().__init__(
            provider="ollama",
            model=model,
            api_key=api_key,
            base_url=base_url,
        )


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
        language: str = "en",
    ) -> Answer:
        is_ne = (language or "").lower().strip() in ("ne", "nepali", "nep")
        if not results:
            return Answer(
                question=question,
                answer=(
                    "यस प्रश्नका लागि ग्रन्थहरूमा कुनै सान्दर्भिक श्लोक वा सन्दर्भ फेला परेन।"
                    if is_ne
                    else "No relevant references were found in the corpus for this question."
                ),
                model="fallback",
            )
        top_ref = results[0]
        intent = classify_intent(question)
        lines = [
            f"तपाईंको प्रश्न '{question}' सम्बन्धी शास्त्रीय सन्दर्भहरू:"
            if is_ne
            else f"Regarding your question '{question}':"
        ]
        top_text = top_ref.chunk.text.splitlines()[0] if top_ref.chunk.text else ""
        first_sentence = (
            top_ref.chunk.text.split(".")[0]
            if "." in top_ref.chunk.text
            else top_ref.chunk.text[:140]
        )

        if intent == ConsultationIntent.NATAL_IDENTITY:
            if is_ne:
                lines.append(
                    f"\n### १. कुण्डलीको मूल संरचना र लग्न स्वरूप\nशास्त्रीय ग्रन्थ ({top_ref.chunk.work}) अनुसार: {top_text} [१]"
                )
                lines.append("\n### २. मानसिक-भावनात्मक धरातल र चन्द्र-नक्षत्र")
                for index, result in enumerate(results[:3], start=1):
                    clean_t = result.chunk.text.replace("\n", " ").strip()
                    lines.append(
                        f"- **[{index}] {result.chunk.work}** (अध्याय {result.chunk.chapter or 'सामान्य'}, श्लोक {result.chunk.verse or 'सूत्र'}): {clean_t}"
                    )
                lines.append(
                    "\n### ३. आत्मिक उद्देश्य र आत्मकारक ग्रह (सूर्य र आत्मकारक)\nसूर्य र आत्मकारक ग्रहले यस जीवनको मूल आत्मिक लक्ष्य र चेतनाको दिशालाई निर्देशित गर्दछन्।"
                )
                lines.append(
                    "\n### ४. मुख्य सामर्थ्य, शुभ योग र आत्म-विकास\nकुण्डलीका शुभ योग तथा ग्रह बलले विशिष्ट आन्तरिक क्षमता र जीवनमा सन्तुलन प्रदान गर्दछन्।"
                )
            else:
                lines.append(
                    f"\n### 1. Cosmic Blueprint & Ascendant Archetype\nAccording to classical Jyotish authority ({top_ref.chunk.work}), {first_sentence.strip()} [1]."
                )
                lines.append(
                    "\n### 2. Emotional Landscape & Mind (Chandra & Nakshatra)\nNatal Moon and Nakshatra placements govern instinctive emotional perception, intuitive discernment, and inner resilience:"
                )
                for index, result in enumerate(results[:3], start=1):
                    clean_t = result.chunk.text.replace("\n", " ").strip()
                    lines.append(f"- **{_citation_label(index, result)}**: {clean_t}")
                lines.append(
                    "\n### 3. Soul Purpose & Driving Vitality (Surya & Karakas)\nThe Sun and Atmakaraka anchor the highest aspirational calling and core lessons of this incarnation."
                )
                lines.append(
                    "\n### 4. Key Strengths, Yogas & Karmic Evolution\nActive planetary dignities and auspicious Yogas grant distinct natural superpowers to develop throughout life."
                )
        elif intent == ConsultationIntent.HEALTH_WELLNESS:
            if is_ne:
                lines.append(
                    f"\n### १. शारीरिक प्रकृति, रोग प्रतिरोधात्मक क्षमता र मुख्य फलादेश\nशास्त्रीय ग्रन्थ ({top_ref.chunk.work}) अनुसार: {top_text} [१]"
                )
                lines.append("\n### २. ज्योतिषीय आधार र संवेदनशील अङ्ग विश्लेषण")
                for index, result in enumerate(results[:3], start=1):
                    clean_t = result.chunk.text.replace("\n", " ").strip()
                    lines.append(
                        f"- **[{index}] {result.chunk.work}** (अध्याय {result.chunk.chapter or 'सामान्य'}, श्लोक {result.chunk.verse or 'सूत्र'}): {clean_t}"
                    )
                lines.append(
                    "\n### ३. स्वास्थ्य समय-तालिका (३ वटा स्पष्ट मिति दायरा YYYY-MM-DD)\n"
                    "विंशोत्तरी दशा तथा गोचर अनुसार स्वास्थ्य संरक्षण, उच्च ऊर्जा र संवेदनशीलता अवधिको निर्धारण गरिन्छ।"
                )
                lines.append(
                    "\n### ४. शास्त्रीय आयुर्वेदिक दिनचर्या र लाल किताब उपाय\n"
                    "- **४३ दिने मुख्य स्वास्थ्य उपाय**: लगातार ४३ दिन दिउँसो घामको प्रकाशमा गरिने ठोस व्यावहारिक उपाय (सूर्यास्त पछि कहिल्यै होइन)\n"
                    "- **आयुर्वेदिक आहार तथा जीव सेवा**: त्रिदोष सन्तुलन गर्ने आहार तथा गाई वा पशुपन्छीको सेवा\n"
                    "- **कडा सावधानी (निषेध)**: स्वास्थ्य रक्षाका लागि खानपान तथा आचरणमा पूर्ण संयम। [चिकित्सा सम्बन्धी परामर्शका लागि योग्य चिकित्सकको सल्लाह लिनुहोस्]"
                )
            else:
                lines.append(
                    f"\n### 1. Vitality Constitution & Physical Health Verdict\nAccording to classical Jyotish authority ({top_ref.chunk.work}), {first_sentence.strip()} [1]."
                )
                lines.append(
                    "\n### 2. Astrological Mechanism & Vulnerability Mapping\nNatal Lagna (vitality), 6th house (Roga Bhava), and 8th house (Ayur Bhava) govern physical constitution and biological resilience:"
                )
                for index, result in enumerate(results[:3], start=1):
                    clean_t = result.chunk.text.replace("\n", " ").strip()
                    lines.append(f"- **{_citation_label(index, result)}**: {clean_t}")
                lines.append(
                    "\n### 3. Chronobiological & Health Sensitivity Windows\nBiological vitality and immunity fluctuate according to active Vimshottari dasha sub-periods and key planetary transits affecting Tanu and Roga Bhavas."
                )
                lines.append(
                    "\n### 4. Classical Ayurvedic & Lal Kitab Health Regimen\n"
                    "- **43-Day Daytime Health Upaya**: Perform classical daytime remedies strictly between sunrise and sunset (never after sunset).\n"
                    "- **Dietary & Lifestyle Dharma**: Cultivate doshic balance through seasonal Ayurvedic nutrition, hydration, and creature seva.\n"
                    "- **Inviolable Savdhani (Strict Precaution)**: Avoid irregular sleep cycles, maintain dietary discipline, and observe classical health taboos. [Note: Astrological wellness insights do not replace professional medical care.]"
                )
        elif intent == ConsultationIntent.REMEDIAL:
            if is_ne:
                lines.append(
                    f"\n### १. प्रत्यक्ष फलादेश र मुख्य शास्त्रीय निर्णय\nशास्त्रीय ग्रन्थ ({top_ref.chunk.work}) अनुसार: {top_text} [१]"
                )
                lines.append("\n### २. ज्योतिषीय आधार र प्रामाणिक सूत्र")
                for index, result in enumerate(results[:3], start=1):
                    clean_t = result.chunk.text.replace("\n", " ").strip()
                    lines.append(
                        f"- **[{index}] {result.chunk.work}** (अध्याय {result.chunk.chapter or 'सामान्य'}, श्लोक {result.chunk.verse or 'सूत्र'}): {clean_t}"
                    )
                lines.append(
                    "\n### ३. व्यावहारिक मार्गदर्शन तथा समय सिद्धान्त\nविंशोत्तरी महादशा, अन्तर्दशा तथा चन्द्र राशिका आधारमा सक्रिय गोचर प्रभाव अनुसार समय निर्धारण गरिन्छ।"
                )
                lines.append(
                    "\n### ४. प्रामाणिक वैदिक तथा लाल किताब उपाय\n- **४३ दिने मुख्य उपाय**: लगातार ४३ दिन दिउँसो गरिने ठोस व्यावहारिक उपाय\n- **कडा सावधानी (निषेध)**: लाल किताब अनुसार कहिल्यै गर्न नहुने काम वा निषेध"
                )
            else:
                lines.append(
                    f"\n### 1. Core Afflictions & Karmic Imbalances\nAccording to classical Jyotish authority ({top_ref.chunk.work}), {first_sentence.strip()} [1]."
                )
                lines.append("\n### 2. Primary 43-Day Daytime Lal Kitab Upaya")
                for index, result in enumerate(results[:3], start=1):
                    clean_t = result.chunk.text.replace("\n", " ").strip()
                    lines.append(f"- **{_citation_label(index, result)}**: {clean_t}")
                lines.append(
                    "\n### 3. Creature & Household Seva\nSupport daytime charitable seva (feeding birds, cows, or dogs) and align home energetic harmony."
                )
                lines.append(
                    "\n### 4. Inviolable Savdhani (Strict Behavioral Precautions)\nMaintain ethical conduct, avoid prohibited items at home, and strictly observe classical planetary taboos."
                )
        else:
            if is_ne:
                lines.append(
                    f"\n### १. प्रत्यक्ष फलादेश र मुख्य शास्त्रीय निर्णय\nशास्त्रीय ग्रन्थ ({top_ref.chunk.work}) अनुसार: {top_text} [१]"
                )
                lines.append("\n### २. ज्योतिषीय आधार र प्रामाणिक सूत्र")
                for index, result in enumerate(results[:3], start=1):
                    clean_t = result.chunk.text.replace("\n", " ").strip()
                    lines.append(
                        f"- **[{index}] {result.chunk.work}** (अध्याय {result.chunk.chapter or 'सामान्य'}, श्लोक {result.chunk.verse or 'सूत्र'}): {clean_t}"
                    )
                lines.append(
                    "\n### ३. व्यावहारिक मार्गदर्शन तथा समय सिद्धान्त\nविंशोत्तरी महादशा, अन्तर्दशा तथा चन्द्र राशिका आधारमा सक्रिय गोचर प्रभाव अनुसार समय निर्धारण गरिन्छ।"
                )
                lines.append(
                    "\n### ४. प्रामाणिक वैदिक तथा लाल किताब उपाय\n- **नित्य नियम**: सम्बन्धित ग्रहको वैदिक वा बीज मन्त्र जप गर्नुहोस्।\n- **सावधानी**: नकारात्मक आचरण, अनुचित लेनदेन तथा लाल किताब अनुसार निषेधित कार्यहरूबाट टाढा रहनुहोस्।"
                )
            else:
                first_sentence = (
                    top_ref.chunk.text.split(".")[0]
                    if "." in top_ref.chunk.text
                    else top_ref.chunk.text[:140]
                )
                lines.append(
                    f"\n### 1. Direct Verdict & Classical Principle\nAccording to classical Jyotish authority ({top_ref.chunk.work}), {first_sentence.strip()} [1]."
                )
                lines.append("\n### 2. Astrological Mechanism & Scriptural Grounding")
                for index, result in enumerate(results[:3], start=1):
                    clean_t = result.chunk.text.replace("\n", " ").strip()
                    lines.append(f"- **{_citation_label(index, result)}**: {clean_t}")
                lines.append(
                    "\n### 3. Concrete Guidelines & Timing Principles\nTiming and manifestation are governed by the active Vimshottari Dasha sub-periods and key planetary transits relative to the natal Moon."
                )
                lines.append(
                    "\n### 4. Classical Remediation & Dharmic Alignment\n- **Primary Upaya**: Recite the designated Beeja Mantra of the relevant planetary lord.\n- **Savdhani (Precaution)**: Maintain ethical conduct, support daytime charitable seva, and avoid classical planetary taboos."
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
