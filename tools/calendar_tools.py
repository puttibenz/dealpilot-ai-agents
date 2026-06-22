"""
Calendar Tools — Google Calendar API Integration with local mock fallback
Implementation: วันที่ 4
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/gmail.send'
]


def get_google_credentials() -> Optional[Credentials]:
    """
    โหลดหรือขอสิทธิ์ (OAuth) สำหรับการเชื่อมต่อ Google APIs (Calendar & Gmail)
    """
    # ค้นหาพาธของ client_secret.json จากตำแหน่งที่เป็นไปได้
    possible_paths = [
        Path("agents/credentials/client_secret.json"),
        Path("credentials/client_secret.json"),
        Path(__file__).parent.parent / "agents" / "credentials" / "client_secret.json",
        Path(__file__).parent.parent / "credentials" / "client_secret.json"
    ]
    
    client_secret_path = None
    for p in possible_paths:
        if p.exists():
            client_secret_path = p
            break
            
    if not client_secret_path:
        # พยายามหาใน current working directory ในแบบอื่นๆ
        for p in Path(".").rglob("client_secret.json"):
            client_secret_path = p
            break

    if not client_secret_path:
        print("⚠️ Warning: client_secret.json not found. Operating in local Mock Mode.")
        return None
        
    # ไฟล์เก็บ token
    token_path = Path("token.json")
    creds = None
    
    if token_path.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        except Exception as e:
            print(f"⚠️ Warning: Failed to load token.json: {str(e)}")
            
    # ถ้าไม่มี token หรือ token หมดอายุ
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"⚠️ Refresh token expired or failed: {str(e)}")
                creds = None
        
        if not creds:
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(client_secret_path), SCOPES
                )
                # เปิดเบราว์เซอร์สำหรับเข้าสู่ระบบและยืนยันสิทธิ์
                creds = flow.run_local_server(port=0)
                # บันทึก token สำหรับใช้งานครั้งต่อไป
                with open(token_path, "w") as token_file:
                    token_file.write(creds.to_json())
            except Exception as e:
                print(f"❌ Failed to authorize OAuth: {str(e)}")
                return None
                
    return creds


def create_followup_event(lead_name: str, event_title: str, date_str: str, notes: str) -> dict:
    """
    สร้างนัดหมายติดตามผลใน Google Calendar จริง หรือปฏิทินจำลอง (mock_calendar.json)
    """
    creds = get_google_credentials()
    
    # แปลงวันที่
    try:
        event_date = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        event_date = datetime.now() + timedelta(days=1)
        date_str = event_date.strftime("%Y-%m-%d")

    # กำหนดช่วงเวลา (ให้เริ่ม 09:00 น. นาน 30 นาที)
    start_time = f"{date_str}T09:00:00"
    end_time = f"{date_str}T09:30:00"

    if creds:
        try:
            service = build('calendar', 'v3', credentials=creds)
            event_body = {
                'summary': event_title,
                'description': f"DealPilot Auto-scheduled follow-up for {lead_name}.\nNotes: {notes}",
                'start': {
                    'dateTime': start_time,
                    'timeZone': 'Asia/Bangkok',
                },
                'end': {
                    'dateTime': end_time,
                    'timeZone': 'Asia/Bangkok',
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': 30},
                    ],
                },
            }
            
            event = service.events().insert(calendarId='primary', body=event_body).execute()
            print(f"   📅 Google Calendar Event Created: {event.get('summary')} ({date_str})")
            return {
                "success": True,
                "event_id": event.get("id"),
                "link": event.get("htmlLink"),
                "title": event_title,
                "date": date_str,
                "mode": "real"
            }
        except Exception as e:
            print(f"   ⚠️ Failed to call Google Calendar API: {str(e)}. Falling back to Mock Mode.")

    # Local Mock fallback: บันทึกข้อมูลจำลองลงไฟล์ JSON
    mock_dir = Path("data")
    mock_dir.mkdir(exist_ok=True)
    mock_file = mock_dir / "mock_calendar.json"
    
    calendar_events = []
    if mock_file.exists():
        try:
            with open(mock_file, "r", encoding="utf-8") as f:
                calendar_events = json.load(f)
        except Exception:
            pass
            
    mock_event = {
        "event_id": f"mock_{int(datetime.now().timestamp())}_{lead_name.replace(' ', '_').lower()}_{date_str}",
        "title": event_title,
        "lead_name": lead_name,
        "start_time": start_time,
        "end_time": end_time,
        "notes": notes,
        "created_at": datetime.now().isoformat()
    }
    calendar_events.append(mock_event)
    
    with open(mock_file, "w", encoding="utf-8") as f:
        json.dump(calendar_events, f, ensure_ascii=False, indent=2)
        
    print(f"   📝 Mock Calendar Event Saved to local file: {event_title} on {date_str}")
    return {
        "success": True,
        "event_id": mock_event["event_id"],
        "link": "http://mock.calendar.google.com",
        "title": event_title,
        "date": date_str,
        "mode": "mock"
    }


def create_followup_schedule(lead_name: str, email_subject: str, deal_value: float) -> List[dict]:
    """
    สร้างตารางติดตามงาน (Day 0, Day 3, Day 7, Day 14) บันทึกลงปฏิทิน
    """
    ref_date = datetime.now()
    schedule_events = []
    
    intervals = [
        (0, f"ส่งอีเมลแรกเสนอขาย: {lead_name}", f"ส่งอีเมลฉบับแรกหัวข้อ '{email_subject}' มูลค่าดีล ${deal_value:,.2f}"),
        (3, f"Follow-up #1: {lead_name}", "ตรวจสอบการตอบกลับและส่งเมลทวงถามฉบับที่ 1 หากยังไม่มีการตอบรับ"),
        (7, f"Follow-up #2: {lead_name}", "ส่งอีเมลติดตามฉบับที่ 2 เพื่อกระตุ้นความสนใจเพิ่มเติม"),
        (14, f"Break-up Email: {lead_name}", "ส่งอีเมลถอดใจฉบับสุดท้ายเพื่อสรุปหรือยุติการติดต่อดีลนี้ชั่วคราว")
    ]
    
    for days, title, notes in intervals:
        target_date = ref_date + timedelta(days=days)
        date_str = target_date.strftime("%Y-%m-%d")
        
        event_result = create_followup_event(
            lead_name=lead_name,
            event_title=title,
            date_str=date_str,
            notes=notes
        )
        schedule_events.append(event_result)
        
    return schedule_events
