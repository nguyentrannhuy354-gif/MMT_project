"""
Feature: List / Kill processes.
"""

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


def handle_process_command(action: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    payload = payload or {}
    if action == "list_processes":
        return {"status": "ok", "data": list_processes()}
    if action == "kill_process":
        return {"status": "ok", "data": kill_process(int(payload.get("pid", -1)))}
    return {"status": "error", "data": f"unknown process action {action}"}
