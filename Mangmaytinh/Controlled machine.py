import socket
import pyautogui
import os
import shutil
import subprocess

HOST = '0.0.0.0'
PORT = 5001

def take_screenshot(conn):
    print("taking screenshot")
    screenshot = pyautogui.screenshot()
    file_path = "screenshot.png"
    screenshot.save(file_path)

    with open(file_path, "rb") as f:
        conn.sendall(f.read())

    print("screenshot sent!")

def copy_file(src, dest):
    print("copying file from {src} to {dest}")
    try:
        shutil.copy(src, dest)
        return "Copy success"
    except Exception as e:
        return str(e)

def shutdown():
    print("shutdown command received")
    if os.name == 'nt':  # Windows
        subprocess.call("shutdown /s /t 5")
    else:  # macOS/Linux
        subprocess.call("shutdown -h now")

def restart():
    print("restart commmand received")
    if os.name == 'nt':
        subprocess.call("shutdown /r /t 5")
    else:
        subprocess.call("reboot")

def start_client():
    print("client starting...")
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(("127.0.0.1", PORT))

    while True:
        command = client.recv(1024).decode()

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

        elif command == "exit":
            break

    client.close()

start_client()