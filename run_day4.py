"""
DealPilot — Day 4 Pipeline Runner Script
รันระบบ Multi-Agent แบบสมบูรณ์ End-to-End:
CRM Agent -> Research Agent -> Writer Agent -> Scheduler Agent
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
from agents.scheduler_agent import scheduler_agent


def main():
    # 1. จัดการพารามิเตอร์ CLI
    parser = argparse.ArgumentParser(description="DealPilot Day 4 Sequential Pipeline")
    parser.add_argument(
        "--sdr-id",
        type=str,
        default="sdr_001",
        help="รหัส SDR ที่ต้องการจำลองสไตล์การเขียน (sdr_001 = สมชาย, sdr_002 = เเควิน)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/briefing.html",
        help="พาธไฟล์เอาต์พุต HTML สรุปผลประจำวันบนเครื่องโลคัล (ค่าดีฟอลต์คือ data/briefing.html)"
    )
    parser.add_argument(
        "--recipient-email",
        type=str,
        default="sales_rep@company.com",
        help="อีเมลปลายทางของ SDR สำหรับการรับ Daily Briefing (ค่าดีฟอลต์คือ sales_rep@company.com)"
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

    # โหลดโปรไฟล์ SDR
    sdr_profile = load_sdr_style(args.sdr_id)
    print(f"📂 CRM Data File: {absolute_csv_path}")
    print(f"👤 SDR Persona: {sdr_profile.get('sdr_name')} (ID: {args.sdr_id})")
    print(f"📝 Style Description: {sdr_profile.get('style_description')}")
    print(f"📧 SDR Target Briefing Email: {args.recipient_email}")
    print(f"📁 Output File Path: {Path(args.output).resolve()}")
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
        for event in crm_runner.run(user_id="sdr_001", session_id="session_crm_d4", new_message=crm_message):
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
        for event in research_runner.run(user_id="sdr_001", session_id="session_research_d4", new_message=research_message):
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
    
    # ดึงตัวอย่างอีเมลในอดีต (Few-shot)
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
            for event in writer_runner.run(user_id="sdr_001", session_id=f"session_writer_d4_{idx}", new_message=writer_message):
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
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # --------------------------------------------------------------------------
    # STEP 4: รัน Scheduler Agent (จัดนัดหมายปฏิทินและจัดส่งรายงานสรุป)
    # --------------------------------------------------------------------------
    print("\n[Step 4] ⏳ กำลังเรียกใช้ Scheduler Agent เพื่อจัดตารางกิจกรรมในปฏิทินและส่ง Daily Briefing...")
    
    # รวบรวมข้อมูลเพื่อจัดส่งในรูปแบบ JSON string
    scheduler_input_data = []
    for item in ranked_leads:
        company_key = item.get("lead", {}).get("company", "").lower().strip()
        lead = item.get("lead", {})
        research_info = research_by_company.get(company_key, {})
        email_draft = draft_emails.get(company_key, {})
        
        scheduler_input_data.append({
            "priority": item.get("priority"),
            "score": item.get("score"),
            "lead": lead,
            "research": research_info,
            "email_draft": email_draft
        })

    scheduler_input_json = json.dumps(scheduler_input_data, ensure_ascii=False, indent=2)
    
    scheduler_input_text = (
        f"ข้อมูลผู้เสนอขาย (SDR):\n"
        f"- ชื่อ SDR: {sdr_profile.get('sdr_name')}\n"
        f"- รายละเอียดสไตล์: {sdr_profile.get('style_description')}\n"
        f"- อีเมลผู้รับรายงาน: {args.recipient_email}\n\n"
        f"--- ข้อมูลลูกค้าวิจัย และร่างอีเมลเสนอขาย (JSON) ---\n"
        f"{scheduler_input_json}\n\n"
        f"กรุณาดำเนินการดังนี้:\n"
        f"1. เรียกใช้งานเครื่องมือ `scheduler_create_schedule_tool` สำหรับลูกค้าแต่ละรายเพื่อสร้างตารางปฏิทินติดตามผล โดยใช้ชื่อจริง ยอดดีล และหัวข้อร่างอีเมลเสนอขาย\n"
        f"2. รวมข้อมูลนัดหมายปฏิทินที่สร้างกลับเข้ามาใส่ในข้อมูลโครงสร้างลูกค้าของแต่ละรายในฟิลด์ 'calendar_schedule'\n"
        f"3. ส่งข้อมูล JSON ที่รวมปฏิทินแล้วไปยังเครื่องมือ `scheduler_generate_html_briefing_tool` ร่วมกับชื่อ SDR และสไตล์ของท่าน เพื่อแปลงเป็นหน้าบอร์ด HTML สุดหรู\n"
        f"4. นำผลลัพธ์ HTML ส่งไปยังอีเมลของท่าน ({args.recipient_email}) ด้วยเครื่องมือ `scheduler_send_briefing_tool`\n"
        f"5. ส่งคืน JSON สรุปตามโครงสร้าง `SchedulerAgentOutputSchema` (ระบุ briefing_html_path เป็น 'data/briefing.html')"
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
        print("✅ Scheduler Agent ทำงานเสร็จสมบูรณ์!")
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการรัน Scheduler Agent: {str(e)}")
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
        print("❌ ERROR: ไม่สามารถแปลงเอาต์พุตของ Scheduler Agent เป็น JSON ได้")
        print(f"RAW OUTPUT:\n{scheduler_text}")
        sys.exit(1)

    # คัดลอกไฟล์ HTML ไปยังพาธที่กำหนดใน --output
    dest_path = Path(args.output)
    src_path = Path("data/briefing.html")
    
    if src_path.exists():
        try:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            import shutil
            shutil.copy(src_path, dest_path)
            print(f"🎉 คัดลอกไฟล์รายงาน Daily Briefing สำเร็จ: {dest_path.absolute()}")
        except Exception as e:
            print(f"⚠️ ไม่สามารถคัดลอกไฟล์รายงานไปยัง {dest_path}: {str(e)}")
    else:
        print("⚠️ ไม่พบไฟล์ briefing.html ต้นทางในโฟลเดอร์ data/")


if __name__ == "__main__":
    main()
