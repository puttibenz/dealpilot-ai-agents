"""
DealPilot — Day 2 Pipeline Runner Script
Run CRM Agent and pass results to Research Agent sequentially.
"""

import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Force output stream encoding to utf-8
sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables
load_dotenv()

from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types

from agents.crm_agent import crm_agent
from agents.research_agent import research_agent


def main():
    print("🚀 DealPilot Multi-Agent Pipeline — Starting Day 2 Demo...")
    
    # 1. ตรวจสอบ API Key
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ ERROR: GOOGLE_API_KEY not found in environment or .env file.")
        sys.exit(1)
        
    csv_path = os.getenv("CRM_CSV_PATH", "data/mock_crm.csv")
    absolute_csv_path = Path(csv_path).resolve()
    
    if not absolute_csv_path.exists():
        print(f"❌ ERROR: CRM file not found at {absolute_csv_path}")
        sys.exit(1)

    print(f"📂 CRM Data File: {absolute_csv_path}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    # STEP 1: Run CRM Agent (Rank Leads)
    # --------------------------------------------------------------------------
    print("\n[Step 1] [Running] Calling CRM Agent to filter Top 5 Leads...")
    
    crm_message = types.Content(
        role="user",
        parts=[types.Part(text=f"Please rank the leads from this CSV file: {csv_path}")]
    )
    
    crm_runner = Runner(
        agent=crm_agent,
        session_service=InMemorySessionService(),
        app_name="dealpilot_crm_app",
        auto_create_session=True
    )
    
    crm_text = ""
    try:
        for event in crm_runner.run(user_id="sdr_001", session_id="session_crm_d2", new_message=crm_message):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        crm_text += part.text
                        
        print("✅ CRM Agent analysis complete!")
        
    except Exception as e:
        print(f"❌ Error occurred while running CRM Agent: {str(e)}")
        sys.exit(1)

    # Parse CRM
    try:
        crm_data = json.loads(crm_text)
        ranked_leads = crm_data.get("ranked_leads", [])
    except json.JSONDecodeError:
        print("❌ ERROR: Could not parse CRM Agent output as JSON")
        print(crm_text)
        sys.exit(1)

    if not ranked_leads:
        print("⚠️ No Ranked Leads found from CRM Agent")
        sys.exit(0)
        
    companies = [item.get("lead", {}).get("company") for item in ranked_leads if item.get("lead", {}).get("company")]
    print(f"🎯 Received {len(companies)} target companies: {', '.join(companies)}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # STEP 2: Run Research Agent (Analyze news and pain points)
    # --------------------------------------------------------------------------
    print("\n[Step 2] [Running] Sending company names to Research Agent for analysis...")
    
    research_input_text = f"Please research and analyze news, pain points, and suggest talking points for these companies: {', '.join(companies)}"
    research_message = types.Content(
        role="user",
        parts=[types.Part(text=research_input_text)]
    )
    
    research_runner = Runner(
        agent=research_agent,
        session_service=InMemorySessionService(),
        app_name="dealpilot_research_app",
        auto_create_session=True
    )
    
    research_text = ""
    try:
        for event in research_runner.run(user_id="sdr_001", session_id="session_research_d2", new_message=research_message):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        research_text += part.text
                        
        print("✅ Research Agent analysis complete!")
        
    except Exception as e:
        print(f"❌ Error occurred while running Research Agent: {str(e)}")
        sys.exit(1)

    # Parse Research
    try:
        research_data = json.loads(research_text)
        research_results = research_data.get("research_results", [])
    except json.JSONDecodeError:
        print("❌ ERROR: Could not parse Research Agent output as JSON")
        print(research_text)
        sys.exit(1)

    # สร้าง Dictionary ค้นหาผลวิจัยบริษัท
    research_by_company = {item.get("company", "").lower().strip(): item for item in research_results}

    # --------------------------------------------------------------------------
    # DISPLAY: Print integrated dashboard (CRM + Research)
    # --------------------------------------------------------------------------
    print("\n================================================================================")
    print("📊 DEALPILOT INTEGRATED PIPELINE DASHBOARD — CRM & COMPANY RESEARCH RESULTS")
    print("================================================================================")
    
    for item in ranked_leads:
        priority = item.get("priority")
        score = item.get("score")
        lead = item.get("lead", {})
        
        name = lead.get("name")
        company = lead.get("company")
        value = lead.get("deal_value", 0.0)
        stage = lead.get("deal_stage")
        
        # Get research results
        research_info = research_by_company.get(company.lower().strip(), {})
        news = research_info.get("recent_news", ["No news found"])
        pain_points = research_info.get("pain_points", ["No company challenges found"])
        talking_points = research_info.get("talking_points", ["Could not generate talking points"])
        sources = research_info.get("sources", ["Not specified"])
        
        print(f"🏆 Rank #{priority} | {name} @ {company} | Score: {score} | Deal: ${value:,.2f} ({stage})")
        print(f"📰 Recent News Highlights ({', '.join(sources)}):")
        for n in news[:2]:
            print(f"  • {n}")
        print("⚠️ Business Challenges (Pain Points):")
        for p in pain_points[:2]:
            print(f"  • {p}")
        print("💡 Conversation Starters (Talking Points for SDR):")
        for t in talking_points[:2]:
            print(f"  • {t}")
        print("-" * 80)
        
    print("\n🎉 CRM + Research Pipeline execution completed!")


if __name__ == "__main__":
    main()
