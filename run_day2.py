"""
DealPilot — Day 2 Pipeline Runner Script
รัน CRM Agent และส่งต่อผลลัพธ์ไปให้ Research Agent ประมวลผลแบบ Sequential
"""

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
        for event in crm_runner.run(user_id="sdr_001", session_id="session_crm_d2", new_message=crm_message):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        crm_text += part.text
                        
        print("✅ CRM Agent วิเคราะห์สำเร็จ!")
        
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการรัน CRM Agent: {str(e)}")
        sys.exit(1)

    # Parse ผลลัพธ์จาก CRM
    try:
        crm_data = json.loads(crm_text)
        ranked_leads = crm_data.get("ranked_leads", [])
    except json.JSONDecodeError:
        print("❌ ERROR: ไม่สามารถแปลงเอาต์พุตของ CRM Agent เป็น JSON ได้")
        print(crm_text)
        sys.exit(1)

    if not ranked_leads:
        print("⚠️ ไม่พบข้อมูล Ranked Leads จาก CRM Agent")
        sys.exit(0)
        
    companies = [item.get("lead", {}).get("company") for item in ranked_leads if item.get("lead", {}).get("company")]
    print(f"🎯 ได้รับรายชื่อ {len(companies)} บริษัทเป้าหมาย: {', '.join(companies)}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # --------------------------------------------------------------------------
    # STEP 2: รัน Research Agent (สืบค้นและวิเคราะห์ข้อมูลบริษัท)
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
        for event in research_runner.run(user_id="sdr_001", session_id="session_research_d2", new_message=research_message):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        research_text += part.text
                        
        print("✅ Research Agent วิเคราะห์ข่าวสารสำเร็จ!")
        
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการรัน Research Agent: {str(e)}")
        sys.exit(1)

    # Parse ผลลัพธ์จาก Research
    try:
        research_data = json.loads(research_text)
        research_results = research_data.get("research_results", [])
    except json.JSONDecodeError:
        print("❌ ERROR: ไม่สามารถแปลงเอาต์พุตของ Research Agent เป็น JSON ได้")
        print(research_text)
        sys.exit(1)

    # สร้าง Dictionary ค้นหาผลวิจัยบริษัท
    research_by_company = {item.get("company", "").lower().strip(): item for item in research_results}

    # --------------------------------------------------------------------------
    # DISPLAY: แสดงบอร์ดแบบรวบรวมข้อมูล CRM + Research เข้าด้วยกัน
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
        
        # ค้นหาผลลัพธ์การสืบค้นข้อมูล
        research_info = research_by_company.get(company.lower().strip(), {})
        news = research_info.get("recent_news", ["ไม่พบข่าวสารล่าสุุด"])
        pain_points = research_info.get("pain_points", ["ไม่พบความท้าทายของบริษัท"])
        talking_points = research_info.get("talking_points", ["ไม่สามารถสร้างTalking points ได้"])
        sources = research_info.get("sources", ["ไม่ระบุแหล่งข่าว"])
        
        print(f"🏆 อันดับ #{priority} | {name} @ {company} | คะแนนโอกาสชนะ: {score} | มูลค่าดีล: ${value:,.2f} ({stage})")
        print(f"📰 ข่าวเด่นล่าสุด ({', '.join(sources)}):")
        for n in news[:2]:
            print(f"  • {n}")
        print("⚠️ จุดท้าทายของธุรกิจ (Pain Points):")
        for p in pain_points[:2]:
            print(f"  • {p}")
        print("💡 ประโยคเปิดใจเสนอขาย (Talking Points สำหรับ SDR):")
        for t in talking_points[:2]:
            print(f"  • {t}")
        print("-" * 80)
        
    print("\n🎉 สิ้นสุดรายงานการสืบค้น Pipeline CRM + Research เรียบร้อยแล้ว!")


if __name__ == "__main__":
    main()
