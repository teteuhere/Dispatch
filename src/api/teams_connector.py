import os
import sys
import json
import uvicorn
import logging
import threading
import webview
from datetime import datetime
from pydantic import BaseModel
from utils.logger import setup_logger
from utils.security import IntelSecurity
from contextlib import asynccontextmanager
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from api.connector import MicrosoftConnector
from fastapi.templating import Jinja2Templates
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException


# --- 1. PATH RECALIBRATION ---
if getattr(sys, 'frozen', False):
    PROJECT_ROOT = os.path.dirname(sys.executable)
else:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.abspath(os.path.join(script_dir, "..", ".."))

# FALLBACK
if not os.path.exists(os.path.join(PROJECT_ROOT, "config")):
    PROJECT_ROOT = os.getcwd()

CONFIG_PATH = os.path.join(PROJECT_ROOT, "config", "targets.json")
SECRETS_PATH = os.path.join(PROJECT_ROOT, "config", "secrets.json")
KEY_PATH = os.path.join(PROJECT_ROOT, "config", "master.key") # <--- NEW KEY PATH
LOG_PATH = os.path.join(PROJECT_ROOT, "logs", "mission_log.log")

os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
logger = setup_logger()

# --- 2. SECURITY INITIALIZATION ---
# Initialize the Security Officer
security_officer = IntelSecurity(KEY_PATH)

scheduler = BackgroundScheduler()
JOB_ID = 'mission_trigger'

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"SYSTEM BOOT | SECURE MODE")
    if os.path.exists(CONFIG_PATH):
        load_schedule_logic()
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)

# --- 3. RESOURCE LOCATOR ---
def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

frontend_path = "src/frontend"
if getattr(sys, 'frozen', False):
    frontend_path = get_resource_path("src/frontend")

app.mount("/static", StaticFiles(directory=frontend_path), name="static")
templates = Jinja2Templates(directory=frontend_path)

# --- 4. DATA HELPER & SECURITY LOGIC ---
class NewTarget(BaseModel):
    name: str
    email: str
class ConfigUpdate(BaseModel):
    trigger_time: str
class SecretsUpdate(BaseModel):
    email_user: str
    email_pass: str
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587

def load_json(path):
    """Standard JSON Loader for non-sensitive data"""
    try:
        if not os.path.exists(path): return {}
        with open(path, 'r') as f: return json.load(f)
    except: return {}

def save_json(path, data):
    """Standard JSON Saver for non-sensitive data"""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f: json.dump(data, f, indent=4)
        return True
    except: return False

def load_secrets():
    """SECURE LOADER: Handles Encryption"""
    if not os.path.exists(SECRETS_PATH): return {}

    try:
        with open(SECRETS_PATH, 'r') as f:
            content = f.read()

        # Migration Check: If it starts with '{', it's old plain text.
        if content.strip().startswith('{'):
            logger.warning("DETECTED PLAIN TEXT SECRETS. MIGRATING TO ENCRYPTED STORAGE...")
            data = json.loads(content)
            save_secrets(data) # Immediately encrypt it
            return data

        # Otherwise, assume it's encrypted
        return security_officer.decrypt_payload(content)
    except Exception as e:
        logger.error(f"DECRYPTION FAILURE: {e}")
        return {}

def save_secrets(data):
    """SECURE SAVER: Encrypts before writing"""
    try:
        encrypted_string = security_officer.encrypt_payload(data)
        os.makedirs(os.path.dirname(SECRETS_PATH), exist_ok=True)
        with open(SECRETS_PATH, 'w') as f:
            f.write(encrypted_string)
        return True
    except Exception as e:
        logger.error(f"ENCRYPTION FAILURE: {e}")
        return False

# --- 5. CORE LOGIC ---
def execute_mission():
    logger.info("MANUAL/AUTO OVERRIDE INITIATED...")
    targets = load_json(CONFIG_PATH)
    secrets = load_secrets() # <--- USE SECURE LOAD

    if not targets.get('operatives'):
        logger.error("INTEL FAILURE: No targets.")
        return

    comms = MicrosoftConnector(logger, secrets)
    comms.authenticate()

    if comms.connected:
        for op in targets['operatives']:
            logger.info(f"TARGET ACQUIRED: {op['email']}")
            comms.send_dispatch(op['email'], "EMAIL_ALERT")
            comms.send_dispatch(op['email'], "TEAMS_MESSAGE")
        logger.info("PROTOCOL EXECUTED SUCCESSFULLY.")
    else:
        logger.error("ABORT: SMTP Connection Failed.")

def load_schedule_logic():
    c = load_json(CONFIG_PATH)
    t = c.get('mission_config', {}).get('trigger_time')
    if t:
        try:
            h, m = t.split(':')
            scheduler.add_job(execute_mission, 'cron', hour=h, minute=m, id=JOB_ID, replace_existing=True)
            logger.info(f"TIMER ARMED. Target Time: {t}")
        except: pass

# --- 6. API ENDPOINTS ---
@app.get("/", response_class=HTMLResponse)
async def read_dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/trigger")
async def trigger_mission(bt: BackgroundTasks):
    bt.add_task(execute_mission)
    return {"status": "Execution Initiated"}

@app.get("/api/logs")
async def get_logs():
    try:
        if not os.path.exists(LOG_PATH): return {"logs": ["System initializing..."]}
        with open(LOG_PATH, "r") as f: return {"logs": f.readlines()[-20:]}
    except: return {"logs": ["Waiting for logs..."]}

@app.get("/api/targets")
async def get_targets():
    data = load_json(CONFIG_PATH)
    return {"operatives": data.get('operatives', [])}

@app.post("/api/targets")
async def add_target(t: NewTarget):
    c = load_json(CONFIG_PATH)
    if 'operatives' not in c: c['operatives'] = []
    c['operatives'].append({"name": t.name, "email": t.email})
    save_json(CONFIG_PATH, c)
    return {"status": "success"}

@app.get("/api/config")
async def get_config(): return load_json(CONFIG_PATH).get('mission_config', {})

@app.post("/api/config")
async def update_config(d: ConfigUpdate):
    c = load_json(CONFIG_PATH)
    if 'mission_config' not in c: c['mission_config'] = {}
    c['mission_config']['trigger_time'] = d.trigger_time
    save_json(CONFIG_PATH, c)
    try:
        h, m = d.trigger_time.split(':')
        scheduler.add_job(execute_mission, 'cron', hour=h, minute=m, id=JOB_ID, replace_existing=True)
    except: pass
    return {"status": "success"}

@app.get("/api/settings")
async def get_settings():
    secrets = load_secrets() # <--- USE SECURE LOAD
    if secrets.get("EMAIL_PASS"):
        secrets["EMAIL_PASS"] = "********"
    return secrets

@app.post("/api/settings")
async def update_settings(d: SecretsUpdate):
    secrets = {"EMAIL_USER": d.email_user, "EMAIL_PASS": d.email_pass, "SMTP_SERVER": d.smtp_server, "SMTP_PORT": str(d.smtp_port)}
    save_secrets(secrets) # <--- USE SECURE SAVE
    logger.info("SECURITY CLEARANCE UPDATED (ENCRYPTED).")
    return {"status": "success"}

# --- 7. LAUNCHER PROTOCOL ---
def start_server():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")

if __name__ == "__main__":
    api_thread = threading.Thread(target=start_server, daemon=True)
    api_thread.start()

    webview.create_window(
        "DISPATCH CENTRAL",
        "http://127.0.0.1:8000",
        width=1200,
        height=800,
        background_color='#0a0a0a',
        resizable=True
    )
    webview.start()
