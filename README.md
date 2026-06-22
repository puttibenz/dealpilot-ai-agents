# DealPilot 🎯

> AI Sales Agent ที่ช่วย SDR ปิดดีลเร็วขึ้นด้วย Daily Sales Briefing
>
> *"Your SDR's morning coffee — but for deals."*

## Problem

Sales Development Representatives (SDR) ใช้เวลา 60%+ ต่อวันกับงานที่ไม่ใช่การขาย:
- ค้นหาว่าต้อง follow-up ลูกค้าคนไหน
- Research ข้อมูลบริษัทลูกค้า
- เขียน email เหมือนๆ กันซ้ำๆ

## Solution

DealPilot คือระบบ multi-agent ที่ส่ง Daily Sales Briefing ทุกเช้า ประกอบด้วย:
- Top 5 leads ที่ควรติดต่อวันนี้ (ranked by win probability)
- Draft email สำหรับแต่ละ lead ที่เขียนในสไตล์ของ SDR คนนั้น
- ข้อมูล research บริษัทล่าสุด
- Follow-up schedule อัตโนมัติ

## Architecture

```
CRM/CSV Data ──► CRM Agent ──► Research Agent ──► Writer Agent ──► Scheduler Agent
                     │               │                  │                │
                 rank leads     web search          draft email      calendar
                 by score       company info        per SDR style    + reminders
                                                         │
                                                    Daily Briefing
                                                    (HTML + Email)
```

## Key Concepts Demonstrated

| # | Concept | Implementation |
|---|---------|----------------|
| 1 | Multi-agent system (ADK) | SequentialAgent orchestrator + 4 sub-agents |
| 2 | MCP Server | Web Search MCP + Gmail MCP + Google Calendar MCP |
| 3 | Security features | Secret Manager, input sanitization, PII masking |
| 4 | Deployability | Cloud Run deployment + Cloud Scheduler |
| 5 | Agent Skills (CLI) | `adk run dealpilot` CLI command |

## Setup Instructions

### Prerequisites
- Python 3.11+
- Google Cloud Project with APIs enabled
- Gemini API key

### Local Development

```bash
# 1. Clone repo
git clone <repo-url>
cd dealpilot

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# แก้ไข .env ใส่ API keys จริง

# 5. Run
python run_day4.py --sdr-id="sdr_001" --output=data/briefing_sdr001.html --recipient-email="puttimej@gmail.com"
```

### Production Deployment

```bash
# Build & Deploy to Cloud Run
docker build -t dealpilot -f docker/Dockerfile .
gcloud run deploy dealpilot --image dealpilot --region us-central1
```

## Usage

### Run via CLI
```bash
python run_day4.py --sdr-id="sdr_001" --output=data/briefing_sdr001.html --recipient-email="your_email@example.com"
```

### Web UI
```bash
python ui/app.py
# เปิด http://localhost:8080
```

## Security
- Google Cloud Secret Manager สำหรับ API keys
- Input sanitization ป้องกัน prompt injection ใน tools/crm_tools.py
- PII masking สำหรับปกปิดอีเมลและเบอร์โทรศัพท์ใน logs ด้วย utils/logging.py

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Agent Framework | Google ADK |
| LLM | Gemini 2.0 Flash |
| Language | Python 3.11 |
| MCP Tools | Web Search, Gmail, Google Calendar |
| Security | Google Cloud Secret Manager |
| Deployment | Google Cloud Run |
| Web UI | FastAPI + Jinja2 |
| Testing | pytest |
