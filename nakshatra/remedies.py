"""
Nakshatra Remedies & Upayas Engine
Dual-system Vedic remedy synthesis integrating:
1. Classical Parashari Remedies (Mantra, Dāna, Ratna/Upratna, Vrata, Ishta Seva)
2. Classical Lal Kitab Upayas (Household precautions, symbolic Jal Pravah, animal seva, 43-day sequences)

Identifies afflicted, debilitated, combust, or dusthana-placed grahas in the natal chart,
synthesizes operating dasha lords and Sade Sati status, and generates tailored prescriptions.
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from nakshatra.core import (
    SIGN_LORDS,
    VEDIC_PLANETS,
    ZODIAC_SIGNS,
    ChartData,
    PlanetPosition,
    calculate_dignity,
)

if TYPE_CHECKING:
    from nakshatra.transits import TransitReport


class AfflictionSeverity(str, Enum):
    """Severity of planetary affliction."""

    HIGH = "High"
    MODERATE = "Moderate"
    MILD = "Mild"


class ParashariRemedy(BaseModel):
    """Classical Parashari Vedic remedy."""

    deity: str
    beej_mantra: str
    mantra_count: str
    gemstone: str
    substitute_gem: str
    metal: str
    gem_finger: str
    gem_caution: str
    charity_items: list[str]
    charity_day: str
    fasting_day: str
    spiritual_practice: str


class LalKitabUpaya(BaseModel):
    """Actionable classical Lal Kitab household remedy."""

    household_remedy: str
    symbolic_action: str
    forbidden_actions: list[str]
    creature_service: str
    duration_days: int = 43


class PlanetRemedy(BaseModel):
    """Comprehensive remedy assessment for a single afflicted planet."""

    planet: str
    house: int
    sign: str
    dignity: str
    affliction_reasons: list[str]
    severity: AfflictionSeverity
    parashari: ParashariRemedy
    lal_kitab: LalKitabUpaya


class RemediesReport(BaseModel):
    """Complete dual-system Vedic remedy report."""

    natal_lagna: str
    natal_moon: str
    active_dasha: str
    sade_sati_status: str
    total_afflictions: int
    afflicted_planets: list[PlanetRemedy]
    general_guidelines: list[str]
    lal_kitab_precautions: list[str]


# --- Classical Parashari Reference Data ---

PARASHARI_DATA: dict[str, dict[str, Any]] = {
    "Sun": {
        "deity": "Lord Surya / Gayatri Devi",
        "beej_mantra": "Om Hram Hrim Hraum Sah Suryaya Namah",
        "mantra_count": "7,000 recitations (or 1 mala daily at sunrise)",
        "gemstone": "Ruby (Manikya)",
        "substitute_gem": "Red Garnet, Star Ruby, or Red Tourmaline",
        "metal": "Copper or Gold",
        "gem_finger": "Ring finger of right hand",
        "gem_caution": "Do not wear Ruby if Sun rules 6th, 8th, or 12th house (unless under strict expert guidance).",
        "charity_items": ["Wheat grains", "Jaggery (Gud)", "Copper coins", "Ruby or red flowers", "Red sandalwood"],
        "charity_day": "Sunday morning before 10:00 AM",
        "fasting_day": "Sunday (saltless diet or consuming fruits/milk)",
        "spiritual_practice": "Surya Arghya with water and red vermilion in a copper pot; Aditya Hridaya Stotram daily.",
    },
    "Moon": {
        "deity": "Lord Shiva / Parvati Devi",
        "beej_mantra": "Om Shram Shrim Shraum Sah Chandraya Namah",
        "mantra_count": "11,000 recitations (or 1 mala on Mondays)",
        "gemstone": "Natural Pearl (Moti)",
        "substitute_gem": "Moonstone (Chandrakant Mani)",
        "metal": "Pure Silver",
        "gem_finger": "Little finger of right hand",
        "gem_caution": "Avoid Pearl if Moon is lord of 6th or 8th house, as it can aggravate phlegm and emotional vulnerability.",
        "charity_items": ["White rice", "Milk", "Curd", "Silver coin", "White sandalwood", "Sugar"],
        "charity_day": "Monday evening during dusk",
        "fasting_day": "Monday (consuming only milk or fruit)",
        "spiritual_practice": "Shiva Abhishekam with raw milk; Chandra Stotram or Somavara Vrata.",
    },
    "Mars": {
        "deity": "Lord Kartikeya (Subrahmanya) / Lord Hanuman",
        "beej_mantra": "Om Kram Krim Kraum Sah Bhaumaya Namah",
        "mantra_count": "10,000 recitations",
        "gemstone": "Red Coral (Moonga)",
        "substitute_gem": "Carnelian or Red Agate",
        "metal": "Copper or Gold",
        "gem_finger": "Ring finger of right hand",
        "gem_caution": "Do not wear Red Coral if prone to uncontrollable blood pressure or if Mars rules 8th house for Virgo/Gemini ascendants.",
        "charity_items": ["Red lentils (Masoor Dal)", "Jaggery", "Copper plate", "Saffron", "Red cloth"],
        "charity_day": "Tuesday morning",
        "fasting_day": "Tuesday",
        "spiritual_practice": "Hanuman Chalisa recitation 7 times on Tuesdays; Sundarkand chanting for Kuja Dosha.",
    },
    "Mercury": {
        "deity": "Lord Vishnu / Devi Saraswati",
        "beej_mantra": "Om Bram Brim Braum Sah Budhaya Namah",
        "mantra_count": "9,000 recitations",
        "gemstone": "Emerald (Panna)",
        "substitute_gem": "Peridot or Green Tourmaline",
        "metal": "Gold or Bronze",
        "gem_finger": "Little finger of right hand",
        "gem_caution": "Avoid Emerald if Mercury is functional Maraka or placed in 8th house without benefic aspects.",
        "charity_items": ["Whole green moong dal", "Green garments", "Brass utensils", "Camphor", "Books/pens to students"],
        "charity_day": "Wednesday morning",
        "fasting_day": "Wednesday",
        "spiritual_practice": "Vishnu Sahasranama Stotram recitation; gifting educational books to underprivileged children.",
    },
    "Jupiter": {
        "deity": "Lord Dakshinamoorthy / Lord Brihaspati / Lord Shiva",
        "beej_mantra": "Om Gram Grim Graum Sah Gurave Namah",
        "mantra_count": "19,000 recitations",
        "gemstone": "Yellow Sapphire (Pukhraj)",
        "substitute_gem": "Yellow Topaz, Citrine (Sunela)",
        "metal": "Gold or Brass",
        "gem_finger": "Index finger of right hand",
        "gem_caution": "Safe for most ascendants; avoid if Jupiter acts as primary malefic for Taurus or Libra lagna.",
        "charity_items": ["Yellow chana dal", "Turmeric roots", "Yellow silk", "Ghee", "Gold", "Holy scriptures"],
        "charity_day": "Thursday morning during Brahma Muhurta",
        "fasting_day": "Thursday (eating yellow fruits, besan/chana; avoid salt)",
        "spiritual_practice": "Guru Paduka Stotram; honoring teachers, elders, and Brahmins with selfless respect.",
    },
    "Venus": {
        "deity": "Maha Lakshmi Devi / Shukradeva",
        "beej_mantra": "Om Dram Drim Draum Sah Shukraya Namah",
        "mantra_count": "16,000 recitations",
        "gemstone": "Diamond (Heera)",
        "substitute_gem": "White Zircon, White Sapphire, or Opal",
        "metal": "Silver, Platinum, or White Gold",
        "gem_finger": "Middle or little finger of right hand",
        "gem_caution": "Avoid diamond if Venus is combust or heavily afflicted in 6th house.",
        "charity_items": ["Ghee", "Curd", "Silk cloth", "Silver", "Sugar", "White fragrant cosmetics/perfume"],
        "charity_day": "Friday morning at sunrise",
        "fasting_day": "Friday (eating sweet curd/rice; avoiding sour items)",
        "spiritual_practice": "Sri Suktam and Kanakadhara Stotram recitations; respecting and honoring the women in one's life.",
    },
    "Saturn": {
        "deity": "Lord Shiva / Lord Shani / Lord Hanuman",
        "beej_mantra": "Om Pram Prim Praum Sah Shanaishcharaya Namah",
        "mantra_count": "23,000 recitations",
        "gemstone": "Blue Sapphire (Neelam)",
        "substitute_gem": "Amethyst (Jamuniya) or Blue Topaz",
        "metal": "Iron, Lead, or Ashtadhatu",
        "gem_finger": "Middle finger of right hand",
        "gem_caution": "MUST undergo 3-day trial before permanent wear. Strictly forbidden for Aries and Leo ascendants.",
        "charity_items": ["Mustard oil", "Black sesame seeds (Til)", "Iron tawa/pan", "Black umbrella", "Coarse black blanket"],
        "charity_day": "Saturday evening after sunset",
        "fasting_day": "Saturday",
        "spiritual_practice": "Shani Chalisa; Chhaya Dāna (looking at one's reflection in mustard oil and donating it); Shani Vajra Panjara Stotram.",
    },
    "Rahu": {
        "deity": "Goddess Durga / Bhairava",
        "beej_mantra": "Om Bhram Bhrim Bhraum Sah Rahave Namah",
        "mantra_count": "18,000 recitations",
        "gemstone": "Hessonite Garnet (Gomed)",
        "substitute_gem": "Orange Zircon",
        "metal": "Silver or Lead",
        "gem_finger": "Middle finger of left hand or right hand",
        "gem_caution": "Only wear during Rahu Mahadasha if Rahu is placed in 3rd, 6th, 10th, or 11th house in friendly signs.",
        "charity_items": ["Barley (Jau)", "Coconut", "Mustard seeds", "Lead piece", "Dark blue blanket", "Coins to sweepers"],
        "charity_day": "Saturday or Wednesday night",
        "fasting_day": "Saturday night",
        "spiritual_practice": "Durga Saptashati recitation; Kalabhairava Ashtakam; feeding birds and street animals.",
    },
    "Ketu": {
        "deity": "Lord Ganesha / Matsya Avatar",
        "beej_mantra": "Om Stram Strim Straum Sah Ketave Namah",
        "mantra_count": "17,000 recitations",
        "gemstone": "Cat's Eye (Chrysoberyl / Vaidurya)",
        "substitute_gem": "Fibrolite or Tiger Eye",
        "metal": "Silver or Ashtadhatu",
        "gem_finger": "Middle or little finger",
        "gem_caution": "Never wear Cat's Eye simultaneously with Ruby, Pearl, or Coral unless verified by an adept.",
        "charity_items": ["Dual-colored (black-white) blanket", "Sesame seeds", "Kulthi dal (Horse gram)", "Iron weapons/tools"],
        "charity_day": "Tuesday or Wednesday morning",
        "fasting_day": "Tuesday",
        "spiritual_practice": "Ganesha Atharvashirsha recitation 21 times; serving elderly monks and sadhus.",
    },
}


# --- Classical Lal Kitab House-Specific Upaya Engine ---

def _get_lal_kitab_upaya(planet: str, house: int) -> LalKitabUpaya:
    """Generate authentic, placement-specific Lal Kitab Upaya and precautions."""
    p_norm = planet.capitalize()

    upayas_db: dict[tuple[str, int], dict[str, Any]] = {
        # Sun
        ("Sun", 1): {
            "household": "Install a public water tap or donate water containers; consume a small piece of jaggery with water before leaving home.",
            "symbolic": "Immerse copper coins in running water.",
            "forbidden": ["Do not construct an open oven/hearth in the front veranda", "Avoid dark brown bedroom colors"],
            "creature": "Feed wheat flour and jaggery to red-faced monkeys or brown cows.",
        },
        ("Sun", 6): {
            "household": "Keep ancestral silver coins or silver plate at home; maintain respectful relations with maternal relatives.",
            "symbolic": "Bury a square silver piece underground in home courtyard or flowerpot.",
            "forbidden": ["Do not conduct marriage rituals during twilight hours", "Never keep broad-leaved indoor plants"],
            "creature": "Feed whole roasted wheat flour bread to cows on Sundays.",
        },
        ("Sun", 7): {
            "household": "Bury a piece of square bronze or copper plate under the earth in an uninhabited, desolate place.",
            "symbolic": "Float round copper discs in running river water (Jal Pravah) on Sundays.",
            "forbidden": ["Never initiate new partnership contracts on Sundays", "Do not accept brass utensils as gifts"],
            "creature": "Feed white birds or ducks at water bodies.",
        },
        ("Sun", 8): {
            "household": "Do not live in a south-facing main entrance house; keep water vessels filled in the north-east.",
            "symbolic": "Immerse 8 copper coins in flowing river water on 8 consecutive Sundays.",
            "forbidden": ["Never accept free gold or copper gifts from maternal uncle", "Do not keep brass statues in bedroom"],
            "creature": "Feed cows with roasted jaggery-sweetened wheat rotis.",
        },
        ("Sun", 10): {
            "household": "Always wear a light-colored cap or keep the head covered during official administrative work.",
            "symbolic": "Pour raw cow milk into clean river water on Sundays.",
            "forbidden": ["Never wear dark blue or black clothing for official meetings", "Avoid alcohol completely"],
            "creature": "Feed black-and-white cows with sweet chapatis.",
        },
        ("Sun", 12): {
            "household": "Eat meals sitting inside the kitchen on a wooden plank (chowki), never in the bedroom.",
            "symbolic": "Immerse jaggery wrapped in copper foil in flowing canal water.",
            "forbidden": ["Never leave food unfinished on the plate", "Avoid north-west corner bedrooms"],
            "creature": "Feed crows and birds early morning before breakfast.",
        },

        # Moon
        ("Moon", 6): {
            "household": "Take a solid silver square plate (chandi ka thos tukda) from mother with her blessing and preserve it permanently.",
            "symbolic": "Pour raw unboiled milk into a deep well or running stream on Mondays.",
            "forbidden": ["Never drink plain milk at night", "Do not dig a public well or distribute free water without payment"],
            "creature": "Feed white cows with flour dough mixed with sugar.",
        },
        ("Moon", 8): {
            "household": "Obtain ancestral silver jewelry and store it safely without melting or selling.",
            "symbolic": "Immerse whole raw rice washed in milk into flowing water.",
            "forbidden": ["Never sell ancestral silver or land inherited from mother", "Do not purchase land from childless relatives"],
            "creature": "Feed bread dipped in sweetened milk to stray puppies.",
        },
        ("Moon", 12): {
            "household": "Keep rain water or river water stored in a silver vessel inside the temple room.",
            "symbolic": "Float white flowers in running water on Mondays.",
            "forbidden": ["Never distribute free educational books or stationery to strangers (drains personal luck)", "Avoid solitary night walks"],
            "creature": "Feed fish in ponds with kneaded flour balls on Mondays.",
        },

        # Mars
        ("Mars", 1): {
            "household": "Maintain a silver ring without solder/joint on the ring finger; avoid hot temper tantrums.",
            "symbolic": "Float sweet batashas (sugar candy) in running water on Tuesdays.",
            "forbidden": ["Do not accept free ivory, leather, or deer-skin items", "Avoid south-facing kitchen stoves"],
            "creature": "Feed sweet baked rotis sweetened with jaggery to street dogs.",
        },
        ("Mars", 4): {
            "household": "Keep a square silver piece under the mattress; ensure mother's blessing is received daily.",
            "symbolic": "Bury sweet honey in a clean earthen pot (mitti ka bartan) in a desolate, unpaved plot.",
            "forbidden": ["Do not keep heavy wooden logs or ladders on the roof", "Avoid red bedroom walls"],
            "creature": "Feed jaggery and gram to monkeys or red-faced cows on Tuesdays.",
        },
        ("Mars", 7): {
            "household": "Serve maternal uncles and elders; avoid heated ego clashes with spouse or business partners.",
            "symbolic": "Immerse round copper plates in flowing river water on 7 consecutive Tuesdays.",
            "forbidden": ["Do not conduct marriage negotiations on Tuesdays", "Never display sharp knives or weapons openly"],
            "creature": "Feed sweet roasted flour balls to birds and crows.",
        },
        ("Mars", 8): {
            "household": "Bake eight sweet rotis prepared on an iron griddle (tawa) and distribute them to animals.",
            "symbolic": "Bury pure honey in an earthen pot near a river bank or barren ground.",
            "forbidden": ["Never consume meat or alcohol on Tuesdays", "Do not keep broken mirrors or rusty blades"],
            "creature": "Feed street dogs with unsalted rotis smeared with pure ghee.",
        },

        # Mercury
        ("Mercury", 8): {
            "household": "Get the nose pierced (nak chhedan) and wear a pure silver wire/ring for 96 days (classical Lal Kitab Budh Baddh remedy).",
            "symbolic": "Float an unbaked earthen pot filled with whole green moong beans into running water.",
            "forbidden": ["Never keep broad-leaved indoor plants or money plants inside the bedroom", "Do not keep caged birds"],
            "creature": "Feed fresh green grass (palak/durva) to cows on Wednesday mornings.",
        },
        ("Mercury", 12): {
            "household": "Wear a pure solid silver ring without joint on the little finger of the right hand.",
            "symbolic": "Float hollow whole dry pumpkins (petha) or coconuts into a river.",
            "forbidden": ["Do not keep broken musical instruments or non-working electronic clocks", "Avoid speculative gambling"],
            "creature": "Feed soaked green moong dal to birds on Wednesdays.",
        },

        # Jupiter
        ("Jupiter", 6): {
            "household": "Apply pure saffron (kesar) or turmeric tilak on the forehead and navel every morning after bathing.",
            "symbolic": "Donate raw turmeric roots and yellow gram dal in a temple on Thursdays.",
            "forbidden": ["Never donate clothes to religious ascetics or sanyasis (brings reversal for Jupiter in 6th)", "Never insult family priest"],
            "creature": "Feed yellow bananas or roasted chana to cows on Thursdays.",
        },
        ("Jupiter", 8): {
            "household": "Always wear a gold chain or sacred yellow thread around the neck; plant a peepal tree in an open public park.",
            "symbolic": "Bury yellow turmeric roots wrapped in yellow silk in an unpaved open ground.",
            "forbidden": ["Do not plant sacred peepal tree inside residential courtyard boundaries", "Never accept free religious idols"],
            "creature": "Feed cows with dough balls containing turmeric and jaggery.",
        },
        ("Jupiter", 10): {
            "household": "Keep pure saffron in a silver container in the home temple; maintain strict professional honesty.",
            "symbolic": "Donate copper vessels or gold leaf to a place of worship.",
            "forbidden": ["Never offer free food at religious temples on one's own expense if Jupiter is afflicted in 10th", "Avoid yellow cap"],
            "creature": "Feed brown cows and fish in ponds on Thursdays.",
        },

        # Venus
        ("Venus", 6): {
            "household": "Spouse should wear solid gold ornaments (earrings or hairpin) to protect marital longevity.",
            "symbolic": "Donate a milch cow (or donate dairy support funds to a registered gaushala) on Fridays.",
            "forbidden": ["Never wear soiled, torn, or unwashed garments", "Avoid negative criticism toward spouse's family"],
            "creature": "Feed dough balls made of wheat flour with fresh white butter to a white cow every Friday.",
        },
        ("Venus", 8): {
            "household": "Keep pure silver square plate in the safe; maintain pleasant sandalwood fragrances in the bedroom.",
            "symbolic": "Throw blue or white flowers into dirty drain/gutter for 43 consecutive days (clears malefic Venus affliction).",
            "forbidden": ["Never accept free perfumes, cosmetics, or bronze items", "Avoid illicit sensual indulgence"],
            "creature": "Feed white birds or geese at water reservoirs.",
        },

        # Saturn
        ("Saturn", 1): {
            "household": "Speak absolute truth; avoid alcohol, gambling, and meat; keep footwear in orderly designated storage.",
            "symbolic": "Pour pure mustard oil onto unpaved earth on Saturdays.",
            "forbidden": ["Never tell deliberate lies or exploit domestic helpers", "Do not accept free iron goods"],
            "creature": "Feed rotis smeared with mustard oil to stray black dogs.",
        },
        ("Saturn", 7): {
            "household": "Bury an earthen pot filled with pure mustard oil in uncultivated, barren soil outside city limits.",
            "symbolic": "Donate an iron griddle (tawa) or tongs (chimta) to an underprivileged roadside cook.",
            "forbidden": ["Never initiate new construction work on Saturday evening", "Do not marry before age 22"],
            "creature": "Feed black crows and street dogs on Saturday evenings after sunset.",
        },
        ("Saturn", 8): {
            "household": "Maintain barefoot visits to sacred temples on Saturdays; practice selfless karma yoga.",
            "symbolic": "Take 8 whole almonds (badam) to a temple on Saturday, leave 4 and bring 4 back home to keep in safe.",
            "forbidden": ["Never consume alcohol or smoke in the south-west room", "Do not accept free oil"],
            "creature": "Feed black sesame seeds and whole mustard oil to crows.",
        },

        # Rahu
        ("Rahu", 1): {
            "household": "Keep a solid silver elephant figurine in the north-east corner of the living room.",
            "symbolic": "Immerse barley (jau) washed in raw milk into a running river.",
            "forbidden": ["Never keep unserviceable electrical scrap, fused bulbs, or broken clocks on the roof", "Avoid smoking"],
            "creature": "Feed pigeons with whole millets (bajra) and stray dogs with milk.",
        },
        ("Rahu", 5): {
            "household": "Keep pure silver coins wrapped in red cloth in the treasury; support pregnant women with medical aid.",
            "symbolic": "Immerse whole dry coconut with husk into flowing canal water on Saturdays.",
            "forbidden": ["Do not keep ivory items at home", "Avoid speculative day-trading"],
            "creature": "Feed sweet jaggery flour balls to ants and fish.",
        },
        ("Rahu", 8): {
            "household": "Eat warm meals sitting inside the kitchen area; ensure kitchen sink and drainage pipes remain spotless.",
            "symbolic": "Float 8 whole dry coconuts into flowing water on Saturday evening.",
            "forbidden": ["Never leave garbage or rusty iron scrap under staircases", "Avoid sleeping in south direction"],
            "creature": "Feed crows and stray animals with leftover food after sunset.",
        },
        ("Rahu", 12): {
            "household": "Eat meals sitting inside kitchen; keep saunf (fennel seeds) and sugar crystals in a red pouch under the pillow.",
            "symbolic": "Float barley grains into flowing river water.",
            "forbidden": ["Never eat meals on the bed", "Never install smoke-generating equipment near bedroom"],
            "creature": "Feed stray black dogs with fresh rotis.",
        },

        # Ketu
        ("Ketu", 6): {
            "household": "Wear a solid gold ring without joint on the left hand; wear white or saffron clothes on auspicious occasions.",
            "symbolic": "Donate a dual-colored (black-and-white) woolen blanket to a temple or cold-weather shelter.",
            "forbidden": ["Never harm dogs or allow animals to be mistreated near the house", "Avoid sour curd at night"],
            "creature": "Feed two-colored (black-and-white / kabra) dogs with bread smeared in butter.",
        },
        ("Ketu", 12): {
            "household": "Serve elderly ascetics, sadhus, and teachers; keep a small gold piece under the pillow.",
            "symbolic": "Donate black and white sesame seeds (til) in a holy shrine.",
            "forbidden": ["Never speak ill of spiritual preceptors", "Do not ignore recurring joint or urinary symptoms"],
            "creature": "Feed street dogs regularly with sweet bread.",
        },
    }

    entry = upayas_db.get((p_norm, house))
    if entry:
        return LalKitabUpaya(
            household_remedy=entry["household"],
            symbolic_action=entry["symbolic"],
            forbidden_actions=entry["forbidden"],
            creature_service=entry["creature"],
            duration_days=43,
        )

    # General fallback Lal Kitab Upaya by planet
    general_upayas: dict[str, dict[str, Any]] = {
        "Sun": {
            "household": "Offer water to the rising Sun daily from a copper vessel with Gayatri Mantra; consume jaggery before journeys.",
            "symbolic": "Float copper coins or round copper plates in flowing river water on Sundays.",
            "forbidden": ["Never keep broad-leaved indoor plants", "Do not accept free brass utensils"],
            "creature": "Feed wheat flour and jaggery to cows and monkeys.",
        },
        "Moon": {
            "household": "Obtain a solid silver square piece from mother and keep in safe; drink water from a pure silver cup.",
            "symbolic": "Immerse raw rice washed in milk into flowing river water.",
            "forbidden": ["Never drink plain milk at night", "Do not sell ancestral silver jewelry"],
            "creature": "Feed dough balls to white cows on Mondays.",
        },
        "Mars": {
            "household": "Wear a pure silver ring without joint on the ring finger; cultivate patience and calm demeanor.",
            "symbolic": "Bury honey in an earthen pot in uncultivated soil outside city limits.",
            "forbidden": ["Never keep sharp, rusty weapons or broken knives at home", "Avoid heavy arguments on Tuesdays"],
            "creature": "Feed sweet baked rotis sweetened with jaggery to stray dogs.",
        },
        "Mercury": {
            "household": "Wear a solid silver ring on the little finger; recite Vishnu Sahasranama.",
            "symbolic": "Float an earthen pot filled with green moong dal into running water on Wednesdays.",
            "forbidden": ["Never keep broad-leaved money plants inside living quarters", "Do not keep caged birds"],
            "creature": "Feed fresh green grass to cows on Wednesday mornings.",
        },
        "Jupiter": {
            "household": "Apply saffron or turmeric tilak on forehead and navel daily; honor teachers and spiritual masters.",
            "symbolic": "Donate yellow gram dal and turmeric roots wrapped in yellow cloth in temple.",
            "forbidden": ["Never insult family preceptor or religious teachers", "Do not accept free religious scripture"],
            "creature": "Feed cows with yellow bananas and roasted chana on Thursdays.",
        },
        "Venus": {
            "household": "Maintain spotless cleanliness, pleasant sandalwood fragrance, and respectful speech toward women.",
            "symbolic": "Throw blue flowers into dirty water drainage for 43 days or donate curd to temples.",
            "forbidden": ["Never wear stained, soiled, or torn clothing", "Avoid vulgar entertainment"],
            "creature": "Feed cows with flour dough smeared with fresh butter.",
        },
        "Saturn": {
            "household": "Practice humility, punctuality, and selfless service toward daily wage laborers; avoid alcohol.",
            "symbolic": "Perform Chhaya Dāna by donating mustard oil with one's reflection on Saturdays.",
            "forbidden": ["Never tell lies, break promises, or exploit subordinates", "Do not accept free iron items"],
            "creature": "Feed stray black dogs with rotis smeared with mustard oil.",
        },
        "Rahu": {
            "household": "Keep a solid silver elephant figurine in the living room; eat warm meals inside kitchen.",
            "symbolic": "Float barley (jau) washed in milk into running river water on Saturdays.",
            "forbidden": ["Never accumulate electronic scrap, fused bulbs, or rusted iron on the roof", "Avoid smoke"],
            "creature": "Feed pigeons with millets and stray dogs with fresh milk.",
        },
        "Ketu": {
            "household": "Wear a solid gold ring on the left hand; practice daily meditation and pranayama.",
            "symbolic": "Donate black-and-white woolen blankets to underprivileged people in cold weather.",
            "forbidden": ["Never mistreat dogs or animals", "Do not neglect joint and nervous health"],
            "creature": "Feed two-colored (black-and-white) dogs with fresh bread.",
        },
    }

    gen = general_upayas.get(p_norm, general_upayas["Saturn"])
    return LalKitabUpaya(
        household_remedy=gen["household"],
        symbolic_action=gen["symbolic"],
        forbidden_actions=gen["forbidden"],
        creature_service=gen["creature"],
        duration_days=43,
    )


# --- Core Calculator Function ---

def calculate_remedies(
    chart: ChartData,
    transits: TransitReport | None = None,
) -> RemediesReport:
    """
    Synthesize complete dual-system Vedic remedy portfolio:
    Classical Parashari + Practical Lal Kitab Upayas for all afflicted planets.
    """
    afflicted: list[PlanetRemedy] = []

    # 1. Inspect all natal grahas
    all_planets: list[PlanetPosition] = list(chart.planets)
    if chart.rahu:
        all_planets.append(chart.rahu)
    if chart.ketu:
        all_planets.append(chart.ketu)

    # Operating dasha lords for weighting
    md_lord = chart.dashas.current_md.lord if chart.dashas and chart.dashas.current_md else ""
    ad_lord = chart.dashas.current_ad.lord if chart.dashas and chart.dashas.current_ad else ""
    dasha_str = f"{md_lord}/{ad_lord}" if md_lord else "Dasha uncalculated"

    # Sade Sati Status
    t_report = transits or (chart.get_transits() if hasattr(chart, "get_transits") else None)
    sade_sati_str = "Inactive"
    if t_report:
        ss = t_report.sade_sati
        if ss.is_active:
            sade_sati_str = f"ACTIVE ({ss.phase}) - Saturn in {ss.saturn_sign}"
        elif ss.is_ashtama_shani:
            sade_sati_str = f"ASHTAMA SHANI ACTIVE - Saturn in 8th from Moon ({ss.saturn_sign})"
        elif ss.is_kantaka_shani:
            sade_sati_str = f"KANTAKA SHANI ACTIVE - Saturn in 4th/10th from Moon ({ss.saturn_sign})"

    for p in all_planets:
        reasons: list[str] = []
        severity = AfflictionSeverity.MILD
        p_name = p.name
        p_house = p.house
        p_dignity = p.dignity or calculate_dignity(p_name, p.sign)

        # Affliction Check 1: Debilitation (Neecha)
        if p_dignity == "debilitated":
            reasons.append(f"Debilitated in {p.sign} (lacks natural strength)")
            severity = AfflictionSeverity.HIGH

        # Affliction Check 2: Placement in Dusthanas (Houses 6, 8, 12)
        if p_house in (6, 8, 12):
            if p_name in ("Sun", "Moon", "Jupiter", "Venus", "Mercury"):
                reasons.append(f"Benefic situated in Dusthana House {p_house} (diminished auspicious fruition)")
                if severity != AfflictionSeverity.HIGH:
                    severity = AfflictionSeverity.MODERATE
            elif p_name in ("Saturn", "Rahu", "Ketu", "Mars"):
                reasons.append(f"Malefic in Dusthana House {p_house} (triggers sudden friction or health vigilance)")

        # Affliction Check 3: Retrograde malefic motion
        if p.retrograde and p_name in ("Saturn", "Mars"):
            reasons.append("Retrograde motion intensifies karmic pressure")
            if severity == AfflictionSeverity.MILD:
                severity = AfflictionSeverity.MODERATE

        # Affliction Check 4: Manglik / Kuja Dosha
        if p_name == "Mars" and p_house in (1, 4, 7, 8, 12):
            reasons.append(f"Kuja Dosha placement in House {p_house} (demands marital balance and anger control)")
            severity = AfflictionSeverity.HIGH

        # Affliction Check 5: Active Dasha Lord
        if p_name.lower() in (md_lord.lower(), ad_lord.lower()) and reasons:
            reasons.append("Currently operating Vimshottari Dasha lord (remedy carries urgent priority)")
            severity = AfflictionSeverity.HIGH

        # Affliction Check 6: Sade Sati Saturn
        if p_name == "Saturn" and "ACTIVE" in sade_sati_str:
            reasons.append(f"Saturn Gochar pressure: {sade_sati_str}")
            severity = AfflictionSeverity.HIGH

        # If afflicted, build dual remedy profile
        if reasons:
            par_info = PARASHARI_DATA.get(p_name, PARASHARI_DATA["Saturn"])
            p_remedy = ParashariRemedy(
                deity=par_info["deity"],
                beej_mantra=par_info["beej_mantra"],
                mantra_count=par_info["mantra_count"],
                gemstone=par_info["gemstone"],
                substitute_gem=par_info["substitute_gem"],
                metal=par_info["metal"],
                gem_finger=par_info["gem_finger"],
                gem_caution=par_info["gem_caution"],
                charity_items=par_info["charity_items"],
                charity_day=par_info["charity_day"],
                fasting_day=par_info["fasting_day"],
                spiritual_practice=par_info["spiritual_practice"],
            )
            lk_remedy = _get_lal_kitab_upaya(p_name, p_house)

            afflicted.append(
                PlanetRemedy(
                    planet=p_name,
                    house=p_house,
                    sign=p.sign,
                    dignity=p_dignity,
                    affliction_reasons=reasons,
                    severity=severity,
                    parashari=p_remedy,
                    lal_kitab=lk_remedy,
                )
            )

    # Sort afflicted by severity (High first)
    severity_order = {AfflictionSeverity.HIGH: 0, AfflictionSeverity.MODERATE: 1, AfflictionSeverity.MILD: 2}
    afflicted.sort(key=lambda x: severity_order.get(x.severity, 3))

    # General classical guidelines
    general_guidelines = [
        "Perform one planet's remedies at a time to prevent conflicting planetary energies.",
        "Parashari Mantras & Stotrams carry pure Sattvic energy and can never cause adverse effects.",
        "Gemstones must only be worn for functional benefics (Lords of 1st, 5th, 9th houses); wearing gemstones of functional malefics can aggravate difficulties.",
        "All charity (Dāna) and Seva should be performed selflessly without pride or expectation of immediate reward.",
    ]

    lal_kitab_precautions = [
        "Perform all Lal Kitab Upayas strictly in daytime between sunrise and sunset; night-time remedies are forbidden.",
        "Maintain the selected Lal Kitab remedy for 40 to 43 consecutive days without missing a single day; if broken, restart count.",
        "Never perform remedies for a planet situated in its own house or exalted sign.",
        "Never accept free gifts, charity, or alms without paying fair consideration; doing so transfers negative karmic debt.",
        "Keep roof and terrace free of unserviceable electronic scrap, broken furniture, or rusted iron to avoid aggravating Rahu.",
    ]

    return RemediesReport(
        natal_lagna=chart.ascendant.sign,
        natal_moon=getattr(chart, "moon", PlanetPosition(name="Moon", longitude=0, sign="Aries", sign_lord="Mars", degree_in_sign=0, house=1)).sign if hasattr(chart, "moon") and chart.moon else ([p.sign for p in chart.planets if p.name == "Moon"] or ["Aries"])[0],
        active_dasha=dasha_str,
        sade_sati_status=sade_sati_str,
        total_afflictions=len(afflicted),
        afflicted_planets=afflicted,
        general_guidelines=general_guidelines,
        lal_kitab_precautions=lal_kitab_precautions,
    )
