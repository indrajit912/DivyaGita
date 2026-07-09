# Local Production Deployment Guide for Windows

This document provides a comprehensive plan for hosting and deploying **DivyaGita** (and other Flask applications) as a persistent local service on a **Windows** machine.

---

## 1. Deployment Architecture Overview

Local development servers (`flask run` / Werkzeug) are single-threaded by default, slow, and not designed to handle concurrency or system crashes. For a persistent, production-like setup, we use:

```
+--------------------+
|  Windows Operating |   [System Boot / User Login Event]
|       System       |-----------------+
+--------------------+                 |
          |                            v
          |                 +--------------------+
          |                 |    Windows Task    |
          |                 |     Scheduler      |
          |                 +--------------------+
          |                            |
          v                            v  (starts runner)
+--------------------------------------------------------+
|                      DivyaGita                         |
|  +--------------------------------------------------+  |
|  |             Waitress WSGI Server                 |  |
|  |     - Pure Python                                |  |
|  |     - Native Windows support                     |  |
|  |     - Multi-threaded (8 concurrent threads)      |  |
|  |     - Binds to 127.0.0.1:5000                    |  |
|  +--------------------------------------------------+  |
|                          |                             |
|                          v                             |
|  +--------------------------------------------------+  |
|  |              Flask Application                   |  |
|  |     - Production Config                          |  |
|  |     - SQLAlchemy SQLite instance                 |  |
|  +--------------------------------------------------+  |
+--------------------------------------------------------+
```

### Why Waitress?
- **Native Windows Compatibility:** Gunicorn and uWSGI rely on Unix-specific features (like `fork()` system calls) and cannot run natively on Windows. Waitress is a pure-python, production-grade WSGI server built to work seamlessly on both Windows and Unix.
- **Concurrency:** Uses a multi-threaded architecture (defaulting to 8 threads) to process concurrent requests, preventing long-running requests from blocking other users.
- **Robustness:** Isolates connection buffering and HTTP validation from the Flask application code.

---

## 2. Prerequisites & Software Requirements

1. **Python 3.14+** installed and added to the system `PATH`.
2. **Administrator Command Prompt or PowerShell** for service configuration.
3. Dependencies installed in the virtual environment.

---

## 3. Step-by-Step Installation & Configuration

### Step 1: Install Dependencies
Open PowerShell inside `C:\Users\indra\Documents\hello_world\divyagita` and run:
```powershell
# 1. Activate the environment
.venv\Scripts\Activate.ps1

# 2. Upgrade pip and install requirements (including waitress)
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 2: Initialize Database and Secrets
Ensure the database and migration schemas are compiled:
```powershell
flask db upgrade
flask setup-db
```
The command automatically seeds the chapters and verses while creating the default `.env` configuration file.

---

## 4. Commands to Control the Application

### Start Manually with Waitress
To run the server manually in production mode:
```powershell
.venv\Scripts\python run_production.py
```

### Stop the Server
Press `Ctrl + C` in the terminal window to terminate. If running as a background task, retrieve and terminate by PID (see Section 6).

---

## 5. Configuring Automatic Startup on Windows

We recommend **Windows Task Scheduler** for developer machines because it runs out-of-the-box, requires no third-party installers, and can execute scripts silently in the background at startup.

### Configuration via Task Scheduler (GUI)
1. Press `Win + R`, type `taskschd.msc`, and press **Enter**.
2. In the right panel, click **Create Task...** (do not use "Basic Task").
3. **General Tab:**
   - **Name:** `DivyaGita Service`
   - **User Account:** Select your current user.
   - Select **Run only when user is logged on** (simplest for accessing user resources) or **Run whether user is logged on or not** (runs silently as a system daemon).
4. **Triggers Tab:**
   - Click **New...**
   - Set **Begin the task:** to **At log on** (recommended) or **At startup**.
   - Click **OK**.
5. **Actions Tab:**
   - Click **New...**
   - **Action:** Start a program.
   - **Program/script:** `powershell.exe`
   - **Add arguments:** `-WindowStyle Hidden -Command "& 'C:\Users\indra\Documents\hello_world\divyagita\.venv\Scripts\python.exe' 'C:\Users\indra\Documents\hello_world\divyagita\run_production.py'"`
   - **Start in:** `C:\Users\indra\Documents\hello_world\divyagita`
   - Click **OK**.
6. **Conditions Tab:**
   - Uncheck **Start the task only if the computer is on AC power**.
7. **Settings Tab:**
   - Uncheck **Stop the task if it runs longer than**.
   - Click **OK** to save the task.

### Alternative: Windows Service using NSSM (Non-Sucking Service Manager)
If you require a true Windows System Service that is managed via the Services console (`services.msc`):
1. Download NSSM from [nssm.cc](https://nssm.cc) and add it to your path.
2. Open an Admin Command Prompt and run:
   ```cmd
   nssm install DivyaGitaService
   ```
3. In the GUI panel that opens:
   - **Path:** `C:\Users\indra\Documents\hello_world\divyagita\.venv\Scripts\python.exe`
   - **Startup directory:** `C:\Users\indra\Documents\hello_world\divyagita`
   - **Arguments:** `run_production.py`
4. Click **Install service**. Start the service via:
   ```cmd
   net start DivyaGitaService
   ```

---

## 6. How to Monitor Port Usage

To identify which port your application is using or to locate conflicting services running on the machine, use these PowerShell commands.

### Find Process using a specific Port (e.g. 5000)
```powershell
Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue | 
    Select-Object LocalAddress, LocalPort, State, OwningProcess | 
    Format-Table -AutoSize
```

### Map the OwningProcess PID to a Program Name
If the command above returns PID `1234`, find the application name using:
```powershell
Get-Process -Id 1234
```

### Kill a blocking service on a Port
If you need to free up a port, terminate the process by PID:
```powershell
Stop-Process -Id 1234 -Force
```

---

## 7. How to Update or Uninstall the Application

### Deploying Updates
1. Stop the active task/service:
   ```powershell
   # If using NSSM
   nssm stop DivyaGitaService
   ```
2. Pull the latest code via git:
   ```bash
   git pull origin main
   ```
3. Update package dependencies and migrate databases:
   ```powershell
   .venv\Scripts\python -m pip install -r requirements.txt
   flask db upgrade
   ```
4. Restart the service:
   ```powershell
   nssm start DivyaGitaService
   ```

### Clean Uninstallation
1. Stop and delete the Windows service/task:
   ```cmd
   nssm remove DivyaGitaService confirm
   ```
   *(Or delete `DivyaGita Service` from the Task Scheduler library).*
2. Delete the application directory:
   ```powershell
   Remove-Item -Recurse -Force C:\Users\indra\Documents\hello_world\divyagita
   ```

---

## 8. Logging, Monitoring & Troubleshooting

- **Access Console Output:** When running via Task Scheduler as a hidden window, direct standard output to a file inside `run_production.py` or within NSSM's **I/O** redirect tab (set stdout to `C:\Users\indra\Documents\hello_world\divyagita\logs\stdout.log`).
- **Debugging SQLite Lockups:** If you encounter `sqlite3.OperationalError: database is locked`, ensure that:
  - There are no duplicate background processes accessing the DB file.
  - Transactions are committed and closed properly in your routes.
- **Viewing Windows Event Viewer:** Check `Windows Logs -> Application` for logs concerning NSSM or Task Scheduler execution failures.

---

## 9. Local Security Best Practices

1. **Bind to Localhost only:** By default, `run_production.py` binds to `127.0.0.1`. Do not change this to `0.0.0.0` unless you explicitly want other devices on your local network (Wi-Fi/LAN) to access the application.
2. **Environment Variable Security:** Never commit your `.env` file containing secret keys to git. Ensure it is excluded in `.gitignore`.
3. **Session Cookie Parameters:** In production configs, ensure `SESSION_COOKIE_HTTPONLY=True` is set to block cross-site scripting (XSS) attacks from accessing session IDs.

---

## 10. Multi-App Hosting Strategy (Running Multiple Flask Apps)

When hosting multiple Flask web applications (e.g. `DivyaGita`, `ExpenseWise`) on a single Windows machine, observe these design rules to maintain order and prevent service overlaps:

### 1. Unique Port Allocation
Assign a static, dedicated port range for your local applications. For example:
- `DivyaGita`: Port `5000`
- `ExpenseWise`: Port `5001`
- `TaskTracker`: Port `5002`

Set this port explicitly in each application's `.env` configuration file:
```dotenv
PORT=5001
```

### 2. Service Naming Conventions
Use clear, scoped names for Windows Services or Scheduled Tasks:
- Task/Service Name: `Dev_DivyaGita_Service`
- Task/Service Name: `Dev_ExpenseWise_Service`

### 3. Isolated Virtual Environments
Never share virtual environments. Keep a `.venv` directory inside each project folder. This prevents library version conflicts (e.g., App A requires SQLAlchemy 2.0 while App B requires SQLAlchemy 1.4).

```text
C:\Users\indra\Documents\hello_world\
├── divyagita\
│   ├── .venv\        # Python Env A
│   └── run_production.py (binds to 5000)
│
└── expensewise\
    ├── .venv\        # Python Env B
    └── run_production.py (binds to 5001)
```

### 4. Consolidated Logs Directory
To monitor all local background services at a glance, redirect output logs to a structured logs folder inside each project:
- `C:\Users\indra\Documents\hello_world\divyagita\logs\stdout.log`
- `C:\Users\indra\Documents\hello_world\expensewise\logs\stdout.log`

---

## 11. Enabling Access from Other Devices on the Local Network (LAN/Wi-Fi)

To access your deployed DivyaGita web application from other devices (like smartphones, tablets, or other laptops) on the same Wi-Fi/local area network:

### 1. Verification of Host Binding
Ensure `run_production.py` binds to `0.0.0.0`. In the updated configuration, it reads the `HOST` variable from the environment or defaults to `0.0.0.0` (which listens to all network adapters).

### 2. Find the Host Machine's Local IP Address
To find your Windows laptop's IP address on the local network:
- **PowerShell:**
  ```powershell
  Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.254.*" -and $_.InterfaceAlias -notlike "*Loopback*" } | Select-Object IPAddress, InterfaceAlias
  ```
- **Command Prompt:** Run `ipconfig` and find the `IPv4 Address` under your active connection adapter (e.g., `Wireless LAN adapter Wi-Fi` or `Ethernet adapter`). It typically looks like `192.168.x.x` or `10.x.x.x`.

### 3. Open Windows Defender Firewall
Windows Firewall blocks inbound connections on custom ports by default. Run this PowerShell command **as Administrator** to create a rule allowing traffic on port `5000`:

```powershell
New-NetFirewallRule -DisplayName "Allow DivyaGita Local Access" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
```
*(If you host other apps on different ports, e.g., `5001`, create separate rules or specify a port range `-LocalPort 5000-5005`).*

### 4. Connect from Other Devices
1. Ensure the other device is connected to the **same Wi-Fi router / local network** as your Windows laptop.
2. Open a web browser on the other device.
3. Enter the URL: `http://<YOUR_LAPTOP_IP>:5000` (for example, `http://192.168.1.15:5000`).
