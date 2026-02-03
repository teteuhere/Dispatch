# DISPATCH // TACTICAL CLI

**Dispatch Protocol** is a lightweight, headless Command Line Interface (CLI) designed for automated communication operations. It executes mass notifications via **SMTP (Email)** and **Microsoft Graph (Teams DMs)** using a secure, encrypted credential vault.

Designed to be compiled into a `.exe` and triggered by **Windows Task Scheduler** for "set and forget" reliability.

---

## 📂 Operational Structure

The system logic has been stripped down for efficiency. No web servers. No HTML. Just pure logic.

```text
DispatchProtocol/
├── DispatchProtocol.exe   # Compiled Binary (The Trigger)
└── config/                # Intel & Logistics
    ├── header.csv         # Target List (Name, Email)
    ├── body.json          # Mission Payload (Subject, Body)
    ├── secrets.enc        # ENCRYPTED Credentials (AES-128)
    └── master.key         # Decryption Key (REQUIRED)

```

> **⚠️ CRITICAL:** The `.exe` must always be in the same folder as the `config/` directory.

---

## 🔐 Security Protocol (The Vault)

We no longer use plain text `.env` files. We use a **Fernet Symmetric Key** vault.

### 1. Setup Credentials

Before compiling, you must run the setup script to lock your credentials.

```bash
python setup_vault.py

```

You will be prompted to enter:

* **SMTP:** Gmail/Outlook User & App Password.
* **Azure:** Tenant ID, Client ID, Secret (For Teams DMs).

*This generates `config/master.key` and `config/secrets.enc`.*

---

## 🚀 Deployment Instructions

### Phase 1: Configuration (Intel)

1. **Targets (`config/header.csv`):**
Edit this file with Excel or Notepad. Format:
```csv
Name,Email
Miguel O'Hara,miguel@lyla.ai
Peter Parker,peter@dailybugle.com

```


2. **Message (`config/body.json`):**
Set the broadcast content.
```json
{
    "subject": "System Update",
    "body": "Daily report is mandatory. Do not be late."
}

```



### Phase 2: Compilation (Armory)

Run this command on a **Windows** machine to generate the standalone executable.

```bash
pip install -r requirements.txt
pyinstaller --noconfirm --onefile --console --name "DispatchProtocol" --clean src/dispatch/main.py

```

*Artifact located at: `dist/DispatchProtocol.exe*`

### Phase 3: Automation (Field Ops)

To run this automatically every day (e.g., at 20:45):

1. Open **Windows Task Scheduler**.
2. **Create Basic Task** -> Name: "Dispatch Protocol".
3. **Trigger**: Daily @ 20:45.
4. **Action**: Start a Program.
* **Program**: Browse to `DispatchProtocol.exe`.
* **Start in (IMPORTANT):** Paste the full path to the folder containing the exe (e.g., `C:\Ops\Dispatch\`). *If you skip this, it won't find the config files.*



---

## 📡 Capabilities

### 📧 SMTP (Email)

* Standard TLS encryption (Port 587).
* Sends automatically to every email in the CSV.

### 💬 Microsoft Teams (Graph API)

* **Direct Messages:** Uses Azure App Registration to look up the user's Profile ID via their email and sends a private DM.
* **Fallback:** If Azure keys are missing, it logs the attempt internally without crashing.
* **Requirements:**
* Permission: `User.Read.All` (To find the ID).
* Permission: `Chat.Create` & `Chat.ReadWrite` (To send the message).



---

## 🛠️ Developer Mode

To run manually without compiling:

```bash
# 1. Install Dependencies
pip install -r requirements.txt

# 2. Run CLI
python src/dispatch/main.py

```

* **[1] Start Dispatch:** Fires the email/teams loop immediately.
* **[2] Manage Contacts:** Add/Remove people from the CSV via terminal.
* **[3] Check Connection:** Verifies Vault decryption and SMTP login.

---

> *"Radio check complete. Standing by."*
