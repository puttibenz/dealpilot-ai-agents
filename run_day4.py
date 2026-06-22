"""
DealPilot — Day 4 Pipeline Runner Script
Run the complete end-to-end Multi-Agent system:
CRM Agent -> Research Agent -> Writer Agent -> Scheduler Agent
"""

import argparse
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Force output stream encoding to utf-8 for consistency
sys.stdout.reconfigure(encoding='utf-8')

# โหลด env จากโปรเจกต์ root
load_dotenv()

from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types

from agents.crm_agent import crm_agent
from agents.research_agent import research_agent
from agents.writer_agent import writer_agent, load_sdr_style
from agents.scheduler_agent import scheduler_agent


def main():
    # 1. Parse CLI arguments
    parser = argparse.ArgumentParser(description="DealPilot Day 4 Sequential Pipeline")
    parser.add_argument(
        "--sdr-id",
        type=str,
        default="sdr_001",
        help="SDR ID to simulate writing style (sdr_001 = Somchai, sdr_002 = Kevin)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/briefing.html",
        help="Local output path for the daily briefing HTML report (default: data/briefing.html)"
    )
    parser.add_argument(
        "--recipient-email",
        type=str,
        default="sales_rep@company.com",
        help="Recipient email address for the Daily Briefing (default: sales_rep@company.com)"
    )
    args = parser.parse_args()

    print("🚀 DealPilot 4-Agent Pipeline — Starting Day 4 End-to-End Demo...")
    
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
    print(f"📧 SDR Target Briefing Email: {args.recipient_email}")
    print(f"📁 Output File Path: {Path(args.output).resolve()}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    # --------------------------------------------------------------------------
    # STEP 1: Run CRM Agent (Rank Leads)
    # --------------------------------------------------------------------------
    print("\n[Step 1] [Running] Calling CRM Agent to filter Top 5 Leads...")
    crm_message = types.Content(
        role="user",
        parts=[types.Part(text=f"Please fetch and rank the leads from this CSV file: {csv_path}")]
    )
    crm_runner = Runner(
        agent=crm_agent,
        session_service=InMemorySessionService(),
        app_name="dealpilot_crm_app",
        auto_create_session=True
    )
    
    crm_text = ""
    try:
        for event in crm_runner.run(user_id="sdr_001", session_id="session_crm_d4", new_message=crm_message):
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

    # --------------------------------------------------------------------------
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
        for event in research_runner.run(user_id="sdr_001", session_id="session_research_d4", new_message=research_message):
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

    # --------------------------------------------------------------------------
    # STEP 3: Run Writer Agent (Draft personalized emails)
    # --------------------------------------------------------------------------
    print(f"\n[Step 3] [Running] Invoking Writer Agent to draft emails in the style of {sdr_profile.get('sdr_name')}...")
    
    # ดึงตัวอย่างอีเมลในอดีต (Few-shot)
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
        
        # ค้นคว้าข้อมูลบริษัท
        research_info = research_by_company.get(company.lower().strip(), {})
        news = research_info.get("recent_news", [])
        pain_points = research_info.get("pain_points", [])
        talking_points = research_info.get("talking_points", [])
        sources = research_info.get("sources", [])
        
        # รวบรวมข้อมูลสำหรับสร้างเมล
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
        
        print(f" ✍️ Drafting email for Lead #{idx+1}: {name} ({company})...")
        
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
            for event in writer_runner.run(user_id="sdr_001", session_id=f"session_writer_d4_{idx}", new_message=writer_message):
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            writer_text += part.text
            
            draft_emails[company.lower().strip()] = json.loads(writer_text)
            
        except Exception as e:
            print(f"  ⚠️ Email draft failed for {company}: {str(e)}")
            draft_emails[company.lower().strip()] = {
                "subject": "Request for Information",
                "body": "Email draft failed due to system error.",
                "opening_hook": "None",
                "personalization_notes": "System Error"
            }
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # --------------------------------------------------------------------------
    # STEP 4: Run Scheduler Agent (Schedule calendar events and deliver briefing)
    # --------------------------------------------------------------------------
    print("\n[Step 4] [Running] Calculating dates and creating Google Calendar follow-up schedules...")
    
    # รวบรวมข้อมูลเพื่อจัดส่งในรูปแบบ JSON string
    scheduler_input_data = []
    from tools.calendar_tools import create_followup_schedule
    
    for item in ranked_leads:
        company_key = item.get("lead", {}).get("company", "").lower().strip()
        lead = item.get("lead", {})
        research_info = research_by_company.get(company_key, {})
        email_draft = draft_emails.get(company_key, {})
        
        print(f" 📅 Scheduling calendar events for: {lead.get('name')} ({lead.get('company')})...")
        calendar_schedule = create_followup_schedule(
            lead_name=lead.get("name"),
            email_subject=email_draft.get("subject", "Request for Information"),
            deal_value=lead.get("deal_value", 0.0)
        )
        
        scheduler_input_data.append({
            "priority": item.get("priority"),
            "score": item.get("score"),
            "lead": lead,
            "research": research_info,
            "email_draft": email_draft,
            "calendar_schedule": calendar_schedule
        })

    scheduler_input_json = json.dumps(scheduler_input_data, ensure_ascii=False, indent=2)
    
    scheduler_input_text = (
        f"SDR Representative Information:\n"
        f"- SDR Name: {sdr_profile.get('sdr_name')}\n"
        f"- Style Description: {sdr_profile.get('style_description')}\n"
        f"- Recipient Email: {args.recipient_email}\n\n"
        f"--- Company Research, Email Drafts, and Calendar Schedules (JSON) ---\n"
        f"{scheduler_input_json}\n\n"
        f"Please execute the following steps:\n"
        f"1. Calendar follow-up events in the 'calendar_schedule' field have already been pre-calculated and created. Do not invoke the calendar scheduling tool again.\n"
        f"2. You must pass this complete and unaltered JSON data to the `scheduler_generate_html_briefing_tool` along with the SDR name and style description to convert it into a dashboard HTML page.\n"
        f"3. Deliver the generated HTML content immediately to the recipient email ({args.recipient_email}) using the `scheduler_send_briefing_tool` tool.\n"
        f"4. Return the summary JSON conforming to `SchedulerAgentOutputSchema`, extracting all calendar schedule details from the input and listing them in 'scheduled_events', and specifying 'briefing_html_path' as 'data/briefing.html'."
    )

    scheduler_message = types.Content(
        role="user",
        parts=[types.Part(text=scheduler_input_text)]
    )
    
    scheduler_runner = Runner(
        agent=scheduler_agent,
        session_service=InMemorySessionService(),
        app_name="dealpilot_scheduler_app",
        auto_create_session=True
    )
    
    scheduler_text = ""
    try:
        for event in scheduler_runner.run(user_id="sdr_001", session_id="session_scheduler_d4", new_message=scheduler_message):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        scheduler_text += part.text
        print("✅ Scheduler Agent completed successfully!")
    except Exception as e:
        print(f"❌ Error occurred while running Scheduler Agent: {str(e)}")
        sys.exit(1)

    # Parse Scheduler Output
    try:
        scheduler_output = json.loads(scheduler_text)
        print("\n================================================================================")
        print("📊 SCHEDULER AGENT OUTPUT SUMMARY")
        print("================================================================================")
        print(json.dumps(scheduler_output, ensure_ascii=False, indent=2))
        print("================================================================================")
    except json.JSONDecodeError:
        print("❌ ERROR: Could not parse Scheduler Agent output as JSON")
        print(f"RAW OUTPUT:\n{scheduler_text}")
        sys.exit(1)

    # Copy HTML file to the path specified in --output
    dest_path = Path(args.output)
    src_path = Path("data/briefing.html")
    
    if src_path.exists():
        try:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            import shutil
            shutil.copy(src_path, dest_path)
            print(f"🎉 Copied Daily Briefing report file successfully: {dest_path.absolute()}")
        except Exception as e:
            print(f"⚠️ Could not copy report file to {dest_path}: {str(e)}")
    else:
        print("⚠️ Source briefing.html not found in data/ folder")


if __name__ == "__main__":
    main()
