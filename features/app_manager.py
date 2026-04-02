"""
Feature: List / Start / Stop (by name) applications.
"""

import subprocess
from typing import Any, Dict, List, Optional

try:
    import psutil  # type: ignore
except Exception:
    psutil = None


def list_apps() -> List[Dict[str, Any]]:
    if psutil is None:
        return [{"error": "psutil not installed"}]
    apps: List[Dict[str, Any]] = []
    for proc in psutil.process_iter(attrs=["pid", "name", "username"]):
        info = proc.info
        apps.append(
            {
                "pid": info.get("pid"),
                "name": info.get("name"),
                "user": info.get("username"),
            }
        )
    return apps


def start_app(command: str) -> str:
    if not command:
        return "error: empty command"
    try:
        subprocess.Popen(command, shell=True)
        return "started"
    except Exception as exc:  # noqa: BLE001
        return f"error: {exc}"


def stop_app(name: str) -> str:
    if psutil is None:
        return "psutil not installed"
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