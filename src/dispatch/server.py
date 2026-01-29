import os
import sys
import json
import uvicorn
import logging
import threading
import webview
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from apscheduler.schedulers.background import BackgroundScheduler
from pydantic import BaseModel

from utils.logger import setup_logger
from utils.security import IntelSecurity
from api.connector import MicrosoftConnector

# --- 1. PATH RECALIBRATION ---
if getattr(sys, 'frozen', False):
    PROJECT_ROOT = os.path.dirname(sys.executable)
else:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.abspath(os.path.join(script_dir, "..", ".."))

if not os.path.exists(os.path.join(PROJECT_ROOT, "config")):
    PROJECT_ROOT = os.getcwd()

CONFIG_PATH = os.path.join(PROJECT_ROOT, "config", "targets.json")
SECRETS_PATH = os.path.join(PROJECT_ROOT, "config", "secrets.json")
KEY_PATH = os.path.join(PROJECT_ROOT, "config", "master.key")
LOG_PATH = os.path.join(PROJECT_ROOT, "logs", "mission_log.log")

os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
logger = setup_logger()
security_officer = IntelSecurity(KEY_PATH)

scheduler = BackgroundScheduler()
JOB_ID = 'mission_trigger'

@asynccontextmanager
async def lifespan(app: FastAPI):
    if os.path.exists(CONFIG_PATH):
        load_schedule_logic()
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)

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

# --- UPDATED DATA MODELS ---
class NewTarget(BaseModel):
    name: str
    email: str

# UPDATED: Now includes Subject and Body
class ConfigUpdate(BaseModel):
    trigger_time: str
    email_subject: str
    email_body: str

class SecretsUpdate(BaseModel):
    email_user: str
    email_pass: str
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587

# --- HELPERS ---
def load_json(path):
    try:
        if not os.path.exists(path): return {}
        with open(path, 'r') as f: return json.load(f)
    except: return {}

def save_json(path, data):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f: json.dump(data, f, indent=4)
        return True
    except: return False

def load_secrets():
    if not os.path.exists(SECRETS_PATH): return {}
    try:
        with open(SECRETS_PATH, 'r') as f: content = f.read()
        if content.strip().startswith('{'):
            data = json.loads(content)
            save_secrets(data)
            return data
        return security_officer.decrypt_payload(content)
    except: return {}

def save_secrets(data):
    try:
        encrypted = security_officer.encrypt_payload(data)
        os.makedirs(os.path.dirname(SECRETS_PATH), exist_ok=True)
        with open(SECRETS_PATH, 'w') as f: f.write(encrypted)
        return True
    except: return False

def execute_mission():
    logger.info("MANUAL/AUTO OVERRIDE INITIATED...")
    targets = load_json(CONFIG_PATH)
    secrets = load_secrets()

    if not targets.get('operatives'):
        logger.error("INTEL FAILURE: No targets.")
        return

    mission_config = targets.get('mission_config', {})

    subject = mission_config.get('subject', 'AVISO DE SISTEMA')
    body = mission_config.get('body', 'Nenhuma mensagem configurada no despacho.')

    comms = MicrosoftConnector(logger, secrets)
    comms.authenticate()

    if comms.connected:
        for op in targets['operatives']:
            logger.info(f"TARGET ACQUIRED: {op['email']}")

            comms.send_dispatch(op['email'], "EMAIL_ALERT", subject, body)
            comms.send_dispatch(op['email'], "TEAMS_MESSAGE", subject, body)

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
            logger.info(f"TIMER ARMED. Target: {t}")
        except: pass

# --- API ENDPOINTS ---
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
    return {"operatives": load_json(CONFIG_PATH).get('operatives', [])}

@app.post("/api/targets")
async def add_target(t: NewTarget):
    c = load_json(CONFIG_PATH)
    if 'operatives' not in c: c['operatives'] = []
    c['operatives'].append({"name": t.name, "email": t.email})
    save_json(CONFIG_PATH, c)
    return {"status": "success"}

@app.get("/api/config")
async def get_config():
    # Return defaults if keys missing
    conf = load_json(CONFIG_PATH).get('mission_config', {})
    if 'subject' not in conf: conf['subject'] = "ALERTA DE SEGURANÇA"
    if 'body' not in conf: conf['body'] = "Por favor, feche a planilha."
    return conf

@app.post("/api/config")
async def update_config(d: ConfigUpdate):
    c = load_json(CONFIG_PATH)
    if 'mission_config' not in c: c['mission_config'] = {}

    # Save Time, Subject, and Body
    c['mission_config']['trigger_time'] = d.trigger_time
    c['mission_config']['subject'] = d.email_subject
    c['mission_config']['body'] = d.email_body

    save_json(CONFIG_PATH, c)

    try:
        h, m = d.trigger_time.split(':')
        scheduler.add_job(execute_mission, 'cron', hour=h, minute=m, id=JOB_ID, replace_existing=True)
    except: pass
    return {"status": "success"}

@app.get("/api/settings")
async def get_settings():
    secrets = load_secrets()
    if secrets.get("EMAIL_PASS"): secrets["EMAIL_PASS"] = "********"
    return secrets

@app.post("/api/settings")
async def update_settings(d: SecretsUpdate):
    secrets = {"EMAIL_USER": d.email_user, "EMAIL_PASS": d.email_pass, "SMTP_SERVER": d.smtp_server, "SMTP_PORT": str(d.smtp_port)}
    save_secrets(secrets)
    logger.info("SECURITY CLEARANCE UPDATED.")
    return {"status": "success"}

def start_server():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")

if __name__ == "__main__":
    api_thread = threading.Thread(target=start_server, daemon=True)
    api_thread.start()
    webview.create_window("DISPATCH CENTRAL", "http://127.0.0.1:8000", width=1200, height=800, background_color='#0a0a0a', resizable=True)
    webview.start()
