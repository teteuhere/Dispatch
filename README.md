# DISPATCH // CENTRAL COMMAND

![Status](https://img.shields.io/badge/STATUS-OPERATIONAL-success?style=for-the-badge)
![Security](https://img.shields.io/badge/SECURITY-ENCRYPTED-blue?style=for-the-badge)
![Platform](https://img.shields.io/badge/PLATFORM-NATIVE_DESKTOP-orange?style=for-the-badge)

**Dispatch** is a tactical automated communication system designed to execute scheduled protocols (Email/Teams) from a secure, native desktop interface. It features a stealth "Dark Mode" dashboard, Fernet-grade encryption for credentials, and automated H-Hour scheduling.

> **System Update:** This unit has been upgraded from a containerized web service to a standalone Desktop Application (GTK/WebView). Docker is no longer required for operation.

---

## 📂 Operational Structure

```text
Dispatch/
├── config/             # Mission Data (Auto-Generated)
│   ├── targets.json    # Operatives, Schedule, & Message Content
│   ├── secrets.json    # ENCRYPTED Credentials (AES/Fernet)
│   └── master.key      # Encryption Key (DO NOT DELETE)
├── logs/               # Persistent Telemetry
├── scripts/            # Factory Scripts
│   ├── build_linux.sh  # Compiles Binary for Linux
│   └── build_exe.sh    # Cross-Compiles .exe for Windows (via Docker)
├── src/
│   ├── frontend/       # HTML/JS Dashboard (PT-BR Localized)
│   └── dispatch/       # Core Logic
│       ├── api/        # SMTP & Connectors
│       ├── utils/      # Security & Logging
│       └── server.py   # Main Engine (FastAPI + PyWebView)
└── requirements.txt    # Python Dependencies

```

---

## 🚀 Deployment Protocols

### Option A: Linux (Native Binary)

*Recommended for your local kernel (`theo@kernel`).*

1. **Compile the Asset:**
```bash
chmod +x scripts/build_linux.sh
./scripts/build_linux.sh

```


2. **Execute:**
Run the binary directly. It will launch a secure window.
```bash
./dist/dispatch

```



### Option B: Windows Executable (.exe)

*Recommended for field agents on Windows.*

1. **Build the Artifact:**
We use a Dockerized PyInstaller to cross-compile from Linux to Windows.
```bash
chmod +x scripts/build_exe.sh
./scripts/build_exe.sh

```


2. **Deploy:**
* Take `dist/dispatch.exe`.
* Run it anywhere. No installation required.



### Option C: Developer Mode (Source)

*For making modifications to the mainframe.*

```bash
# Activate Environment
source .venv/bin/activate

# Launch directly
python src/dispatch/server.py

```

---

## 🕹️ Dashboard Controls

The interface is fully localized in **Portuguese (PT-BR)** and runs in a dedicated window (no browser required).

* **⚙️ Settings (Configurações):**
* Click the **Gear Icon**.
* Enter your Gmail/SMTP credentials.
* *Security Note:* Credentials are automatically **Encrypted** and saved to `config/secrets.json`.


* **📄 Protocol (Protocolo):**
* Click the **Document Icon**.
* Set the **Subject** (Assunto) and **Body** (Mensagem) for the dispatch.
* HTML formatting is applied automatically to bypass spam filters.


* **Next Execution (Próxima Execução):**
* Click "Editar Horário" to change the H-Hour (Format: 24h `HH:MM`).


* **Target Manifest:**
* Manage your list of operatives. Changes save instantly to `config/targets.json`.



---

## 🔐 Security Protocols

This system uses **Fernet Symmetric Encryption** to protect your credentials.

1. **Encryption:** When you save passwords in the UI, the system generates a `config/master.key` and encrypts `secrets.json`.
2. **The Key:** The `master.key` is the only way to decrypt your data. **If you lose this file, you lose your saved passwords.**
3. **Git Safety:** The `.gitignore` is configured to block `secrets.json` and `master.key` to prevent accidental leaks.

---

## 🛠️ Configuration Files

### `targets.json`

Stores the mission parameters. Can be edited via the Dashboard.

```json
{
    "mission_config": {
        "trigger_time": "20:30",
        "subject": "Lembrete Operacional",
        "body": "Favor fechar as planilhas."
    },
    "operatives": [
        { "name": "Miguel", "email": "miguel@2099.com" }
    ]
}

```

---

> *"The future isn't written. It's dispatched."*
