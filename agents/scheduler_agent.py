"""
Scheduler Agent — Agent 4
Schedule follow-up calendar events and send daily briefing email.
Implementation: Day 4
"""

import os
from pathlib import Path
from typing import List, Optional
from google.adk.agents import Agent
from pydantic import BaseModel, Field

from tools.calendar_tools import create_followup_schedule
from tools.email_tools import send_briefing_email


class CalendarEventSchema(BaseModel):
    event_id: str = Field(description="Created calendar event ID")
    link: str = Field(description="Google Calendar event link")
    title: str = Field(description="Calendar event title")
    date: str = Field(description="Scheduled date (YYYY-MM-DD)")
    mode: str = Field(description="Operation mode: real or mock")


class SchedulerAgentOutputSchema(BaseModel):
    scheduled_events: List[CalendarEventSchema] = Field(description="List of all scheduled calendar events")
    briefing_sent: bool = Field(description="Status indicating if the Daily Briefing email was sent successfully")
    briefing_recipient: str = Field(description="Recipient email address of the Daily Briefing report")
    briefing_html_path: str = Field(description="Local file path to the generated HTML briefing report")


# โหลด instruction prompt
PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "scheduler_agent_prompt.txt"
with open(PROMPT_PATH, "r", encoding="utf-8") as f:
    SCHEDULER_AGENT_INSTRUCTION = f.read()


# โหลด ADK model จาก env หรือ default
ADK_MODEL = os.getenv("ADK_MODEL", "gemini-3.1-flash-lite")


# กำหนด tools สำหรับ Agent
def scheduler_create_schedule_tool(lead_name: str, email_subject: str, deal_value: float) -> List[dict]:
    """
    Create a 4-step follow-up calendar schedule (Day 0, Day 3, Day 7, Day 14) in Google Calendar for this Lead.
    
    Args:
        lead_name: Contact name of the Lead.
        email_subject: Subject line of the introductory email.
        deal_value: Expected deal value.
        
    Returns:
        List of 4 scheduled calendar events as dictionaries.
    """
    return create_followup_schedule(lead_name, email_subject, deal_value)


def scheduler_send_briefing_tool(html_content: str, recipient_email: str) -> bool:
    """
    Send the daily briefing HTML report to the user's (SDR) email and save it locally to data/briefing.html.
    
    Args:
        html_content: Full HTML content of today's briefing report.
        recipient_email: SDR recipient email address.
        
    Returns:
        True if sent or simulated successfully.
    """
    try:
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        briefing_file = data_dir / "briefing.html"
        with open(briefing_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"   [File] Saved local briefing copy to: {briefing_file.absolute()}")
    except Exception as e:
        print(f"   [Warning] Failed to save local briefing HTML: {str(e)}")

    return send_briefing_email(html_content, recipient_email)


def scheduler_generate_html_briefing_tool(leads_data_json: str, sdr_name: str, style_description: str) -> str:
    """
    Generate a premium, formatted HTML Daily Briefing report from the compiled drafts and calendar schedules.
    
    Args:
        leads_data_json: JSON string containing details of all Leads including research, email drafts, and calendar schedules.
        sdr_name: Name of the SDR.
        style_description: Writing style description of the SDR.
        
    Returns:
        Formatted HTML content string.
    """
    import json
    from tools.email_tools import generate_html_briefing
    try:
        drafts = json.loads(leads_data_json)
        return generate_html_briefing(drafts, sdr_name, style_description)
    except Exception as e:
        return f"Error generating HTML briefing: {str(e)}"


# Instantiate Scheduler Agent
scheduler_agent = Agent(
    name="scheduler_agent",
    description="Agent for calendar follow-up scheduling and Daily Briefing delivery (Calendar Follow-up & Briefing Agent)",
    model=ADK_MODEL,
    instruction=SCHEDULER_AGENT_INSTRUCTION,
    tools=[scheduler_create_schedule_tool, scheduler_send_briefing_tool, scheduler_generate_html_briefing_tool],
    output_schema=SchedulerAgentOutputSchema
)
