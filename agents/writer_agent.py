"""
Writer Agent — Agent 3
Draft personalized emails matching the SDR style using few-shot learning.

Implementation: Day 3
See Project Plan Section 2.2 (Agent 3)
"""

import json
import os
from pathlib import Path
from typing import List, Optional
from google.adk.agents import Agent
from pydantic import BaseModel, Field


# โครงสร้างสำหรับ output ของ Writer Agent
class DraftEmailSchema(BaseModel):
    subject: str = Field(description="Catchy and brief email subject line, max 60 characters")
    body: str = Field(description="Email body text, under 150 words, matching the style and persona of the SDR")
    opening_hook: str = Field(description="The opening hook sentence of the email connecting to company news or pain points")
    personalization_notes: str = Field(description="Explanatory notes on how the email was personalized for the prospect")


# โหลด instruction prompt
PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "writer_agent_prompt.txt"
with open(PROMPT_PATH, "r", encoding="utf-8") as f:
    WRITER_AGENT_INSTRUCTION = f.read()


# โหลด ADK model จาก env หรือ default
ADK_MODEL = os.getenv("ADK_MODEL", "gemini-3.5-flash")


def load_sdr_style(sdr_id: str) -> dict:
    """
    Load SDR writing style profile and sample emails from JSON file.
    
    Args:
        sdr_id: The ID of the SDR (e.g., sdr_001, sdr_002).
        
    Returns:
        Dictionary containing writing style profile and few-shot email templates.
    """
    sdr_dir = Path(__file__).parent.parent / "data" / "sdr_styles"
    file_path = sdr_dir / f"{sdr_id}.json"
    
    if not file_path.exists():
        # fallback ไปยัง sdr_001 (สมชาย) ในกรณีไม่พบไฟล์
        file_path = sdr_dir / "sdr_001.json"
        if not file_path.exists():
            return {
                "sdr_id": "default",
                "sdr_name": "General Sales Assistant",
                "style_description": "Standard, polite, and concise style",
                "past_emails": []
            }
            
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


# Instantiate Writer Agent
writer_agent = Agent(
    name="writer_agent",
    description="Agent for drafting personalized sales outreach emails matching specific SDR styles (Personalized Email Writer Agent)",
    model=ADK_MODEL,
    instruction=WRITER_AGENT_INSTRUCTION,
    output_schema=DraftEmailSchema
)
