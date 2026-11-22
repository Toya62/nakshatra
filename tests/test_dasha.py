"""
Unit tests for Vimshottari Dasha subdivisions (backend).

Regression: the Timeline view defaults to the current Mahadasha and renders
its bhuktis from ``current_md.subs``. ``current_md`` used to be converted
without subdivisions, so the "Mahadasha Breakdown" card rendered its header
over a blank grid. Same for ``current_ad.subs`` (pratyantardashas).
"""

from __future__ import annotations

from nakshatra.core import BirthData, calculate_chart


def _live_example_chart():
    """17 Feb 1984, 09:31, Kathmandu — the chart shown on the live site."""
    birth = BirthData(
        year=1984,
        month=2,
        day=17,
        hour=9,
        minute=31,
        latitude=27.7172,
        longitude=85.3240,
        timezone="Asia/Kathmandu",
    )
    return calculate_chart(birth)


def test_current_md_carries_bhuktis():
    d = _live_example_chart().dashas
    assert d.current_md is not None
    assert d.current_md.lord == "Mars"
    assert d.current_md.subs is not None
    assert len(d.current_md.subs) == 9
    assert [ad.lord for ad in d.current_md.subs] == [
        "Mars", "North Node", "Jupiter", "Saturn", "Mercury",
        "South Node", "Venus", "Sun", "Moon",
    ]
    # Every bhukti carries its pratyantardashas.
    assert all(len(ad.subs or []) == 9 for ad in d.current_md.subs)


def test_current_ad_carries_pratyantardashas():
    d = _live_example_chart().dashas
    assert d.current_ad is not None
    assert d.current_ad.lord == "Saturn"
    assert d.current_ad.subs is not None
    assert len(d.current_ad.subs) == 9
    assert d.current_ad.subs[0].lord == "Saturn"
    # A pratyantardasha (level 3) has no further subdivisions.
    assert d.current_pd is not None
    assert d.current_pd.subs is None


def test_mahadasha_tree_intact():
    d = _live_example_chart().dashas
    assert len(d.mahadashas) == 10
    assert all(len(md.subs or []) == 9 for md in d.mahadashas)
    # The current MD in the list matches the current_md pointer.
    listed = next(m for m in d.mahadashas if m.lord == d.current_md.lord)
    assert listed.start == d.current_md.start
    assert [ad.lord for ad in listed.subs] == [ad.lord for ad in d.current_md.subs]
