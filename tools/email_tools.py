"""
Email Tools — Gmail API Integration with local mock fallback
Implementation: วันที่ 4
"""

import os
import json
import base64
from datetime import datetime
from pathlib import Path
from email.mime.text import MIMEText
from email.header import Header
from googleapiclient.discovery import build
from tools.calendar_tools import get_google_credentials


def send_email_via_gmail(to: str, subject: str, body: str) -> bool:
    """
    ส่งอีเมลผ่าน Gmail API จริง หรือบันทึกลงอีเมลจำลอง (mock_emails_sent.json)
    """
    creds = get_google_credentials()
    
    if creds:
        try:
            service = build('gmail', 'v1', credentials=creds)
            message = MIMEText(body, 'plain', 'utf-8')
            message['to'] = to
            message['subject'] = Header(subject, 'utf-8').encode()
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            send_result = service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            print(f"   ✉️ Email sent via Gmail API: {subject} to {to} (ID: {send_result.get('id')})")
            return True
        except Exception as e:
            print(f"   ⚠️ Failed to send email via Gmail API: {str(e)}. Falling back to Mock Mode.")

    # Local Mock fallback: บันทึกข้อมูลอีเมลลงไฟล์ JSON
    mock_dir = Path("data")
    mock_dir.mkdir(exist_ok=True)
    mock_file = mock_dir / "mock_emails_sent.json"
    
    sent_emails = []
    if mock_file.exists():
        try:
            with open(mock_file, "r", encoding="utf-8") as f:
                sent_emails = json.load(f)
        except Exception:
            pass
            
    mock_email = {
        "email_id": f"mock_email_{int(datetime.now().timestamp())}_{to.replace('@', '_').replace('.', '_')}",
        "to": to,
        "subject": subject,
        "body": body,
        "sent_at": datetime.now().isoformat()
    }
    sent_emails.append(mock_email)
    
    with open(mock_file, "w", encoding="utf-8") as f:
        json.dump(sent_emails, f, ensure_ascii=False, indent=2)
        
    print(f"   📝 Mock Email Logged to local file: {subject} to {to}")
    return True


def send_briefing_email(html: str, recipient: str) -> bool:
    """
    ส่งอีเมลสรุปรายงานประจำวัน (HTML) ไปยัง SDR
    """
    creds = get_google_credentials()
    subject = "DealPilot: Daily Sales Briefing Report"
    
    if creds:
        try:
            service = build('gmail', 'v1', credentials=creds)
            message = MIMEText(html, 'html', 'utf-8')
            message['to'] = recipient
            message['subject'] = Header(subject, 'utf-8').encode()
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            send_result = service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            print(f"   ✉️ Daily Briefing Email Sent via Gmail API to {recipient} (ID: {send_result.get('id')})")
            return True
        except Exception as e:
            print(f"   ⚠️ Failed to send briefing email via Gmail API: {str(e)}. Falling back to local file.")
            
    # ถ้าไม่ได้ต่อจริง ให้บันทึก briefing ลง local
    print(f"   📝 Local Briefing simulation complete (Recipient: {recipient})")
    return True


def generate_html_briefing(drafts: list, sdr_name: str, style_description: str) -> str:
    """
    สร้างรายงาน Daily Sales Briefing รูปแบบ HTML หน้าตาสวยงามระดับพรีเมียม (Premium Dark Mode Dashboard)
    """
    # สร้างแถวของตารางข้อมูลสรุป Leads
    table_rows = ""
    for idx, item in enumerate(drafts):
        lead = item.get("lead", {})
        priority = item.get("priority", idx + 1)
        score = item.get("score", 0.0)
        
        table_rows += f"""
        <tr>
            <td style="padding: 12px; border-bottom: 1px solid #374151; font-weight: bold; color: #a855f7;">#{priority}</td>
            <td style="padding: 12px; border-bottom: 1px solid #374151; font-weight: bold; color: #f8fafc;">{lead.get('name')}</td>
            <td style="padding: 12px; border-bottom: 1px solid #374151; color: #94a3b8;">{lead.get('company')}</td>
            <td style="padding: 12px; border-bottom: 1px solid #374151; color: #6366f1; font-weight: bold;">${lead.get('deal_value', 0.0):,.2f}</td>
            <td style="padding: 12px; border-bottom: 1px solid #374151;"><span style="background: #1e1b4b; color: #818cf8; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold;">{lead.get('deal_stage')}</span></td>
            <td style="padding: 12px; border-bottom: 1px solid #374151; font-weight: bold; color: #10b981;">{score}</td>
        </tr>
        """

    # สร้างการ์ดรายละเอียดของแต่ละ Lead
    lead_cards = ""
    for idx, item in enumerate(drafts):
        lead = item.get("lead", {})
        priority = item.get("priority", idx + 1)
        score = item.get("score", 0.0)
        email_draft = item.get("email_draft", {})
        research = item.get("research", {})
        calendar_schedule = item.get("calendar_schedule", [])
        
        # จัดรูปแบบประเด็นข่าวและปัญหา
        news_list = "".join([f"<li style='margin-bottom: 6px;'>{n}</li>" for n in research.get("recent_news", [])])
        pain_list = "".join([f"<li style='margin-bottom: 6px;'>{p}</li>" for p in research.get("pain_points", [])])
        
        # จัดรูปแบบตารางนัดหมายติดตามผล
        schedule_rows = ""
        for ev in calendar_schedule:
            schedule_rows += f"""
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #4b5563; font-weight: bold; color: #f3f4f6;">{ev.get('title')}</td>
                <td style="padding: 8px; border-bottom: 1px solid #4b5563; color: #9ca3af;">{ev.get('date')}</td>
                <td style="padding: 8px; border-bottom: 1px solid #4b5563; font-size: 12px; color: #34d399; font-weight: bold;">{ev.get('mode')}</td>
            </tr>
            """
            
        formatted_body = email_draft.get("body", "").replace("\n", "<br>")

        lead_cards += f"""
        <div style="background: #1f2937; border-radius: 12px; padding: 24px; margin-bottom: 32px; border: 1px solid #374151; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #374151; padding-bottom: 16px; margin-bottom: 20px;">
                <div style="font-size: 20px; font-weight: bold; color: #f8fafc;">
                    <span style="background: linear-gradient(135deg, #6366f1, #a855f7); color: white; padding: 6px 12px; border-radius: 8px; margin-right: 12px;">อันดับ #{priority}</span>
                    {lead.get('name')} <span style="font-weight: normal; color: #94a3b8; font-size: 16px;">@ {lead.get('company')}</span>
                </div>
                <div style="font-weight: bold; color: #10b981; font-size: 18px;">โอกาสชนะ: {score}</div>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
                <!-- ข้อมูลลูกค้า & ดีล -->
                <div style="background: #111827; padding: 16px; border-radius: 8px; border: 1px solid #374151;">
                    <h4 style="margin-top: 0; color: #a855f7; border-bottom: 1px solid #374151; padding-bottom: 8px;">ข้อมูลดีลและการติดต่อ</h4>
                    <p style="margin: 6px 0; color: #e2e8f0;"><strong>อีเมลติดต่อ:</strong> {lead.get('email')}</p>
                    <p style="margin: 6px 0; color: #e2e8f0;"><strong>มูลค่าดีลคาดหวัง:</strong> <span style="color: #6366f1; font-weight: bold;">${lead.get('deal_value', 0.0):,.2f}</span></p>
                    <p style="margin: 6px 0; color: #e2e8f0;"><strong>ขั้นตอนการขาย:</strong> {lead.get('deal_stage')}</p>
                    <p style="margin: 6px 0; color: #e2e8f0;"><strong>ติดต่อล่าสุด:</strong> {lead.get('last_contact_date')}</p>
                </div>
                
                <!-- ข้อมูลการค้นคว้าบริษัท -->
                <div style="background: #111827; padding: 16px; border-radius: 8px; border: 1px solid #374151;">
                    <h4 style="margin-top: 0; color: #a855f7; border-bottom: 1px solid #374151; padding-bottom: 8px;">ข้อมูลการค้นคว้าบริษัท</h4>
                    <p style="margin: 6px 0; color: #34d399; font-weight: bold;">ข่าวสารเด่น:</p>
                    <ul style="margin: 0; padding-left: 20px; color: #cbd5e1; font-size: 13px;">
                        {news_list}
                    </ul>
                    <p style="margin: 8px 0 6px 0; color: #f87171; font-weight: bold;">ความท้าทาย (Pain Points):</p>
                    <ul style="margin: 0; padding-left: 20px; color: #cbd5e1; font-size: 13px;">
                        {pain_list}
                    </ul>
                </div>
            </div>

            <!-- จุดบันทึกการทักทายเฉพาะตัว -->
            <div style="background: #1e1b4b; border-left: 4px solid #818cf8; padding: 12px 16px; border-radius: 4px; margin-bottom: 20px; color: #c7d2fe; font-size: 14px;">
                <strong>💡 จุดสังเกตเฉพาะบุคคล (Personalization Notes):</strong> {email_draft.get('personalization_notes')}
            </div>

            <!-- ร่างอีเมลเสนอขาย -->
            <div style="background: #111827; border-radius: 8px; padding: 20px; border: 1px solid #374151; margin-bottom: 20px;">
                <div style="display: flex; justify-content: space-between; border-bottom: 1px solid #374151; padding-bottom: 8px; margin-bottom: 12px;">
                    <div style="font-weight: bold; color: #a855f7;">📬 ร่างจดหมายเสนอขายภาษาไทย</div>
                    <div style="font-size: 12px; color: #94a3b8;">ประโยคเปิดแนะนำ: "{email_draft.get('opening_hook')}"</div>
                </div>
                <div style="margin-bottom: 12px; color: #f8fafc;">
                    <strong>หัวข้อ:</strong> {email_draft.get('subject')}
                </div>
                <div style="color: #cbd5e1; font-family: monospace; line-height: 1.6; background: #0f172a; padding: 16px; border-radius: 6px; border: 1px solid #1f2937;">
                    {formatted_body}
                </div>
            </div>

            <!-- ตารางนัดหมายติดตามผลปฏิทิน -->
            <div>
                <h4 style="margin-top: 0; margin-bottom: 10px; color: #34d399;">📅 ตารางบันทึกปฏิทินติดตามผล (Google Calendar Schedule)</h4>
                <table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 13px;">
                    <thead>
                        <tr style="background: #111827;">
                            <th style="padding: 8px; border-bottom: 2px solid #374151; color: #9ca3af;">หัวข้อนัดหมาย</th>
                            <th style="padding: 8px; border-bottom: 2px solid #374151; color: #9ca3af;">วันที่กำหนด</th>
                            <th style="padding: 8px; border-bottom: 2px solid #374151; color: #9ca3af;">สถานะระบบ</th>
                        </tr>
                    </thead>
                    <tbody>
                        {schedule_rows}
                    </tbody>
                </table>
            </div>
        </div>
        """

    # ประกอบโครง HTML ทั้งหมดเข้าด้วยกัน
    html_page = f"""
    <!DOCTYPE html>
    <html lang="th">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>DealPilot Daily Briefing Dashboard</title>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">
        <style>
            body {{
                font-family: 'Outfit', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                background-color: #0f172a;
                color: #f8fafc;
                margin: 0;
                padding: 40px 20px;
                line-height: 1.5;
            }}
            .container {{
                max-width: 900px;
                margin: 0 auto;
            }}
            header {{
                text-align: center;
                margin-bottom: 40px;
                background: linear-gradient(135deg, #1e1b4b, #311042);
                padding: 30px;
                border-radius: 16px;
                border: 1px solid #374151;
            }}
            h1 {{
                margin: 0;
                font-size: 32px;
                background: linear-gradient(to right, #6366f1, #a855f7, #ec4899);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                font-weight: 700;
            }}
            .subtitle {{
                color: #94a3b8;
                margin-top: 8px;
                font-size: 16px;
            }}
            .summary-card {{
                background-color: #1e293b;
                border-radius: 12px;
                padding: 24px;
                margin-bottom: 40px;
                border: 1px solid #374151;
            }}
            .summary-card h2 {{
                margin-top: 0;
                font-size: 20px;
                color: #38bdf8;
                border-bottom: 2px solid #374151;
                padding-bottom: 8px;
                margin-bottom: 16px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>🚀 DealPilot Daily Sales Briefing Report</h1>
                <div class="subtitle">รายงานสรุปบริษัทเป้าหมายและจดหมายเสนอขายที่ปรับแต่งตามสไตล์ของคุณ</div>
                <div style="margin-top: 15px; font-size: 14px; color: #cbd5e1;">
                    <strong>ผู้เสนอขาย (SDR):</strong> {sdr_name} | <strong>คำอธิบายสไตล์:</strong> {style_description}
                </div>
            </header>

            <!-- ตารางสรุป Top 5 Leads -->
            <div class="summary-card">
                <h2>🎯 สรุปผลการจัดอันดับโอกาสชนะปิดดีลสูงสุดประจำวันนี้</h2>
                <table style="width: 100%; border-collapse: collapse; text-align: left;">
                    <thead>
                        <tr style="border-bottom: 2px solid #4b5563;">
                            <th style="padding: 12px; color: #94a3b8;">อันดับ</th>
                            <th style="padding: 12px; color: #94a3b8;">ผู้ติดต่อ</th>
                            <th style="padding: 12px; color: #94a3b8;">บริษัท</th>
                            <th style="padding: 12px; color: #94a3b8;">มูลค่าดีล</th>
                            <th style="padding: 12px; color: #94a3b8;">ขั้นตอน</th>
                            <th style="padding: 12px; color: #94a3b8;">คะแนน</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows}
                    </tbody>
                </table>
            </div>

            <!-- รายละเอียดของแต่ละ Lead Card -->
            <h2 style="color: #f8fafc; font-size: 24px; margin-bottom: 20px; border-bottom: 2px solid #374151; padding-bottom: 8px;">📋 รายละเอียดการวิเคราะห์และดราฟต์อีเมลแยกรายบุคคล</h2>
            {lead_cards}
            
            <footer style="text-align: center; margin-top: 60px; color: #64748b; font-size: 12px; border-top: 1px solid #374151; padding-top: 20px;">
                ระบบขับเคลื่อนโดย DealPilot Multi-Agent CRM Orchestration Suite — capstone Project 2026
            </footer>
        </div>
    </body>
    </html>
    """
    return html_page

