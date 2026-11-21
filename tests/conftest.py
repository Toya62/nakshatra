"""
Pytest session fixtures for Nakshatra tests.
Ensures valid corpus and index structures exist on clean checkouts (such as CI runners).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from nakshatra.ai.corpus import ingest_corpus


@pytest.fixture(autouse=True, scope="session")
def ensure_corpus_and_index():
    """Ensure minimal corpus and index exist on CI where index/ and corpus/ are gitignored."""
    index_manifest = Path("index/manifest.json")
    if not index_manifest.is_file():
        corpus_dir = Path("corpus")
        works = {
            "bphs": (
                "BPHS",
                "Chapter 1, Verse 1: The Sun in the first house gives career success and high vitality.\n"
                "Chapter 1, Verse 2: Jupiter in the first house gives boundless wisdom and virtues.\n",
            ),
            "phaladeepika": (
                "Phaladeepika",
                "Chapter 6, Verse 1: Hamsa and Malavya are Pancha Mahapurusha Yogas giving royal stature.\n"
                "Chapter 26, Verse 2: Saturn transiting eighth house from Moon causes Ashtama Shani and Sade Sati.\n",
            ),
            "saravali": (
                "Saravali",
                "Chapter 31, Verse 1: Budhaditya Yoga is formed by conjunction of Sun and Mercury.\n"
                "Chapter 22, Verse 1: Moon in Taurus gives immense wealth and stability.\n",
            ),
            "jaimini_sutras": (
                "Jaimini Upadesha Sutras",
                "Chapter 1, Verse 1: Seven Chara Karakas include Atmakaraka, Amatyakaraka, and Darakaraka.\n"
                "Chapter 1, Verse 3: When Atmakaraka and Amatyakaraka conjoin, Raja Yoga forms.\n",
            ),
            "uttara_kalamrita": (
                "Uttara Kalamrita",
                "Chapter 4, Verse 2: Retrograde debilitated planet rules yield auspicious exalted fruits.\n"
                "Chapter 4, Verse 1: Rahu and Ketu in Kendras act as Yogakarakas.\n",
            ),
            "lal_kitab": (
                "Lal Kitab",
                "Chapter 1, Verse 1: General rules and divine upayas for afflicted planets.\n"
                "Chapter 8, Verse 3: Upayas for Saturn and Sade Sati.\n",
            ),
        }
        for dir_name, (work_name, text) in works.items():
            w_dir = corpus_dir / dir_name
            w_dir.mkdir(parents=True, exist_ok=True)
            meta = w_dir / "meta.json"
            if not meta.is_file():
                meta.write_text(
                    json.dumps(
                        {
                            "work": work_name,
                            "translator": "Classical Test Translation",
                            "license": "Public Domain",
                            "source": "classical shastras",
                        }
                    ),
                    encoding="utf-8",
                )
            txt = w_dir / f"{dir_name}.txt"
            if not txt.is_file():
                txt.write_text(text, encoding="utf-8")

        Path("index").mkdir(parents=True, exist_ok=True)
        ingest_corpus("corpus", "index")
