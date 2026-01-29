# SPIDER-OPS // DISPATCH CONTROL

![Status](https://img.shields.io/badge/STATUS-OPERATIONAL-success?style=for-the-badge)
![Security](https://img.shields.io/badge/SECURITY-CLASSIFIED-red?style=for-the-badge)

**Spider-Ops** is a tactical automated dispatch system designed to execute scheduled communication protocols. It features a stealth "Dark Mode" dashboard, automated scheduling (H-Hour), and real-time target management.

---

## 📂 Operational Structure

```text
TeamsIntegration/
├── config/             # Mission Parameters
│   └── targets.json    # List of operatives & H-Hour time
├── logs/               # Persistent Log Storage (Black Box)
├── scripts/            # Deployment Scripts
│   ├── run.sh          # Linux/Docker Launcher
│   └── build_exe.sh    # Windows Executable Builder
├── src/
│   ├── frontend/       # HTML/JS Dashboard (PT-BR Localized)
│   └── teamsintegration/
│       ├── api/        # SMTP & Teams Connectors
│       ├── utils/      # Logging Logic
│       └── server.py   # FastAPI Core & Scheduler
├── .env                # Classified Credentials (GitIgnored)
└── Dockerfile          # Container Blueprint

```

---

## 🚀 Deployment Protocols

### Option A: Docker Container (Linux/Server)

*Recommended for always-on servers (Daemon Mode).*

1. **Configure Credentials:**
Create a `.env` file in the root directory:
```properties
EMAIL_USER=your_email@gmail.com
EMAIL_PASS=your_app_password_here
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

```


2. **Deploy:**
Execute the deployment script. This will build the image and start the container in detached mode with persistent storage.
```bash
chmod +x scripts/run.sh
./scripts/run.sh

```


3. **Access:**
Open your browser to: `http://localhost:8000`

### Option B: Windows Executable (.exe)

*Recommended for portable use on client machines.*

1. **Build the Artifact:**
We use a Dockerized PyInstaller to cross-compile from Linux to Windows.
```bash
chmod +x scripts/build_exe.sh
./scripts/build_exe.sh

```


*Result:* The file `spider-ops-server.exe` will appear in the `dist/` folder.
2. **Installation on Windows:**
* Create a folder (e.g., `C:\SpiderOps`).
* Copy `spider-ops-server.exe` to that folder.
* Copy your `.env` file to that folder.
* Create a `logs` folder inside.


3. **Run:**
Double-click the `.exe`. The dashboard will be available at `http://localhost:8000`.

---

## 🕹️ Dashboard Controls

The interface is fully localized in **Portuguese (PT-BR)** and features a "Sysadmin" aesthetic.

* **Next Execution (Próxima Execução):** Displays the scheduled H-Hour.
* *Edit:* Click "Editar Horário" to change the daily trigger time (Format: 24h `HH:MM`).


* **Force Execution (Forçar Execução):** Manually triggers the dispatch protocol immediately.
* **Target Manifest (Manifesto de Alvos):** Real-time list of recipients.
* *Add Target:* Click to recruit a new operative (saves to `targets.json` instantly).


* **System Log:** Live telemetry stream. Logs are saved to `logs/mission_log.log` and persist across reboots.

---

## 🛠️ Configuration

### `targets.json`

Located in `config/targets.json`. Can be edited via the Dashboard or manually.

```json
{
    "mission_config": {
        "trigger_time": "20:30",
        "timezone_offset": -3
    },
    "operatives": [
        {
            "name": "Agent Miguel",
            "email": "miguel@alchemax.com"
        }
    ]
}

```

### Persistence

The `scripts/run.sh` script mounts the host's `logs/` and `config/` directories into the container.

* **Logs:** If you delete the container, your logs remain safe in the `logs/` folder.
* **Config:** Changes made in the dashboard are written to `config/targets.json` on your host disk.

---

## 🔧 Development

**Requirements:**

* Python 3.10+
* Docker

**Manual Start (Dev Mode):**

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/teamsintegration/server.py

```

---

> *"With great power comes great responsibility... and automated logging."*
