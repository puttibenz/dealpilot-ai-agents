"""
CRM Agent — Agent 1
ดึงข้อมูล leads จาก CRM และ rank ตาม win probability score

Implementation: วันที่ 1
ดู Project Plan Section 2.2 (Agent 1)
"""

import os
from pathlib import Path
from typing import List, Optional
from google.adk.agents import Agent
from google.genai import types
from pydantic import BaseModel, Field

from models.data_models import Lead, RankedLead, AgentOutput
from tools.crm_tools import fetch_leads_from_csv, score_lead, rank_leads


# โครงสร้างสำหรับ output ของ Agent (Structured JSON Output)
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


# กำหนด tools สำหรับ Agent
def crm_fetch_tool(filepath: str) -> List[Lead]:
    """
    ดึงข้อมูล leads ทั้งหมดจากไฟล์ CRM CSV
    
    Args:
        filepath: พาธของไฟล์ CSV ที่เก็บข้อมูล leads
        
    Returns:
        รายการของ Lead objects ทั้งหมด
    """
    return fetch_leads_from_csv(filepath)


def lead_scorer_tool(leads: List[Lead], top_n: int = 5) -> List[RankedLead]:
    """
    คำนวณคะแนน (score) และจัดอันดับ leads (rank) ตามโอกาสในการปิดดีล
    
    Args:
        leads: รายการของ leads ที่ดึงมาจาก crm_fetch_tool
        top_n: จำนวน leads ที่สำคัญที่สุดที่ต้องการส่งคืน (ค่าเริ่มต้นคือ 5)
        
    Returns:
        รายการของ RankedLead objects เรียงจากคะแนนสูงสุดลงมา
    """
    return rank_leads(leads, top_n=top_n)


def fetch_and_rank_leads_tool(filepath: str, top_n: int = 5) -> List[RankedLead]:
    """
    ดึงข้อมูล leads จากไฟล์ CSV และจัดอันดับเป็น RankedLead ในขั้นตอนเดียว
    
    Args:
        filepath: พาธของไฟล์ CSV
        top_n: จำนวน leads ที่ต้องการจัดอันดับ
        
    Returns:
        รายการของ RankedLead objects เรียงจากคะแนนสูงสุดลงมา
    """
    leads = fetch_leads_from_csv(filepath)
    return rank_leads(leads, top_n=top_n)


# สร้าง CRM Agent
crm_agent = Agent(
    name="crm_agent",
    description="Agent สำหรับการดึงข้อมูลและจัดอันดับลูกค้าเป้าหมาย (CRM Lead Scoring & Ranking)",
    model=ADK_MODEL,
    instruction=CRM_AGENT_INSTRUCTION,
    tools=[crm_fetch_tool, lead_scorer_tool, fetch_and_rank_leads_tool],
    output_schema=CRMAgentOutputSchema
)
