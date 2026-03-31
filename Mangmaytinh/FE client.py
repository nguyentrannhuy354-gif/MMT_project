import socket
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk

HOST = '0.0.0.0'
PORT = 5000

conn = None

# =====================
# CONNECT
# =====================
def connect():
    global conn
    log("Starting server...")

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(1)

    log("Waiting for client...")
    conn, addr = server.accept()

    log(f"Connected to {addr}")

# =====================
# SCREENSHOT
# =====================
def screenshot():
    if conn is None:
        log("Client not connected")
        return

    conn.send("screenshot".encode())

    with open("received.png", "wb") as f:
        data = conn.recv(10000000)
        f.write(data)

    img = Image.open("received.png")
    img = img.resize((300, 200))

    photo = ImageTk.PhotoImage(img)
    img_label.config(image=photo)
    img_label.image = photo

    log("Screenshot received")

# =====================
# COPY FILE
# =====================
def copy_file():
    if conn is None:
        log("Client not connected")
        return

    src = filedialog.askopenfilename(title="Select file to send")
    dest = filedialog.asksaveasfilename(title="Save as")

    if src and dest:
        command = f"copy|{src}|{dest}"
        conn.send(command.encode())

        result = conn.recv(1024).decode()
        log(result)

# =====================
# SHUTDOWN / RESTART
# =====================
def shutdown():
    if conn:
        conn.send("shutdown".encode())
        log("Shutdown sent")

def restart():
    if conn:
        conn.send("restart".encode())
        log("Restart sent")

# =====================
# LOG
# =====================
def log(msg):
    text.insert(tk.END, msg + "\n")
    text.see(tk.END)

# =====================
# UI
# =====================
root = tk.Tk()
root.title("Server Controller")
root.geometry("400x500")

tk.Button(root, text="Connect", command=connect).pack(pady=5)
tk.Button(root, text="📸 Screenshot", command=screenshot).pack(pady=5)
tk.Button(root, text="📁 Copy File", command=copy_file).pack(pady=5)
tk.Button(root, text="⚡ Shutdown", command=shutdown).pack(pady=5)
tk.Button(root, text="🔄 Restart", command=restart).pack(pady=5)

img_label = tk.Label(root)
img_label.pack(pady=10)

text = tk.Text(root, height=10)
text.pack()

root.mainloop()