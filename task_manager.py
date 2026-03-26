"""
Task manager feature: list/start/stop apps and processes.
Relies on psutil when available; otherwise falls back to subprocess for starting only.
"""

import subprocess
from typing import Any, Dict, List, Optional

try:
    import psutil  # type: ignore
except Exception:
    psutil = None


def list_processes() -> List[Dict[str, Any]]:
    if psutil is None:
        return [{"error": "psutil not installed"}]
    result: List[Dict[str, Any]] = []
    for proc in psutil.process_iter(attrs=["pid", "name", "username"]):
        info = proc.info
        result.append(
            {
                "pid": info.get("pid"),
                "name": info.get("name"),
                "user": info.get("username"),
            }
        )
    return result


def start_app(command: str) -> str:
    if not command:
        return "error: empty command"
    try:
        subprocess.Popen(command, shell=True)
        return "started"
    except Exception as exc:  # noqa: BLE001
        return f"error: {exc}"


def kill_process(pid: int) -> str:
    if psutil is None:
        return "psutil not installed"
    try:
        p = psutil.Process(pid)
        p.terminate()
        p.wait(5)
        return "terminated"
    except psutil.NoSuchProcess:
        return "no such process"
    except psutil.TimeoutExpired:
        p.kill()
        return "killed"
    except Exception as exc:  # noqa: BLE001
        return f"error: {exc}"


def stop_app_by_name(name: str) -> str:
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


def handle_task_command(action: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    payload = payload or {}
    if action == "list_processes":
        return {"status": "ok", "data": list_processes()}
    if action == "start_app":
        return {"status": "ok", "data": start_app(payload.get("command", ""))}
    if action == "kill_process":
        return {"status": "ok", "data": kill_process(int(payload.get("pid", -1)))}
    if action == "list_apps":
        # same as list_processes for now; apps are a subset
        return {"status": "ok", "data": list_processes()}
    if action == "stop_app":
        return {"status": "ok", "data": stop_app_by_name(payload.get("name", ""))}
    return {"status": "error", "data": f"unknown task action {action}"}
