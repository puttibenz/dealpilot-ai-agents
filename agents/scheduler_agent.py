"""
Scheduler Agent — Agent 4
วาง follow-up calendar และส่ง briefing email
Implementation: วันที่ 4
"""

import os
from pathlib import Path
from typing import List, Optional
from google.adk.agents import Agent
from pydantic import BaseModel, Field

from tools.calendar_tools import create_followup_schedule
from tools.email_tools import send_briefing_email


class CalendarEventSchema(BaseModel):
    event_id: str = Field(description="ไอดีนัดหมายปฏิทินที่สร้างขึ้น")
    link: str = Field(description="ลิงก์สำหรับเข้าดูนัดหมาย Google Calendar")
    title: str = Field(description="ชื่อหัวข้อนัดหมาย")
    date: str = Field(description="วันที่นัดหมาย (YYYY-MM-DD)")
    mode: str = Field(description="โหมดการทำงาน: real หรือ mock")


class SchedulerAgentOutputSchema(BaseModel):
    scheduled_events: List[CalendarEventSchema] = Field(description="รายการนัดหมายทั้งหมดที่สร้างขึ้นบนปฏิทิน")
    briefing_sent: bool = Field(description="สถานะการส่งอีเมลรายงาน Daily Briefing สำเร็จหรือไม่")
    briefing_recipient: str = Field(description="อีเมลปลายทางของผู้รับรายงานสรุป")
    briefing_html_path: str = Field(description="พาธของไฟล์ HTML สรุปผลประจำวันบนโลคัลดิสก์")


# โหลด instruction prompt
PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "scheduler_agent_prompt.txt"
with open(PROMPT_PATH, "r", encoding="utf-8") as f:
    SCHEDULER_AGENT_INSTRUCTION = f.read()


# โหลด ADK model จาก env หรือ default
ADK_MODEL = os.getenv("ADK_MODEL", "gemini-3.1-flash-lite")


# กำหนด tools สำหรับ Agent
def scheduler_create_schedule_tool(lead_name: str, email_subject: str, deal_value: float) -> List[dict]:
    """
    สร้างนัดหมายติดตามผล 4 ช่วงเวลา (Day 0, Day 3, Day 7, Day 14) ใน Google Calendar สำหรับ Lead คนนี้
    
    Args:
        lead_name: ชื่อติดต่อของ Lead
        email_subject: หัวข้อจดหมายเสนอขายแรก
        deal_value: มูลค่าของดีลเสนอขาย
        
    Returns:
        รายการนัดหมาย 4 ช่วงเวลาที่บันทึกสำเร็จ
    """
    return create_followup_schedule(lead_name, email_subject, deal_value)


def scheduler_send_briefing_tool(html_content: str, recipient_email: str) -> bool:
    """
    ส่ง Daily Briefing รายงานสรุปรูปแบบ HTML เข้าอีเมลผู้ใช้ (SDR) และบันทึกลงใน data/briefing.html
    
    Args:
        html_content: เนื้อหา HTML สรุปฉบับเต็มของวันนี้
        recipient_email: อีเมลของ SDR ผู้รับรายงานสรุป
        
    Returns:
        True หากจำลองหรือส่งออกสำเร็จ
    """
    try:
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        briefing_file = data_dir / "briefing.html"
        with open(briefing_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"   💾 Saved local briefing copy to: {briefing_file.absolute()}")
    except Exception as e:
        print(f"   ⚠️ Failed to save local briefing HTML: {str(e)}")

    return send_briefing_email(html_content, recipient_email)


def scheduler_generate_html_briefing_tool(leads_data_json: str, sdr_name: str, style_description: str) -> str:
    """
    สร้างรายงาน Daily Briefing HTML รูปแบบพรีเมียม สวยงาม จากข้อมูลดราฟต์และตารางนัดหมายปฏิทิน
    
    Args:
        leads_data_json: ข้อมูล JSON string ของ Leads ทั้งหมดที่รวมรายละเอียดของ Lead, ข้อมูลการค้นคว้า (research), ร่างอีเมล (email_draft), และตารางนัดหมายปฏิทิน (calendar_schedule) เข้าด้วยกันแล้ว
        sdr_name: ชื่อของ SDR
        style_description: คำอธิบายสไตล์ของ SDR
        
    Returns:
        เนื้อหา HTML ที่จัดรูปแบบสวยงามเรียบร้อยแล้ว
    """
    import json
    from tools.email_tools import generate_html_briefing
    try:
        drafts = json.loads(leads_data_json)
        return generate_html_briefing(drafts, sdr_name, style_description)
    except Exception as e:
        return f"Error generating HTML briefing: {str(e)}"


# สร้าง Scheduler Agent
scheduler_agent = Agent(
    name="scheduler_agent",
    description="Agent สำหรับการจัดตารางติดตามงานปฏิทินและจัดส่ง Daily Briefing HTML (Calendar Follow-up & Briefing Agent)",
    model=ADK_MODEL,
    instruction=SCHEDULER_AGENT_INSTRUCTION,
    tools=[scheduler_create_schedule_tool, scheduler_send_briefing_tool, scheduler_generate_html_briefing_tool],
    output_schema=SchedulerAgentOutputSchema
)
