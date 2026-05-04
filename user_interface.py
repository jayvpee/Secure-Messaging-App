"""user_interface.py
Tkinter GUI. Handles local session key generation and symmetric encryption.
"""
import tkinter as tk
from tkinter import messagebox
import requests
from message_encryption import Encryption

class UserInterface(tk.Tk):
    def __init__(self):
        super().__init__()
        self.base_url = "http://10.192.127.93:5000"
        self.current_user = None
        self.active_contact = None
        
        self.encryption = Encryption()
        self.active_sessions = {}  # Stores raw 32-byte AES keys mapped to contact IDs

        self.title("CipherChat")
        self.geometry("850x500")
        self.setup_widgets()

    def setup_widgets(self):
        left_frame = tk.Frame(self, bd=2, relief="groove")
        left_frame.pack(side="left", fill="y", padx=10, pady=10)

        tk.Label(left_frame, text="User ID").pack(pady=5)
        self.user_entry = tk.Entry(left_frame)
        self.user_entry.pack(pady=5, fill="x", padx=10)

        self.login_btn = tk.Button(left_frame, text="Login/Register", command=self.login_user)
        self.login_btn.pack(pady=5)

        tk.Label(left_frame, text="Add Contact").pack(pady=5)
        self.contact_entry = tk.Entry(left_frame)
        self.contact_entry.pack(pady=5, fill="x", padx=10)

        self.add_contact_btn = tk.Button(left_frame, text="Add Contact", command=self.add_contact)
        self.add_contact_btn.pack(pady=5)

        self.start_chat_btn = tk.Button(left_frame, text="Start Chat", command=self.start_chat)
        self.start_chat_btn.pack(pady=5)

        self.contact_list = tk.Listbox(left_frame, height=15)
        self.contact_list.pack(pady=10, fill="both", expand=True, padx=10)
        self.contact_list.bind("<<ListboxSelect>>", self.select_contact)

        right_frame = tk.Frame(self, bd=2, relief="groove")
        right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        self.chat_title = tk.Label(right_frame, text="No chat selected", font=("Arial", 14, "bold"))
        self.chat_title.pack(pady=5)

        self.chat_box = tk.Text(right_frame, state="disabled", width=60, height=20)
        self.chat_box.pack(padx=10, pady=10, fill="both", expand=True)

        bottom_frame = tk.Frame(right_frame)
        bottom_frame.pack(fill="x", padx=10, pady=10)

        self.message_entry = tk.Entry(bottom_frame)
        self.message_entry.pack(side="left", fill="x", expand=True, padx=8, pady=8)
        self.message_entry.bind("<Return>", lambda e: self.send_message())

        self.send_btn = tk.Button(bottom_frame, text="Send", command=self.send_message)
        self.send_btn.pack(side="left", padx=5)

        self.fetch_btn = tk.Button(bottom_frame, text="Fetch", command=self.refresh_chat)
        self.fetch_btn.pack(side="left", padx=5)

    def login_user(self):
        user_id = self.user_entry.get().strip()
        if not user_id: return
        try:
            resp = requests.post(f"{self.base_url}/register", json={
                "user_id": user_id, "public_key": self.encryption.get_public_key_b64()
            })
            if resp.status_code == 200 and resp.json().get("success"):
                self.current_user = user_id
                messagebox.showinfo("Success", f"Logged in as {user_id}")
        except:
            messagebox.showerror("Error", "Connection failed")

    def add_contact(self):
        contact_id = self.contact_entry.get().strip()
        if contact_id and contact_id not in self.contact_list.get(0, tk.END):
            self.contact_list.insert(tk.END, contact_id)
            self.contact_entry.delete(0, tk.END)

    def select_contact(self, event=None):
        selection = self.contact_list.curselection()
        if not selection: return
        self.active_contact = self.contact_list.get(selection[0])
        self.chat_title.config(text=f"Chat with {self.active_contact}")
        self.start_chat()

    def start_chat(self):
        """Initializes or retrieves the Session Key for the active contact."""
        if not self.active_contact or not self.current_user: return
        
        # 1. Check if we already have the session key in local memory
        if self.active_contact in self.active_sessions:
            self.refresh_chat()
            return

        # 2. Check if the server has an active session for this pair
        resp = requests.get(f"{self.base_url}/get_session", params={"user_id": self.current_user, "contact": self.active_contact})
        if resp.status_code == 200 and resp.json().get("success"):
            wrapped_key = resp.json().get("wrapped_key")
            self.active_sessions[self.active_contact] = self.encryption.unwrap_session_key(wrapped_key)
            self.refresh_chat()
            return

        # 3. No session exists. Generate a new Session Key.
        resp = requests.get(f"{self.base_url}/get_key", params={"user_id": self.active_contact})
        if not resp.json().get("success"):
            messagebox.showwarning("Warning", "Contact has no public key. They must login first.")
            return
            
        contact_pub_key = resp.json().get("public_key")
        raw_session_key = self.encryption.generate_session_key()
        
        # Wrap it for both users
        sender_wrapped = self.encryption.wrap_session_key(raw_session_key, self.encryption.get_public_key_b64())
        receiver_wrapped = self.encryption.wrap_session_key(raw_session_key, contact_pub_key)
        
        # Upload session keys to server
        requests.post(f"{self.base_url}/init_session", json={
            "sender": self.current_user, "receiver": self.active_contact,
            "sender_key": sender_wrapped, "receiver_key": receiver_wrapped
        })

        # Store locally and load chat
        self.active_sessions[self.active_contact] = raw_session_key
        self.refresh_chat()

    def send_message(self):
        if not self.active_contact or self.active_contact not in self.active_sessions: return
        msg = self.message_entry.get().strip()
        if not msg: return

        # Encrypt with the raw AES session key
        session_key = self.active_sessions[self.active_contact]
        ciphertext = self.encryption.encrypt_message(msg, session_key)

        requests.post(f"{self.base_url}/send", json={
            "sender": self.current_user, "receiver": self.active_contact, "ciphertext": ciphertext
        })
        self.message_entry.delete(0, tk.END)
        self.refresh_chat()

    def refresh_chat(self):
        if not self.active_contact or self.active_contact not in self.active_sessions: return
        session_key = self.active_sessions[self.active_contact]

        resp = requests.get(f"{self.base_url}/conversation", params={"user_id": self.current_user, "contact": self.active_contact})
        if resp.status_code != 200: return

        self.chat_box.config(state="normal")
        self.chat_box.delete("1.0", tk.END)

        for msg_data in resp.json():
            try:
                decrypted = self.encryption.decrypt_message(msg_data["ciphertext"], session_key)
                prefix = "You" if msg_data["sender"] == self.current_user else msg_data["sender"]
                self.chat_box.insert(tk.END, f"{prefix}: {decrypted}\n\n")
            except:
                self.chat_box.insert(tk.END, f"[Encrypted]\n\n")

        self.chat_box.config(state="disabled")
        self.chat_box.see(tk.END)

if __name__ == "__main__":
    app = UserInterface()
    app.mainloop()