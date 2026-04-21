"""user_interface.py
Tkinter GUI for the secure messaging app MVP (API version).
"""

import tkinter as tk
from tkinter import messagebox
import requests


class UserInterface(tk.Tk):
    def __init__(self):
        super().__init__()

        self.base_url = "https://onscreen-mutt-catwalk.ngrok-free.dev"  # THIS WILL ALAWYS change when resstart the ngrok
        self.current_user = None
        self.active_contact = None

        self.title("CipherChat")
        self.geometry("850x500")

        self.setup_widgets()

    def setup_widgets(self):
        # left panel
        left_frame = tk.Frame(self, bd=2, relief="groove")
        left_frame.pack(side="left", fill="y", padx=10, pady=10)

        tk.Label(left_frame, text="User ID").pack(pady=5)
        self.user_entry = tk.Entry(left_frame)
        self.user_entry.pack(pady=5, fill="x", padx=10)

        self.login_btn = tk.Button(
            left_frame,
            text="Login/Register",
            command=self.login_user
        )
        self.login_btn.pack(pady=5)

        tk.Label(left_frame, text="Add Contact").pack(pady=5)
        self.contact_entry = tk.Entry(left_frame)
        self.contact_entry.pack(pady=5, fill="x", padx=10)

        self.add_contact_btn = tk.Button(
            left_frame,
            text="Add Contact",
            command=self.add_contact
        )
        self.add_contact_btn.pack(pady=5)

        self.start_chat_btn = tk.Button(
            left_frame,
            text="Start Chat",
            command=self.start_chat
        )
        self.start_chat_btn.pack(pady=5)

        self.contact_list = tk.Listbox(left_frame, height=15)
        self.contact_list.pack(pady=10, fill="both", expand=True, padx=10)
        self.contact_list.bind("<<ListboxSelect>>", self.select_contact)

        # right panel
        right_frame = tk.Frame(self, bd=2, relief="groove")
        right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        self.chat_title = tk.Label(
            right_frame,
            text="No chat selected",
            font=("Arial", 14, "bold")
        )
        self.chat_title.pack(pady=5)

        self.chat_box = tk.Text(
            right_frame,
            state="disabled",
            width=60,
            height=20
        )
        self.chat_box.pack(padx=10, pady=10, fill="both", expand=True)

        bottom_frame = tk.Frame(right_frame)
        bottom_frame.pack(fill="x", padx=10, pady=10)

        self.message_entry = tk.Entry(bottom_frame)
        self.message_entry.pack(side="left", fill="x", expand=True, padx=8, pady=8)
        self.message_entry.bind("<Return>", self.send_message_event)

        self.send_btn = tk.Button(
            bottom_frame,
            text="Send",
            command=self.send_message
        )
        self.send_btn.pack(side="left", padx=5)

        self.fetch_btn = tk.Button(
            bottom_frame,
            text="Fetch",
            command=self.fetch_messages
        )
        self.fetch_btn.pack(side="left", padx=5)

    def login_user(self):
        user_id = self.user_entry.get().strip()
        if not user_id:
            messagebox.showerror("Error", "Please enter a User ID")
            return

        try:
            response = requests.post(
                f"{self.base_url}/register",
                json={"user_id": user_id}
            )
            if response.status_code == 200 and response.json().get("success"):
                self.current_user = user_id
                messagebox.showinfo("Success", f"Logged in as {user_id}")
            else:
                messagebox.showerror("Error", "Login failed")
        except requests.exceptions.ConnectionError:
            messagebox.showerror("Connection Error", f"Cannot reach server at {self.base_url}")

    def add_contact(self):
        if not self.current_user:
            messagebox.showerror("Error", "Please log in first")
            return

        contact_id = self.contact_entry.get().strip()
        if not contact_id:
            messagebox.showerror("Error", "Please enter a contact ID")
            return

        # avoid duplicates in the listbox
        existing = self.contact_list.get(0, tk.END)
        if contact_id in existing:
            messagebox.showwarning("Warning", f"{contact_id} is already in your contacts")
            return

        self.contact_list.insert(tk.END, contact_id)
        self.contact_entry.delete(0, tk.END)

    def start_chat(self):
        selection = self.contact_list.curselection()
        if not selection:
            messagebox.showerror("Error", "Select a contact first")
            return

        self.active_contact = self.contact_list.get(selection[0])
        self.chat_title.config(text=f"Chat with {self.active_contact}")
        self.refresh_chat()

    def send_message_event(self, event):
        self.send_message()

    def send_message(self):
        if not self.current_user:
            messagebox.showerror("Error", "Please log in first")
            return
        if not self.active_contact:
            messagebox.showerror("Error", "Start a chat first")
            return

        msg = self.message_entry.get().strip()
        if not msg:
            return

        try:
            response = requests.post(
                f"{self.base_url}/send",
                json={
                    "sender": self.current_user,
                    "receiver": self.active_contact,
                    "message": msg
                }
            )
            if response.status_code == 200 and response.json().get("success"):
                self.message_entry.delete(0, tk.END)
                self.refresh_chat()
            else:
                messagebox.showerror("Error", "Message not sent")
        except requests.exceptions.ConnectionError:
            messagebox.showerror("Connection Error", f"Cannot reach server at {self.base_url}")

    def fetch_messages(self):
        if not self.active_contact:
            messagebox.showerror("Error", "Start a chat first")
            return
        self.refresh_chat()

    def select_contact(self, event=None):
        selection = self.contact_list.curselection()
        if not selection:
            return

        self.active_contact = self.contact_list.get(selection[0])
        self.chat_title.config(text=f"Chat with {self.active_contact}")
        self.refresh_chat()

    def refresh_chat(self):
        if not self.current_user or not self.active_contact:
            return

        try:
            response = requests.get(
                f"{self.base_url}/conversation",
                params={"user_id": self.current_user, "contact": self.active_contact}
            )

            if response.status_code != 200:
                return

            conversation = response.json()

            self.chat_box.config(state="normal")
            self.chat_box.delete("1.0", tk.END)

            for line in conversation:
                self.chat_box.insert(tk.END, line + "\n\n")

            self.chat_box.config(state="disabled")
            self.chat_box.see(tk.END)

        except requests.exceptions.ConnectionError:
            messagebox.showerror("Connection Error", f"Cannot reach server at {self.base_url}")


if __name__ == "__main__":
    app = UserInterface()
    app.mainloop()
