import os
import sys
import json
import uvicorn
import logging
from datetime import datetime
from dotenv import load_dotenv

from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from apscheduler.schedulers.background import BackgroundScheduler
from pydantic import BaseModel

# Local imports
from utils.logger import setup_logger
from api.connector import MicrosoftConnector

# --- 1. PATH & SETUP ---
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

env_path = os.path.join(application_path, '.env')
load_dotenv(dotenv_path=env_path, override=True)

CONFIG_PATH = os.path.join(application_path, "config", "targets.json")

app = FastAPI()
logger = setup_logger()
scheduler = BackgroundScheduler()
scheduler.start()

JOB_ID = 'mission_trigger' # Tag for the scheduler job

# --- 2. RESOURCE LOCATOR ---
def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

frontend_path = get_resource_path("src/frontend")
app.mount("/static", StaticFiles(directory=frontend_path), name="static")
templates = Jinja2Templates(directory=frontend_path)

# --- 3. INTEL MANAGEMENT ---
class NewTarget(BaseModel):
    name: str
    email: str

class ConfigUpdate(BaseModel):
    trigger_time: str

def load_intel():
    try:
        if not os.path.exists(CONFIG_PATH):
             # Fallback for Dev
             return json.load(open("config/targets.json"))
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"CONFIG ERROR: {e}")
        return None

def save_intel(data):
    try:
        write_path = CONFIG_PATH
        if not os.path.exists(os.path.dirname(CONFIG_PATH)):
            write_path = "config/targets.json"
        with open(write_path, 'w') as f:
            json.dump(data, f, indent=4)
        return True
    except Exception as e:
        logger.error(f"SAVE ERROR: {e}")
        return False

# --- 4. CORE LOGIC ---
def execute_mission():
    logger.info("MANUAL/AUTO OVERRIDE INITIATED. Executing Protocol...")
    config = load_intel()
    if not config:
        logger.error("INTEL FAILURE: Config missing.")
        return

    comms = MicrosoftConnector(logger)
    comms.authenticate()

    if comms.connected:
        for operative in config['operatives']:
            email = operative['email']
            logger.info(f"TARGET ACQUIRED: {email}")
            comms.send_dispatch(email, "EMAIL_ALERT")
            comms.send_dispatch(email, "TEAMS_MESSAGE")
        logger.info("PROTOCOL EXECUTED SUCCESSFULLY.")
    else:
        logger.error("ABORT: SMTP Connection Failed.")

# --- 5. API ENDPOINTS ---
@app.get("/", response_class=HTMLResponse)
async def read_dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/trigger")
async def trigger_mission(background_tasks: BackgroundTasks):
    background_tasks.add_task(execute_mission)
    return {"status": "Execution Initiated", "timestamp": datetime.now()}

@app.get("/api/logs")
async def get_logs():
    try:
        log_path = os.path.join(application_path, "logs", "mission_log.log")
        if not os.path.exists(log_path): log_path = "logs/mission_log.log"
        with open(log_path, "r") as f:
            lines = f.readlines()[-20:]
            return {"logs": lines}
    except:
        return {"logs": ["System initializing...", "Waiting for logs..."]}

@app.get("/api/targets")
async def get_targets():
    config = load_intel()
    return {"operatives": config.get('operatives', [])} if config else {"operatives": []}

@app.post("/api/targets")
async def add_target(target: NewTarget):
    config = load_intel()
    if not config: raise HTTPException(status_code=500, detail="Config not found")

    for op in config['operatives']:
        if op['email'] == target.email:
             raise HTTPException(status_code=400, detail="Operative already exists")

    config['operatives'].append({"name": target.name, "email": target.email})

    if save_intel(config):
        logger.info(f"NEW RECRUIT ADDED: {target.email}")
        return {"status": "success", "operative": target}
    else:
        raise HTTPException(status_code=500, detail="Failed to save intel")

# [NEW] GET CONFIG
@app.get("/api/config")
async def get_config():
    config = load_intel()
    return config['mission_config'] if config else {}

# [NEW] UPDATE TIME
@app.post("/api/config")
async def update_config(data: ConfigUpdate):
    # Validate format
    try:
        datetime.strptime(data.trigger_time, "%H:%M")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid time format. Use HH:MM")

    config = load_intel()
    if not config: raise HTTPException(status_code=500, detail="Config not found")

    # Update Json
    config['mission_config']['trigger_time'] = data.trigger_time

    if save_intel(config):
        # Update Scheduler
        try:
            h, m = data.trigger_time.split(':')
            scheduler.add_job(execute_mission, 'cron', hour=h, minute=m, id=JOB_ID, replace_existing=True)
            logger.info(f"TIMER UPDATED: {data.trigger_time}")
            return {"status": "success", "trigger_time": data.trigger_time}
        except Exception as e:
             logger.error(f"SCHEDULER ERROR: {e}")
             raise HTTPException(status_code=500, detail="Scheduler update failed")
    else:
        raise HTTPException(status_code=500, detail="Save failed")

# --- STARTUP ---
@app.on_event("startup")
def load_schedule():
    config = load_intel()
    if config:
        t_time = config['mission_config']['trigger_time']
        try:
            h, m = t_time.split(':')
            # Use replace_existing to allow updates
            scheduler.add_job(execute_mission, 'cron', hour=h, minute=m, id=JOB_ID, replace_existing=True)
            logger.info(f"TIMER ARMED. Target Time: {t_time}")
        except: pass

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
