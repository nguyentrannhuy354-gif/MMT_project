import socket
import tkinter as tk
import pyautogui
import shutil
import os
import subprocess

PORT = 5000

# =====================
# FUNCTIONS
# =====================
def take_screenshot(conn):
    log("Taking screenshot...")
    img = pyautogui.screenshot()
    img.save("screen.png")

    with open("screen.png", "rb") as f:
        conn.sendall(f.read())

    log("Screenshot sent")

def copy_file(src, dest):
    try:
        shutil.copy(src, dest)
        return "Copy success"
    except Exception as e:
        return str(e)

def shutdown():
    log("Shutdown command")
    if os.name == 'nt':
        subprocess.call("shutdown /s /t 5")
    else:
        subprocess.call("shutdown -h now")

def restart():
    log("Restart command")
    if os.name == 'nt':
        subprocess.call("shutdown /r /t 5")
    else:
        subprocess.call("reboot")

# =====================
# CLIENT LOGIC
# =====================
def start_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(("127.0.0.1", PORT))

    log("Connected to server")

    while True:
        command = client.recv(1024).decode()
        log(f"Command: {command}")

        if command == "screenshot":
            take_screenshot(client)

        elif command.startswith("copy"):
            _, src, dest = command.split("|")
            result = copy_file(src, dest)
            client.send(result.encode())

        elif command == "shutdown":
            shutdown()

        elif command == "restart":
            restart()

# =====================
# UI
# =====================
def log(msg):
    text.insert(tk.END, msg + "\n")
    text.see(tk.END)

root = tk.Tk()
root.title("Client Machine")
root.geometry("300x300")

tk.Button(root, text="Start Client", command=start_client).pack(pady=10)

text = tk.Text(root, height=10)
text.pack()

root.mainloop()