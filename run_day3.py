"""
DealPilot — Day 3 Pipeline Runner Script
รันระบบ Multi-Agent (CRM Agent -> Research Agent -> Writer Agent) ร่วมกันแบบบูรณาการ
"""

import argparse
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# บังคับการแสดงผลภาษาไทยให้ถูกต้องบน Windows console
sys.stdout.reconfigure(encoding='utf-8')

# โหลด env จากโปรเจกต์ root
load_dotenv()

from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types

from agents.crm_agent import crm_agent
from agents.research_agent import research_agent
from agents.writer_agent import writer_agent, load_sdr_style


def main():
    # 1. จัดการพารามิเตอร์ CLI
    parser = argparse.ArgumentParser(description="DealPilot Day 3 Pipeline Demo")
    parser.add_argument(
        "--sdr-id",
        type=str,
        default="sdr_001",
        help="รหัส SDR ที่ต้องการจำลองสไตล์การเขียน (sdr_001 = สมชาย, sdr_002 = เควิน)"
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

    # โหลดโปรไฟล์ SDR
    sdr_profile = load_sdr_style(args.sdr_id)
    print(f"📂 CRM Data File: {absolute_csv_path}")
    print(f"👤 SDR Persona: {sdr_profile.get('sdr_name')} (ID: {args.sdr_id})")
    print(f"📝 Style Description: {sdr_profile.get('style_description')}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    # --------------------------------------------------------------------------
    # STEP 1: รัน CRM Agent (จัดอันดับ Leads)
    # --------------------------------------------------------------------------
    print("\n[Step 1] ⏳ กำลังเรียกใช้ CRM Agent เพื่อคัดกรอง Top 5 Leads...")
    crm_message = types.Content(
        role="user",
        parts=[types.Part(text=f"กรุณาจัดอันดับ leads จากไฟล์ CSV นี้: {csv_path}")]
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
        print("✅ CRM Agent วิเคราะห์สำเร็จ!")
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการรัน CRM Agent: {str(e)}")
        sys.exit(1)

    # Parse CRM
    try:
        crm_data = json.loads(crm_text)
        ranked_leads = crm_data.get("ranked_leads", [])
    except json.JSONDecodeError as e:
        print("❌ ERROR: ไม่สามารถแปลงเอาต์พุตของ CRM Agent เป็น JSON ได้")
        print(f"ERROR DETAILS: {str(e)}")
        print(f"RAW OUTPUT:\n{crm_text}")
        sys.exit(1)

    if not ranked_leads:
        print("⚠️ ไม่พบข้อมูล Ranked Leads")
        sys.exit(0)

    companies = [item.get("lead", {}).get("company") for item in ranked_leads if item.get("lead", {}).get("company")]
    print(f"🎯 ได้รับรายชื่อ {len(companies)} บริษัทเป้าหมาย: {', '.join(companies)}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # --------------------------------------------------------------------------
    # STEP 2: รัน Research Agent (วิเคราะห์ข่าวสารและปัญหา)
    # --------------------------------------------------------------------------
    print("\n[Step 2] ⏳ กำลังส่งรายชื่อบริษัทไปให้ Research Agent วิเคราะห์ข่าวสารและปัญหา...")
    research_input_text = f"กรุณาช่วยค้นหาข่าวสารวิเคราะห์และสกัดประเด็นเปิดการขายสำหรับบริษัทเหล่านี้: {', '.join(companies)}"
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
        print("✅ Research Agent วิเคราะห์ข่าวสารสำเร็จ!")
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการรัน Research Agent: {str(e)}")
        sys.exit(1)

    # Parse Research
    try:
        research_data = json.loads(research_text)
        research_results = research_data.get("research_results", [])
    except json.JSONDecodeError:
        print("❌ ERROR: ไม่สามารถแปลงเอาต์พุตของ Research Agent เป็น JSON ได้")
        sys.exit(1)

    research_by_company = {item.get("company", "").lower().strip(): item for item in research_results}
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # --------------------------------------------------------------------------
    # STEP 3: รัน Writer Agent (เขียนดราฟต์อีเมลรายบุคคล)
    # --------------------------------------------------------------------------
    print(f"\n[Step 3] ⏳ กำลังเรียกใช้ Writer Agent เพื่อร่างอีเมลในสไตล์ {sdr_profile.get('sdr_name')}...")
    
    # ดึงตัวอย่างอีเมลในอดีต (Few-shot) เพื่อนำมาจัดรูปแบบลงในข้อความพรอมต์
    past_emails_formatted = ""
    for idx, sample in enumerate(sdr_profile.get("past_emails", [])):
        past_emails_formatted += f"\nตัวอย่างที่ {idx+1}:\nหัวข้อ: {sample.get('subject')}\nเนื้อหา:\n{sample.get('body')}\n"

    sdr_context_info = (
        f"ชื่อ SDR: {sdr_profile.get('sdr_name')}\n"
        f"คำอธิบายสไตล์การเขียน: {sdr_profile.get('style_description')}\n"
        f"--- ตัวอย่างอีเมลในอดีต (Few-shot Examples) ---{past_emails_formatted}"
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
            f"--- ข้อมูลลูกค้าเป้าหมาย ---\n"
            f"ชื่อผู้ติดต่อ: {name}\n"
            f"อีเมล: {email}\n"
            f"บริษัท: {company}\n"
            f"มูลค่าดีล: ${value:,.2f}\n"
            f"ขั้นตอนดีล: {stage}\n\n"
            f"--- ข้อมูลวิจัยบริษัท ---\n"
            f"ข่าวเด่น: {', '.join(news)}\n"
            f"จุดท้าทาย (Pain points): {', '.join(pain_points)}\n"
            f"ประเด็นเปิดการขายแนะนำ (Talking points): {', '.join(talking_points)}\n"
            f"แหล่งอ้างอิง: {', '.join(sources)}\n\n"
            f"--- ข้อมูลโปรไฟล์ SDR ---\n"
            f"{sdr_context_info}\n\n"
            f"กรุณาร่างอีเมลเสนอขายภาษาไทยในสไตล์ของ SDR คนนี้โดยดึงจุดเด่นข้อมูลวิจัยมาใช้ประโยชน์"
        )
        
        print(f" ✍️ กำลังร่างอีเมลให้ Lead #{idx+1}: {name} ({company})...")
        
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
            print(f"  ⚠️ ร่างอีเมลล้มเหลวสำหรับ {company}: {str(e)}")
            draft_emails[company.lower().strip()] = {
                "subject": "สอบถามข้อมูลเพิ่มเติม",
                "body": "ร่างอีเมลล้มเหลวเนื่องจากข้อผิดพลาดในระบบ",
                "opening_hook": "ไม่มี",
                "personalization_notes": "ข้อผิดพลาดระบบ"
            }

    # --------------------------------------------------------------------------
    # DISPLAY: แสดงบอร์ดแบบบูรณาการ CRM + Research + Email Drafts
    # --------------------------------------------------------------------------
    print("\n================================================================================")
    print("📧 DEALPILOT DAILY BRIEFINIG DASHBOARD — CRM, RESEARCH & PERSONALIZED EMAILS")
    print("================================================================================")
    
    for item in ranked_leads:
        priority = item.get("priority")
        score = item.get("score")
        lead = item.get("lead", {})
        
        name = lead.get("name")
        company = lead.get("company")
        value = lead.get("deal_value", 0.0)
        stage = lead.get("deal_stage")
        
        # ดึงร่างอีเมล
        email_draft = draft_emails.get(company.lower().strip(), {})
        subject = email_draft.get("subject", "ไม่พบหัวข้ออีเมล")
        body = email_draft.get("body", "ไม่พบเนื้อหาอีเมล")
        hook = email_draft.get("opening_hook", "ไม่พบประโยคเปิด")
        notes = email_draft.get("personalization_notes", "ไม่ระบุ")
        
        print(f"🏆 อันดับ #{priority} | {name} @ {company} | คะแนนโอกาสชนะ: {score} | มูลค่าดีล: ${value:,.2f} ({stage})")
        print(f"📝 จุดบันทึกการทักทายเฉพาะตัว (Personalization Notes):\n  » {notes}")
        print(f"📬 ร่างอีเมล (สำนวนของ SDR: {sdr_profile.get('sdr_name')}):")
        print(f"  [หัวข้อ]: {subject}")
        print("  " + "-" * 76)
        # เติมย่อหน้าเพื่อให้ดูจัดวางสวยงามใน terminal
        formatted_body = "  " + body.replace("\n", "\n  ")
        print(formatted_body)
        print("=" * 80)
        
    print("\n🎉 สิ้นสุดรายงานการสร้างดราฟต์อีเมล Pipeline CRM + Research + Writer เรียบร้อยแล้ว!")


if __name__ == "__main__":
    main()
