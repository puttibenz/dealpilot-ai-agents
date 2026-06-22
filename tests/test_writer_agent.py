"""
Tests for Writer Agent
Implementation: Day 3
"""

import pytest
from agents.writer_agent import load_sdr_style


def test_load_sdr_style():
    """Test that SDR writing style profiles are loaded correctly from JSON files."""
    # Load sdr_001 (Somchai) profile
    somchai = load_sdr_style("sdr_001")
    assert somchai["sdr_id"] == "sdr_001"
    assert "Somchai" in somchai["sdr_name"]
    assert "Professional" in somchai["style_description"]
    assert len(somchai["past_emails"]) == 3
    assert somchai["past_emails"][0]["subject"] is not None
    assert somchai["past_emails"][0]["body"] is not None

    # Load sdr_002 (Kevin) profile
    kevin = load_sdr_style("sdr_002")
    assert kevin["sdr_id"] == "sdr_002"
    assert "Kevin" in kevin["sdr_name"]
    assert "Casual" in kevin["style_description"]
    assert len(kevin["past_emails"]) == 3

    # Test fallback option when an invalid ID is provided
    fallback = load_sdr_style("invalid_id")
    assert fallback["sdr_id"] == "sdr_001"  # Returns Somchai's profile as default fallback
