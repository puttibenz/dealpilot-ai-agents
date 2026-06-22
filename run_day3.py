"""
DealPilot — Day 3 Pipeline Runner Script
Run integrated Multi-Agent system (CRM Agent -> Research Agent -> Writer Agent).
"""

import argparse
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Force output stream encoding to utf-8 for consistency
sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables
load_dotenv()

from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types

from agents.crm_agent import crm_agent
from agents.research_agent import research_agent
from agents.writer_agent import writer_agent, load_sdr_style


def main():
    # 1. Parse CLI arguments
    parser = argparse.ArgumentParser(description="DealPilot Day 3 Pipeline Demo")
    parser.add_argument(
        "--sdr-id",
        type=str,
        default="sdr_001",
        help="SDR ID to simulate writing style (sdr_001 = Somchai, sdr_002 = Kevin)"
    )
    args = parser.parse_args()

    print("🚀 DealPilot 3-Agent Pipeline — Starting Day 3 Demo...")
    
    # 2. ตรวจสอบ API Key
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ ERROR: GOOGLE_API_KEY not found in environment or .env file.")
        sys.exit(1)
        
    csv_path = os.getenv("CRM_CSV_PATH", "data/mock_crm.csv")
    absolute_csv_path = Path(csv_path).resolve()
    
    if not absolute_csv_path.exists():
        print(f"❌ ERROR: CRM file not found at {absolute_csv_path}")
        sys.exit(1)

    # Load SDR profile
    sdr_profile = load_sdr_style(args.sdr_id)
    print(f"📂 CRM Data File: {absolute_csv_path}")
    print(f"👤 SDR Persona: {sdr_profile.get('sdr_name')} (ID: {args.sdr_id})")
    print(f"📝 Style Description: {sdr_profile.get('style_description')}")
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
        for event in crm_runner.run(user_id="sdr_001", session_id="session_crm_d3", new_message=crm_message):
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
    except json.JSONDecodeError as e:
        print("❌ ERROR: Could not parse CRM Agent output as JSON")
        print(f"ERROR DETAILS: {str(e)}")
        print(f"RAW OUTPUT:\n{crm_text}")
        sys.exit(1)

    if not ranked_leads:
        print("⚠️ No Ranked Leads found")
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
        for event in research_runner.run(user_id="sdr_001", session_id="session_research_d3", new_message=research_message):
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
        sys.exit(1)

    research_by_company = {item.get("company", "").lower().strip(): item for item in research_results}
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # STEP 3: Run Writer Agent (Draft personalized emails)
    # --------------------------------------------------------------------------
    print(f"\n[Step 3] [Running] Invoking Writer Agent to draft emails in the style of {sdr_profile.get('sdr_name')}...")
    
    # Retrieve past emails (Few-shot examples)
    past_emails_formatted = ""
    for idx, sample in enumerate(sdr_profile.get("past_emails", [])):
        past_emails_formatted += f"\nExample #{idx+1}:\nSubject: {sample.get('subject')}\nBody:\n{sample.get('body')}\n"

    sdr_context_info = (
        f"SDR Name: {sdr_profile.get('sdr_name')}\n"
        f"Writing Style Description: {sdr_profile.get('style_description')}\n"
        f"--- Past Emails (Few-shot Examples) ---{past_emails_formatted}"
    )

    draft_emails = {}
    for idx, item in enumerate(ranked_leads):
        lead = item.get("lead", {})
        company = lead.get("company", "")
        name = lead.get("name", "")
        email = lead.get("email", "")
        value = lead.get("deal_value", 0.0)
        stage = lead.get("deal_stage", "")
        
        # Fetch company research info
        research_info = research_by_company.get(company.lower().strip(), {})
        news = research_info.get("recent_news", [])
        pain_points = research_info.get("pain_points", [])
        talking_points = research_info.get("talking_points", [])
        sources = research_info.get("sources", [])
        
        # Compile information for email generation
        writer_input_text = (
            f"--- Target Lead Info ---\n"
            f"Contact Name: {name}\n"
            f"Email: {email}\n"
            f"Company: {company}\n"
            f"Expected Deal Value: ${value:,.2f}\n"
            f"Deal Stage: {stage}\n\n"
            f"--- Company Research Info ---\n"
            f"Recent News: {', '.join(news)}\n"
            f"Challenges (Pain points): {', '.join(pain_points)}\n"
            f"Suggested Talking points: {', '.join(talking_points)}\n"
            f"Sources: {', '.join(sources)}\n\n"
            f"--- SDR Profile Info ---\n"
            f"{sdr_context_info}\n\n"
            f"Please draft the sales email in English in the style of this SDR by utilizing the highlights of the research."
        )
        
        print(f" [Writer] Drafting email for Lead #{idx+1}: {name} ({company})...")
        
        writer_message = types.Content(
            role="user",
            parts=[types.Part(text=writer_input_text)]
        )
        
        writer_runner = Runner(
            agent=writer_agent,
            session_service=InMemorySessionService(),
            app_name=f"dealpilot_writer_app_{idx}",
            auto_create_session=True
        )
        
        writer_text = ""
        try:
            for event in writer_runner.run(user_id="sdr_001", session_id=f"session_writer_d3_{idx}", new_message=writer_message):
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            writer_text += part.text
            
            draft_emails[company.lower().strip()] = json.loads(writer_text)
            
        except Exception as e:
            print(f"  [Warning] Email draft failed for {company}: {str(e)}")
            draft_emails[company.lower().strip()] = {
                "subject": "Request for Information",
                "body": "Email draft failed due to system error.",
                "opening_hook": "None",
                "personalization_notes": "System Error"
            }

    # --------------------------------------------------------------------------
    # DISPLAY: Print integrated dashboard
    # --------------------------------------------------------------------------
    print("\n================================================================================")
    print("📧 DEALPILOT DAILY BRIEFING DASHBOARD — CRM, RESEARCH & PERSONALIZED EMAILS")
    print("================================================================================")
    
    for item in ranked_leads:
        priority = item.get("priority")
        score = item.get("score")
        lead = item.get("lead", {})
        
        name = lead.get("name")
        company = lead.get("company")
        value = lead.get("deal_value", 0.0)
        stage = lead.get("deal_stage")
        
        # Get draft email details
        email_draft = draft_emails.get(company.lower().strip(), {})
        subject = email_draft.get("subject", "Email subject not found")
        body = email_draft.get("body", "Email body not found")
        hook = email_draft.get("opening_hook", "Opening hook not found")
        notes = email_draft.get("personalization_notes", "Not specified")
        
        print(f"🏆 Rank #{priority} | {name} @ {company} | Score: {score} | Deal: ${value:,.2f} ({stage})")
        print(f"📝 Personalization Notes:\n  » {notes}")
        print(f"📬 Email Draft (SDR Persona: {sdr_profile.get('sdr_name')}):")
        print(f"  [Subject]: {subject}")
        print("  " + "-" * 76)
        # Format body block indentation
        formatted_body = "  " + body.replace("\n", "\n  ")
        print(formatted_body)
        print("=" * 80)
        
    print("\n🎉 Integrated Pipeline (CRM + Research + Writer) finished successfully!")


if __name__ == "__main__":
    main()
