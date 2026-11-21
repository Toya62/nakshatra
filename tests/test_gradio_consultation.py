import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from app import consult_rag_ui

def test_consult_rag_ui_empty_question():
    res = consult_rag_ui(
        question="",
        include_chart=False,
        year=2000,
        month=1,
        day=1,
        hour=12,
        minute=0,
        lat=23.1765,
        lon=75.7885,
        tz="Asia/Kolkata",
    )
    assert "Please enter a question" in res

def test_consult_rag_ui_without_chart():
    res = consult_rag_ui(
        question="What are classical results of Jupiter in 1st house?",
        include_chart=False,
        year=2000,
        month=1,
        day=1,
        hour=12,
        minute=0,
        lat=23.1765,
        lon=75.7885,
        tz="Asia/Kolkata",
        language="en",
    )
    assert isinstance(res, str)
    assert len(res) > 30
    assert "Jupiter" in res or "Classical Scriptural References" in res
