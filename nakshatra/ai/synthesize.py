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
from typing import Any

from pydantic import BaseModel, Field

from nakshatra.ai.retrieval import SearchResult

SYSTEM_PROMPT = (
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
    "       - **Window 1: Preparation & Application Window (YYYY-MM-DD to YYYY-MM-DD)**: Actionable seed-planting or application window under active dasha sub-period.\n"
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
    "6. Anti-Fatalism & Constructive Reframing: Never use archaic fatalistic or terrifying terms (such as 'ruined', 'doomed', 'death', 'unavoidable disaster'). "
    "Reframe challenging periods (Sade Sati, Ashtama Shani, Rahu Dasha) into strategic discipline, conscious effort, and Lal Kitab upayas.\n"
    "7. Modern Allegorical Translation: Never recite ancient curses or archaic allegories literally. Translate 'pitri dosha' into generational patterns, "
    "father/authority figure dynamics, and behavioral rectification. Focus on character, purpose, and conscious evolution.\n"
    "8. Dignified Spousal & Relationship Analysis: NEVER use derogatory, vulgar, misogynistic, or sexually explicit terms. "
    "Frame relationship dynamics around compatibility, emotional maturity, mutual respect, communication boundaries, and character development.\n"
    "9. Classical Excerpt Handling: Classical texts contain ancient calendar tables or worked-out arithmetic examples (e.g. 'Assume birth on June 1, 1984', Ahargana). "
    "NEVER mistake illustrative ancient math for the seeker's actual chart. Extract and cite only astrological principles.\n"
    "10. Professional Boundaries: Astrological counseling does not replace licensed medical, psychiatric, legal, or financial professionals. "
    "When relevant, advise consulting licensed human specialists.\n"
    "11. Formatting Purity: Do NOT append a redundant 'References:' or 'Citations:' bibliography list at the end of the text. "
    "The UI automatically renders dedicated interactive citation cards below the response."
)

SYSTEM_PROMPT_NE = (
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


def get_system_prompt(language: str = "en") -> str:
    """Return language-specific system prompt."""
    lang = (language or "en").lower().strip()
    if lang in ("ne", "nepali", "nep"):
        return SYSTEM_PROMPT_NE
    return SYSTEM_PROMPT


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


def _format_birth_summary(chart: dict[str, Any]) -> str:
    """Format structured natal chart facts, house lords, ashtakavarga, and transits for synthesis."""
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
                lines.append(
                    f"  • {p.get('name')}: House {p.get('house')} in {p.get('sign')} "
                    f"({deg_val:.2f}° {p.get('nakshatra')} Pada {p.get('pada')}){retro}"
                )

    # Real Ashtakavarga Points
    av = chart.get("ashtakavarga")
    if isinstance(av, dict):
        sav = av.get("sarvashtakavarga")
        if isinstance(sav, list) and len(sav) == 12:
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

        def _clean_node_name(name: str | None) -> str:
            if not name:
                return "Unknown"
            if name == "North Node":
                return "Rahu"
            if name == "South Node":
                return "Ketu"
            return name

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


def build_prompt(
    question: str,
    results: list[SearchResult],
    birth_context: dict[str, Any] | None = None,
    language: str = "en",
) -> str:
    """Assemble the consultation prompt with classical references and natal context."""
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
        summary = _format_birth_summary(birth_context)
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
            "Explain the timing and interpretive framework clearly, and guide the seeker to provide their exact birth date, "
            "time, and location to calculate personalized date ranges down to specific months and weeks.]\n"
        )
    lines.append(f"Question: {question}")
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
        "- **Window 1: Preparation & Application Window (YYYY-MM-DD to YYYY-MM-DD)**\n"
        "- **Window 2: Peak Favorable Window (YYYY-MM-DD to YYYY-MM-DD)**\n"
        "- **Window 3: Caution & Delay Factor (YYYY-MM-DD to YYYY-MM-DD)**\n\n"
        "### 4. Classical Lal Kitab Prescription\n"
        "Prescribe the exact 43-day daytime Lal Kitab upaya, creature/household service, and strict Savdhani (precautionary taboos) from the context.\n\n"
        "Never recite ancient mathematical calculation algorithms, table numbers, or worked-out arithmetic examples from the commentary texts. "
        "Do NOT append a redundant 'References:' or 'Citations:' bibliography list at the end of your response, as the platform interface automatically renders dedicated interactive citation cards below your answer."
    )
    if (language or "").lower().strip() in ("ne", "nepali", "nep"):
        lines.append(
            "\nभाषा निर्देशन: सोधकर्ताको भाषा नेपाली भएकाले सम्पूर्ण परामर्श, विश्लेषण तथा उपायहरू "
            "अत्यन्त शुद्ध, आदरार्थी, स्पष्ट तथा शास्त्रीय नेपाली भाषामा प्रस्तुत गर्नुहोस्।\n"
            "अनिवार्य संरचना निर्देशन:\n"
            "कुनै पनि भूमिका वा अनावश्यक सम्बोधन नगरी सिधै निम्न ४ भागमा प्रामाणिक उत्तर दिनुहोस्:\n"
            "### १. प्रत्यक्ष फलादेश र मुख्य निर्णय\n"
            "### २. ज्योतिषीय आधार र गणितीय प्रमाण\n"
            "### ३. यकिन समय-तालिका (३ वटा स्पष्ट मिति दायरा YYYY-MM-DD)\n"
            "### ४. प्रामाणिक लाल किताब उपाय तथा सावधानी (४३ दिने दिउँसो गरिने उपाय र कडा निषेध)\n"
            "अन्त्यमा सन्दर्भ सूची नदोहोर्‍याउनुहोस्।"
        )
    return "\n".join(lines)


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


def _strip_trailing_references(text: str) -> str:
    """Strip redundant trailing References/Citations section from LLM output.

    The frontend UI renders dedicated interactive citation cards from structured
    metadata, so a raw text bibliography at the bottom of the answer creates
    duplicate visual display.
    """
    pattern = (
        r"(?i)\n+(?:###?\s*)?(?:references|citations|classical citations|shloka citations|"
        r"सन्दर्भहरू?|उद्धरणहरू?)\s*:?\s*\n+.*$"
    )
    return re.sub(pattern, "", text, flags=re.DOTALL).rstrip()


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
                model = "gemini-3.8-flash"
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
        prompt = build_prompt(question, results, birth_context, language=language)
        sys_prompt = get_system_prompt(language)
        try:
            try:
                text = self._complete(prompt, system_prompt=sys_prompt)
            except TypeError:
                text = self._complete(prompt)
            clean_answer = _strip_trailing_references(text)
            return Answer(
                question=question,
                answer=clean_answer,
                citations=extract_citations(text, results),
                model=self.model,
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
                timeout=120.0,
            )
        return self._client

    def _complete_openai(self, prompt: str, system_prompt: str = SYSTEM_PROMPT) -> str:
        client = self._openai_client()
        max_tokens = int(os.environ.get("MAX_OUTPUT_TOKENS", "4096"))
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
            "timeout": 120.0,
            "max_tokens": max_tokens,
        }
        response = client.chat.completions.create(**kwargs)
        return str(response.choices[0].message.content)

    def _complete_google(self, prompt: str, system_prompt: str = SYSTEM_PROMPT) -> str:
        rotation_models = [
            "gemini-3.8-flash",
        ]
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
        for cand in candidates:
            try:
                response = self._client.models.generate_content(model=cand, contents=full_contents)
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
        prompt = build_prompt(question, results, birth_context, language=language)
        sys_prompt = get_system_prompt(language)
        try:
            if self.provider == "google":
                yield from self._stream_google(prompt, system_prompt=sys_prompt)
            elif self.provider in ("openai", "ollama"):
                yield from self._stream_openai(prompt, system_prompt=sys_prompt)
            else:
                try:
                    yield self._complete(prompt, system_prompt=sys_prompt)
                except TypeError:
                    yield self._complete(prompt)
        except Exception as e:
            fb = FallbackSynthesizer()
            notice_prefix = (
                "9router"
                if (self._base_url and "20128" in self._base_url)
                else (
                    "Ollama"
                    if self.provider == "ollama"
                    else ("OpenAI" if self.provider == "openai" else "Gemini")
                )
            )
            yield f"*[Notice: {notice_prefix} service temporarily unavailable ({e}). Retrieved classical scriptural citations:]*\n\n"
            yield from fb.synthesize_stream(question, results, birth_context, language=language)

    def _stream_openai(self, prompt: str, system_prompt: str = SYSTEM_PROMPT) -> Iterator[str]:
        client = self._openai_client()
        max_tokens = int(os.environ.get("MAX_OUTPUT_TOKENS", "4096"))
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
            "stream": True,
            "timeout": 120.0,
            "max_tokens": max_tokens,
        }
        response = client.chat.completions.create(**kwargs)
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                yield str(chunk.choices[0].delta.content)

    def _stream_google(self, prompt: str, system_prompt: str = SYSTEM_PROMPT) -> Iterator[str]:
        rotation_models = [
            "gemini-3.8-flash",
        ]
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
        for cand in candidates:
            try:
                stream_response = self._client.models.generate_content_stream(
                    model=cand, contents=full_contents
                )
                self.model = cand
                for chunk in stream_response:
                    if chunk.text:
                        yield str(chunk.text)
                return
            except Exception as e:
                last_err = e
                err_str = str(e)
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
        lines = [
            f"तपाईंको प्रश्न '{question}' सम्बन्धी शास्त्रीय सन्दर्भहरू:"
            if is_ne
            else f"Regarding your question '{question}':"
        ]
        for index, result in enumerate(results, start=1):
            lines.append(f"{_citation_label(index, result)}: {result.chunk.text}")
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
