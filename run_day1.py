"""
DealPilot — Day 1 Runner Script
รัน CRM Agent standalone และแสดงผลการจัดอันดับลูกค้าเป้าหมายใน terminal
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


def main():
    print("🚀 DealPilot CRM Agent — Starting Day 1 Demo...")
    
    # 1. ตรวจสอบ API Key
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ ERROR: GOOGLE_API_KEY not found in environment or .env file.")
        print("กรุณาสร้างไฟล์ .env และใส่ GOOGLE_API_KEY ของคุณก่อนรัน")
        sys.exit(1)
        
    csv_path = os.getenv("CRM_CSV_PATH", "data/mock_crm.csv")
    absolute_csv_path = Path(csv_path).resolve()
    
    if not absolute_csv_path.exists():
        print(f"❌ ERROR: CRM file not found at {absolute_csv_path}")
        sys.exit(1)
        
    print(f"📂 CRM Data File: {absolute_csv_path}")
    print(f"🤖 ADK Agent Name: {crm_agent.name}")
    print(f"🧠 LLM Model: {crm_agent.model}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

    # 2. เตรียมข้อความสั่งงาน (ส่งพาธไฟล์ CRM ไปให้ Agent ประมวลผล)
    new_message = types.Content(
        role="user",
        parts=[types.Part(text=f"กรุณาจัดอันดับ leads จากไฟล์ CSV นี้: {csv_path}")]
    )

    # 3. สร้าง Runner ของ ADK เพื่อควบคุมและจัดเก็บ Session
    runner = Runner(
        agent=crm_agent,
        session_service=InMemorySessionService(),
        app_name="dealpilot_crm_app",
        auto_create_session=True
    )

    print("⏳ กำลังเรียกใช้ CRM Agent เพื่อประมวลผลข้อมูลและคำนวณคะแนน...")
    
    final_text = ""
    try:
        # รัน Agent แบบ stream ดึงคำตอบออกแสดงผล
        for event in runner.run(user_id="sdr_001", session_id="session_day1", new_message=new_message):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        final_text += part.text
                        
        print("\n✅ การประมวลผลของ Agent เสร็จสิ้น!")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        # 4. แปลงคำตอบ JSON และแสดงผลในรูปแบบ Dashboard ที่สวยงาม
        try:
            output_data = json.loads(final_text)
            ranked_leads = output_data.get("ranked_leads", [])
            
            print(f"\n🎯 Top {len(ranked_leads)} Leads ที่มีโอกาสสูงสุดในการปิดดีลวันนี้:")
            print("=" * 80)
            
            for item in ranked_leads:
                priority = item.get("priority")
                score = item.get("score")
                reason = item.get("score_reason")
                lead = item.get("lead", {})
                
                name = lead.get("name")
                company = lead.get("company")
                email = lead.get("email")
                value = lead.get("deal_value", 0.0)
                stage = lead.get("deal_stage")
                last_contact = lead.get("last_contact_date")
                
                print(f"🏆 อันดับ #{priority} | คะแนน: {score} | ดีล: ${value:,.2f}")
                print(f"👤 ผู้ติดต่อ: {name} ({email}) | บริษัท: {company}")
                print(f"📈 ขั้นตอนดีล: {stage} | ติดต่อล่าสุด: {last_contact}")
                print(f"💡 เหตุผลการจัดอันดับ: {reason}")
                print("-" * 80)
                
        except json.JSONDecodeError:
            print("⚠️ ไม่สามารถแปลงคำตอบเป็น JSON ได้โดยตรง ผลลัพธ์ดิบ:")
            print(final_text)
            
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการรัน Agent: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
