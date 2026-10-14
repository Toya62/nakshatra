"""
Unit tests for Nakshatra Model Context Protocol (MCP) Server.
Validates registration and invocation of all 7 astrological tools.
"""

from __future__ import annotations

import pytest

from nakshatra.mcp_server import server


@pytest.mark.asyncio
async def test_mcp_server_tool_registration():
    """Verify all 7 core tools are registered on the MCP server."""
    tools = await server.list_tools()
    tool_names = {t.name for t in tools}

    expected_tools = {
        "calculate_birth_chart",
        "get_daily_panchanga",
        "match_kundali_compatibility",
        "get_muhurtha_election",
        "get_transits_gochar",
        "detect_vedic_yogas",
        "consult_scripture_rag",
    }
    assert expected_tools.issubset(tool_names)


@pytest.mark.asyncio
async def test_mcp_calculate_birth_chart():
    """Test calculate_birth_chart via MCP tool calling."""
    res = await server.call_tool(
        "calculate_birth_chart",
        {
            "year": 1997,
            "month": 5,
            "day": 22,
            "hour": 4,
            "minute": 53,
            "second": 0,
            "latitude": 27.8667,
            "longitude": 83.4833,
            "timezone": "Asia/Kathmandu",
            "format": "summary",
        },
    )
    assert not res.is_error
    text = res.content[0].text
    assert "VEDIC BIRTH CHART (KUNDALI)" in text
    assert "Ascendant (Lagna): Aries" in text
    assert "Sun" in text
    assert "Moon" in text


@pytest.mark.asyncio
async def test_mcp_get_daily_panchanga():
    """Test get_daily_panchanga via MCP tool calling."""
    res = await server.call_tool(
        "get_daily_panchanga",
        {
            "year": 2026,
            "month": 10,
            "day": 14,
            "hour": 12,
            "minute": 0,
            "latitude": 28.6139,
            "longitude": 77.2090,
            "timezone": "Asia/Kolkata",
        },
    )
    assert not res.is_error
    text = res.content[0].text
    assert "VEDIC PANCHANGA REPORT" in text
    assert "1. VARA" in text
    assert "2. TITHI" in text


@pytest.mark.asyncio
async def test_mcp_match_kundali_compatibility():
    """Test match_kundali_compatibility via MCP tool calling."""
    res = await server.call_tool(
        "match_kundali_compatibility",
        {
            "b_year": 1997,
            "b_month": 5,
            "b_day": 22,
            "b_hour": 4,
            "b_minute": 53,
            "b_latitude": 27.8667,
            "b_longitude": 83.4833,
            "b_timezone": "Asia/Kathmandu",
            "g_year": 1995,
            "g_month": 11,
            "g_day": 28,
            "g_hour": 8,
            "g_minute": 30,
            "g_latitude": 28.6139,
            "g_longitude": 77.2090,
            "g_timezone": "Asia/Kolkata",
            "bride_name": "Sita",
            "groom_name": "Rama",
        },
    )
    assert not res.is_error
    text = res.content[0].text
    assert "VEDIC ASHTAKOOTA COMPATIBILITY REPORT" in text
    assert "TOTAL ASHTAKOOTA:" in text
    assert "KUJA DOSHA (MANGLIK):" in text


@pytest.mark.asyncio
async def test_mcp_get_muhurtha_election():
    """Test get_muhurtha_election via MCP tool calling."""
    res = await server.call_tool(
        "get_muhurtha_election",
        {
            "year": 2026,
            "month": 10,
            "day": 14,
            "hour": 12,
            "minute": 0,
            "latitude": 28.6139,
            "longitude": 77.2090,
            "timezone": "Asia/Kolkata",
        },
    )
    assert not res.is_error
    text = res.content[0].text
    assert "VEDIC MUHURTHA & ELECTION REPORT" in text
    assert "ACTIVE HORA" in text
    assert "CHOGHADIYA" in text


@pytest.mark.asyncio
async def test_mcp_detect_vedic_yogas():
    """Test detect_vedic_yogas via MCP tool calling."""
    res = await server.call_tool(
        "detect_vedic_yogas",
        {
            "year": 1997,
            "month": 5,
            "day": 22,
            "hour": 4,
            "minute": 53,
            "latitude": 27.8667,
            "longitude": 83.4833,
            "timezone": "Asia/Kathmandu",
        },
    )
    assert not res.is_error
    text = res.content[0].text
    assert "VEDIC YOGA DETECTION REPORT" in text


@pytest.mark.asyncio
async def test_mcp_get_transits_gochar():
    """Test get_transits_gochar via MCP tool calling."""
    res = await server.call_tool(
        "get_transits_gochar",
        {
            "birth_year": 1997,
            "birth_month": 5,
            "birth_day": 22,
            "birth_hour": 4,
            "birth_minute": 53,
            "birth_latitude": 27.8667,
            "birth_longitude": 83.4833,
            "birth_timezone": "Asia/Kathmandu",
        },
    )
    assert not res.is_error
    text = res.content[0].text
    assert "TRANSIT (GOCHAR) REPORT" in text
    assert "SADE SATI" in text


@pytest.mark.asyncio
async def test_mcp_consult_scripture_rag():
    """Test consult_scripture_rag tool executes gracefully."""
    res = await server.call_tool(
        "consult_scripture_rag",
        {
            "question": "What happens when Jupiter is in 1st house?",
        },
    )
    assert not res.is_error
    text = res.content[0].text
    # Either returns consultation synthesis or graceful index notice
    assert len(text) > 0
