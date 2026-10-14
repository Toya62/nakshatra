"""
Unit tests for Nakshatra Astrological Predictor & Synthesizer Engine.
"""

from __future__ import annotations

import pytest

from nakshatra.core import BirthData, calculate_chart
from nakshatra.predictor import (
    DomainCategory,
    DomainPrediction,
    PromiseTier,
    dasha_lord_relationship,
    evaluate_all_domains,
    evaluate_career,
    evaluate_domain,
    evaluate_health,
    evaluate_relationship,
    evaluate_spiritual_dharma,
    evaluate_wealth,
    filter_active_yogas,
    get_house_by_number,
    get_house_lord,
    get_house_occupants,
    get_house_sav,
    get_planet_by_name,
)


@pytest.fixture(scope="module")
def sample_chart():
    """Deterministic sample birth chart (May 15, 1990 in New York)."""
    birth = BirthData(
        year=1990,
        month=5,
        day=15,
        hour=14,
        minute=30,
        latitude=40.7128,
        longitude=-74.0060,
        timezone="America/New_York",
        place_name="New York, NY",
    )
    return calculate_chart(birth)


class TestPredictorHelpers:
    """Test helper lookup and calculation functions."""

    def test_get_planet_by_name(self, sample_chart):
        sun = get_planet_by_name(sample_chart, "Sun")
        assert sun is not None
        assert sun.name == "Sun"

        rahu = get_planet_by_name(sample_chart, "Rahu")
        assert rahu is not None
        assert rahu.name == "Rahu"

        asc = get_planet_by_name(sample_chart, "Ascendant")
        assert asc is not None
        assert asc.name == "Ascendant"

        missing = get_planet_by_name(sample_chart, "Pluto")
        assert missing is None

    def test_get_house_by_number(self, sample_chart):
        h1 = get_house_by_number(sample_chart, 1)
        assert h1 is not None
        assert h1.house == 1

        h10 = get_house_by_number(sample_chart, 10)
        assert h10 is not None
        assert h10.house == 10

        h13 = get_house_by_number(sample_chart, 13)
        assert h13 is None

    def test_get_house_lord(self, sample_chart):
        lord1 = get_house_lord(sample_chart, 1)
        assert lord1 is not None
        assert isinstance(lord1, str)

        lord10 = get_house_lord(sample_chart, 10)
        assert lord10 is not None
        assert isinstance(lord10, str)

    def test_get_house_occupants(self, sample_chart):
        all_occupants = []
        for h in range(1, 13):
            all_occupants.extend(get_house_occupants(sample_chart, h))
        # Total bodies in 12 houses = 7 grahas + Rahu + Ketu = 9
        assert len(all_occupants) == 9

    def test_get_house_sav(self, sample_chart):
        sav1 = get_house_sav(sample_chart, 1)
        assert sav1 is not None
        assert 15 <= sav1 <= 45  # standard Vedic bindu range


class TestDashaRelationship:
    """Test classical Bhavat Bhavam distance calculation between MD & AD lords."""

    def test_dasha_relationship_valid(self, sample_chart):
        md_lord = sample_chart.dashas.current_md.lord
        ad_lord = sample_chart.dashas.current_ad.lord

        rel = dasha_lord_relationship(md_lord, ad_lord, sample_chart)
        assert "pair" in rel
        assert "name" in rel
        assert "nature" in rel
        assert "description" in rel
        assert "/" in rel["pair"]

    def test_dasha_relationship_conjunction(self, sample_chart):
        # Same planet for MD and AD
        rel = dasha_lord_relationship("Sun", "Sun", sample_chart)
        assert rel["pair"] == "1/1"
        assert "Conjunction" in rel["name"]

    def test_dasha_relationship_missing(self, sample_chart):
        rel = dasha_lord_relationship(None, None, sample_chart)
        assert rel["pair"] == "None"


class TestYogaFiltering:
    """Test filtering of yogas triggered by active dasha lords."""

    def test_filter_active_yogas(self, sample_chart):
        md_lord = sample_chart.dashas.current_md.lord
        ad_lord = sample_chart.dashas.current_ad.lord

        active = filter_active_yogas(sample_chart, md_lord, ad_lord)
        assert isinstance(active, list)
        assert len(active) > 0
        for y in active:
            assert y.is_formed
            assert y.strength != "Cancelled"


class TestDomainEvaluators:
    """Test individual domain prediction evaluators."""

    def test_evaluate_career(self, sample_chart):
        pred = evaluate_career(sample_chart)
        assert isinstance(pred, DomainPrediction)
        assert pred.domain == DomainCategory.CAREER
        assert pred.promise_tier in PromiseTier
        assert 10 in pred.primary_houses
        assert len(pred.classical_citations) >= 2
        assert len(pred.remedies) >= 2
        assert len(pred.key_verdict) > 10

    def test_evaluate_relationship(self, sample_chart):
        pred = evaluate_relationship(sample_chart)
        assert isinstance(pred, DomainPrediction)
        assert pred.domain == DomainCategory.RELATIONSHIP
        assert pred.promise_tier in PromiseTier
        assert 7 in pred.primary_houses
        assert "Venus" in pred.karakas
        assert len(pred.classical_citations) >= 2

    def test_evaluate_wealth(self, sample_chart):
        pred = evaluate_wealth(sample_chart)
        assert isinstance(pred, DomainPrediction)
        assert pred.domain == DomainCategory.WEALTH
        assert pred.promise_tier in PromiseTier
        assert 2 in pred.primary_houses
        assert 11 in pred.primary_houses
        assert "Jupiter" in pred.karakas
        assert len(pred.remedies) >= 2

    def test_evaluate_spiritual_dharma(self, sample_chart):
        pred = evaluate_spiritual_dharma(sample_chart)
        assert isinstance(pred, DomainPrediction)
        assert pred.domain == DomainCategory.SPIRITUAL_DHARMA
        assert pred.promise_tier in PromiseTier
        assert 9 in pred.primary_houses
        assert 12 in pred.primary_houses
        assert "Ketu" in pred.karakas

    def test_evaluate_health(self, sample_chart):
        pred = evaluate_health(sample_chart)
        assert isinstance(pred, DomainPrediction)
        assert pred.domain == DomainCategory.HEALTH
        assert pred.promise_tier in PromiseTier
        assert 1 in pred.primary_houses
        assert 6 in pred.primary_houses

    def test_evaluate_all_domains(self, sample_chart):
        all_preds = evaluate_all_domains(sample_chart)
        assert len(all_preds) == 5
        for cat in ("career", "relationship", "wealth", "spiritual_dharma", "health"):
            assert cat in all_preds
            assert isinstance(all_preds[cat], DomainPrediction)

    def test_evaluate_domain_by_string(self, sample_chart):
        pred = evaluate_domain("career", sample_chart)
        assert pred.domain == DomainCategory.CAREER

        with pytest.raises(ValueError):
            evaluate_domain("invalid_domain", sample_chart)

    def test_evaluate_with_transits(self, sample_chart):
        transits = sample_chart.get_transits()
        pred = evaluate_career(sample_chart, transits=transits)
        assert isinstance(pred, DomainPrediction)
        assert len(pred.active_transits) > 0

    def test_chart_get_predictions_method(self, sample_chart):
        preds = sample_chart.get_predictions()
        assert len(preds) == 5
        career = sample_chart.get_predictions(domain="career")
        assert career.domain == DomainCategory.CAREER
