# PullDrop

# Pulldrop

Pulldrop is a simple cross-machine file transfer app.

✨ Features:
- Send files to server
- Receive files from server
- GUI-based (Tkinter)
- Save settings (server IP/port)
- Progress logging
- Packaged into EXE (PyInstaller)

🛠️ Tech stack:
- Python 3.x
- Tkinter
- Sockets
- PyInstaller

⚙️ Usage:
1. Run Pulldrop.exe or Pulldrop.py
2. Select "Start as Client" or "Start as Server"
3. Use Send/Receive buttons

📦 To build EXE:

```bash
pip install pyinstaller
pyinstaller --onefile --noconsole --icon=pulldrop.png Pulldrop.py
