"""message_data.py
Stores user and message data classes.
"""


class User:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.contacts = []

    @classmethod
    def create_user(cls, user_id: str):
        if not user_id or not user_id.strip():
            return None
        return cls(user_id.strip())

    def add_contact(self, contact_id: str) -> bool:
        contact_id = contact_id.strip()
        if not contact_id:
            return False
        if contact_id in self.contacts:
            return False
        self.contacts.append(contact_id)
        return True


class Message:
    def __init__(self, sender: str, receiver: str, message_content: str):
        self.sender = sender
        self.receiver = receiver
        self.message_content = message_content

    @classmethod
    def compose_message(cls, sender: str, receiver: str, message_content: str):
        if not sender or not receiver or not message_content.strip():
            return None
        return cls(sender, receiver, message_content.strip())
