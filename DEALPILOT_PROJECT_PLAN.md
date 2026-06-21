# DealPilot — AI Agent Project Plan
> **สำหรับ:** Kaggle AI Agents: Intensive Vibe Coding Capstone — Track: Agents for Business  
> **เวอร์ชัน:** 1.0  
> **วันที่:** 2026-06-20

---

## 🧠 คำแนะนำสำหรับ AI ที่อ่านไฟล์นี้

ไฟล์นี้คือ **single source of truth** ของโปรเจกต์ DealPilot  
เมื่อได้รับ task ให้:
1. อ่าน Section ที่เกี่ยวข้องก่อนเขียน code ทุกครั้ง
2. ยึด directory structure ตาม Section 5 อย่างเคร่งครัด
3. ทุก agent ต้องใช้ Google ADK และสื่อสารผ่าน `AgentOutput` dataclass เท่านั้น
4. ห้าม hardcode API key — ใช้ environment variable หรือ Secret Manager เสมอ
5. เขียน docstring ทุก function และ comment อธิบาย logic ที่ซับซ้อน

---

## 1. ภาพรวมโปรเจกต์

### 1.1 ปัญหาที่แก้

Sales Development Representatives (SDR) ใช้เวลา **60%+ ต่อวัน** กับงานที่ไม่ใช่การขาย:
- ค้นหาว่าต้อง follow-up ลูกค้าคนไหน
- Research ข้อมูลบริษัทลูกค้า
- เขียน email เหมือนๆ กันซ้ำๆ

### 1.2 โซลูชัน

**DealPilot** คือระบบ multi-agent ที่ส่ง **Daily Sales Briefing** ทุกเช้า 7:00 น. ประกอบด้วย:
- Top 5 leads ที่ควรติดต่อวันนี้ (ranked by win probability)
- Draft email สำหรับแต่ละ lead ที่เขียนในสไตล์ของ SDR คนนั้น
- ข้อมูล research บริษัทล่าสุด (news, funding, pain points)
- Follow-up schedule อัตโนมัติ

### 1.3 Tagline

> *"Your SDR's morning coffee — but for deals."*

---

## 2. สถาปัตยกรรมระบบ

### 2.1 ภาพรวม Agent Pipeline

```
CRM/CSV Data ──► CRM Agent ──► Research Agent ──► Writer Agent ──► Scheduler Agent
                     │               │                  │                │
                 rank leads     web search          draft email      calendar
                 by score       company info        per SDR style    + reminders
                                                         │
                                                    Daily Briefing
                                                    (HTML + Email)
```

### 2.2 Agent ทั้ง 4 ตัว

#### Agent 1: CRM Agent
- **หน้าที่:** ดึงข้อมูล leads จาก CRM และ rank ตาม win probability score
- **Input:** CRM data (CSV หรือ HubSpot API)
- **Output:** `List[RankedLead]` — top leads พร้อม score และเหตุผล
- **Scoring formula:**
  ```
  score = (deal_value * 0.4) + (days_since_last_contact_inverse * 0.3) + (deal_stage_weight * 0.3)
  ```
- **Key tools:** `crm_fetch_tool`, `lead_scorer_tool`

#### Agent 2: Research Agent
- **หน้าที่:** ค้นหาข้อมูลบริษัทลูกค้าที่เป็น top leads
- **Input:** `List[RankedLead]` (company names)
- **Output:** `List[CompanyResearch]` — news, funding, pain points, recent activities
- **Key tools:** MCP Web Search, `web_search_tool`
- **Search queries ที่ใช้:**
  - `"{company} news last 30 days"`
  - `"{company} funding announcement"`
  - `"{company} challenges OR pain points 2025"`

#### Agent 3: Writer Agent
- **หน้าที่:** Draft email ที่ personalized ในสไตล์ของ SDR คนนั้น
- **Input:** `RankedLead` + `CompanyResearch` + past emails ของ SDR
- **Output:** `DraftEmail` — subject line + body + opening hook
- **Key feature:** Few-shot learning จาก past successful emails ของ SDR แต่ละคน
- **Prompt structure:**
  ```
  System: คุณเป็น SDR ชื่อ {name} ที่มีสไตล์การเขียน: {style_description}
  Examples: [3 emails ที่เคยได้ reply]
  Task: เขียน email ถึง {prospect} ที่ {company} โดยใช้ข้อมูล: {research}
  ```

#### Agent 4: Scheduler Agent
- **หน้าที่:** วาง follow-up calendar และส่ง briefing
- **Input:** `List[DraftEmail]`
- **Output:** Calendar events + HTML briefing email
- **Key tools:** Google Calendar MCP, Gmail MCP
- **Follow-up cadence:**
  - Day 0: ส่ง email แรก
  - Day 3: follow-up #1 (ถ้าไม่มี reply)
  - Day 7: follow-up #2
  - Day 14: break-up email

### 2.3 Orchestrator (ADK)

```python
# ADK orchestrator เชื่อมทุก agent แบบ sequential pipeline
orchestrator = SequentialAgent(
    name="dealpilot_orchestrator",
    sub_agents=[crm_agent, research_agent, writer_agent, scheduler_agent]
)
```

---

## 3. Data Models

```python
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Lead:
    """ข้อมูล lead จาก CRM"""
    id: str
    name: str
    company: str
    email: str
    deal_value: float
    deal_stage: str  # "prospecting" | "qualified" | "proposal" | "negotiation"
    last_contact_date: datetime
    notes: Optional[str] = None

@dataclass
class RankedLead:
    """Lead ที่ผ่านการ rank แล้ว"""
    lead: Lead
    score: float           # 0.0 - 100.0
    score_reason: str      # อธิบายว่าทำไมถึงได้คะแนนนี้
    priority: int          # 1 = highest

@dataclass
class CompanyResearch:
    """ผลการ research บริษัทลูกค้า"""
    company: str
    recent_news: list[str]   # max 3 items
    pain_points: list[str]   # inferred from news
    talking_points: list[str]  # ready-to-use ใน email
    sources: list[str]

@dataclass
class DraftEmail:
    """Email ที่ Writer Agent สร้าง"""
    lead: RankedLead
    subject: str
    body: str
    opening_hook: str      # ประโยคแรกที่ดึงดูด
    personalization_notes: str  # อธิบายว่า personalize ตรงไหน

@dataclass
class AgentOutput:
    """Standard output ทุก agent ต้องใช้"""
    success: bool
    data: dict
    error: Optional[str] = None
    metadata: Optional[dict] = None
```

---

## 4. Key Concepts ที่ต้องสาธิต (5/5)

| # | Concept | สาธิตที่ไหน | Implementation |
|---|---------|------------|----------------|
| 1 | Multi-agent system (ADK) | Code | `SequentialAgent` orchestrator + 4 sub-agents |
| 2 | MCP Server | Code | Web Search MCP + Gmail MCP + Google Calendar MCP |
| 3 | Security features | Code + Video | Secret Manager, input sanitization, PII masking |
| 4 | Deployability | Video | Cloud Run deployment + Cloud Scheduler |
| 5 | Agent Skills (CLI) | Code + Video | `adk run dealpilot` CLI command |

---

## 5. Directory Structure

```
dealpilot/
├── README.md                    # สำหรับ judges — setup instructions
├── DEALPILOT_PROJECT_PLAN.md    # ไฟล์นี้
├── requirements.txt
├── .env.example                 # template — ห้ามใส่ค่าจริง
├── docker/
│   └── Dockerfile
│
├── agents/
│   ├── __init__.py
│   ├── orchestrator.py          # ADK SequentialAgent หลัก
│   ├── crm_agent.py             # Agent 1
│   ├── research_agent.py        # Agent 2
│   ├── writer_agent.py          # Agent 3
│   └── scheduler_agent.py       # Agent 4
│
├── tools/
│   ├── __init__.py
│   ├── crm_tools.py             # lead scoring, CRM fetch
│   ├── search_tools.py          # MCP web search wrapper
│   ├── email_tools.py           # Gmail MCP wrapper
│   └── calendar_tools.py        # Google Calendar MCP wrapper
│
├── models/
│   ├── __init__.py
│   └── data_models.py           # dataclasses ทั้งหมดจาก Section 3
│
├── data/
│   └── mock_crm.csv             # mock data สำหรับ demo
│
├── prompts/
│   ├── crm_agent_prompt.txt
│   ├── research_agent_prompt.txt
│   ├── writer_agent_prompt.txt
│   └── scheduler_agent_prompt.txt
│
├── security/
│   └── secret_manager.py        # Google Secret Manager wrapper
│
├── ui/
│   └── app.py                   # FastAPI — web UI สำหรับ demo
│
└── tests/
    ├── test_crm_agent.py
    ├── test_research_agent.py
    ├── test_writer_agent.py
    └── test_scheduler_agent.py
```

---

## 6. แผนการทำงาน 5 วัน

### วันที่ 1 — Foundation + CRM Agent
**เป้าหมาย:** โครงสร้างโปรเจกต์และ CRM Agent ทำงานได้

**Tasks:**
- [ ] สร้าง directory structure ตาม Section 5
- [ ] เขียน `requirements.txt`
- [ ] เขียน `data_models.py` ตาม Section 3 ครบทุก dataclass
- [ ] สร้าง `mock_crm.csv` (20 leads, หลาย deal stages และ values)
- [ ] เขียน `crm_tools.py`:
  - `fetch_leads_from_csv(filepath: str) -> List[Lead]`
  - `score_lead(lead: Lead) -> float`
  - `rank_leads(leads: List[Lead], top_n: int = 5) -> List[RankedLead]`
- [ ] เขียน `crm_agent.py` ใช้ Google ADK
- [ ] เขียน `test_crm_agent.py` และรันผ่าน

**Definition of Done:** รัน CRM Agent ได้ → ได้ `List[RankedLead]` top 5 ออกมาใน terminal

---

### วันที่ 2 — Research Agent + MCP Web Search
**เป้าหมาย:** Research Agent ดึงข้อมูลบริษัทได้จริง

**Tasks:**
- [ ] Setup MCP Web Search server ใน ADK
- [ ] เขียน `search_tools.py`:
  - `search_company_news(company: str) -> List[str]`
  - `extract_pain_points(news: List[str]) -> List[str]`
  - `generate_talking_points(research: CompanyResearch) -> List[str]`
- [ ] เขียน `research_agent.py` ที่รับ `List[RankedLead]` → return `List[CompanyResearch]`
- [ ] เขียน `prompts/research_agent_prompt.txt`
- [ ] เขียน `test_research_agent.py`

**Definition of Done:** ส่ง company name เข้า → ได้ structured research ออกมาพร้อม sources

---

### วันที่ 3 — Writer Agent + Style Learning
**เป้าหมาย:** Writer Agent draft email ในสไตล์ SDR แต่ละคนได้

**Tasks:**
- [ ] สร้าง `data/sdr_styles/` folder พร้อม sample emails ของ SDR 2 คน (mock)
- [ ] เขียน `prompts/writer_agent_prompt.txt` พร้อม few-shot examples
- [ ] เขียน `writer_agent.py`:
  - `load_sdr_style(sdr_id: str) -> str` — โหลด past emails
  - `build_few_shot_prompt(sdr_style: str) -> str`
  - `draft_email(lead: RankedLead, research: CompanyResearch, sdr_id: str) -> DraftEmail`
- [ ] เขียน `test_writer_agent.py` — ตรวจว่า email มี personalization จริง
- [ ] เชื่อม CRM Agent → Research Agent → Writer Agent ใน pipeline ทดสอบ

**Definition of Done:** รัน pipeline 3 agents → ได้ `List[DraftEmail]` ที่แตกต่างกันตาม SDR

---

### วันที่ 4 — Scheduler Agent + Orchestration
**เป้าหมาย:** ระบบทำงานครบ end-to-end

**Tasks:**
- [ ] Setup Gmail MCP และ Google Calendar MCP ใน ADK
- [ ] เขียน `email_tools.py` และ `calendar_tools.py`
- [ ] เขียน `scheduler_agent.py`:
  - `create_followup_schedule(draft: DraftEmail) -> List[CalendarEvent]`
  - `generate_html_briefing(drafts: List[DraftEmail]) -> str`
  - `send_briefing_email(html: str, recipient: str) -> bool`
- [ ] เขียน `orchestrator.py` — ADK `SequentialAgent` เชื่อมทุก agent
- [ ] รัน full pipeline end-to-end:
  ```bash
  adk run dealpilot --sdr-id="sdr_001" --output=briefing.html
  ```

**Definition of Done:** รัน orchestrator → ได้ `briefing.html` พร้อม email drafts ครบ 5 leads

---

### วันที่ 5 — Security + Deploy + Video
**เป้าหมาย:** โปรเจกต์พร้อม submit

**Tasks:**

**Security:**
- [ ] เขียน `security/secret_manager.py` — ดึง secrets จาก Google Secret Manager
- [ ] เพิ่ม input sanitization ใน CRM Agent (ป้องกัน prompt injection)
- [ ] เพิ่ม PII masking สำหรับ email addresses ใน logs
- [ ] เพิ่ม rate limiting ใน MCP tool calls

**Deployment:**
- [ ] เขียน `Dockerfile`
- [ ] Deploy ไป Cloud Run
- [ ] Setup Cloud Scheduler ให้รัน 07:00 ทุกวัน
- [ ] เพิ่ม FastAPI health check endpoint (`/health`)

**Demo UI:**
- [ ] เขียน `ui/app.py` — FastAPI หน้า web แสดง briefing ผ่าน browser
- [ ] หน้า `/` แสดง daily briefing HTML
- [ ] หน้า `/run` trigger manual run

**Documentation:**
- [ ] เขียน `README.md` (ดู Section 9)
- [ ] เขียน `.env.example`

**Video (5 นาที):**
- [ ] 0:00–0:45 — Problem statement
- [ ] 0:45–1:30 — Architecture walkthrough (ใช้แผนภาพจาก Section 2)
- [ ] 1:30–3:30 — Live demo: รัน pipeline → ดู briefing ใน browser
- [ ] 3:30–4:30 — Code walkthrough: security features + MCP setup
- [ ] 4:30–5:00 — Deployment demo บน Cloud Run

---

## 7. Environment Variables

```bash
# .env.example — คัดลอกไปเป็น .env แล้วใส่ค่าจริง
# ห้าม commit .env ไปยัง git เด็ดขาด

# Google AI
GOOGLE_API_KEY=your_gemini_api_key_here
GOOGLE_CLOUD_PROJECT=your_gcp_project_id

# Google Cloud Secret Manager (production)
USE_SECRET_MANAGER=false  # ตั้งเป็น true เมื่อ deploy

# CRM
CRM_MODE=csv  # "csv" | "hubspot" | "salesforce"
CRM_CSV_PATH=data/mock_crm.csv
HUBSPOT_API_KEY=optional_hubspot_key

# Gmail MCP
GMAIL_CREDENTIALS_PATH=credentials/gmail_credentials.json
BRIEFING_RECIPIENT_EMAIL=sdr@yourcompany.com

# Google Calendar MCP
CALENDAR_ID=primary

# ADK
ADK_MODEL=gemini-2.0-flash
ADK_MAX_TOKENS=8192

# Security
ENABLE_PII_MASKING=true
ENABLE_INPUT_SANITIZATION=true
```

---

## 8. การ Implement Security Features

### 8.1 Secret Manager

```python
# security/secret_manager.py
import os
from google.cloud import secretmanager

def get_secret(secret_id: str) -> str:
    """
    ดึง secret จาก Google Cloud Secret Manager
    ถ้า USE_SECRET_MANAGER=false จะใช้ environment variable แทน
    """
    if os.getenv("USE_SECRET_MANAGER", "false").lower() == "false":
        # Development mode: ใช้ env var
        env_key = secret_id.upper().replace("-", "_")
        value = os.getenv(env_key)
        if not value:
            raise ValueError(f"Environment variable {env_key} not set")
        return value
    
    # Production mode: ใช้ Secret Manager
    client = secretmanager.SecretManagerServiceClient()
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")
```

### 8.2 Input Sanitization

```python
# tools/crm_tools.py
import re

def sanitize_lead_input(text: str) -> str:
    """
    ป้องกัน prompt injection จาก CRM data
    ลบ patterns ที่อาจเป็น instruction injection
    """
    # ลบ patterns ที่น่าสงสัย
    patterns = [
        r"ignore previous instructions",
        r"system prompt",
        r"<\|.*?\|>",  # special tokens
        r"\[INST\].*?\[/INST\]",  # instruction tags
    ]
    for pattern in patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)
    return text.strip()
```

### 8.3 PII Masking ใน Logs

```python
# utils/logging.py
import re

def mask_pii(text: str) -> str:
    """Mask email addresses และ phone numbers ใน logs"""
    # Mask emails
    text = re.sub(r'\b[\w.+-]+@[\w-]+\.[\w.]+\b', '***@***.***', text)
    # Mask phone numbers
    text = re.sub(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', '***-***-****', text)
    return text
```

---

## 9. README.md Structure (สำหรับ judges)

README ที่ต้องเขียนต้องมี sections ดังนี้:

```markdown
# DealPilot 🎯

> AI Sales Agent ที่ช่วย SDR ปิดดีลเร็วขึ้นด้วย Daily Sales Briefing

## Problem
## Solution  
## Architecture (รูปแผนภาพจาก Section 2)
## Key Concepts Demonstrated
## Setup Instructions
  ### Prerequisites
  ### Local Development
  ### Production Deployment
## Usage
  ### Run via CLI
  ### Web UI
## Security
## Project Structure
## Tech Stack
```

---

## 10. Mock CRM Data Schema

ไฟล์ `data/mock_crm.csv` ต้องมี columns:

```
id,name,company,email,deal_value,deal_stage,last_contact_date,notes
lead_001,Alice Johnson,TechCorp Inc,alice@techcorp.com,45000,proposal,2026-06-10,Interested in enterprise plan
lead_002,Bob Martinez,StartupXYZ,bob@startupxyz.com,12000,qualified,2026-06-05,Need Q3 budget approval
...
```

สร้าง 20 rows ที่หลากหลาย:
- deal_value: ตั้งแต่ 5,000 ถึง 150,000
- deal_stage: กระจาย prospecting/qualified/proposal/negotiation
- last_contact_date: บางคนนาน 30+ วัน บางคนแค่ 2 วัน

---

## 11. Kaggle Writeup Outline (2,500 คำ)

**Section 1: Problem (300 คำ)**
- SDR pain points
- ตัวเลขเวลาที่เสียไป
- ผลกระทบต่อ revenue

**Section 2: Solution & Why Agents (400 คำ)**
- ทำไมถึงเลือก multi-agent แทน single LLM call
- แต่ละ agent ทำอะไรและทำไม
- Emergent capability จาก agent collaboration

**Section 3: Architecture (500 คำ)**
- แผนภาพ pipeline
- ADK orchestration
- MCP server integration
- Data flow

**Section 4: Implementation (600 คำ)**
- CRM Agent: scoring algorithm
- Research Agent: MCP web search
- Writer Agent: few-shot style learning
- Scheduler Agent: calendar automation

**Section 5: Security (200 คำ)**
- Secret Manager
- Input sanitization
- PII masking

**Section 6: Deployment (200 คำ)**
- Cloud Run
- Cloud Scheduler

**Section 7: Results & Demo (200 คำ)**
- Output examples
- Link to demo video
- Link to GitHub

**Section 8: Lessons Learned (100 คำ)**

---

## 12. Checklist ก่อน Submit

### Code
- [ ] ไม่มี API key หรือ secret ใน code หรือ git history
- [ ] มี `.gitignore` ที่ครอบคลุม `.env`, `credentials/`, `*.key`
- [ ] ทุก function มี docstring
- [ ] มี comment อธิบาย design decisions ที่สำคัญ
- [ ] `README.md` มี setup instructions ที่ทำตามได้จริง
- [ ] รัน tests ผ่านทั้งหมด

### Submission
- [ ] Kaggle Writeup ไม่เกิน 2,500 คำ
- [ ] วิดีโอ YouTube ≤ 5 นาที, public, ไม่ต้อง login
- [ ] GitHub repo เป็น public
- [ ] Project link ใส่ใน Writeup แล้ว
- [ ] เลือก Track: **Agents for Business**
- [ ] กด Submit (ไม่ใช่แค่ Draft)

### Demo Video ต้องแสดง
- [ ] ปัญหาที่แก้
- [ ] Architecture diagram
- [ ] Live demo: pipeline รันจริง
- [ ] Security features
- [ ] Deployment บน Cloud Run

---

## 13. Tech Stack สรุป

| Component | Technology |
|-----------|-----------|
| Agent Framework | Google ADK (Agent Development Kit) |
| LLM | Gemini 2.0 Flash |
| Language | Python 3.11 |
| MCP Tools | Web Search MCP, Gmail MCP, Google Calendar MCP |
| CRM Integration | CSV (demo) / HubSpot API (production) |
| Security | Google Cloud Secret Manager |
| Deployment | Google Cloud Run |
| Scheduler | Google Cloud Scheduler |
| Web UI | FastAPI + Jinja2 |
| Testing | pytest |
| Container | Docker |

---

*ไฟล์นี้อัปเดตล่าสุด: 2026-06-20 | สร้างโดย Claude สำหรับ Kaggle AI Agents Capstone*
