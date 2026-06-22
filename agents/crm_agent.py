"""
CRM Agent — Agent 1
Fetch leads from CRM and rank them based on win probability score.

Implementation: Day 1
See Project Plan Section 2.2 (Agent 1)
"""

import os
from pathlib import Path
from typing import List, Optional
from google.adk.agents import Agent
from google.genai import types
from pydantic import BaseModel, Field

from models.data_models import Lead, RankedLead, AgentOutput
from tools.crm_tools import fetch_leads_from_csv, score_lead, rank_leads


# Agent Output Schema structure (Structured JSON Output)
class LeadSchema(BaseModel):
    id: str
    name: str
    company: str
    email: str
    deal_value: float
    deal_stage: str
    last_contact_date: str # YYYY-MM-DD format
    notes: Optional[str] = None


class RankedLeadSchema(BaseModel):
    lead: LeadSchema
    score: float
    score_reason: str
    priority: int


class CRMAgentOutputSchema(BaseModel):
    ranked_leads: List[RankedLeadSchema]


# โหลด instruction prompt
PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "crm_agent_prompt.txt"
with open(PROMPT_PATH, "r", encoding="utf-8") as f:
    CRM_AGENT_INSTRUCTION = f.read()


# โหลด ADK model จาก env หรือ default
ADK_MODEL = os.getenv("ADK_MODEL", "gemini-2.5-flash")


from datetime import datetime

def lead_to_dict(lead: Lead) -> dict:
    return {
        "id": lead.id,
        "name": lead.name,
        "company": lead.company,
        "email": lead.email,
        "deal_value": lead.deal_value,
        "deal_stage": lead.deal_stage,
        "last_contact_date": lead.last_contact_date.strftime("%Y-%m-%d"),
        "notes": lead.notes
    }

def dict_to_lead(d: dict) -> Lead:
    try:
        last_contact_date = datetime.strptime(d["last_contact_date"], "%Y-%m-%d")
    except Exception:
        last_contact_date = datetime.now()
    return Lead(
        id=d["id"],
        name=d["name"],
        company=d["company"],
        email=d["email"],
        deal_value=d["deal_value"],
        deal_stage=d["deal_stage"],
        last_contact_date=last_contact_date,
        notes=d.get("notes")
    )

def ranked_lead_to_dict(rl: RankedLead) -> dict:
    return {
        "lead": lead_to_dict(rl.lead),
        "score": rl.score,
        "score_reason": rl.score_reason,
        "priority": rl.priority
    }


# Define tools for the Agent
def crm_fetch_tool(filepath: str) -> List[dict]:
    """
    Fetch all leads from CRM CSV file.
    
    Args:
        filepath: Path to the CRM leads CSV file.
        
    Returns:
        List of leads as dictionaries.
    """
    leads = fetch_leads_from_csv(filepath)
    return [lead_to_dict(l) for l in leads]


def lead_scorer_tool(leads: List[dict], top_n: int = 5) -> List[dict]:
    """
    Score and rank leads based on closing probability.
    
    Args:
        leads: List of leads retrieved from crm_fetch_tool.
        top_n: Number of most important leads to return (default: 5).
        
    Returns:
        List of RankedLeads as dictionaries, sorted by score in descending order.
    """
    lead_objects = [dict_to_lead(l) for l in leads]
    ranked_objects = rank_leads(lead_objects, top_n=top_n)
    return [ranked_lead_to_dict(rl) for rl in ranked_objects]


def fetch_and_rank_leads_tool(filepath: str, top_n: int = 5) -> List[dict]:
    """
    Fetch leads from a CSV file and rank them in a single step.
    
    Args:
        filepath: Path to the CSV file.
        top_n: Number of leads to rank.
        
    Returns:
        List of RankedLeads as dictionaries, sorted by score in descending order.
    """
    leads = fetch_leads_from_csv(filepath)
    ranked_objects = rank_leads(leads, top_n=top_n)
    return [ranked_lead_to_dict(rl) for rl in ranked_objects]


# Instantiate CRM Agent
crm_agent = Agent(
    name="crm_agent",
    description="Agent for lead retrieval and prioritization (CRM Lead Scoring & Ranking)",
    model=ADK_MODEL,
    instruction=CRM_AGENT_INSTRUCTION,
    tools=[crm_fetch_tool, lead_scorer_tool, fetch_and_rank_leads_tool],
    output_schema=CRMAgentOutputSchema
)
