import psutil
from typing import Any, Dict, List, Optional


def list_processes() -> List[Dict[str, Any]]:
    return [
        {"pid": p.info.get("pid"), "name": p.info.get("name"), "user": p.info.get("username")}
        for p in psutil.process_iter(attrs=["pid", "name", "username"])
    ]


def kill_process(pid: int) -> str:
    try:
        proc = psutil.Process(pid)
        proc.terminate()
        proc.wait(5)
        return "terminated"
    except psutil.NoSuchProcess:
        return "no such process"
    except psutil.TimeoutExpired:
        proc.kill()
        return "killed"
    except Exception as exc:  # noqa: BLE001
        return f"error: {exc}"


def handle_process(action: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    payload = payload or {}
    if action == "list_processes":
        return {"status": "ok", "data": list_processes()}
    if action == "kill_process":
        return {"status": "ok", "data": kill_process(int(payload.get("pid", -1)))}
    return {"status": "error", "data": f"unknown process action {action}"}
