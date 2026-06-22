"""
CRM Tools — Lead scoring and CRM data fetching

Implementation: Day 1
See Project Plan Section 2.2 (Agent 1) and Section 8.2 (Input Sanitization)
"""

import csv
import re
from datetime import datetime
from typing import List, Optional
from models.data_models import Lead, RankedLead


def sanitize_lead_input(text: str) -> str:
    """
    Prevent prompt injection from CRM data.
    Remove patterns that might be instruction injections.
    """
    if not text:
        return ""
    
    # Remove suspicious patterns
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
    Fetch leads from a CSV file.
    """
    leads = []
    with open(filepath, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            # Parse date
            try:
                last_contact_date = datetime.strptime(
                    row["last_contact_date"].strip(), "%Y-%m-%d"
                )
            except ValueError:
                # fallback
                last_contact_date = datetime.now()

            # Sanitize data for security
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
    Calculate Lead score according to the formula:
    score = (deal_value_normalized * 0.4) + (days_since_last_contact_inverse * 0.3) + (deal_stage_weight * 0.3)
    """
    if ref_date is None:
        ref_date = datetime.now()

    # 1. Normalization of deal_value (max $150,000 counts as 100 points)
    deal_value_normalized = min(lead.deal_value / 150000.0, 1.0) * 100.0

    # 2. Normalization of days_since_last_contact (more recent contact yields more points, deduct 3 points per day)
    # Convert both dates to timezone-naive to avoid TypeError
    lead_date = lead.last_contact_date.replace(tzinfo=None)
    reference = ref_date.replace(tzinfo=None)
    
    days_since_contact = (reference - lead_date).days
    days_since_contact = max(0, days_since_contact) # Prevent negative days for future data
    days_inverse_normalized = max(0.0, 100.0 - (days_since_contact * 3.0))

    # 3. Weight of deal_stage
    stage_weights = {
        "negotiation": 100.0,
        "proposal": 75.0,
        "qualified": 50.0,
        "prospecting": 25.0
    }
    stage_weight = stage_weights.get(lead.deal_stage.lower(), 0.0)

    # Calculate according to formula weights
    score = (deal_value_normalized * 0.4) + (days_inverse_normalized * 0.3) + (stage_weight * 0.3)
    return round(score, 2)


def rank_leads(leads: List[Lead], top_n: int = 5, ref_date: Optional[datetime] = None) -> List[RankedLead]:
    """
    Rank Leads by score and return the top_n leads.
    """
    if ref_date is None:
        ref_date = datetime.now()

    scored_leads = []
    for lead in leads:
        score = score_lead(lead, ref_date)
        
        # Calculate days since last contact
        lead_date = lead.last_contact_date.replace(tzinfo=None)
        reference = ref_date.replace(tzinfo=None)
        days = (reference - lead_date).days
        days = max(0, days)

        # Create English score reasoning parts
        reason_parts = []
        if lead.deal_value >= 100000:
            reason_parts.append(f"High deal value (${lead.deal_value:,.2f})")
        elif lead.deal_value >= 50000:
            reason_parts.append(f"Good deal value (${lead.deal_value:,.2f})")
        else:
            reason_parts.append(f"Entry-level deal value (${lead.deal_value:,.2f})")

        if lead.deal_stage == "negotiation":
            reason_parts.append("In final negotiation stage")
        elif lead.deal_stage == "proposal":
            reason_parts.append("In proposal stage")
        elif lead.deal_stage == "qualified":
            reason_parts.append("Qualified lead stage")
        else:
            reason_parts.append("In prospecting stage")

        if days <= 2:
            reason_parts.append("Contacted recently, high engagement momentum")
        elif days <= 7:
            reason_parts.append(f"Last contacted {days} days ago, active")
        else:
            reason_parts.append(f"No contact for {days} days, needs immediate follow-up")

        score_reason = " | ".join(reason_parts)

        scored_leads.append((lead, score, score_reason))

    # Sort from highest score to lowest
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
