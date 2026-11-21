"""
Classical Lal Kitab 108 House-Specific Upayas, Savdhanis, and Jeev Seva Engine.
Covers all 9 Grahas across all 12 Bhavas (9 x 12 = 108 authentic classical remedies).
All upayas strictly follow the 4 core pillars:
1. Practical Household Remedy (Gharelu Upaya)
2. Symbolic Action (Jal Pravah / Soil Burial / Metal Activation)
3. Creature & Animal Service (Jeev Seva)
4. Inviolable Precautions (Savdhanis / Parhez)
"""

from __future__ import annotations

from typing import Any

LAL_KITAB_108_UPAYAS: dict[tuple[str, int], dict[str, Any]] = {
    # ==================== SUN (SURYA) ====================
    ("Sun", 1): {
        "household": "Install a public water tap or donate water containers; consume a small piece of jaggery with water before leaving home.",
        "symbolic": "Immerse round copper coins in flowing river water (Jal Pravah) on Sundays.",
        "forbidden": [
            "Do not construct an open oven or cooking hearth in the front veranda",
            "Avoid dark brown bedroom walls",
        ],
        "creature": "Feed wheat flour dough and jaggery to red-faced monkeys or brown cows.",
    },
    ("Sun", 2): {
        "household": "Keep a silver coin gifted by mother wrapped in yellow cloth in the cash locker; maintain harmonious speech with family members.",
        "symbolic": "Donate coconut, mustard oil, or raw almonds (badam) at religious shrines.",
        "forbidden": [
            "Never accept gifts of gold, brass, or yellow cloth from in-laws",
            "Do not give false promises to family elders",
        ],
        "creature": "Feed sweet chapatis to cows and monkeys on Sundays.",
    },
    ("Sun", 3): {
        "household": "Maintain affectionate bonding with younger siblings and cousins; bless nephews and nieces.",
        "symbolic": "Float 3 copper coins or whole coconut in running canal water on Sundays.",
        "forbidden": [
            "Never disrespect younger brothers or neighbors",
            "Do not keep non-functional clocks or copper junk",
        ],
        "creature": "Feed whole wheat grains or broken wheat (daliya) to wild birds.",
    },
    ("Sun", 4): {
        "household": "Serve mother and take her blessings every morning; keep ancestral brass utensils spotless.",
        "symbolic": "Immerse a square copper plate in flowing river water on Sundays.",
        "forbidden": [
            "Never trade or deal in bones, ivory, or animal skin",
            "Avoid constructing dark unventilated basements",
        ],
        "creature": "Feed soaked wheat and jaggery to cows and horses.",
    },
    ("Sun", 5): {
        "household": "Maintain kitchen facing east; ensure honesty and commitment towards children and students.",
        "symbolic": "Float red flowers and jaggery wrapped in red cloth in running water on Sundays.",
        "forbidden": [
            "Never make false promises to children",
            "Avoid south-facing kitchen hearths",
        ],
        "creature": "Feed red-faced monkeys or brown cows with roasted wheat flour and jaggery.",
    },
    ("Sun", 6): {
        "household": "Keep ancestral silver coins or silver plate at home; maintain respectful relations with maternal relatives.",
        "symbolic": "Bury a square silver piece underground in home courtyard or flowerpot.",
        "forbidden": [
            "Do not conduct marriage rituals during twilight hours",
            "Never keep broad-leaved indoor plants",
        ],
        "creature": "Feed whole roasted wheat flour bread (rotis) to cows on Sundays.",
    },
    ("Sun", 7): {
        "household": "Bury a piece of square bronze or copper plate under the earth in an uninhabited, desolate place.",
        "symbolic": "Float round copper discs in running river water (Jal Pravah) on Sundays.",
        "forbidden": [
            "Never initiate new partnership contracts on Sundays",
            "Do not accept brass utensils as gifts",
        ],
        "creature": "Feed white birds or ducks at water bodies.",
    },
    ("Sun", 8): {
        "household": "Do not live in a south-facing main entrance house; keep water vessels filled in the north-east.",
        "symbolic": "Immerse 8 copper coins in flowing river water on 8 consecutive Sundays.",
        "forbidden": [
            "Never accept free gold or copper gifts from maternal uncle",
            "Do not keep brass statues in bedroom",
        ],
        "creature": "Feed cows with roasted jaggery-sweetened wheat rotis.",
    },
    ("Sun", 9): {
        "household": "Honor father, grandfathers, and gurus; wear a thin brass or silver ring on index finger.",
        "symbolic": "Donate brass vessels filled with whole wheat grains to a temple on Sundays.",
        "forbidden": [
            "Never accept free religious idols or brass gifts",
            "Avoid harsh words towards mentors and preceptors",
        ],
        "creature": "Feed wheat flour dough balls to fish and sacred cows.",
    },
    ("Sun", 10): {
        "household": "Always wear a light-colored cap or keep the head covered during official administrative work; maintain spotless reputation.",
        "symbolic": "Pour raw cow milk into clean river water on Sundays.",
        "forbidden": [
            "Never wear dark blue or black clothing for official meetings",
            "Avoid alcohol completely",
        ],
        "creature": "Feed black-and-white cows with sweet chapatis.",
    },
    ("Sun", 11): {
        "household": "Eat food sitting in the dining area facing east; maintain strict ethical standards in business gains.",
        "symbolic": "Immerse 11 whole dry almonds in running river water and bring 6 back to keep in safe.",
        "forbidden": [
            "Never consume meat or liquor on Sundays",
            "Never betray business patrons or elder brothers",
        ],
        "creature": "Feed breadcrumbs and whole wheat to crows and pigeons.",
    },
    ("Sun", 12): {
        "household": "Eat meals sitting inside the kitchen on a wooden plank (chowki), never in the bedroom.",
        "symbolic": "Immerse jaggery wrapped in copper foil in flowing canal water.",
        "forbidden": [
            "Never leave food unfinished on the plate",
            "Avoid north-west corner bedrooms",
        ],
        "creature": "Feed crows and birds early morning before breakfast.",
    },

    # ==================== MOON (CHANDRA) ====================
    ("Moon", 1): {
        "household": "Obtain a solid silver square plate (chandi ka thos tukda) from mother with her blessing and preserve it permanently.",
        "symbolic": "Drink water from a pure silver tumbler; pour raw milk on a Shiva Lingam on Mondays.",
        "forbidden": [
            "Never sell silver ancestral jewelry",
            "Avoid excessive water wastage during baths",
        ],
        "creature": "Feed dough balls made of wheat flour to white cows on Mondays.",
    },
    ("Moon", 2): {
        "household": "Maintain soft and compassionate speech; take blessings of maternal elders and mother daily.",
        "symbolic": "Float silver coins or white pearls in running river water on Mondays.",
        "forbidden": [
            "Never accept free silver or liquid dairy from in-laws",
            "Avoid harsh criticism of family members",
        ],
        "creature": "Feed milk-soaked bread to stray puppies and white birds.",
    },
    ("Moon", 3): {
        "household": "Serve younger siblings with affection; keep silver vessels in the house.",
        "symbolic": "Donate rice and raw milk to young girls on Mondays.",
        "forbidden": [
            "Never hoard useless empty bottles or earthen vessels",
            "Avoid disrespecting sisters",
        ],
        "creature": "Feed wheat flour pellets to fish in flowing water.",
    },
    ("Moon", 4): {
        "household": "Serve and care for biological mother; keep a silver pot filled with holy river water at home.",
        "symbolic": "Immerse milk and raw rice in a flowing stream on Mondays.",
        "forbidden": [
            "Never sell ancestral residence or maternal land",
            "Do not keep stagnant rainwater on roofs",
        ],
        "creature": "Feed white cows with flour dough mixed with sugar crystals.",
    },
    ("Moon", 5): {
        "household": "Maintain purity of thoughts; practice meditation and emotional self-regulation.",
        "symbolic": "Donate milk, sugar, and white garments at a temple on Mondays.",
        "forbidden": [
            "Never speak ill of mother or maternal aunt",
            "Do not engage in deceptive financial speculations",
        ],
        "creature": "Feed cows and ducks near water bodies with soaked rice.",
    },
    ("Moon", 6): {
        "household": "Take a solid silver square plate (chandi ka thos tukda) from mother with her blessing and preserve it permanently.",
        "symbolic": "Pour raw unboiled milk into a deep well or running stream on Mondays.",
        "forbidden": [
            "Never drink plain milk at night",
            "Do not dig a public well or distribute free water without payment",
        ],
        "creature": "Feed white cows with flour dough mixed with sugar.",
    },
    ("Moon", 7): {
        "household": "Maintain mutual respect and fidelity with spouse; give gifts of silver to spouse on anniversaries.",
        "symbolic": "Float white flowers and dry coconut in flowing water on Mondays.",
        "forbidden": [
            "Do not marry before age 24 without parental consent",
            "Avoid secret extramarital flirtations",
        ],
        "creature": "Feed sweetened milk to white cows or street dogs.",
    },
    ("Moon", 8): {
        "household": "Obtain ancestral silver jewelry and store it safely without melting or selling.",
        "symbolic": "Immerse whole raw rice washed in milk into flowing water.",
        "forbidden": [
            "Never sell ancestral silver or land inherited from mother",
            "Do not purchase land from childless relatives",
        ],
        "creature": "Feed bread dipped in sweetened milk to stray puppies.",
    },
    ("Moon", 9): {
        "household": "Undertake pilgrimages to sacred water bodies; honor maternal grandparents and religious elders.",
        "symbolic": "Donate silver coins and raw rice in an ancient shrine on Mondays.",
        "forbidden": [
            "Never insult family traditions or spiritual preceptors",
            "Avoid solitary nocturnal travels",
        ],
        "creature": "Feed fish in temple ponds with puffed rice (murmura).",
    },
    ("Moon", 10): {
        "household": "Serve milk to elderly pilgrims and sadhus; avoid taking decisions under impulsive emotional swings.",
        "symbolic": "Float 10 white flowers and raw milk in running river on Mondays.",
        "forbidden": [
            "Avoid consuming alcohol or toxic substances completely",
            "Never drink milk in public during evening",
        ],
        "creature": "Feed black-and-white cows with soaked rice.",
    },
    ("Moon", 11): {
        "household": "Cultivate dependable, honest friendships; drink milk boiled with dried dates (chhuhare).",
        "symbolic": "Pour a cup of raw cow milk into holy river water on Mondays.",
        "forbidden": [
            "Never deceive friends or older siblings for money",
            "Do not indulge in late-night parties",
        ],
        "creature": "Feed birds and stray animals with leftover cooked rice.",
    },
    ("Moon", 12): {
        "household": "Keep rain water or river water stored in a silver vessel inside the temple room.",
        "symbolic": "Float white flowers in running water on Mondays.",
        "forbidden": [
            "Never distribute free educational books or stationery to strangers (drains personal luck)",
            "Avoid solitary night walks",
        ],
        "creature": "Feed fish in ponds with kneaded flour balls on Mondays.",
    },

    # ==================== MARS (MANGAL) ====================
    ("Mars", 1): {
        "household": "Maintain a silver ring without solder/joint on the ring finger; avoid hot temper tantrums.",
        "symbolic": "Float sweet batashas (sugar candy) in running water on Tuesdays.",
        "forbidden": [
            "Do not accept free ivory, leather, or deer-skin items",
            "Avoid south-facing kitchen stoves",
        ],
        "creature": "Feed sweet baked rotis sweetened with jaggery to street dogs.",
    },
    ("Mars", 2): {
        "household": "Speak politely without biting sarcasm; maintain peaceful ties with in-laws and maternal kin.",
        "symbolic": "Immerse red masoor dal wrapped in red cloth in running water on Tuesdays.",
        "forbidden": [
            "Never consume alcohol or red meat on Tuesdays",
            "Do not borrow money from maternal uncle",
        ],
        "creature": "Feed red-faced monkeys or brown cows with roasted gram and jaggery.",
    },
    ("Mars", 3): {
        "household": "Maintain harmonious relations with younger brothers; wear a solid silver ring or bracelet.",
        "symbolic": "Float copper coins or red clay pots in flowing water on Tuesdays.",
        "forbidden": [
            "Never insult or fight with younger brothers",
            "Avoid keeping unused firearms or sharp hunting knives",
        ],
        "creature": "Feed birds with soaked gram and wheat grains.",
    },
    ("Mars", 4): {
        "household": "Keep a square silver piece under the mattress; ensure mother's blessing is received daily.",
        "symbolic": "Bury sweet honey in a clean earthen pot (mitti ka bartan) in a desolate, unpaved plot.",
        "forbidden": [
            "Do not keep heavy wooden logs or ladders on the roof",
            "Avoid red bedroom walls",
        ],
        "creature": "Feed jaggery and gram to monkeys or red-faced cows on Tuesdays.",
    },
    ("Mars", 5): {
        "household": "Be patient with children; do not lose temper during competitive examinations or sports.",
        "symbolic": "Donate sweet red batashas or jaggery in a temple on Tuesdays.",
        "forbidden": [
            "Never use abusive language against ancestors",
            "Avoid gambling and impulsive speculative trades",
        ],
        "creature": "Feed sweet rotis to cows and monkeys on Tuesdays.",
    },
    ("Mars", 6): {
        "household": "Distribute salty foods rather than sweets upon the birth of a male child (pacifies Mars 6th enemies).",
        "symbolic": "Bury a small piece of silver underground near maternal uncle's town or desolate field.",
        "forbidden": [
            "Do not offer sweets to maternal relatives on Tuesdays",
            "Avoid taking uncalculated physical fights",
        ],
        "creature": "Feed street dogs with unsalted rotis smeared with ghee.",
    },
    ("Mars", 7): {
        "household": "Serve maternal uncles and elders; avoid heated ego clashes with spouse or business partners.",
        "symbolic": "Immerse round copper plates in flowing river water on 7 consecutive Tuesdays.",
        "forbidden": [
            "Do not conduct marriage negotiations on Tuesdays",
            "Never display sharp knives or weapons openly",
        ],
        "creature": "Feed sweet roasted flour balls to birds and crows.",
    },
    ("Mars", 8): {
        "household": "Bake eight sweet rotis prepared on an iron griddle (tawa) and distribute them to animals.",
        "symbolic": "Bury pure honey in an earthen pot near a river bank or barren ground.",
        "forbidden": [
            "Never consume meat or alcohol on Tuesdays",
            "Do not keep broken mirrors or rusty blades",
        ],
        "creature": "Feed street dogs with unsalted rotis smeared with pure ghee.",
    },
    ("Mars", 9): {
        "household": "Serve elders, gurus, and spiritual guides; maintain respectful discipline in religious shrines.",
        "symbolic": "Float red sandalwood or red lentils in flowing river on Tuesdays.",
        "forbidden": [
            "Never ridicule spiritual traditions or mendicants",
            "Do not accept free red cloth from ascetics",
        ],
        "creature": "Feed cows and monkeys with boiled gram and jaggery.",
    },
    ("Mars", 10): {
        "household": "Maintain strict professional honesty; avoid taking bribes or abusing administrative power.",
        "symbolic": "Pour fresh milk mixed with water at the roots of a neem or banyan tree.",
        "forbidden": [
            "Never sell ancestral gold or ancestral residence during crises",
            "Avoid dishonest business deals",
        ],
        "creature": "Feed deer or cows in sanctuaries with fresh green fodder.",
    },
    ("Mars", 11): {
        "household": "Cultivate trustworthy business associations; consume honey every morning with lukewarm water.",
        "symbolic": "Donate an earthen pot filled with honey or sindoor in a holy shrine.",
        "forbidden": [
            "Never betray sworn partners or elder brothers",
            "Avoid arrogant behavior towards subordinates",
        ],
        "creature": "Feed crows and stray animals with sweet jaggery chapatis.",
    },
    ("Mars", 12): {
        "household": "Eat meals on a wooden plank inside kitchen; avoid late-night arguments in bedroom.",
        "symbolic": "Float red batashas or jaggery in running canal water on Tuesdays.",
        "forbidden": [
            "Never lend money without legal documentation",
            "Avoid keeping weapons near sleeping area",
        ],
        "creature": "Feed street dogs and stray cattle with freshly baked rotis.",
    },

    # ==================== MERCURY (BUDH) ====================
    ("Mercury", 1): {
        "household": "Wear clean, light-colored clothes; avoid wearing green clothes and refrain from gambling.",
        "symbolic": "Float whole green moong beans wrapped in brass foil into flowing water on Wednesdays.",
        "forbidden": [
            "Never keep caged birds or parrots inside the house",
            "Avoid broad-leaved indoor plants in bedroom",
        ],
        "creature": "Feed fresh green grass (durva/spinach) to cows on Wednesday mornings.",
    },
    ("Mercury", 2): {
        "household": "Maintain absolute truth in speech; refrain from taking false oaths or mimicking disabled persons.",
        "symbolic": "Bury a piece of silver underground in a desolate spot outside the city.",
        "forbidden": [
            "Never accept musical instruments as gifts",
            "Avoid keeping broken glass or damaged electronic clocks",
        ],
        "creature": "Feed green spinach or soaked green gram to goats and cows.",
    },
    ("Mercury", 3): {
        "household": "Clean teeth with alum (phitkari) daily; maintain good relations with sisters and daughters.",
        "symbolic": "Float whole dry hollow gourds or coconuts in flowing river on Wednesdays.",
        "forbidden": [
            "Never keep caged birds or parrots at home",
            "Do not insult or harass sisters or aunts",
        ],
        "creature": "Feed soaked whole moong dal to birds and pigeons.",
    },
    ("Mercury", 4): {
        "household": "Apply saffron tilak; keep silver coins in the safe and avoid unnecessary intellectual arrogance.",
        "symbolic": "Pour raw milk into running water or well on Wednesdays.",
        "forbidden": [
            "Never keep broad-leaved money plants at home",
            "Avoid trading in non-ethical or speculative shares",
        ],
        "creature": "Feed dough balls to white cows and fish in ponds.",
    },
    ("Mercury", 5): {
        "household": "Wear a solid copper coin or medallion around neck on a white thread; speak words of wisdom.",
        "symbolic": "Float 5 dry coconuts or green pulses in running canal water on Wednesdays.",
        "forbidden": [
            "Never consume alcohol or non-vegetarian food",
            "Do not mock religious scholars or teachers",
        ],
        "creature": "Feed soaked green lentils to wild parrots and birds.",
    },
    ("Mercury", 6): {
        "household": "Wear a solid silver ring without solder on the little finger of the right hand; avoid disputes with in-laws.",
        "symbolic": "Float a copper coin with a hole (chhed wala tambe ka paisa) in running river water.",
        "forbidden": [
            "Never engage in commercial speculation or gambling",
            "Do not keep thorny cacti or bonsai plants",
        ],
        "creature": "Feed green fodder to dairy cattle on Wednesdays.",
    },
    ("Mercury", 7): {
        "household": "Maintain pleasant, honest communication with spouse and business partners; honor sister-in-law.",
        "symbolic": "Immerse an earthen pot filled with green moong into flowing water.",
        "forbidden": [
            "Never initiate partnership contracts on Wednesdays",
            "Avoid flirtatious double-entendre speech",
        ],
        "creature": "Feed soaked grains to pigeons and ducks.",
    },
    ("Mercury", 8): {
        "household": "Get the nose pierced (nak chhedan) and wear a pure silver wire/ring for 96 days (classical Lal Kitab Budh Baddh remedy).",
        "symbolic": "Float an unbaked earthen pot filled with whole green moong beans into running water.",
        "forbidden": [
            "Never keep broad-leaved indoor plants or money plants inside the bedroom",
            "Do not keep caged birds",
        ],
        "creature": "Feed fresh green grass (palak/durva) to cows on Wednesday mornings.",
    },
    ("Mercury", 9): {
        "household": "Pierce the nose and wear silver wire; take holy dips in sacred rivers on auspicious days.",
        "symbolic": "Float green moong dal wrapped in yellow cloth in flowing river water.",
        "forbidden": [
            "Never insult ancestral religious traditions",
            "Avoid keeping defaced religious books at home",
        ],
        "creature": "Feed green vegetables and spinach to cows on Wednesdays.",
    },
    ("Mercury", 10): {
        "household": "Maintain high professional integrity; avoid signing contracts without reading all clauses.",
        "symbolic": "Float hollow unpainted wooden toys or dry gourds in running water.",
        "forbidden": [
            "Never accept alcohol or free electronic items from business partners",
            "Avoid keeping money plants",
        ],
        "creature": "Feed birds and street cows with fresh green moong and vegetables.",
    },
    ("Mercury", 11): {
        "household": "Wear a copper coin with a hole around neck; avoid taking unsecured personal loans.",
        "symbolic": "Float 11 green camphor tablets or green moong in running water on Wednesdays.",
        "forbidden": [
            "Never deceive commercial partners or elder sisters",
            "Do not maintain messy, unorganized accounting books",
        ],
        "creature": "Feed soaked pulses to crows and pigeons.",
    },
    ("Mercury", 12): {
        "household": "Wear a pure solid silver ring without joint on the little finger of the right hand.",
        "symbolic": "Float hollow whole dry pumpkins (petha) or coconuts into a river.",
        "forbidden": [
            "Do not keep broken musical instruments or non-working electronic clocks",
            "Avoid speculative gambling",
        ],
        "creature": "Feed soaked green moong dal to birds on Wednesdays.",
    },

    # ==================== JUPITER (GURU) ====================
    ("Jupiter", 1): {
        "household": "Apply pure saffron (kesar) or turmeric tilak on the forehead and navel every morning after bathing.",
        "symbolic": "Donate yellow brass utensils and raw turmeric roots in a temple on Thursdays.",
        "forbidden": [
            "Never accept religious idols or holy books for free",
            "Never disrespect teachers or Brahmins",
        ],
        "creature": "Feed yellow bananas or roasted chana to cows on Thursdays.",
    },
    ("Jupiter", 2): {
        "household": "Maintain truthful, auspicious speech; keep a piece of gold or turmeric root wrapped in yellow cloth in safe.",
        "symbolic": "Donate yellow gram dal (chana dal) and raw turmeric in a place of worship.",
        "forbidden": [
            "Never accept free gold or yellow garments from in-laws",
            "Avoid consuming meat or intoxicating liquors",
        ],
        "creature": "Feed soaked yellow chana dal to horses and cows.",
    },
    ("Jupiter", 3): {
        "household": "Serve and respect elder relatives; wear a gold chain or sacred yellow thread.",
        "symbolic": "Float yellow flowers and turmeric in running river water on Thursdays.",
        "forbidden": [
            "Never insult or quarrel with elder siblings or neighbors",
            "Do not accept free religious articles",
        ],
        "creature": "Feed wheat flour dough balls mixed with turmeric to birds.",
    },
    ("Jupiter", 4): {
        "household": "Serve mother and seek her blessings; keep ancestral brass vessels in the temple.",
        "symbolic": "Pour raw cow milk at the roots of a sacred peepal or banyan tree.",
        "forbidden": [
            "Never sell ancestral religious heirlooms",
            "Avoid building residential rooms over ancestral well",
        ],
        "creature": "Feed cows with sweet dough balls containing jaggery and turmeric.",
    },
    ("Jupiter", 5): {
        "household": "Maintain selfless devotion in education and parenting; support underprivileged students.",
        "symbolic": "Donate educational books, pens, and yellow sweets to poor students on Thursdays.",
        "forbidden": [
            "Never accept charity or free scholarships if financially stable",
            "Avoid arrogance in scholarship",
        ],
        "creature": "Feed monkeys and birds with roasted yellow chickpeas.",
    },
    ("Jupiter", 6): {
        "household": "Apply pure saffron (kesar) or turmeric tilak on forehead and navel every morning; maintain humble lifestyle.",
        "symbolic": "Donate raw turmeric roots and yellow gram dal in a temple on Thursdays.",
        "forbidden": [
            "Never donate clothes to religious ascetics or sanyasis (brings reversal for Jupiter in 6th)",
            "Never insult family priest",
        ],
        "creature": "Feed yellow bananas or roasted chana to cows on Thursdays.",
    },
    ("Jupiter", 7): {
        "household": "Honor and support spouse; avoid religious dogmatism and maintain open-minded family dialogue.",
        "symbolic": "Donate yellow lemons and gold leaf or brass vessels in a temple.",
        "forbidden": [
            "Never build a temple inside residential bedroom",
            "Avoid conducting marital fights in front of elders",
        ],
        "creature": "Feed brown cows with wheat flour dough and yellow gram dal.",
    },
    ("Jupiter", 8): {
        "household": "Always wear a gold chain or sacred yellow thread around neck; plant a peepal tree in an open public park.",
        "symbolic": "Bury yellow turmeric roots wrapped in yellow silk in an unpaved open ground.",
        "forbidden": [
            "Do not plant sacred peepal tree inside residential courtyard boundaries",
            "Never accept free religious idols",
        ],
        "creature": "Feed cows with dough balls containing turmeric and jaggery.",
    },
    ("Jupiter", 9): {
        "household": "Serve spiritual preceptors and gurus; visit ancient sacred pilgrimage shrines.",
        "symbolic": "Float 9 yellow flowers or yellow turmeric roots in holy river water on Thursdays.",
        "forbidden": [
            "Never ridicule ancient scriptures or spiritual saints",
            "Avoid accepting free saffron or yellow cloth",
        ],
        "creature": "Feed fish in temple ponds with sweet dough pellets.",
    },
    ("Jupiter", 10): {
        "household": "Keep pure saffron in a silver container in the home temple; maintain strict professional honesty.",
        "symbolic": "Donate copper vessels or gold leaf to a place of worship.",
        "forbidden": [
            "Never offer free food at religious temples on one's own expense if Jupiter is afflicted in 10th",
            "Avoid yellow cap",
        ],
        "creature": "Feed brown cows and fish in ponds on Thursdays.",
    },
    ("Jupiter", 11): {
        "household": "Honor elder brothers and mentors; consume a pinch of saffron in warm milk on Thursdays.",
        "symbolic": "Float yellow turmeric roots in flowing stream on 11 consecutive Thursdays.",
        "forbidden": [
            "Never betray sworn mentors or patrons",
            "Avoid keeping broken yellow brass idols",
        ],
        "creature": "Feed soaked chickpeas (chana) to birds and street cows.",
    },
    ("Jupiter", 12): {
        "household": "Keep a small piece of pure gold or saffron in the bedroom safe; practice evening meditation.",
        "symbolic": "Float dry coconuts or yellow flowers in running river water on Thursdays.",
        "forbidden": [
            "Never give false testimony or break sworn promises",
            "Avoid solitary night wandering",
        ],
        "creature": "Feed cows with sweet dough balls containing raw sugar and turmeric.",
    },

    # ==================== VENUS (SHUKRA) ====================
    ("Venus", 1): {
        "household": "Spouse should wear solid gold jewelry; avoid using harsh or foul language at home.",
        "symbolic": "Donate white fragrant items, curd, or camphor in a temple on Fridays.",
        "forbidden": [
            "Never wear unwashed, wrinkled, or torn clothes",
            "Avoid illicit romantic affairs",
        ],
        "creature": "Feed dough balls made of wheat flour with fresh white butter to a white cow.",
    },
    ("Venus", 2): {
        "household": "Maintain spotless cleanliness and sweet fragrance in the house; respect spouse and women.",
        "symbolic": "Donate pure desi ghee or white camphor at a sacred shrine on Fridays.",
        "forbidden": [
            "Never accept free perfumes or cosmetics from strangers",
            "Avoid using sarcastic words with spouse",
        ],
        "creature": "Feed white cows with flour dough mixed with sugar crystals.",
    },
    ("Venus", 3): {
        "household": "Show utmost respect and generosity to sisters-in-law and female relatives.",
        "symbolic": "Float 3 white fragrant flowers and raw milk in running water on Fridays.",
        "forbidden": [
            "Never disrespect or insult female relatives",
            "Avoid borrowing luxury vehicles or perfumes",
        ],
        "creature": "Feed birds and ducks with white rice grains.",
    },
    ("Venus", 4): {
        "household": "Keep a square silver piece under the mattress; maintain beautiful interior aesthetics.",
        "symbolic": "Immerse raw rice and white sandalwood in a flowing river on Fridays.",
        "forbidden": [
            "Never sell ancestral jewelry inherited from mother or mother-in-law",
            "Avoid damp, cluttered bathrooms",
        ],
        "creature": "Feed white cows with fresh sweet dough balls.",
    },
    ("Venus", 5): {
        "household": "Maintain high moral rectitude in romance; encourage children in arts, dance, or music.",
        "symbolic": "Donate white silk cloth or pure ghee to a sacred shrine on Fridays.",
        "forbidden": [
            "Never engage in deceitful romantic affairs",
            "Avoid excessive sensual indulgence",
        ],
        "creature": "Feed white birds and geese at ponds with puffed rice.",
    },
    ("Venus", 6): {
        "household": "Spouse should wear solid gold ornaments (earrings or hairpin) to protect marital longevity.",
        "symbolic": "Donate a milch cow (or donate dairy support funds to a registered gaushala) on Fridays.",
        "forbidden": [
            "Never wear soiled, torn, or unwashed garments",
            "Avoid negative criticism toward spouse's family",
        ],
        "creature": "Feed dough balls made of wheat flour with fresh white butter to a white cow every Friday.",
    },
    ("Venus", 7): {
        "household": "Maintain deep marital loyalty; keep pleasant sandalwood and floral fragrances in bedroom.",
        "symbolic": "Float white flowers and dry coconut in flowing canal water on Fridays.",
        "forbidden": [
            "Never engage in secret extramarital affairs",
            "Do not accept free bronze or brass utensils",
        ],
        "creature": "Feed white cows with sweet rotis smeared with white butter.",
    },
    ("Venus", 8): {
        "household": "Keep pure silver square plate in the safe; maintain pleasant sandalwood fragrances in the bedroom.",
        "symbolic": "Throw blue or white flowers into dirty drain/gutter for 43 consecutive days (clears malefic Venus affliction).",
        "forbidden": [
            "Never accept free perfumes, cosmetics, or bronze items",
            "Avoid illicit sensual indulgence",
        ],
        "creature": "Feed white birds or geese at water reservoirs.",
    },
    ("Venus", 9): {
        "household": "Honor married women and elders; visit sacred shrines with spouse on wedding anniversary.",
        "symbolic": "Donate pure silver ornaments or white silk cloth in a shrine on Fridays.",
        "forbidden": [
            "Never disrespect spiritual customs or female mentors",
            "Avoid wearing dirty underwear or unwashed clothes",
        ],
        "creature": "Feed cows and ducks with sweet rice cooked in milk (kheer).",
    },
    ("Venus", 10): {
        "household": "Maintain impeccable moral integrity in professional affairs; dress impeccably and smartly.",
        "symbolic": "Pour cow milk into a deep well or running stream on Fridays.",
        "forbidden": [
            "Never indulge in workplace romances or harassment",
            "Avoid non-ethical trade in luxury goods",
        ],
        "creature": "Feed white cows and stray animals with fresh bread.",
    },
    ("Venus", 11): {
        "household": "Keep pure silver coins wrapped in white silk in treasury; maintain honest friendships.",
        "symbolic": "Donate mustard oil or pure ghee in a holy temple on Fridays.",
        "forbidden": [
            "Never betray friends for sensual or financial favors",
            "Avoid excessive alcoholic parties",
        ],
        "creature": "Feed birds and stray animals with cooked white rice.",
    },
    ("Venus", 12): {
        "household": "Spouse should donate whole dry coconut and kapoor (camphor) in a temple; maintain serene bedroom decor.",
        "symbolic": "Bury a square silver piece in desolate barren land outside the city.",
        "forbidden": [
            "Never speak ill of women or wife in public",
            "Avoid keeping dry or wilted flowers in bedroom",
        ],
        "creature": "Feed white cows with fresh green grass and dough balls on Fridays.",
    },

    # ==================== SATURN (SHANI) ====================
    ("Saturn", 1): {
        "household": "Speak absolute truth; avoid alcohol, gambling, and meat; keep footwear in orderly designated storage.",
        "symbolic": "Pour pure mustard oil onto unpaved earth on Saturdays.",
        "forbidden": [
            "Never tell deliberate lies or exploit domestic helpers",
            "Do not accept free iron goods",
        ],
        "creature": "Feed rotis smeared with mustard oil to stray black dogs.",
    },
    ("Saturn", 2): {
        "household": "Undertake barefoot pilgrimages to temples on Saturdays; maintain serene and calm speech.",
        "symbolic": "Donate mustard oil and black sesame seeds in an iron bowl on Saturdays.",
        "forbidden": [
            "Never consume alcohol or non-vegetarian food",
            "Avoid accepting free oil or iron items",
        ],
        "creature": "Feed black cows and street dogs with mustard-oil smeared bread.",
    },
    ("Saturn", 3): {
        "household": "Help younger siblings and manual laborers; keep iron tools organized and rust-free.",
        "symbolic": "Float 3 iron nails or dark blue cloth in flowing river water on Saturdays.",
        "forbidden": [
            "Never mistreat servants, drivers, or carpenters",
            "Avoid keeping scrap iron on the balcony",
        ],
        "creature": "Feed crows with fried bread (pakoras) on Saturdays.",
    },
    ("Saturn", 4): {
        "household": "Serve elderly parents with selfless care; keep water vessels filled in the home.",
        "symbolic": "Pour raw milk into a deep well or flowing canal water on Saturdays.",
        "forbidden": [
            "Never drink milk from black cows",
            "Never initiate building construction during nighttime",
        ],
        "creature": "Feed fish in ponds with flour balls mixed with black sesame.",
    },
    ("Saturn", 5): {
        "household": "Maintain high ethics in parenting and investment; distribute salty snacks during religious festivities.",
        "symbolic": "Donate 5 whole almonds or dark blankets at an ancient temple on Saturdays.",
        "forbidden": [
            "Never build a house or purchase real estate before age 48 without elder's consent",
            "Avoid gambling",
        ],
        "creature": "Feed sweet rotis smeared with mustard oil to black dogs.",
    },
    ("Saturn", 6): {
        "household": "Be kind and fair to daily wage laborers; maintain spotless cleanliness in bathrooms and drains.",
        "symbolic": "Feed oil-smeared bread to stray dogs; donate iron tawa or chimta to roadside cooks.",
        "forbidden": [
            "Never buy new iron articles or leather shoes on Saturdays",
            "Avoid disputes with subordinates",
        ],
        "creature": "Feed black dogs and crows regularly on Saturday evenings.",
    },
    ("Saturn", 7): {
        "household": "Bury an earthen pot filled with pure mustard oil in uncultivated, barren soil outside city limits.",
        "symbolic": "Donate an iron griddle (tawa) or tongs (chimta) to an underprivileged roadside cook.",
        "forbidden": [
            "Never initiate new construction work on Saturday evening",
            "Do not marry before age 22",
        ],
        "creature": "Feed black crows and street dogs on Saturday evenings after sunset.",
    },
    ("Saturn", 8): {
        "household": "Maintain barefoot visits to sacred temples on Saturdays; practice selfless karma yoga.",
        "symbolic": "Take 8 whole almonds (badam) to a temple on Saturday, leave 4 and bring 4 back home to keep in safe.",
        "forbidden": [
            "Never consume alcohol or smoke in the south-west room",
            "Do not accept free oil",
        ],
        "creature": "Feed black sesame seeds and whole mustard oil to crows.",
    },
    ("Saturn", 9): {
        "household": "Respect ancestral traditions and elderly mendicants; wear an iron ring from a black horse shoe on middle finger.",
        "symbolic": "Float yellow turmeric roots mixed with mustard seeds in running river on Saturdays.",
        "forbidden": [
            "Never accept free shelter or free iron from in-laws",
            "Avoid mocking elderly sadhus",
        ],
        "creature": "Feed black cows and crows with soaked black gram (urad dal).",
    },
    ("Saturn", 10): {
        "household": "Maintain unyielding honesty in career; never accept bribes or exploit workers.",
        "symbolic": "Feed ten visually impaired individuals or daily wage laborers on Saturdays.",
        "forbidden": [
            "Never drink alcohol or consume intoxicants at official gatherings",
            "Do not accept free iron machinery",
        ],
        "creature": "Feed black dogs with bread smeared with mustard oil.",
    },
    ("Saturn", 11): {
        "household": "Cultivate truthful friendships; avoid fraudulent business transactions.",
        "symbolic": "Pour pure mustard oil onto the ground in front of a temple on Saturdays.",
        "forbidden": [
            "Never betray business patrons or elder brothers",
            "Avoid living in a south-facing house",
        ],
        "creature": "Feed birds and stray dogs with whole fried rotis.",
    },
    ("Saturn", 12): {
        "household": "Sleep in a room free from dark corners or dampness; maintain generous charity for the poor.",
        "symbolic": "Donate a coarse black woolen blanket to an impoverished person on Saturday evening.",
        "forbidden": [
            "Never tell lies under oath",
            "Avoid keeping windows open towards the south during sleep",
        ],
        "creature": "Feed black dogs and crows after sunset on Saturdays.",
    },

    # ==================== RAHU ====================
    ("Rahu", 1): {
        "household": "Keep a solid silver elephant figurine in the north-east corner of the living room.",
        "symbolic": "Immerse barley (jau) washed in raw milk into a running river.",
        "forbidden": [
            "Never keep unserviceable electrical scrap, fused bulbs, or broken clocks on the roof",
            "Avoid smoking",
        ],
        "creature": "Feed pigeons with whole millets (bajra) and stray dogs with milk.",
    },
    ("Rahu", 2): {
        "household": "Keep a silver coin or solid silver ball in pocket or cash box; speak softly without harsh expletives.",
        "symbolic": "Float a solid silver ball or raw barley grains in flowing water on Saturdays.",
        "forbidden": [
            "Never accept electrical appliances as gifts from in-laws",
            "Avoid consuming meat and tobacco",
        ],
        "creature": "Feed birds and stray animals with millets and milk.",
    },
    ("Rahu", 3): {
        "household": "Maintain peaceful relations with neighbors and siblings; keep ivory and elephant figurines strictly avoided.",
        "symbolic": "Float whole dry coconuts in running canal water on Saturdays.",
        "forbidden": [
            "Never keep useless junk, broken tiles, or iron scrap on the terrace",
            "Avoid aggressive online disputes",
        ],
        "creature": "Feed crows and street dogs with breadcrumbs.",
    },
    ("Rahu", 4): {
        "household": "Keep a square silver piece wrapped in red cloth under the pillow; keep kitchen clutter-free.",
        "symbolic": "Immerse 400 grams of coriander seeds (dhania) or almonds in flowing river water on Saturdays.",
        "forbidden": [
            "Never renovate or break the home's water tank or drainage without consulting",
            "Avoid dark blue paints",
        ],
        "creature": "Feed fish in ponds with dough pellets on Saturdays.",
    },
    ("Rahu", 5): {
        "household": "Keep pure silver coins wrapped in red cloth in the treasury; support pregnant women with medical aid.",
        "symbolic": "Immerse whole dry coconut with husk into flowing canal water on Saturdays.",
        "forbidden": [
            "Do not keep ivory items at home",
            "Avoid speculative day-trading",
        ],
        "creature": "Feed sweet jaggery flour balls to ants and fish.",
    },
    ("Rahu", 6): {
        "household": "Keep a solid silver ball in pocket; keep work desk clean and free of tangled cables.",
        "symbolic": "Donate dark blue or black blankets to the destitute on Saturdays.",
        "forbidden": [
            "Never harm dogs or allow animals to be beaten near the house",
            "Avoid unnecessary legal entanglements",
        ],
        "creature": "Feed black dogs with sweet rotis and milk.",
    },
    ("Rahu", 7): {
        "household": "Fill an earthen pot with river water and silver coins, seal it tightly, and bury it in deep soil outside town.",
        "symbolic": "Float 7 dry coconuts into flowing river water on Saturday evening.",
        "forbidden": [
            "Never marry before age 21",
            "Do not initiate partnership contracts with untrustworthy strangers",
        ],
        "creature": "Feed stray dogs with fresh milk and bread.",
    },
    ("Rahu", 8): {
        "household": "Eat warm meals sitting inside the kitchen area; ensure kitchen sink and drainage pipes remain spotless.",
        "symbolic": "Float 8 whole dry coconuts into flowing water on Saturday evening.",
        "forbidden": [
            "Never leave garbage or rusty iron scrap under staircases",
            "Avoid sleeping in south direction",
        ],
        "creature": "Feed crows and stray animals with leftover food after sunset.",
    },
    ("Rahu", 9): {
        "household": "Wear a gold chain or saffron tilak; maintain respect towards ancestral elders and spiritual gurus.",
        "symbolic": "Float 900 grams of raw barley grains washed in cow milk in running water.",
        "forbidden": [
            "Never ridicule religious preceptors or family priests",
            "Avoid accepting free electronics",
        ],
        "creature": "Feed street dogs and fish in ponds on Thursdays and Saturdays.",
    },
    ("Rahu", 10): {
        "household": "Always wear a light-colored cap or keep head covered during administrative work; maintain spotless ethics.",
        "symbolic": "Pour raw milk into running water or donate copper vessels filled with sugar in a temple.",
        "forbidden": [
            "Never consume alcohol or smoke in the workplace",
            "Avoid dark blue or black shirts for important meetings",
        ],
        "creature": "Feed black dogs and crows with fresh bread.",
    },
    ("Rahu", 11): {
        "household": "Drink water from a pure silver cup; maintain high moral standards in business profits.",
        "symbolic": "Immerse whole dry coconut with husk into flowing canal water on Saturdays.",
        "forbidden": [
            "Never accept electronic appliances or smoked glass from in-laws",
            "Avoid speculative gambling",
        ],
        "creature": "Feed pigeons and street birds with whole millets (bajra).",
    },
    ("Rahu", 12): {
        "household": "Eat meals sitting inside kitchen; keep saunf (fennel seeds) and sugar crystals in a red pouch under the pillow.",
        "symbolic": "Float barley grains into flowing river water.",
        "forbidden": [
            "Never eat meals on the bed",
            "Never install smoke-generating equipment near bedroom",
        ],
        "creature": "Feed stray black dogs with fresh rotis.",
    },

    # ==================== KETU ====================
    ("Ketu", 1): {
        "household": "Wear a solid gold ring on the left hand index finger; cultivate spiritual detachment and focus.",
        "symbolic": "Donate a two-colored (black-and-white) woolen blanket in an ancient temple.",
        "forbidden": [
            "Never mistreat or harm stray dogs",
            "Avoid wearing multi-colored patched clothing",
        ],
        "creature": "Feed two-colored (black-and-white / kabra) dogs with bread smeared with ghee.",
    },
    ("Ketu", 2): {
        "household": "Apply saffron tilak on forehead; keep a piece of solid silver in the cash locker.",
        "symbolic": "Float yellow lemons or sesame seeds in flowing water on Tuesdays.",
        "forbidden": [
            "Never accept free gold or yellow items from maternal kin",
            "Avoid harsh, abusive vocabulary",
        ],
        "creature": "Feed street dogs with sweet rotis on Tuesdays.",
    },
    ("Ketu", 3): {
        "household": "Wear gold earrings or a gold chain; maintain harmonious ties with younger siblings.",
        "symbolic": "Float 3 dual-colored stones or black-and-white sesame seeds in running canal water.",
        "forbidden": [
            "Never quarrel with siblings or neighbors",
            "Do not ignore recurring ear or throat infections",
        ],
        "creature": "Feed birds and stray dogs regularly with bread.",
    },
    ("Ketu", 4): {
        "household": "Keep a silver vessel filled with holy river water at home; seek mother's blessings daily.",
        "symbolic": "Pour raw milk and yellow flowers into running stream on Tuesdays.",
        "forbidden": [
            "Never sell ancestral family home without elder's consent",
            "Avoid keeping dry plants in courtyard",
        ],
        "creature": "Feed dough balls to white cows and fish in ponds.",
    },
    ("Ketu", 5): {
        "household": "Recite sacred spiritual texts; donate educational books and stationery to underprivileged children.",
        "symbolic": "Donate white and black sesame seeds in a temple on Tuesdays.",
        "forbidden": [
            "Never speak ill of spiritual teachers or sages",
            "Avoid uncalculated speculative investments",
        ],
        "creature": "Feed sweet bread to stray dogs and pigeons.",
    },
    ("Ketu", 6): {
        "household": "Wear a solid gold ring without joint on the left hand; wear white or saffron clothes on auspicious occasions.",
        "symbolic": "Donate a dual-colored (black-and-white) woolen blanket to a temple or cold-weather shelter.",
        "forbidden": [
            "Never harm dogs or allow animals to be mistreated near the house",
            "Avoid sour curd at night",
        ],
        "creature": "Feed two-colored (black-and-white / kabra) dogs with bread smeared in butter.",
    },
    ("Ketu", 7): {
        "household": "Maintain mutual respect and fidelity with spouse; avoid unreasonable suspicion or withdrawal.",
        "symbolic": "Float 7 two-colored dry coconuts in flowing river on Tuesdays.",
        "forbidden": [
            "Never conduct marriage ceremonies without parental blessings",
            "Avoid keeping broken pottery",
        ],
        "creature": "Feed street dogs and white cows with freshly baked rotis.",
    },
    ("Ketu", 8): {
        "household": "Wear a gold chain or gold wire around neck; keep a pet dog at home or care for community dogs.",
        "symbolic": "Donate a dual-colored blanket and black-white sesame seeds in a shrine on Tuesdays.",
        "forbidden": [
            "Never consume meat or alcohol in the bedroom",
            "Avoid ignoring chronic urinary or knee complaints",
        ],
        "creature": "Feed two-colored street dogs with bread soaked in warm milk.",
    },
    ("Ketu", 9): {
        "household": "Serve spiritual preceptors and ascetics; apply saffron or sandalwood tilak on forehead daily.",
        "symbolic": "Float yellow lemons and sesame seeds into flowing river water.",
        "forbidden": [
            "Never insult ancestral traditions or sadhus",
            "Avoid accepting free gold from holy men",
        ],
        "creature": "Feed fish in temple ponds with kneaded flour pellets.",
    },
    ("Ketu", 10): {
        "household": "Maintain high professional character; keep a small piece of silver in pocket during job interviews.",
        "symbolic": "Pour raw milk mixed with honey at the roots of a sacred tree.",
        "forbidden": [
            "Never take credit for subordinate's work",
            "Avoid dark multi-patterned work attire",
        ],
        "creature": "Feed two-colored stray dogs with rotis smeared with butter.",
    },
    ("Ketu", 11): {
        "household": "Wear a solid gold ring on the index finger; cultivate sincere and selfless friendships.",
        "symbolic": "Donate black and white blankets or sesame seeds to an old-age home on Tuesdays.",
        "forbidden": [
            "Never deceive commercial partners or elder relatives",
            "Avoid hoardings of unusable electronic junk",
        ],
        "creature": "Feed stray dogs and birds with sweet baked rotis.",
    },
    ("Ketu", 12): {
        "household": "Serve elderly ascetics, sadhus, and teachers; keep a small gold piece under the pillow.",
        "symbolic": "Donate black and white sesame seeds (til) in a holy shrine.",
        "forbidden": [
            "Never speak ill of spiritual preceptors",
            "Do not ignore recurring joint or urinary symptoms",
        ],
        "creature": "Feed street dogs regularly with sweet bread.",
    },
}
