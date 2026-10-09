"""
Tests for Nakshatra Vedic Astrology Engine.
"""

from __future__ import annotations

import pytest
from nakshatra.core import (
    BirthData,
    Ayanamsa,
    HouseSystem,
    calculate_chart,
    get_sign,
    get_degree_in_sign,
    get_nakshatra,
    calculate_dignity,
)


class TestCoreCalculations:
    """Test core calculation functions."""
    
    def test_get_sign(self):
        assert get_sign(0.0) == "Aries"
        assert get_sign(30.0) == "Taurus"
        assert get_sign(60.0) == "Gemini"
        assert get_sign(359.9) == "Pisces"
    
    def test_get_degree_in_sign(self):
        assert get_degree_in_sign(0.0) == 0.0
        assert get_degree_in_sign(15.5) == 15.5
        assert get_degree_in_sign(30.0) == 0.0
        assert get_degree_in_sign(45.25) == 15.25
    
    def test_get_nakshatra(self):
        # Ashwini: 0° - 13°20'
        nak, lord, pada = get_nakshatra(0.0)
        assert nak == "Ashwini"
        assert lord == "Ketu"
        assert pada == 1
        
        # Mid-Ashwini (6.67° falls in 3rd pada: 0-3.33=pada1, 3.33-6.67=pada2, 6.67-10=pada3)
        nak, lord, pada = get_nakshatra(6.67)
        assert nak == "Ashwini"
        assert pada == 3
        
        # Early Ashwini (2°) should be pada 1
        nak, lord, pada = get_nakshatra(2.0)
        assert pada == 1
        
        # Bharani: 13°20' - 26°40' (starts at 13.333...)
        nak, lord, pada = get_nakshatra(13.334)
        assert nak == "Bharani"
        assert lord == "Venus"
    
    def test_calculate_dignity(self):
        assert calculate_dignity("Sun", "Aries") == "exalted"
        assert calculate_dignity("Sun", "Libra") == "debilitated"
        assert calculate_dignity("Sun", "Leo") == "own_sign"
        assert calculate_dignity("Moon", "Taurus") == "exalted"
        assert calculate_dignity("Mars", "Capricorn") == "exalted"
        assert calculate_dignity("Jupiter", "Cancer") == "exalted"
        assert calculate_dignity("Venus", "Pisces") == "exalted"
        assert calculate_dignity("Saturn", "Libra") == "exalted"
        assert calculate_dignity("Mercury", "Virgo") == "exalted"


class TestChartCalculation:
    """Test full chart calculation."""
    
    def test_basic_chart(self):
        birth = BirthData(
            year=1990, month=5, day=15, hour=14, minute=30,
            latitude=40.7128, longitude=-74.0060,
            timezone="America/New_York",
            place_name="New York, NY"
        )
        
        chart = calculate_chart(birth)
        
        # Verify structure
        assert chart.zodiac.value == "sidereal"
        assert chart.ayanamsa == Ayanamsa.LAHIRI
        assert chart.house_system == HouseSystem.WHOLE_SIGN
        
        # Verify planets (9 grahas)
        planet_names = [p.name for p in chart.planets]
        expected = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
        for p in expected:
            assert p in planet_names
        
        # Verify Rahu/Ketu
        assert chart.rahu.name == "Rahu"
        assert chart.ketu.name == "Ketu"
        # Rahu and Ketu should be ~180° apart
        diff = abs(chart.rahu.longitude - chart.ketu.longitude)
        diff = min(diff, 360 - diff)
        assert abs(diff - 180) < 1.0  # Within 1 degree
        
        # Verify Ascendant
        assert chart.ascendant.name == "Ascendant"
        assert chart.ascendant.house == 1
        
        # Verify Midheaven
        assert chart.midheaven.name == "Midheaven"
        
        # Verify houses (12)
        assert len(chart.houses) == 12
        house_nums = [h.house for h in chart.houses]
        assert house_nums == list(range(1, 13))
        
        # Verify aspects exist
        assert isinstance(chart.aspects, list)
    
    def test_chart_json_serialization(self):
        birth = BirthData(
            year=1990, month=5, day=15, hour=14, minute=30,
            latitude=40.7128, longitude=-74.0060,
            timezone="America/New_York"
        )
        
        chart = calculate_chart(birth)
        json_str = chart.to_json()
        
        assert isinstance(json_str, str)
        assert "Sun" in json_str
        assert "Ascendant" in json_str
        assert "nakshatra" in json_str
    
    def test_chart_dict_serialization(self):
        birth = BirthData(
            year=1990, month=5, day=15, hour=14, minute=30,
            latitude=40.7128, longitude=-74.0060,
            timezone="America/New_York"
        )
        
        chart = calculate_chart(birth)
        data = chart.to_dict()
        
        assert isinstance(data, dict)
        assert "planets" in data
        assert "houses" in data
        assert "aspects" in data
        assert data["ayanamsa"] == "lahiri"
        assert data["house_system"] == "WholeSign"
    
    def test_different_ayanamsas(self):
        birth = BirthData(
            year=1990, month=5, day=15, hour=14, minute=30,
            latitude=40.7128, longitude=-74.0060,
            timezone="America/New_York"
        )
        
        for ayanamsa in Ayanamsa:
            chart = calculate_chart(birth, ayanamsa=ayanamsa)
            assert chart.ayanamsa == ayanamsa
            # Sun position should differ between ayanamsas
            if ayanamsa != Ayanamsa.LAHIRI:
                lahiri_chart = calculate_chart(birth, ayanamsa=Ayanamsa.LAHIRI)
                # At least one planet should have different longitude
                diffs = [
                    abs(p1.longitude - p2.longitude)
                    for p1, p2 in zip(chart.planets, lahiri_chart.planets)
                ]
                assert any(d > 0.01 for d in diffs), f"{ayanamsa.value} should differ from Lahiri"
    
    def test_different_house_systems(self):
        birth = BirthData(
            year=1990, month=5, day=15, hour=14, minute=30,
            latitude=40.7128, longitude=-74.0060,
            timezone="America/New_York"
        )
        
        for house_system in HouseSystem:
            chart = calculate_chart(birth, house_system=house_system)
            assert chart.house_system == house_system
            assert len(chart.houses) == 12
    
    def test_indian_birth(self):
        """Test with Indian coordinates (Bangalore)."""
        birth = BirthData(
            year=1990, month=5, day=15, hour=14, minute=30,
            latitude=12.9716, longitude=77.5946,
            timezone="Asia/Kolkata",
            place_name="Bangalore, India"
        )
        
        chart = calculate_chart(birth)
        
        # Should have valid data - 7 grahas
        assert len(chart.planets) == 7  # 7 grahas
        assert chart.ascendant.sign in [
            "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
            "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
        ]
    
    def test_planet_house_assignment(self):
        """Verify planets are assigned to correct houses (Whole Sign)."""
        birth = BirthData(
            year=1990, month=5, day=15, hour=14, minute=30,
            latitude=40.7128, longitude=-74.0060,
            timezone="America/New_York"
        )
        
        chart = calculate_chart(birth)
        
        # Get ascendant sign
        asc_sign = chart.ascendant.sign
        signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                 "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
        asc_idx = signs.index(asc_sign)
        
        # Each planet's house should match whole sign from ascendant
        for planet in chart.planets:
            planet_idx = signs.index(planet.sign)
            expected_house = ((planet_idx - asc_idx) % 12) + 1
            assert planet.house == expected_house, \
                f"{planet.name} in {planet.sign} should be in house {expected_house}, got {planet.house}"


class TestBirthData:
    """Test BirthData model."""
    
    def test_datetime_utc_conversion(self):
        birth = BirthData(
            year=1990, month=5, day=15, hour=14, minute=30,
            latitude=40.7128, longitude=-74.0060,
            timezone="America/New_York"  # EDT = UTC-4 in May
        )
        
        utc_dt = birth.datetime_utc
        # 14:30 EDT = 18:30 UTC
        assert utc_dt.hour == 18
        assert utc_dt.minute == 30
    
    def test_birth_data_validation(self):
        # Valid data should work
        birth = BirthData(
            year=2000, month=1, day=1, hour=12, minute=0,
            latitude=0.0, longitude=0.0, timezone="UTC"
        )

class TestVedicExtensions:
    """Test rich Vedic extensions: dashas, vargas, ashtakavarga, shadbala, upagrahas."""

    def test_vimshottari_dashas(self):
        birth = BirthData(
            year=1997, month=5, day=22, hour=4, minute=53,
            latitude=27.8667, longitude=83.4833,
            timezone="Asia/Kathmandu",
            place_name="Palpa, Nepal"
        )
        chart = calculate_chart(birth)
        assert chart.dashas is not None
        assert chart.dashas.birth_nakshatra == "Vishakha"
        assert chart.dashas.balance_lord == "Jupiter"
        assert chart.dashas.balance_years > 0.0

        # Verify MDs
        assert len(chart.dashas.mahadashas) >= 9
        first_md = chart.dashas.mahadashas[0]
        assert first_md.lord == "Jupiter"
        assert first_md.subs is not None
        assert len(first_md.subs) == 9  # 9 Antardashas

        first_ad = first_md.subs[0]
        assert first_ad.subs is not None
        assert len(first_ad.subs) == 9  # 9 Pratyantardashas

        # Active current dasha
        assert chart.dashas.current_md is not None
        assert chart.dashas.current_ad is not None
        assert chart.dashas.current_pd is not None

    def test_vargas_shodashavarga(self):
        birth = BirthData(
            year=1997, month=5, day=22, hour=4, minute=53,
            latitude=27.8667, longitude=83.4833,
            timezone="Asia/Kathmandu",
        )
        chart = calculate_chart(birth)
        assert chart.vargas is not None
        expected_vargas = ["D1", "D2", "D3", "D4", "D7", "D9", "D10", "D12", "D16", "D20", "D24", "D27", "D30", "D40", "D45", "D60"]
        for v in expected_vargas:
            assert v in chart.vargas
            assert "Moon" in chart.vargas[v]
            assert "Sun" in chart.vargas[v]

        # In reference chart, Moon Navamsa (D9) is Cancer
        assert chart.vargas["D9"]["Moon"] == "Cancer"

    def test_ashtakavarga(self):
        birth = BirthData(
            year=1997, month=5, day=22, hour=4, minute=53,
            latitude=27.8667, longitude=83.4833,
            timezone="Asia/Kathmandu",
        )
        chart = calculate_chart(birth)
        assert chart.ashtakavarga is not None
        assert chart.ashtakavarga.grand_total == 337
        assert len(chart.ashtakavarga.sarvashtakavarga) == 12

    def test_shadbala(self):
        birth = BirthData(
            year=1997, month=5, day=22, hour=4, minute=53,
            latitude=27.8667, longitude=83.4833,
            timezone="Asia/Kathmandu",
        )
        chart = calculate_chart(birth)
        assert chart.shadbala is not None
        for p in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
            assert p in chart.shadbala
            assert chart.shadbala[p].total_rupas > 0
            assert isinstance(chart.shadbala[p].sufficient, bool)

    def test_upagrahas(self):
        birth = BirthData(
            year=1997, month=5, day=22, hour=4, minute=53,
            latitude=27.8667, longitude=83.4833,
            timezone="Asia/Kathmandu",
        )
        chart = calculate_chart(birth)
        assert chart.upagrahas is not None
        names = [u.name for u in chart.upagrahas]
        assert "Dhuma" in names
        assert "Vyatipata" in names
        assert "Parivesha" in names
        assert "Indrachapa" in names
        assert "Upaketu" in names

    def test_reference_chart_concordance(self):
        """Test against TNP LCP.txt reference chart."""
        birth = BirthData(
            year=1997, month=5, day=22, hour=4, minute=53, second=0,
            latitude=27 + 52/60, longitude=83 + 29/60,
            timezone="Asia/Kathmandu",
            place_name="Palpa, Nepal"
        )
        chart = calculate_chart(birth)

        # Check Signs
        assert chart.ascendant.sign == "Aries"
        p_signs = {p.name: p.sign for p in chart.planets}
        assert p_signs["Sun"] == "Taurus"
        assert p_signs["Moon"] == "Scorpio"
        assert p_signs["Mars"] == "Leo"
        assert p_signs["Mercury"] == "Aries"
        assert p_signs["Jupiter"] == "Capricorn"
        assert p_signs["Venus"] == "Taurus"
        assert p_signs["Saturn"] == "Pisces"
        assert chart.rahu.sign == "Virgo"
        assert chart.ketu.sign == "Pisces"

        # Check Houses (Whole Sign)
        p_houses = {p.name: p.house for p in chart.planets}
        assert chart.ascendant.house == 1
        assert p_houses["Sun"] == 2
        assert p_houses["Moon"] == 8
        assert p_houses["Mars"] == 5
        assert p_houses["Mercury"] == 1
        assert p_houses["Jupiter"] == 10
        assert p_houses["Venus"] == 2
        assert p_houses["Saturn"] == 12
        assert chart.rahu.house == 6
        assert chart.ketu.house == 12


if __name__ == "__main__":
    pytest.main([__file__, "-v"])