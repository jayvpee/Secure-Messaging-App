"""message_handler.py
Handles message operations and data storage for the backend.
"""

from message_data import User, Session, Message

class MessageHandler:
    def __init__(self):
        self.users = {}
        self.sessions = []
        self.messages = []

    def register_user(self, user_id: str, public_key: str) -> bool:
        if user_id in self.users:
            self.users[user_id].public_key = public_key
            return True

        user = User.create_user(user_id, public_key)
        if user is None:
            return False

        self.users[user_id] = user
        return True

    def get_public_key(self, user_id: str):
        user = self.users.get(user_id)
        return user.public_key if user else None

    def store_session(self, user1: str, user2: str, key1: str, key2: str) -> bool:
        # Check if session already exists
        for s in self.sessions:
            if (s.user1 == user1 and s.user2 == user2) or (s.user1 == user2 and s.user2 == user1):
                return False # Session exists
        
        self.sessions.append(Session(user1, user2, key1, key2))
        return True

    def get_session(self, user1: str, user2: str):
        for s in self.sessions:
            if s.user1 == user1 and s.user2 == user2:
                return {"my_key": s.user1_wrapped_key}
            elif s.user1 == user2 and s.user2 == user1:
                return {"my_key": s.user2_wrapped_key}
        return None

    def send_message(self, sender: str, receiver: str, ciphertext: str) -> bool:
        if not ciphertext:
            return False
        self.messages.append(Message(sender, receiver, ciphertext))
        return True

    def get_conversation(self, user_id: str, contact_id: str) -> list:
        conversation = []
        for msg in self.messages:
            if (msg.sender == user_id and msg.receiver == contact_id) or \
               (msg.sender == contact_id and msg.receiver == user_id):
                conversation.append({
                    "sender": msg.sender,
                    "ciphertext": msg.ciphertext
                })
        return conversation