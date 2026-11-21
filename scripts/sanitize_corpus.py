def sanitize_bphs_vol1():
    path = "corpus/bphs/bphs_vol1.txt"
    with open(path, encoding="utf-8") as f:
        text = f.read()

    # 1. Mercury indicates harlots
    text = text.replace(
        "Mercury indicates \nharlots, mean females and females belonging to traders’ com- \nmunity.",
        "Mercury indicates \nclever, mercantile females, and youth belonging to the trading \ncommunity.",
    )
    # 2. Libra prostitutes
    text = text.replace(
        "female is a virgin; Libra prostitutes, Gemini a house wife and \nso on and so forth.",
        "female is a virgin; Libra women of commerce and fine arts, Gemini a house wife and \nso on and so forth.",
    )
    # 3. Ch. 24 verses 10-13 (v.79 in some editions)
    old_10_13 = (
        "10-13J- Malefics in the 12th and 7th while decreasing \n"
        "fcloon is in the 5th denote that the native will be controlled by \n"
        "his spouse who will be inimical to the race (or family). If the \n"
        "^th house is' Occupied or owned by Saturn/Mars, the native \n"
        "Will beget a harlot as his spouse of she Will be attached tp Othfer \n"
        "men illegally. Should Venus be in a Navamsa of Mars of in a \n"
        "Rasi of Mars or be in aspect to or conjunct Mars, the native \n"
        "Will “kiss” the private parts of the femalc.,^|f Venus is sQ \n"
        "related to Saturn, the native will “kiss” the j private parts of \n\n\n"
        "the male. niv c gailtugsd avitn/s udi io 1 triisani «i "
    )

    new_10_13 = (
        "10-13. Malefics in the 12th and 7th while the decreasing \n"
        "Moon is in the 5th denote that the native will experience domestic \n"
        "friction and temperament clashes in marriage. If the \n"
        "7th house is occupied or owned by Saturn and Mars with malefic aspects, the native \n"
        "may experience intense relationship strain, lack of trust, or marital instability. \n"
        "Should Venus be in a Navamsa of Mars or in a \n"
        "Rasi of Mars or be in aspect to or conjunct Mars, the native \n"
        "possesses intense sensual passions, requiring emotional maturity and fidelity. If Venus is so \n"
        "related to Saturn, the native requires discipline against sensual dissipation."
    )
    text = text.replace(old_10_13, new_10_13)

    # 4. Line 14344
    text = text.replace(
        "The native will coaleasce with harlots.",
        "The native may succumb to sensual distractions or extramarital entanglements.",
    )

    # 5. Line 16056
    text = text.replace(
        "will enjoy pleasures and will befriend \nprostitutes.",
        "will enjoy pleasures and will befriend \nquestionable or self-indulgent associations.",
    )

    # 6. Line 32286
    text = text.replace(
        "skill in sexual acts and in sporting with harlots. Should increa-",
        "delight in sensual romance and worldly entertainments. Should increa-",
    )

    # 7. Line 32583
    text = text.replace(
        "addicted to \nprostitutes and will long for licentious pleasures.",
        "prone to \nexcessive sensual pursuits and worldly indulgences.",
    )
    text = text.replace(
        "will be \naddicted to courtezans and if in the 9th",
        "will be \nfond of sensual entertainment and if in the 9th",
    )

    # 8. Line 32963
    text = text.replace(
        "seeking pleasures through \nharlots.", "seeking pleasures through \nsensual pursuits."
    )

    # 9. Line 33192
    text = text.replace(
        "seek union with dancing females (i.e. prostitutes), will suffer",
        "seek union with frivolous or deceptive companions, will suffer",
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print("Sanitized corpus/bphs/bphs_vol1.txt")


def sanitize_bphs_vol2():
    path = "corpus/bphs/bphs_vol2.txt"
    with open(path, encoding="utf-8") as f:
        text = f.read()

    text = text.replace(
        "on account of association \nwith prostitutes.",
        "on account of association \nwith questionable or dissipative companions.",
    )

    text = text.replace(
        "Venus — Marriage, enjoyments, conveyance, prostitute and \nsexual intercourse with women.",
        "Venus — Marriage, aesthetic enjoyments, conveyances, sensuality, and worldly pleasures.",
    )

    text = text.replace(
        "woman concerned will be of a defective vagina, will have ugly \nbreasts, with sinister (impropitious) eyes, without robes or orna-",
        "woman concerned may experience physical or reproductive sensitivities, lack of comfort, with fatigued eyes, without robes or orna-",
    )

    text = text.replace(
        "35. If the 7th house be in the Navamsa of Mars, the \n"
        "vagina (female organ of the woman concerned), will be diseased \n"
        "and if the 7th house be the Navamsa of a benefic, she will have \n"
        "a well formed female organ and will be beloved by her husband.",
        "35. If the 7th house be in the Navamsa of Mars, the \n"
        "native or spouse may experience physical sensitivities related to reproductive health or emotional discord; \n"
        "and if the 7th house be the Navamsa of a benefic, she will have \n"
        "physical vitality, grace, and will be beloved by her husband.",
    )

    text = text.replace(
        "If the mark \nbe blackish, the woman concerned becomes an adulteress or \nwidow.",
        "If the mark \nbe blackish, the woman concerned faces marital hardship or emotional \nestrangement.",
    )

    text = text.replace(
        "in the centre of the back she will become an adulteress. It will",
        "in the centre of the back denotes vulnerability to marital disharmony. It will",
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print("Sanitized corpus/bphs/bphs_vol2.txt")


if __name__ == "__main__":
    sanitize_bphs_vol1()
    sanitize_bphs_vol2()
