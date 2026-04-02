Remote PC Control (Python, modular)

Features
- List / start / stop applications
- List / kill processes
- Length‑prefixed JSON protocol that’s easy to extend with new feature modules

Project structure
project/

├── client.py         # controller UI (CLI)

├── server.py         # controlled machine

└── features/  ├── app_manager.py, process_manager.py

Requirements
- Python 3.8+
- Dependencies: psutil (install below). mss only if you later add screenshots.

Setup
python3 -m pip install --upgrade psutil

Running (VS Code or any shell)
Open two terminals:

Terminal 1 – start server (on the controlled machine):
python3 server.py

Terminal 2 – start client (controller):
python3 client.py

When prompted for the server IP:
- Same machine: 127.0.0.1
- Different machines on LAN: server’s IPv4 (e.g., from ipconfig on Windows or ipconfig getifaddr en0 on macOS).
- Ensure the firewall allows TCP port 12345

Usage (client menu)
1) List processes
2) Kill process (enter PID)
3) List apps
4) Start app (enter command)
5) Stop app (by process name)
x) Exit

Tabular output is shown for lists; errors are clearly reported.

Protocol (brief)
- Transport: TCP
- Message: 4‑byte big‑endian length prefix + UTF‑8 JSON
- Request: { "action": "...", ... }
- Response: { "status": "ok" | "error", "data": ... }


Extending
- Add a new file under features/ with a handle_<name>(action, payload) function.
- Import and route it in server.py’s dispatch logic.

Notes
- No authentication/TLS included; add both for real deployments.
- Run the server with sufficient permissions for starting/stopping apps where required.
