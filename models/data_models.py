"""
DealPilot Data Models
ข้อมูล dataclasses ทั้งหมดที่ใช้ในระบบ — ดู Project Plan Section 3
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class Lead:
    """ข้อมูล lead จาก CRM"""
    id: str
    name: str
    company: str
    email: str
    deal_value: float
    deal_stage: str  # "prospecting" | "qualified" | "proposal" | "negotiation"
    last_contact_date: datetime
    notes: Optional[str] = None


@dataclass
class RankedLead:
    """Lead ที่ผ่านการ rank แล้ว"""
    lead: Lead
    score: float           # 0.0 - 100.0
    score_reason: str      # อธิบายว่าทำไมถึงได้คะแนนนี้
    priority: int          # 1 = highest


@dataclass
class CompanyResearch:
    """ผลการ research บริษัทลูกค้า"""
    company: str
    recent_news: list[str] = field(default_factory=list)    # max 3 items
    pain_points: list[str] = field(default_factory=list)    # inferred from news
    talking_points: list[str] = field(default_factory=list) # ready-to-use ใน email
    sources: list[str] = field(default_factory=list)


@dataclass
class DraftEmail:
    """Email ที่ Writer Agent สร้าง"""
    lead: RankedLead
    subject: str
    body: str
    opening_hook: str           # ประโยคแรกที่ดึงดูด
    personalization_notes: str  # อธิบายว่า personalize ตรงไหน


@dataclass
class AgentOutput:
    """Standard output — ทุก agent ต้องใช้ format นี้"""
    success: bool
    data: dict = field(default_factory=dict)
    error: Optional[str] = None
    metadata: Optional[dict] = None
