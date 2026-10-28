"""
Unit tests for Nakshatra CLI argument parsing and commands.
"""

from __future__ import annotations

from nakshatra.cli import _build_chart_parser


def test_build_chart_parser():
    """Verify chart argument parser options."""
    parser = _build_chart_parser()
    args = parser.parse_args([
        "--dob", "2000-01-01",
        "--time", "12:00",
        "--lat", "23.1765",
        "--lon", "75.7885",
        "--tz", "Asia/Kolkata",
        "--format", "json",
    ])
    assert args.dob == "2000-01-01"
    assert args.time == "12:00"
    assert args.lat == 23.1765
    assert args.lon == 75.7885
    assert args.tz == "Asia/Kolkata"
    assert args.format == "json"


def test_chart_parser_flags():
    """Verify boolean feature flags (panchanga, yogas)."""
    parser = _build_chart_parser()
    args = parser.parse_args([
        "--panchanga",
        "--yogas",
        "--pretty",
    ])
    assert args.panchanga is True
    assert args.yogas is True
    assert args.pretty is True
