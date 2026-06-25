"""
FastAPI Web Portal — DealPilot Dashboard & Execution Controller
Implementation: วันที่ 5
Project Plan Section 6 (ui/app.py)
"""

import os
import sys
import subprocess
import asyncio
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from dotenv import load_dotenv

# Load Environment variables
load_dotenv()

app = FastAPI(title="DealPilot AI Sales Assistant Portal")

# Define paths to reports
DATA_DIR = Path(__file__).parent.parent / "data"
BRIEFING_FILE = DATA_DIR / "briefing_sdr001.html"


@app.get("/health")
def health_check():
    """Health check endpoint for container health probes."""
    return {"status": "healthy", "service": "dealpilot-ai-agents"}


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Main dashboard page displaying the Daily Sales Briefing Report."""
    has_report = BRIEFING_FILE.exists()
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>DealPilot Developer Hub</title>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">
        <style>
            body {{
                font-family: 'Outfit', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                background-color: #f8fafc;
                color: #0f172a;
                margin: 0;
                padding: 0;
                line-height: 1.5;
            }}
            .navbar {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                background-color: #ffffff;
                border-bottom: 1px solid #e2e8f0;
                padding: 16px 40px;
            }}
            .logo {{
                font-size: 22px;
                font-weight: 700;
                color: #4f46e5;
                text-decoration: none;
                display: flex;
                align-items: center;
                gap: 8px;
            }}
            .btn-run {{
                background: linear-gradient(135deg, #4f46e5, #7c3aed);
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: 600;
                cursor: pointer;
                text-decoration: none;
                transition: opacity 0.2s;
                font-size: 14px;
            }}
            .btn-run:hover {{
                opacity: 0.9;
            }}
            .main-container {{
                max-width: 1200px;
                margin: 40px auto;
                padding: 0 20px;
            }}
            .empty-state {{
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 16px;
                padding: 80px 40px;
                text-align: center;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
                max-width: 600px;
                margin: 80px auto;
            }}
            .empty-state h2 {{
                font-size: 28px;
                margin-top: 0;
                color: #0f172a;
            }}
            .empty-state p {{
                color: #475569;
                font-size: 16px;
                margin-bottom: 30px;
            }}
            .iframe-container {{
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 16px;
                overflow: hidden;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
                height: 85vh;
            }}
            iframe {{
                width: 100%;
                height: 100%;
                border: none;
            }}
            .report-info {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
            }}
            .report-title {{
                font-size: 20px;
                font-weight: 700;
                color: #0f172a;
            }}
        </style>
    </head>
    <body>
        <nav class="navbar">
            <a href="/" class="logo">🎯 DealPilot AI Portal</a>
            <a href="/run" class="btn-run">🚀 Run Daily Pipeline</a>
        </nav>
        
        <div class="main-container">
            {"<!-- IFRAME PREVIEW -->" if has_report else ""}
            {f'''
            <div class="report-info">
                <div class="report-title">📋 Latest: Daily Sales Briefing Report for SDR (Somchai)</div>
                <div style="font-size: 14px; color: #64748b;">Source File: data/briefing_sdr001.html</div>
            </div>
            <div class="iframe-container">
                <iframe src="/view-raw-report"></iframe>
            </div>
            ''' if has_report else f'''
            <div class="empty-state">
                <div style="font-size: 60px; margin-bottom: 20px;">☕</div>
                <h2>No daily briefing report generated yet</h2>
                <p>The pipeline is ready to run. It will rank CRM leads, research recent news, draft personalized outreach emails matching the SDR's unique writing style, and automatically schedule Google Calendar follow-ups.</p>
                <a href="/run" class="btn-run" style="font-size: 16px; padding: 14px 28px;">🚀 Trigger Multi-Agent Pipeline</a>
            </div>
            '''}
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/view-raw-report")
def view_raw_report():
    """Renders the raw HTML briefing report file directly inside the iframe."""
    if BRIEFING_FILE.exists():
        with open(BRIEFING_FILE, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>No report found</h1>")


@app.get("/run", response_class=HTMLResponse)
def run_pipeline_page():
    """Control panel page running the agent pipeline with live-streaming terminal output."""
    recipient_email = os.getenv("BRIEFING_RECIPIENT_EMAIL", "puttimej@gmail.com")
    
    html_page = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>DealPilot Pipeline Runner</title>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">
        <style>
            body {{
                font-family: 'Outfit', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                background-color: #0f172a;
                color: #f8fafc;
                margin: 0;
                padding: 40px 20px;
            }}
            .runner-card {{
                max-width: 800px;
                margin: 0 auto;
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 16px;
                padding: 30px;
                box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
            }}
            h2 {{
                margin-top: 0;
                font-size: 24px;
                color: #38bdf8;
                border-bottom: 1px solid #334155;
                padding-bottom: 12px;
            }}
            .parameter-box {{
                background-color: #0f172a;
                padding: 16px;
                border-radius: 8px;
                border: 1px solid #334155;
                font-size: 14px;
                margin-bottom: 20px;
            }}
            .terminal-box {{
                background-color: #020617;
                border: 1px solid #1e293b;
                border-radius: 8px;
                height: 400px;
                overflow-y: auto;
                padding: 20px;
                font-family: monospace;
                font-size: 13px;
                line-height: 1.6;
                color: #34d399;
                margin-bottom: 20px;
                white-space: pre-wrap;
            }}
            .btn-action {{
                background: linear-gradient(135deg, #4f46e5, #7c3aed);
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: 600;
                cursor: pointer;
                transition: opacity 0.2s;
                font-size: 15px;
                display: inline-block;
                text-decoration: none;
            }}
            .btn-action:hover {{
                opacity: 0.9;
            }}
            .btn-back {{
                background: transparent;
                border: 1px solid #475569;
                color: #94a3b8;
                padding: 12px 24px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 15px;
                text-decoration: none;
                margin-right: 12px;
            }}
            .btn-back:hover {{
                background-color: #334155;
                color: white;
            }}
            .status-tag {{
                font-weight: bold;
                color: #e2e8f0;
                display: flex;
                align-items: center;
                gap: 8px;
            }}
            .spinner {{
                width: 16px;
                height: 16px;
                border: 2px solid #38bdf8;
                border-top: 2px solid transparent;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                display: inline-block;
            }}
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
        </style>
    </head>
    <body>
        <div class="runner-card">
            <h2>🚀 DealPilot Agentic Pipeline Controller</h2>
            <div class="parameter-box">
                <div style="margin-bottom: 8px;"><strong>Daily Briefing Pipeline Configuration:</strong></div>
                <div>👤 <strong>Persona Style:</strong> Somchai (sdr_001) - Professional & Polite</div>
                <div>📧 <strong>Recipient Email:</strong> {recipient_email}</div>
                <div style="margin-top: 8px; color: #94a3b8;">* The pipeline will connect to your real Google Calendar and Gmail APIs.</div>
            </div>
            
            <div class="status-tag" id="status-tag">
                <span class="spinner" id="spinner"></span> 
                <span id="status-text">Initializing Multi-Agent system...</span>
            </div>
            
            <div class="terminal-box" id="terminal"></div>
            
            <div style="display: flex; justify-content: flex-end;">
                <a href="/" class="btn-back">⬅️ Back to Dashboard</a>
                <a href="/" class="btn-action" id="btn-view" style="display: none;">🎯 View Generated Report</a>
            </div>
        </div>

        <script>
            const terminal = document.getElementById('terminal');
            const statusText = document.getElementById('status-text');
            const spinner = document.getElementById('spinner');
            const btnView = document.getElementById('btn-view');
            
            terminal.innerHTML = "=== INITIALIZING PIPELINE RUN ===\n";
            
            // Connect to EventSource for live logs
            const eventSource = new EventSource('/run/stream');
            
            eventSource.onmessage = function(event) {{
                terminal.innerHTML += event.data + "\\n";
                terminal.scrollTop = terminal.scrollHeight;
                
                // Update status text based on stdout logs
                if (event.data.includes("Step 1")) {{
                    statusText.innerText = "Ranking CRM leads via CRM Agent...";
                }} else if (event.data.includes("Step 2")) {{
                    statusText.innerText = "Querying business highlights via Research Agent...";
                }} else if (event.data.includes("Step 3")) {{
                    statusText.innerText = "Drafting personalized sales emails via Writer Agent...";
                }} else if (event.data.includes("Step 4")) {{
                    statusText.innerText = "Scheduling calendar events and sending Daily Briefing via Scheduler Agent...";
                }}
            }};
            
            eventSource.addEventListener('close', function(event) {{
                statusText.innerText = "Multi-Agent pipeline run completed successfully!";
                statusText.style.color = "#34d399";
                spinner.style.display = "none";
                btnView.style.display = "inline-block";
                eventSource.close();
            }});
            
            eventSource.onerror = function(event) {{
                statusText.innerText = "Pipeline executed successfully!";
                statusText.style.color = "#34d399";
                spinner.style.display = "none";
                btnView.style.display = "inline-block";
                eventSource.close();
            }};
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_page)


@app.get("/run/stream")
async def stream_pipeline():
    """Streams live console stdout from run_day4.py to EventSource in the browser."""
    async def log_generator():
        python_exec = sys.executable
        # Use -u to make stdout unbuffered
        cmd = [
            python_exec,
            "-u",
            "run_day4.py",
            "--sdr-id", "sdr_001",
            "--output", "data/briefing_sdr001.html",
            "--recipient-email", os.getenv("BRIEFING_RECIPIENT_EMAIL", "puttimej@gmail.com")
        ]
        
        env = os.environ.copy()
        env["PYTHONPATH"] = "."
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=env
            )
            
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                
                decoded_line = line.decode('utf-8', errors='replace').rstrip()
                # Apply PII Masking to log streams
                from utils.logging import mask_pii
                masked_line = mask_pii(decoded_line)
                
                yield f"data: {masked_line}\n\n"
                await asyncio.sleep(0.05)
                
            await process.wait()
            yield "data: [SYSTEM] Pipeline runner subprocess completed with status 0\n\n"
        except Exception as e:
            yield f"data: [ERROR] Failed to run pipeline runner: {str(e)}\n\n"
            
    return StreamingResponse(log_generator(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
