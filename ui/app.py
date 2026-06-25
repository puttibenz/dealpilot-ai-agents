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


pipeline_process = None


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
            
            terminal.innerHTML = "=== INITIALIZING PIPELINE RUN ===\\n";
            
            // Start the pipeline runner in the background
            fetch('/run/start')
                .then(response => response.json())
                .then(data => {{
                    terminal.innerHTML += "System initialized. Starting sequential agents...\\n";
                    
                    // Poll log status every 1 second
                    const pollInterval = setInterval(() => {{
                        fetch('/run/status')
                            .then(res => res.json())
                            .then(status => {{
                                if (status.logs) {{
                                    terminal.innerHTML = "=== INITIALIZING PIPELINE RUN ===\\n" + status.logs;
                                    terminal.scrollTop = terminal.scrollHeight;
                                    
                                    // Update status text based on logs
                                    if (status.logs.includes("Step 1")) {{
                                        statusText.innerText = "Ranking CRM leads via CRM Agent...";
                                    }}
                                    if (status.logs.includes("Step 2")) {{
                                        statusText.innerText = "Querying business highlights via Research Agent...";
                                    }}
                                    if (status.logs.includes("Step 3")) {{
                                        statusText.innerText = "Drafting personalized sales emails via Writer Agent...";
                                    }}
                                    if (status.logs.includes("Step 4")) {{
                                        statusText.innerText = "Scheduling calendar events and sending Daily Briefing via Scheduler Agent...";
                                    }}
                                }}
                                
                                // Check if finished
                                if (!status.is_running) {{
                                    clearInterval(pollInterval);
                                    statusText.innerText = "Multi-Agent pipeline run completed successfully!";
                                    statusText.style.color = "#34d399";
                                    spinner.style.display = "none";
                                    btnView.style.display = "inline-block";
                                }}
                            }})
                            .catch(err => {{
                                console.error("Error fetching pipeline status:", err);
                            }});
                    }}, 1000);
                }})
                .catch(err => {{
                    terminal.innerHTML += "[ERROR] Failed to start pipeline runner: " + err + "\\n";
                    statusText.innerText = "Error starting pipeline!";
                    statusText.style.color = "#ef4444";
                    spinner.style.display = "none";
                }});
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_page)


@app.get("/run/start")
def start_pipeline():
    """Starts the run_day4.py pipeline in the background and writes logs to a file."""
    global pipeline_process
    
    # If a process is already running, don't start another one
    if pipeline_process and pipeline_process.poll() is None:
        return {"status": "already_running"}
        
    log_file_path = DATA_DIR / "pipeline_run.log"
    DATA_DIR.mkdir(exist_ok=True)
    
    # Clear old log file
    if log_file_path.exists():
        try:
            log_file_path.unlink()
        except Exception:
            pass
            
    python_exec = sys.executable
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
        # Open log file for output redirection
        log_file = open(log_file_path, "w", encoding="utf-8", errors="replace")
        pipeline_process = subprocess.Popen(
            cmd,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            env=env
        )
        return {"status": "started"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/run/status")
def get_pipeline_status():
    """Reads the masked logs from the pipeline_run.log file."""
    global pipeline_process
    
    log_file_path = DATA_DIR / "pipeline_run.log"
    logs = ""
    
    if log_file_path.exists():
        try:
            with open(log_file_path, "r", encoding="utf-8", errors="replace") as f:
                logs = f.read()
        except Exception as e:
            logs = f"Error reading logs: {str(e)}"
            
    # Apply PII Masking
    from utils.logging import mask_pii
    masked_logs = mask_pii(logs)
    
    is_running = False
    if pipeline_process and pipeline_process.poll() is None:
        is_running = True
        
    return {
        "is_running": is_running,
        "logs": masked_logs
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
