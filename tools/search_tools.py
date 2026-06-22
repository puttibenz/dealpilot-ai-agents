"""
Search Tools — MCP Web Search wrapper and mock company business database fallback.

Implementation: Day 2
See Project Plan Section 2.2 (Agent 2)
"""

import re
from typing import List
from models.data_models import CompanyResearch


# Mock news and research database for 20 companies in mock_crm.csv for fast and stable execution
MOCK_COMPANY_DATABASE = {
    "shield tech": {
        "news": [
            "Shield Tech announces new series C funding of $50M for AI defense systems",
            "Shield Tech secures contract with US government for secure network communications",
            "Security breach attempt repelled successfully by Shield Tech's advanced firewall systems"
        ],
        "pain_points": [
            "Security systems require constant audits due to government agency contracts.",
            "Scaling cloud infrastructure under strict security compliance is difficult.",
            "Need for secure, encrypted communication channels across all devices."
        ],
        "talking_points": [
            "Congrats on the Series C funding of $50M for AI defense systems!",
            "We understand your system needs to support high-security government communications.",
            "We offer a solution to help monitor and manage data access permissions in compliance with safety standards."
        ],
        "sources": ["TechCrunch", "Government Technology", "Defense News"]
    },
    "apex finance": {
        "news": [
            "Apex Finance reports 40% growth in digital asset management transactions",
            "Apex Finance to launch automated portfolio balancing tools next month",
            "Regulatory compliance changes force Apex Finance to upgrade reporting systems"
        ],
        "pain_points": [
            "Difficulty in updating reporting systems to comply with new financial regulations.",
            "Rapidly growing digital asset transaction volumes causing occasional system load spikes.",
            "Automated portfolio management still requires more precise calculation models."
        ],
        "talking_points": [
            "Congrats on the 40% growth in digital asset transactions!",
            "We can help ease the burden of updating your systems for the latest financial compliance regulations.",
            "Our AI Agents can seamlessly integrate with your automated portfolio balancing tools."
        ],
        "sources": ["Bloomberg", "FinTech Futures", "Wall Street Journal"]
    },
    "stark industries": {
        "news": [
            "Stark Industries reveals new arc-reactor data monitoring technology",
            "Tony Stark announces transition of software infrastructure to clean energy monitoring",
            "Stark Industries experiences increased demand for real-time sensor analytics in energy grids"
        ],
        "pain_points": [
            "Real-time sensor data collection in energy grids is too large for manual processing.",
            "Migrating legacy software infrastructure to the new clean energy monitoring system is complex.",
            "Requires a continuous 24/7 safety and operations monitoring system."
        ],
        "talking_points": [
            "Very impressed by the new arc-reactor data monitoring technology!",
            "We offer a real-time sensor analytics platform that aligns with your clean energy monitoring initiatives.",
            "Our AI Agent can help automate safety monitoring and risk analysis for energy grids 24/7."
        ],
        "sources": ["Stark Energy Portal", "Wired", "Scientific American"]
    },
    "tomb exploration ltd": {
        "news": [
            "Tomb Exploration Ltd expands operations to remote archaeological sites in South America",
            "Tomb Exploration Ltd partners with mapping agencies for offline GPS synchronization",
            "Connectivity issues plague Tomb Exploration's field research teams in remote jungle areas"
        ],
        "pain_points": [
            "Intermittent internet connectivity in remote areas prevents data synchronization back to HQ.",
            "Difficulty in synchronizing offline maps and GPS data.",
            "Field researchers spend too much time manually entering survey data."
        ],
        "talking_points": [
            "Congrats on expanding operations to South America!",
            "We have an offline-first sync solution that helps gather and queue data without internet access.",
            "Our AI can help digitize paper-based field survey records from photographs to save time."
        ],
        "sources": ["Archaeology Today", "National Geographic", "Global Mapping News"]
    },
    "techcorp inc": {
        "news": [
            "TechCorp Inc launches new enterprise software division for workflow automation",
            "TechCorp Inc experiences customer service backlog due to rapid user expansion",
            "Industry analysts praise TechCorp's new security features in the cloud"
        ],
        "pain_points": [
            "Large backlog of customer support tickets due to rapid user base expansion.",
            "Connecting the new workflow automation system with clients' legacy applications.",
            "Training support staff on the new cloud security standards."
        ],
        "talking_points": [
            "Congrats on the launch of your new workflow automation enterprise division!",
            "We can help manage your customer service backlog with AI customer support agents.",
            "We can simplify integrating your new automation workflows with clients' legacy databases."
        ],
        "sources": ["TechInAsia", "Enterprise Software Review", "SaaS Insider"]
    }
}


def search_company_news(company: str) -> List[str]:
    """
    Search for the latest company news within the past 30 days.
    
    Args:
        company: The name of the company to search news for.
        
    Returns:
        List of recent news stories (maximum 3).
    """
    company_lower = company.lower().strip()
    
    # Try direct target matching in the mock database first
    for name, data in MOCK_COMPANY_DATABASE.items():
        if name in company_lower or company_lower in name:
            return data["news"]
            
    # Fallback dynamic news generation if company is not in the Mock DB
    return [
        f"{company} announces major expansion of its digital services and cloud solutions division.",
        f"{company} focuses on automating manual workflows to increase operational efficiency in 2026.",
        f"{company} partners with technology leaders to enhance security and regulatory compliance."
    ]


def extract_pain_points(news: List[str]) -> List[str]:
    """
    Analyze news information and extract key challenges or pain points for the company.
    
    Args:
        news: List of recent news highlights.
        
    Returns:
        List of company challenges/pain points.
    """
    # Check for matching news in the mock database
    for data in MOCK_COMPANY_DATABASE.values():
        if any(n in data["news"] for n in news):
            return data["pain_points"]
            
    # Dynamic heuristic extraction for general news
    pain_points = []
    for item in news:
        item_lower = item.lower()
        if "expansion" in item_lower or "rapid" in item_lower:
            pain_points.append("Difficulty scaling operations to match rapid growth.")
        if "workflow" in item_lower or "manual" in item_lower:
            pain_points.append("Reliance on manual processes causing delays and human error.")
        if "security" in item_lower or "compliance" in item_lower or "regulation" in item_lower:
            pain_points.append("Pressure from audits and compliance with strict security regulations.")
            
    # Fallback if no keywords match
    if not pain_points:
        pain_points = [
            "Slow internal workflows lacking automation for data processing.",
            "Lack of real-time insights to support executive decision-making.",
            "Bottlenecks in customer service due to exponential user growth."
        ]
        
    return pain_points[:3]


def generate_talking_points(research: CompanyResearch) -> List[str]:
    """
    Generate starting hooks / talking points that SDRs can use in their emails.
    
    Args:
        research: CompanyResearch object containing news and pain points.
        
    Returns:
        List of concise and engaging talking points in English.
    """
    company_lower = research.company.lower().strip()
    
    # Try fetching from mock database directly if present
    for name, data in MOCK_COMPANY_DATABASE.items():
        if name in company_lower or company_lower in name:
            return data["talking_points"]
            
    # Heuristic generation
    talking_points = []
    talking_points.append(f"I saw the recent news about {research.company}'s cloud and digital expansion plans, which look very promising.")
    
    if research.pain_points:
        primary_pain = research.pain_points[0]
        talking_points.append(f"We know that companies facing challenges like '{primary_pain}' can directly benefit from our Multi-Agent system.")
        
        talking_points.append(f"Congrats on {research.company}'s latest tech partnership! We would love to collaborate on automated monitoring systems.")
    
    return talking_points[:3]
