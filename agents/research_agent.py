"""
Research Agent — Agent 2
Search for prospect company news/info and summarize business updates.

Implementation: Day 2
See Project Plan Section 2.2 (Agent 2)
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


# Output schema structure for the Research Agent
class CompanyResearchSchema(BaseModel):
    company: str = Field(description="Name of the company researched")
    recent_news: List[str] = Field(description="List of recent news highlights for the company, max 3 items")
    pain_points: List[str] = Field(description="List of business challenges or pain points faced by the company")
    talking_points: List[str] = Field(description="List of engaging conversation starters or talking points for the SDR")
    sources: List[str] = Field(description="List of news/information sources")


class ResearchAgentOutputSchema(BaseModel):
    research_results: List[CompanyResearchSchema] = Field(
        description="List of research results and analysis for all specified companies"
    )


# โหลด instruction prompt
PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "research_agent_prompt.txt"
with open(PROMPT_PATH, "r", encoding="utf-8") as f:
    RESEARCH_AGENT_INSTRUCTION = f.read()


# โหลด ADK model จาก env หรือ default
ADK_MODEL = os.getenv("ADK_MODEL", "gemini-2.5-flash")


# Define tools for the Agent
def search_news_tool(company: str) -> List[str]:
    """
    Search for the latest business news of the specified company.
    
    Args:
        company: The name of the company to search news for.
        
    Returns:
        List of recent news titles.
    """
    return search_company_news(company)


def extract_pain_points_tool(news: List[str]) -> List[str]:
    """
    Analyze recent news to extract business challenges or pain points of the company.
    
    Args:
        news: List of recent company news articles.
        
    Returns:
        List of extracted pain points.
    """
    return extract_pain_points(news)


def generate_talking_points_tool(
    company: str, news: List[str], pain_points: List[str], sources: List[str]
) -> List[str]:
    """
    Generate starting hooks/talking points aligned with company news and pain points.
    
    Args:
        company: The company name.
        news: List of news items.
        pain_points: List of pain points.
        sources: List of sources.
        
    Returns:
        List of talking points for the SDR to use in outreach.
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
    Analyze and research a company in a single step (fetches news, pain points, and generates talking points).
    
    Args:
        company: The name of the company to research.
        
    Returns:
        CompanyResearch object containing complete business intelligence data.
    """
    news = search_company_news(company)
    pain = extract_pain_points(news)
    
    # Try to locate matching mock source if present
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


# Instantiate Research Agent
research_agent = Agent(
    name="research_agent",
    description="Agent for searching news and analyzing business pain points of prospect companies (Company Research Agent)",
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
