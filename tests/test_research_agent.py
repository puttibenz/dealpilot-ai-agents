"""
Tests for Research Agent
Implementation: Day 2
"""

import pytest
from models.data_models import CompanyResearch
from tools.search_tools import (
    search_company_news,
    extract_pain_points,
    generate_talking_points,
)


def test_search_company_news():
    """Test that company news search returns realistic mock headlines."""
    # Test case with company in the mock database (case-insensitive & substring matching)
    shield_news = search_company_news("Shield Tech")
    assert len(shield_news) == 3
    assert any("series c funding" in news.lower() for news in shield_news)

    # Test case with company not in the mock database (creates dynamic news)
    unknown_news = search_company_news("Unknown Inc")
    assert len(unknown_news) == 3
    assert any("Unknown Inc" in news for news in unknown_news)


def test_extract_pain_points():
    """Test the capability of extracting pain points for a company."""
    # Test retrieving pain points from mock database
    shield_news = [
        "Shield Tech announces new series C funding of $50M for AI defense systems"
    ]
    pain_points = extract_pain_points(shield_news)
    assert len(pain_points) > 0
    assert any("security" in point.lower() or "safety" in point.lower() for point in pain_points)

    # Test analyzing news outside database
    dynamic_news = ["SomeCorp Inc announces major expansion of workflow automation"]
    dynamic_pain = extract_pain_points(dynamic_news)
    assert len(dynamic_pain) > 0
    assert any("scaling" in point or "difficulty" in point.lower() for point in dynamic_pain)


def test_generate_talking_points():
    """Test generating talking points from research results."""
    research = CompanyResearch(
        company="Apex Finance",
        recent_news=["Apex Finance reports 40% growth in transactions"],
        pain_points=["Transaction reporting system is slow and compliance updates are delayed."],
        sources=["Bloomberg"]
    )
    
    talking_points = generate_talking_points(research)
    assert len(talking_points) > 0
    # Confirm it contains a congratulatory note or refers to the company
    assert any("congrats" in pt.lower() or "apex finance" in pt.lower() for pt in talking_points)
