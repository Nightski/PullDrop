import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import socket
import os
import threading
import json

# Default settings
SETTINGS_FILE = 'settings.json'
default_settings = {
    "server_ip": "192.168.0.3",
    "server_port": 12345
}

# Load settings
if os.path.exists(SETTINGS_FILE):
    with open(SETTINGS_FILE, 'r') as f:
        settings = json.load(f)
else:
    settings = default_settings
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f)

# --- Main Window ---

def start_client():
    client_window = tk.Toplevel(root)
    client_window.title("Pulldrop - Client")

    tk.Label(client_window, text="Server IP:").grid(row=0, column=0, sticky="e")
    ip_entry = tk.Entry(client_window)
    ip_entry.grid(row=0, column=1)
    ip_entry.insert(0, settings["server_ip"])

    tk.Label(client_window, text="Server Port:").grid(row=1, column=0, sticky="e")
    port_entry = tk.Entry(client_window)
    port_entry.grid(row=1, column=1)
    port_entry.insert(0, str(settings["server_port"]))

    log_area = scrolledtext.ScrolledText(client_window, width=50, height=15)
    log_area.grid(row=4, column=0, columnspan=2, padx=10, pady=10)

    def save_settings():
        settings["server_ip"] = ip_entry.get()
        settings["server_port"] = int(port_entry.get())
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f)

    def send_file():
        save_settings()
        file_path = filedialog.askopenfilename()
        if not file_path:
            return
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((settings["server_ip"], settings["server_port"]))

            client_socket.send("SEND".encode().ljust(64))

            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            client_socket.send(str(len(file_name)).encode().ljust(64))
            client_socket.send(file_name.encode())
            client_socket.send(str(file_size).encode().ljust(64))

            with open(file_path, 'rb') as f:
                while True:
                    data = f.read(1024)
                    if not data:
                        break
                    client_socket.send(data)

            log_area.insert(tk.END, f"File '{file_name}' sent successfully.\n")
            log_area.see(tk.END)

        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            client_socket.close()

    def receive_file():
        save_settings()
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((settings["server_ip"], settings["server_port"]))

            client_socket.send("RECEIVE".encode().ljust(64))

            response = client_socket.recv(64).decode().strip()

            if response == "NOFILE":
                messagebox.showinfo("Info", "Server did not select a file.")
                return

            if response != "FILE":
                messagebox.showerror("Error", f"Unexpected server response: {response}")
                return

            file_name_length = int(client_socket.recv(64).decode().strip())
            file_name = client_socket.recv(file_name_length).decode()
            file_size = int(client_socket.recv(64).decode().strip())

            save_path = filedialog.asksaveasfilename(initialfile=file_name, title="Save received file as")

            if not save_path:
                return

            with open(save_path, 'wb') as f:
                received = 0
                while received < file_size:
                    data = client_socket.recv(min(1024, file_size - received))
                    if not data:
                        break
                    f.write(data)
                    received += len(data)

            log_area.insert(tk.END, f"File '{file_name}' received and saved.\n")
            log_area.see(tk.END)

        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            client_socket.close()

    send_button = tk.Button(client_window, text="Send File", command=lambda: threading.Thread(target=send_file).start())
    send_button.grid(row=2, column=0, pady=10)

    receive_button = tk.Button(client_window, text="Receive File", command=lambda: threading.Thread(target=receive_file).start())
    receive_button.grid(row=2, column=1, pady=10)

def start_server():
    server_window = tk.Toplevel(root)
    server_window.title("Pulldrop - Server")

    log_area = scrolledtext.ScrolledText(server_window, width=50, height=20)
    log_area.pack(padx=10, pady=10)

    def log(msg):
        log_area.insert(tk.END, msg + "\n")
        log_area.see(tk.END)

    def server_thread():
        HOST = '0.0.0.0'
        PORT = settings["server_port"]

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((HOST, PORT))
        server_socket.listen(5)
        log(f"Server listening on {HOST}:{PORT}")

        while True:
            client_socket, addr = server_socket.accept()
            log(f"Connected by {addr}")

            def handle_client(client_socket):
                try:
                    command = client_socket.recv(64).decode().strip()

                    if command == "SEND":
                        file_name_length = int(client_socket.recv(64).decode().strip())
                        file_name = client_socket.recv(file_name_length).decode()
                        file_size = int(client_socket.recv(64).decode().strip())

                        log(f"Receiving file: {file_name} ({file_size} bytes)")

                        with open(f"received_{file_name}", 'wb') as f:
                            received = 0
                            while received < file_size:
                                data = client_socket.recv(min(1024, file_size - received))
                                if not data:
                                    break
                                f.write(data)
                                received += len(data)

                        log(f"File '{file_name}' received and saved as 'received_{file_name}'")

                    elif command == "RECEIVE":
                        log("Client requested a file (RECEIVE)...")
                        root = tk.Tk()
                        root.withdraw()
                        file_path = filedialog.askopenfilename(title="Select file to send to client")

                        if not file_path:
                            log("No file selected. Cancelling.")
                            client_socket.send("NOFILE".encode().ljust(64))
                            return

                        file_name = os.path.basename(file_path)
                        file_size = os.path.getsize(file_path)

                        client_socket.send("FILE".encode().ljust(64))
                        client_socket.send(str(len(file_name)).encode().ljust(64))
                        client_socket.send(file_name.encode())
                        client_socket.send(str(file_size).encode().ljust(64))

                        log(f"Sending file: {file_name} ({file_size} bytes)")

                        with open(file_path, 'rb') as f:
                            while True:
                                data = f.read(1024)
                                if not data:
                                    break
                                client_socket.send(data)

                        log(f"File '{file_name}' sent successfully.")

                    else:
                        log("Unknown command received.")

                except Exception as e:
                    log(f"Error: {e}")
                finally:
                    client_socket.close()

            threading.Thread(target=handle_client, args=(client_socket,)).start()

    threading.Thread(target=server_thread, daemon=True).start()

# Main app window
root = tk.Tk()
root.title("Pulldrop")

tk.Label(root, text="Pulldrop File Transfer", font=("Arial", 16)).pack(pady=10)

start_client_button = tk.Button(root, text="Start as Client", width=20, command=start_client)
start_client_button.pack(pady=10)

start_server_button = tk.Button(root, text="Start as Server", width=20, command=start_server)
start_server_button.pack(pady=10)

root.mainloop()
