"""message_data.py
Stores user, session, and message data classes.
"""

class User:
    def __init__(self, user_id: str, public_key: str):
        self.user_id = user_id
        self.public_key = public_key
        self.contacts = []

    @classmethod
    def create_user(cls, user_id: str, public_key: str):
        if not user_id or not user_id.strip() or not public_key:
            return None
        return cls(user_id.strip(), public_key)

    def add_contact(self, contact_id: str) -> bool:
        if not contact_id.strip() or contact_id in self.contacts:
            return False
        self.contacts.append(contact_id.strip())
        return True

class Session:
    def __init__(self, user1: str, user2: str, user1_wrapped_key: str, user2_wrapped_key: str):
        self.user1 = user1
        self.user2 = user2
        self.user1_wrapped_key = user1_wrapped_key
        self.user2_wrapped_key = user2_wrapped_key

class Message:
    def __init__(self, sender: str, receiver: str, ciphertext: str):
        self.sender = sender
        self.receiver = receiver
        self.ciphertext = ciphertext