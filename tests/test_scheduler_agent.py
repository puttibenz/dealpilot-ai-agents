"""
Tests for Scheduler Agent
Implementation: Day 4
"""

import os
import json
import pytest
from pathlib import Path
from unittest.mock import patch
from tools.calendar_tools import create_followup_schedule
from tools.email_tools import generate_html_briefing, send_briefing_email


@pytest.fixture(autouse=True)
def force_mock_mode():
    """Force all functions to run in mock mode by mocking get_google_credentials to return None."""
    with patch("tools.calendar_tools.get_google_credentials", return_value=None):
        with patch("tools.email_tools.get_google_credentials", return_value=None):
            yield


def test_create_followup_schedule():
    """Test date calculation and logging of a 4-step follow-up calendar schedule in mock mode."""
    lead_name = "Bruce Wayne"
    subject = "AI Security Monitoring Systems"
    deal_value = 180000.0
    
    # Remove mock calendar file before running tests
    mock_file = Path("data/mock_calendar.json")
    if mock_file.exists():
        mock_file.unlink()
        
    events = create_followup_schedule(lead_name, subject, deal_value)
    
    assert len(events) == 4
    assert events[0]["title"] == f"Send introductory proposal email: {lead_name}"
    assert events[1]["title"] == f"Follow-up #1: {lead_name}"
    assert events[2]["title"] == f"Follow-up #2: {lead_name}"
    assert events[3]["title"] == f"Break-up Email: {lead_name}"
    
    # Verify that it was successfully saved to a local file
    assert mock_file.exists()
    with open(mock_file, "r", encoding="utf-8") as f:
        file_events = json.load(f)
        assert len(file_events) >= 4
        assert file_events[-1]["lead_name"] == lead_name


def test_generate_html_briefing():
    """Test that the Daily Briefing HTML report is generated correctly and contains all necessary details."""
    drafts = [
        {
            "priority": 1,
            "score": 98.2,
            "lead": {
                "id": "lead_001",
                "name": "Bruce Wayne",
                "company": "Wayne Enterprises",
                "email": "bruce@wayne.com",
                "deal_value": 150000.0,
                "deal_stage": "negotiation",
                "last_contact_date": "2026-06-20",
                "notes": "Interested in enterprise plan."
            },
            "research": {
                "company": "Wayne Enterprises",
                "recent_news": ["Wayne Enterprises announces new clean energy initiatives"],
                "pain_points": ["Difficulty in modernizing legacy factory systems."],
                "talking_points": ["Congratulations on your new clean energy initiatives!"],
                "sources": ["Bloomberg"]
            },
            "email_draft": {
                "subject": "Inquiry regarding clean energy partnership",
                "body": "Hello Bruce...",
                "opening_hook": "Congratulations...",
                "personalization_notes": "Based on recent clean energy news highlights"
            },
            "calendar_schedule": [
                {"title": "Send introductory proposal email: Bruce Wayne", "date": "2026-06-22", "mode": "mock"},
                {"title": "Follow-up #1: Bruce Wayne", "date": "2026-06-25", "mode": "mock"}
            ]
        }
    ]
    
    html = generate_html_briefing(drafts, sdr_name="Somchai", style_description="Professional, polite")
    
    assert "Daily Sales Briefing Report" in html
    assert "Bruce Wayne" in html
    assert "Wayne Enterprises" in html
    assert "$150,000.00" in html
    assert "Somchai" in html
    assert "Professional, polite" in html
    assert "Challenges (Pain Points)" in html


def test_send_briefing_email():
    """Test sending Daily Briefing report in mock mode."""
    html_content = "<h1>Daily Report</h1>"
    recipient = "sales_rep@company.com"
    
    success = send_briefing_email(html_content, recipient)
    assert success is True
