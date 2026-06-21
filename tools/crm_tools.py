"""
CRM Tools — Lead scoring และ CRM data fetching

Implementation: วันที่ 1
ดู Project Plan Section 2.2 (Agent 1) และ Section 8.2 (Input Sanitization)
"""

import csv
import re
from datetime import datetime
from typing import List, Optional
from models.data_models import Lead, RankedLead


def sanitize_lead_input(text: str) -> str:
    """
    ป้องกัน prompt injection จาก CRM data
    ลบ patterns ที่อาจเป็น instruction injection
    """
    if not text:
        return ""
    
    # ลบ patterns ที่น่าสงสัย
    patterns = [
        r"ignore previous instructions",
        r"system prompt",
        r"<\|.*?\|>",  # special tokens
        r"\[INST\].*?\[/INST\]",  # instruction tags
    ]
    for pattern in patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)
    return text.strip()


def fetch_leads_from_csv(filepath: str) -> List[Lead]:
    """
    ดึงข้อมูล leads จาก CSV file
    """
    leads = []
    with open(filepath, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            # แปลงวันที่
            try:
                last_contact_date = datetime.strptime(
                    row["last_contact_date"].strip(), "%Y-%m-%d"
                )
            except ValueError:
                # fallback
                last_contact_date = datetime.now()

            # สุขาภิบาลข้อมูลเพื่อความปลอดภัย
            name = sanitize_lead_input(row["name"])
            company = sanitize_lead_input(row["company"])
            email = sanitize_lead_input(row["email"])
            notes = sanitize_lead_input(row.get("notes", ""))
            
            lead = Lead(
                id=row["id"].strip(),
                name=name,
                company=company,
                email=email,
                deal_value=float(row["deal_value"]),
                deal_stage=row["deal_stage"].strip().lower(),
                last_contact_date=last_contact_date,
                notes=notes if notes else None,
            )
            leads.append(lead)
    return leads


def score_lead(lead: Lead, ref_date: Optional[datetime] = None) -> float:
    """
    คำนวณคะแนนของ Lead ตามสูตร:
    score = (deal_value_normalized * 0.4) + (days_since_last_contact_inverse * 0.3) + (deal_stage_weight * 0.3)
    """
    if ref_date is None:
        ref_date = datetime.now()

    # 1. Normalization ของ deal_value (สูงสุด $150,000 คิดเป็น 100 คะแนน)
    deal_value_normalized = min(lead.deal_value / 150000.0, 1.0) * 100.0

    # 2. Normalization ของ days_since_last_contact (ยิ่งติดต่อล่าสุดยิ่งได้คะแนนเยอะ, หัก 3 คะแนนต่อวัน)
    # ทำการแปลงทั้งสองวันที่ให้เป็น timezone-naive เพื่อหลีกเลี่ยง TypeError
    lead_date = lead.last_contact_date.replace(tzinfo=None)
    reference = ref_date.replace(tzinfo=None)
    
    days_since_contact = (reference - lead_date).days
    days_since_contact = max(0, days_since_contact) # ป้องกันวันติดลบในกรณีข้อมูลอนาคต
    days_inverse_normalized = max(0.0, 100.0 - (days_since_contact * 3.0))

    # 3. น้ำหนักของ deal_stage
    stage_weights = {
        "negotiation": 100.0,
        "proposal": 75.0,
        "qualified": 50.0,
        "prospecting": 25.0
    }
    stage_weight = stage_weights.get(lead.deal_stage.lower(), 0.0)

    # คำนวณตามสูตรสัดส่วนน้ำหนัก
    score = (deal_value_normalized * 0.4) + (days_inverse_normalized * 0.3) + (stage_weight * 0.3)
    return round(score, 2)


def rank_leads(leads: List[Lead], top_n: int = 5, ref_date: Optional[datetime] = None) -> List[RankedLead]:
    """
    จัดอันดับ Leads ตามคะแนน และคืนค่ารายการ top_n อันดับแรก
    """
    if ref_date is None:
        ref_date = datetime.now()

    scored_leads = []
    for lead in leads:
        score = score_lead(lead, ref_date)
        
        # คำนวณวันที่ไม่ได้ติดต่อ
        lead_date = lead.last_contact_date.replace(tzinfo=None)
        reference = ref_date.replace(tzinfo=None)
        days = (reference - lead_date).days
        days = max(0, days)

        # สร้างคำอธิบายเหตุผลเป็นภาษาไทย
        reason_parts = []
        if lead.deal_value >= 100000:
            reason_parts.append(f"มูลค่าดีลสูงมาก (${lead.deal_value:,.2f})")
        elif lead.deal_value >= 50000:
            reason_parts.append(f"มูลค่าดีลดี (${lead.deal_value:,.2f})")
        else:
            reason_parts.append(f"มูลค่าดีลระดับเริ่มต้น (${lead.deal_value:,.2f})")

        if lead.deal_stage == "negotiation":
            reason_parts.append("อยู่ในขั้นตอนเจรจาสัญญาขั้นสุดท้าย (negotiation)")
        elif lead.deal_stage == "proposal":
            reason_parts.append("ส่งใบเสนอราคาแล้ว (proposal)")
        elif lead.deal_stage == "qualified":
            reason_parts.append("ผ่านการตรวจสอบคุณสมบัติ (qualified)")
        else:
            reason_parts.append("อยู่ระหว่างค้นหาความต้องการ (prospecting)")

        if days <= 2:
            reason_parts.append("เพิ่งติดต่อล่าสุด มีความตื่นตัวสูง")
        elif days <= 7:
            reason_parts.append(f"ติดต่อล่าสุด {days} วันก่อน อยู่ในเกณฑ์ดี")
        else:
            reason_parts.append(f"ไม่ได้ติดต่อมานาน {days} วัน ควรทวงถาม/ติดตามงาน")

        score_reason = " | ".join(reason_parts)

        scored_leads.append((lead, score, score_reason))

    # เรียงลำดับจากคะแนนสูงสุดลงมา
    scored_leads.sort(key=lambda x: x[1], reverse=True)

    ranked_leads = []
    for i, (lead, score, score_reason) in enumerate(scored_leads[:top_n]):
        ranked_leads.append(
            RankedLead(
                lead=lead,
                score=score,
                score_reason=score_reason,
                priority=i + 1
            )
        )
    return ranked_leads
