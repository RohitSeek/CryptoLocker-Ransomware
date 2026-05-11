# CryptoLocker Simulation (Cybersecurity Research Project)

A full-stack ransomware simulation designed to demonstrate the mechanics of **Asymmetric Cryptography**, **Command & Control (C&C) communication**, and **Windows System persistence**.

> **Disclaimer:** This project is for educational and ethical hacking purposes only. It is designed to run in a controlled environment (TestFolder) to study malware behavior and defense mechanisms.

## 🚀 Technical Architecture
* **Symmetric Encryption:** AES-256 (CBC Mode) for high-speed file encryption.
* **Asymmetric Handshake:** RSA-2048 (PKCS1_OAEP) used to wrap and transmit the AES key securely to the server.
* **C&C Backend:** Node.js & Express server with a persistent JSON database.
* **Client UI:** Python (Tkinter) dashboard with real-time server polling for remote "Kill-Switch" signals.
* **Persistence:** Windows Registry hooking and automatic environment takeover (Wallpaper Hijacking).

## 🛠️ Tech Stack
- **Python 3.14:** `pycryptodome`, `requests`, `tkinter`
- **Node.js:** `express`, `node-rsa`
- **Deployment:** Compiled into a standalone Windows Executable using `PyInstaller`.

## 📦 How to Run
1. **Server:** Navigate to `/server`, run `npm install`, then `node server.js`.
2. **Client:** Place assets in `/client`. Run `python ransomwareMainFile.py` or use the compiled `.exe`.
3. **Recovery:** Use the server-side log to retrieve the AES key and enter it into the dashboard.
