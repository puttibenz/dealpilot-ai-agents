"""
Writer Agent — Agent 3
Draft email ที่ personalized ในสไตล์ของ SDR คนนั้น ด้วย few-shot learning

Implementation: วันที่ 3
ดู Project Plan Section 2.2 (Agent 3)
"""

import json
import os
from pathlib import Path
from typing import List, Optional
from google.adk.agents import Agent
from pydantic import BaseModel, Field


# โครงสร้างสำหรับ output ของ Writer Agent
class DraftEmailSchema(BaseModel):
    subject: str = Field(description="หัวข้ออีเมล (Subject Line) ที่สั้นกระชับ ดึงดูดความสนใจ ไม่เกิน 60 ตัวอักษร")
    body: str = Field(description="เนื้อหาอีเมล (Email Body) ภาษาไทย ความยาวไม่เกิน 150 คำ ท่อนทักทายและลงท้ายตามสไตล์ของ SDR")
    opening_hook: str = Field(description="ประโยคเปิดใจ (Opening Hook) ประโยคแรกของอีเมลที่เชื่อมกับข่าวสารหรือปัญหาบริษัทลูกค้า")
    personalization_notes: str = Field(description="คำอธิบายว่าเราดึงจุดเด่น/ข่าวสารหรือความชอบของลูกค้าข้อใดมาเขียนเชื่อมโยง")


# โหลด instruction prompt
PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "writer_agent_prompt.txt"
with open(PROMPT_PATH, "r", encoding="utf-8") as f:
    WRITER_AGENT_INSTRUCTION = f.read()


# โหลด ADK model จาก env หรือ default
ADK_MODEL = os.getenv("ADK_MODEL", "gemini-3.5-flash")


def load_sdr_style(sdr_id: str) -> dict:
    """
    โหลดประวัติสไตล์การเขียนและตัวอย่างอีเมลของ SDR จากไฟล์ JSON
    
    Args:
        sdr_id: รหัสของ SDR (เช่น sdr_001, sdr_002)
        
    Returns:
        ข้อมูลพจนานุกรมประวัติการเขียนและตัวอย่าง
    """
    sdr_dir = Path(__file__).parent.parent / "data" / "sdr_styles"
    file_path = sdr_dir / f"{sdr_id}.json"
    
    if not file_path.exists():
        # fallback ไปยัง sdr_001 (สมชาย) ในกรณีไม่พบไฟล์
        file_path = sdr_dir / "sdr_001.json"
        if not file_path.exists():
            return {
                "sdr_id": "default",
                "sdr_name": "ผู้ช่วยฝ่ายขายทั่วไป",
                "style_description": "สไตล์กลางๆ สุภาพ กระชับ",
                "past_emails": []
            }
            
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


# สร้าง Writer Agent
writer_agent = Agent(
    name="writer_agent",
    description="Agent สำหรับการร่างอีเมลเปิดการขายแบบเฉพาะเจาะจงบุคคลในสไตล์ของนักขายแต่ละคน (Personalized Email Writer Agent)",
    model=ADK_MODEL,
    instruction=WRITER_AGENT_INSTRUCTION,
    output_schema=DraftEmailSchema
)
