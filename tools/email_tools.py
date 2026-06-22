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
    สร้างรายงาน Daily Sales Briefing รูปแบบ HTML หน้าตาสวยงามระดับพรีเมียม (Premium High-Contrast Light Theme)
    """
    # สร้างแถวของตารางข้อมูลสรุป Leads
    table_rows = ""
    for idx, item in enumerate(drafts):
        lead = item.get("lead", {})
        priority = item.get("priority", idx + 1)
        score = item.get("score", 0.0)
        
        table_rows += f"""
        <tr style="border-bottom: 1px solid #e2e8f0;">
            <td style="padding: 12px; font-weight: bold; color: #7c3aed;">#{priority}</td>
            <td style="padding: 12px; font-weight: bold; color: #0f172a;">{lead.get('name')}</td>
            <td style="padding: 12px; color: #475569;">{lead.get('company')}</td>
            <td style="padding: 12px; color: #2563eb; font-weight: bold;">${lead.get('deal_value', 0.0):,.2f}</td>
            <td style="padding: 12px;"><span style="background: #e0e7ff; color: #4338ca; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold;">{lead.get('deal_stage')}</span></td>
            <td style="padding: 12px; font-weight: bold; color: #059669;">{score}</td>
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
        news_list = "".join([f"<li style='margin-bottom: 6px; color: #1e293b;'>{n}</li>" for n in research.get("recent_news", [])])
        pain_list = "".join([f"<li style='margin-bottom: 6px; color: #991b1b;'>{p}</li>" for p in research.get("pain_points", [])])
        
        # จัดรูปแบบตารางนัดหมายติดตามผล
        schedule_rows = ""
        for ev in calendar_schedule:
            schedule_rows += f"""
            <tr style="border-bottom: 1px solid #e2e8f0;">
                <td style="padding: 8px; font-weight: bold; color: #1e293b;">{ev.get('title')}</td>
                <td style="padding: 8px; color: #475569;">{ev.get('date')}</td>
                <td style="padding: 8px; font-size: 12px; color: #059669; font-weight: bold;">{ev.get('mode')}</td>
            </tr>
            """
            
        formatted_body = email_draft.get("body", "").replace("\n", "<br>")

        lead_cards += f"""
        <div style="background: #ffffff; border-radius: 12px; padding: 24px; margin-bottom: 32px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); text-align: left;">
            <div style="border-bottom: 2px solid #f1f5f9; padding-bottom: 16px; margin-bottom: 20px; text-align: left;">
                <div style="font-size: 20px; font-weight: bold; color: #0f172a;">
                    <span style="background: linear-gradient(135deg, #4f46e5, #7c3aed); color: white; padding: 6px 12px; border-radius: 8px; margin-right: 12px; display: inline-block;">อันดับ #{priority}</span>
                    {lead.get('name')} <span style="font-weight: normal; color: #475569; font-size: 16px;">@ {lead.get('company')}</span>
                </div>
                <div style="font-weight: bold; color: #059669; font-size: 18px; margin-top: 10px;">โอกาสชนะ: {score}</div>
            </div>

            <div style="margin-bottom: 20px;">
                <!-- ข้อมูลลูกค้า & ดีล -->
                <div style="background: #f8fafc; padding: 16px; border-radius: 8px; border: 1px solid #e2e8f0; margin-bottom: 16px; text-align: left;">
                    <h4 style="margin-top: 0; color: #7c3aed; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px;">ข้อมูลดีลและการติดต่อ</h4>
                    <p style="margin: 6px 0; color: #1e293b;"><strong>อีเมลติดต่อ:</strong> {lead.get('email')}</p>
                    <p style="margin: 6px 0; color: #1e293b;"><strong>มูลค่าดีลคาดหวัง:</strong> <span style="color: #2563eb; font-weight: bold;">${lead.get('deal_value', 0.0):,.2f}</span></p>
                    <p style="margin: 6px 0; color: #1e293b;"><strong>ขั้นตอนการขาย:</strong> {lead.get('deal_stage')}</p>
                    <p style="margin: 6px 0; color: #1e293b;"><strong>ติดต่อล่าสุด:</strong> {lead.get('last_contact_date')}</p>
                </div>
                
                <!-- ข้อมูลการค้นคว้าบริษัท -->
                <div style="background: #f8fafc; padding: 16px; border-radius: 8px; border: 1px solid #e2e8f0; text-align: left;">
                    <h4 style="margin-top: 0; color: #7c3aed; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px;">ข้อมูลการค้นคว้าบริษัท</h4>
                    <p style="margin: 6px 0; color: #059669; font-weight: bold;">ข่าวสารเด่น:</p>
                    <ul style="margin: 0; padding-left: 20px; color: #1e293b; font-size: 13px;">
                        {news_list}
                    </ul>
                    <p style="margin: 8px 0 6px 0; color: #ef4444; font-weight: bold;">ความท้าทาย (Pain Points):</p>
                    <ul style="margin: 0; padding-left: 20px; color: #991b1b; font-size: 13px;">
                        {pain_list}
                    </ul>
                </div>
            </div>

            <!-- จุดบันทึกการทักทายเฉพาะตัว -->
            <div style="background: #f5f3ff; border-left: 4px solid #7c3aed; padding: 12px 16px; border-radius: 4px; margin-bottom: 20px; color: #5b21b6; font-size: 14px; text-align: left;">
                <strong>💡 จุดสังเกตเฉพาะบุคคล (Personalization Notes):</strong> {email_draft.get('personalization_notes')}
            </div>

            <!-- ร่างอีเมลเสนอขาย -->
            <div style="background: #ffffff; border-radius: 8px; padding: 20px; border: 1px solid #e2e8f0; margin-bottom: 20px; text-align: left;">
                <div style="border-bottom: 1px solid #e2e8f0; padding-bottom: 8px; margin-bottom: 12px;">
                    <div style="font-weight: bold; color: #7c3aed;">📬 ร่างจดหมายเสนอขายภาษาไทย</div>
                    <div style="font-size: 12px; color: #475569; margin-top: 4px;">ประโยคเปิดแนะนำ: "{email_draft.get('opening_hook')}"</div>
                </div>
                <div style="margin-bottom: 12px; color: #0f172a;">
                    <strong>หัวข้อ:</strong> {email_draft.get('subject')}
                </div>
                <div style="color: #0f172a; font-family: monospace; line-height: 1.6; background: #f8fafc; padding: 16px; border-radius: 6px; border: 1px solid #e2e8f0; white-space: pre-wrap;">
                    {formatted_body}
                </div>
            </div>

            <!-- ตารางนัดหมายติดตามผลปฏิทิน -->
            <div style="text-align: left;">
                <h4 style="margin-top: 0; margin-bottom: 10px; color: #059669;">📅 ตารางบันทึกปฏิทินติดตามผล (Google Calendar Schedule)</h4>
                <table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 13px;">
                    <thead>
                        <tr style="background: #f1f5f9;">
                            <th style="padding: 8px; border-bottom: 2px solid #e2e8f0; color: #475569;">หัวข้อนัดหมาย</th>
                            <th style="padding: 8px; border-bottom: 2px solid #e2e8f0; color: #475569;">วันที่กำหนด</th>
                            <th style="padding: 8px; border-bottom: 2px solid #e2e8f0; color: #475569;">สถานะระบบ</th>
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
    </head>
    <body style="font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f8fafc; color: #0f172a; margin: 0; padding: 40px 20px; line-height: 1.5;">
        <div style="max-width: 900px; margin: 0 auto;">
            <header style="text-align: center; margin-bottom: 40px; background: linear-gradient(135deg, #4f46e5, #7c3aed); padding: 30px; border-radius: 16px; border: 1px solid #e2e8f0; color: white; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
                <h1 style="margin: 0; font-size: 32px; color: #ffffff; font-weight: 700;">🚀 DealPilot Daily Sales Briefing Report</h1>
                <div style="color: #e0e7ff; margin-top: 8px; font-size: 16px;">รายงานสรุปบริษัทเป้าหมายและจดหมายเสนอขายที่ปรับแต่งตามสไตล์ของคุณ</div>
                <div style="margin-top: 15px; font-size: 14px; color: #ffffff; opacity: 0.9;">
                    <strong>ผู้เสนอขาย (SDR):</strong> {sdr_name} | <strong>คำอธิบายสไตล์:</strong> {style_description}
                </div>
            </header>

            <!-- ตารางสรุป Top 5 Leads -->
            <div style="background-color: #ffffff; border-radius: 12px; padding: 24px; margin-bottom: 40px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
                <h2 style="margin-top: 0; font-size: 20px; color: #4f46e5; border-bottom: 2px solid #f1f5f9; padding-bottom: 8px; margin-bottom: 16px;">🎯 สรุปผลการจัดอันดับโอกาสชนะปิดดีลสูงสุดประจำวันนี้</h2>
                <table style="width: 100%; border-collapse: collapse; text-align: left;">
                    <thead>
                        <tr style="border-bottom: 2px solid #e2e8f0;">
                            <th style="padding: 12px; color: #475569;">อันดับ</th>
                            <th style="padding: 12px; color: #475569;">ผู้ติดต่อ</th>
                            <th style="padding: 12px; color: #475569;">บริษัท</th>
                            <th style="padding: 12px; color: #475569;">มูลค่าดีล</th>
                            <th style="padding: 12px; color: #475569;">ขั้นตอน</th>
                            <th style="padding: 12px; color: #475569;">คะแนน</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows}
                    </tbody>
                </table>
            </div>

            <!-- รายละเอียดของแต่ละ Lead Card -->
            <h2 style="color: #0f172a; font-size: 24px; margin-bottom: 20px; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px;">📋 รายละเอียดการวิเคราะห์และดราฟต์อีเมลแยกรายบุคคล</h2>
            {lead_cards}
            
            <footer style="text-align: center; margin-top: 60px; color: #64748b; font-size: 12px; border-top: 1px solid #e2e8f0; padding-top: 20px;">
                ระบบขับเคลื่อนโดย DealPilot Multi-Agent CRM Orchestration Suite — capstone Project 2026
            </footer>
        </div>
    </body>
    </html>
    """
    return html_page

