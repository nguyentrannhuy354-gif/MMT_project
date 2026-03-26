import subprocess
from typing import Any, Dict, List, Optional

import psutil


def list_apps() -> List[Dict[str, Any]]:
    return [
        {"pid": p.info.get("pid"), "name": p.info.get("name"), "user": p.info.get("username")}
        for p in psutil.process_iter(attrs=["pid", "name", "username"])
    ]


def start_app(command: str) -> str:
    if not command:
        return "error: empty command"
    try:
        subprocess.Popen(command, shell=True)
        return "started"
    except Exception as exc:  # noqa: BLE001
        return f"error: {exc}"


def stop_app(name: str) -> str:
    if not name:
        return "error: empty name"
    stopped = 0
    for proc in psutil.process_iter(attrs=["name"]):
        try:
            if proc.info.get("name", "").lower() == name.lower():
                proc.terminate()
                stopped += 1
        except Exception:
            continue
    if stopped == 0:
        return "no matching app"
    return f"stopped {stopped} instance(s)"


def handle_app(action: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    payload = payload or {}
    if action == "list_apps":
        return {"status": "ok", "data": list_apps()}
    if action == "start_app":
        return {"status": "ok", "data": start_app(payload.get("command", ""))}
    if action == "stop_app":
        return {"status": "ok", "data": stop_app(payload.get("name", ""))}
    return {"status": "error", "data": f"unknown app action {action}"}
