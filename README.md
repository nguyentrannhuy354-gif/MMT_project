Remote PC Control (Python, modular)

Features
- List / start / stop applications
- List / kill processes
- Length‑prefixed JSON protocol (easy to extend with new modules)

Project structure
project/

├── client.py         # controller

├── server.py         # controlled machine

└── features/  ├── app_manager.py, process_manager.py

Requirements
- Python 3.8+
- Dependencies: psutil (install below). mss only if you later add screenshots.

Setup
python3 -m pip install --upgrade psutil
#optional for future screenshot feature
#python3 -m pip install mss

Running (VS Code or any shell)
Open two terminals:

Terminal 1 – start server (on the controlled machine):
python3 server.py

Terminal 2 – start client (controller):
python3 client.py

- If client and server are the same machine: enter 127.0.0.1.
- If different machines on LAN: enter the server’s IPv4 (see ipconfig on Windows or ipconfig getifaddr en0 on macOS).
- Ensure firewall allows TCP port 12345.

Usage (client menu)
1) List processes
2) Kill process (enter PID)
3) List apps
4) Start app (enter command)
5) Stop app (by process name)
x) Exit

Protocol (brief)
- Transport: TCP
- Message: 4‑byte big‑endian length prefix + UTF‑8 JSON
- JSON fields: { "action": "...", ... }
- Server replies: { "status": "ok" | "error", "data": ... }

Extending
- Add a new feature file under features/ with a handle_<name>(action, payload) function.
- Import and route actions in server.py’s dispatch function.

Notes
- No authentication/TLS included; for any real deployment, add both.
- Run server with appropriate permissions if starting/stopping apps requires elevated rights.
