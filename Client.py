"""
User-friendly CLI client for the remote control server.
Supports: list processes, kill process, list applications, start/stop applications.
Protocol: length-prefixed JSON over TCP (backend unchanged).
"""

import json
import socket
import struct
from typing import Any, Dict, Iterable, List, Optional, Tuple

SERVER_PORT = 12345
SOCKET_TIMEOUT = 10  # seconds


# ---------- Transport ---------- #
def send_msg(conn: socket.socket, payload: Dict[str, Any]) -> None:
    data = json.dumps(payload).encode("utf-8")
    conn.sendall(struct.pack(">I", len(data)) + data)


def recv_exact(conn: socket.socket, size: int) -> bytes:
    buf = b""
    while len(buf) < size:
        chunk = conn.recv(size - len(buf))
        if not chunk:
            raise ConnectionError("connection closed")
        buf += chunk
    return buf


def recv_msg(conn: socket.socket) -> Dict[str, Any]:
    header = recv_exact(conn, 4)
    (length,) = struct.unpack(">I", header)
    body = recv_exact(conn, length)
    return json.loads(body.decode("utf-8"))


def request(conn: socket.socket, payload: Dict[str, Any]) -> Dict[str, Any]:
    send_msg(conn, payload)
    return recv_msg(conn)


# ---------- UI helpers ---------- #
def print_menu() -> None:
    print(
        """
======== Remote Control Client ========
[1] List processes
[2] Kill process by PID
[3] List applications
[4] Start application
[5] Stop application
[x] Exit
---------------------------------------
"""
    )


def print_table(rows: List[Dict[str, Any]], columns: Iterable[str]) -> None:
    if not rows:
        print("(empty)")
        return
    cols = list(columns)
    widths = {c: len(c) for c in cols}
    for row in rows:
        for c in cols:
            widths[c] = max(widths[c], len(str(row.get(c, ""))))
    header = " | ".join(c.ljust(widths[c]) for c in cols)
    sep = "-+-".join("-" * widths[c] for c in cols)
    print(header)
    print(sep)
    for row in rows:
        print(" | ".join(str(row.get(c, "")).ljust(widths[c]) for c in cols))


def pretty_print(resp: Dict[str, Any], table_cols: Optional[List[str]] = None) -> None:
    status = resp.get("status")
    data = resp.get("data")
    if status != "ok":
        print(f"[ERROR] {data}")
        return
    if isinstance(data, list) and table_cols:
        print_table(data, table_cols)
    else:
        print(data)


# ---------- Feature handlers ---------- #
def list_processes(conn: socket.socket) -> None:
    resp = request(conn, {"action": "list_processes"})
    pretty_print(resp, ["pid", "name", "user"])


def kill_process(conn: socket.socket) -> None:
    pid_str = input("Enter PID to kill: ").strip()
    if not pid_str.isdigit():
        print("[WARN] PID must be a number.")
        return
    resp = request(conn, {"action": "kill_process", "pid": int(pid_str)})
    pretty_print(resp)


def list_apps(conn: socket.socket) -> None:
    resp = request(conn, {"action": "list_apps"})
    pretty_print(resp, ["pid", "name", "user"])


def start_app(conn: socket.socket) -> None:
    cmd = input("Command to start: ").strip()
    if not cmd:
        print("[WARN] Command cannot be empty.")
        return
    resp = request(conn, {"action": "start_app", "command": cmd})
    pretty_print(resp)


def stop_app(conn: socket.socket) -> None:
    name = input("Process name to stop: ").strip()
    if not name:
        print("[WARN] Name cannot be empty.")
        return
    resp = request(conn, {"action": "stop_app", "name": name})
    pretty_print(resp)


# ---------- Connection ---------- #
def connect(server_ip: str) -> Tuple[Optional[socket.socket], Optional[str]]:
    try:
        conn = socket.create_connection((server_ip, SERVER_PORT), timeout=SOCKET_TIMEOUT)
        conn.settimeout(SOCKET_TIMEOUT)
        return conn, None
    except (OSError, ConnectionError) as exc:
        return None, str(exc)


# ---------- Main loop ---------- #
def main() -> None:
    server_ip = input("Server IP: ").strip()
    conn, err = connect(server_ip)
    if err:
        print(f"Cannot connect: {err}")
        return

    actions = {
        "1": list_processes,
        "2": kill_process,
        "3": list_apps,
        "4": start_app,
        "5": stop_app,
    }

    try:
        while True:
            print_menu()
            choice = input("Select: ").strip().lower()
            if choice == "x":
                print("Goodbye!")
                break
            action = actions.get(choice)
            if not action:
                print("Invalid choice.")
                continue
            try:
                action(conn)
            except (ConnectionError, json.JSONDecodeError, OSError) as exc:
                print(f"Connection error: {exc}")
                break
    finally:
        conn.close()


if __name__ == "__main__":
    main()
