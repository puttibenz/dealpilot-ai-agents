"""
Research Agent — Agent 2
ค้นหาข้อมูลบริษัทลูกค้าที่เป็น top leads ผ่านเครื่องมือค้นหา และสรุปข้อมูลธุรกิจ

Implementation: วันที่ 2
ดู Project Plan Section 2.2 (Agent 2)
"""

import os
from pathlib import Path
from typing import List
from google.adk.agents import Agent
from google.adk.tools import google_search
from pydantic import BaseModel, Field

from models.data_models import CompanyResearch
from tools.search_tools import (
    search_company_news,
    extract_pain_points,
    generate_talking_points,
)


# โครงสร้างสำหรับ output ของ Research Agent
class CompanyResearchSchema(BaseModel):
    company: str = Field(description="ชื่อบริษัทที่ทำการค้นหาข้อมูล")
    recent_news: List[str] = Field(description="รายการข่าวสารล่าสุดของบริษัท สูงสุด 3 รายการ")
    pain_points: List[str] = Field(description="รายการปัญหาหรือจุดท้าทายทางธุรกิจของบริษัท")
    talking_points: List[str] = Field(description="รายการประเด็นเปิดใจ/ประโยคเปิดการขายสำหรับ SDR")
    sources: List[str] = Field(description="แหล่งที่มาของข้อมูลข่าวสาร")


class ResearchAgentOutputSchema(BaseModel):
    research_results: List[CompanyResearchSchema] = Field(
        description="รายการผลการค้นหาและวิเคราะห์ข้อมูลบริษัทสำหรับทุกบริษัทที่กำหนด"
    )


# โหลด instruction prompt
PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "research_agent_prompt.txt"
with open(PROMPT_PATH, "r", encoding="utf-8") as f:
    RESEARCH_AGENT_INSTRUCTION = f.read()


# โหลด ADK model จาก env หรือ default
ADK_MODEL = os.getenv("ADK_MODEL", "gemini-2.5-flash")


# กำหนด tools สำหรับ Agent
def search_news_tool(company: str) -> List[str]:
    """
    ค้นหาข่าวสารทางธุรกิจล่าสุดของบริษัทที่ระบุ
    
    Args:
        company: ชื่อบริษัทที่ต้องการค้นข่าว
        
    Returns:
        รายการหัวข้อข่าวสารล่าสุด
    """
    return search_company_news(company)


def extract_pain_points_tool(news: List[str]) -> List[str]:
    """
    วิเคราะห์ข่าวสารล่าสุดเพื่อสกัดหาความท้าทายหรือปัญหาทางธุรกิจ (Pain Points) ของบริษัท
    
    Args:
        news: รายการข่าวสารของบริษัท
        
    Returns:
        รายการปัญหาที่สกัดได้
    """
    return extract_pain_points(news)


def generate_talking_points_tool(
    company: str, news: List[str], pain_points: List[str], sources: List[str]
) -> List[str]:
    """
    สร้างจุดเสนอเปิดการขาย (Talking Points) ที่สอดคล้องกับข่าวสารและปัญหาของบริษัท
    
    Args:
        company: ชื่อบริษัท
        news: รายการข่าวสาร
        pain_points: รายการปัญหา
        sources: แหล่งที่มาของข่าว
        
    Returns:
        รายการประโยคสำหรับ SDR นำไปใช้ในอีเมล
    """
    research_obj = CompanyResearch(
        company=company,
        recent_news=news,
        pain_points=pain_points,
        talking_points=[],
        sources=sources
    )
    return generate_talking_points(research_obj)


def research_company_tool(company: str) -> CompanyResearch:
    """
    ทำวิจัยวิเคราะห์บริษัทในเครื่องมือเดียว (ดึงข่าว ข้อมูลทุน ปัญหา และสร้าง Talking Points)
    
    Args:
        company: ชื่อบริษัทที่ต้องการวิจัยข้อมูล
        
    Returns:
        วัตถุข้อมูล CompanyResearch ที่มีข้อมูลทางธุรกิจครบถ้วน
    """
    news = search_company_news(company)
    pain = extract_pain_points(news)
    
    # พยายามหาแหล่งข่าวจำลองที่สอดคล้อง
    from tools.search_tools import MOCK_COMPANY_DATABASE
    sources = ["Google Search Fallback"]
    company_lower = company.lower().strip()
    for name, data in MOCK_COMPANY_DATABASE.items():
        if name in company_lower or company_lower in name:
            sources = data["sources"]
            break
            
    research_obj = CompanyResearch(
        company=company,
        recent_news=news,
        pain_points=pain,
        talking_points=[],
        sources=sources
    )
    talking_points = generate_talking_points(research_obj)
    research_obj.talking_points = talking_points
    return research_obj


# สร้าง Research Agent
research_agent = Agent(
    name="research_agent",
    description="Agent สำหรับการสืบค้นข่าวสารและวิเคราะห์จุดเจ็บปวดทางธุรกิจของบริษัทลูกค้าเป้าหมาย (Company Research Agent)",
    model=ADK_MODEL,
    instruction=RESEARCH_AGENT_INSTRUCTION,
    tools=[
        search_news_tool,
        extract_pain_points_tool,
        generate_talking_points_tool,
        research_company_tool
    ],
    output_schema=ResearchAgentOutputSchema
)
