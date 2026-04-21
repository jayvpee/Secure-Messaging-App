"""message_handler.py
Handles message operations of the messaging app.
"""

from message_encryption import Encryption
from message_data import User, Message


class MessageHandler:
    def __init__(self):
        self.encryption = Encryption()
        self.users = {}
        self.messages = []

    def register_user(self, user_id: str) -> bool:
        if user_id in self.users:
            return True

        user = User.create_user(user_id)
        if user is None:
            return False

        self.users[user_id] = user
        return True

    def add_contact(self, user_id: str, contact_id: str) -> bool:
        user = self.users.get(user_id)
        if user is None:
            return False
        return user.add_contact(contact_id)

    def send_message(self, sender: str, receiver: str, message: str) -> bool:
        if not sender or not receiver or not message.strip():
            return False

        encrypted = self.encryption.encrypt(message)
        msg = Message.compose_message(sender, receiver, encrypted)
        if msg is None:
            return False

        self.messages.append(msg)
        return True

    def get_conversation(self, user_id: str, contact_id: str) -> list:
        if not user_id or not contact_id:
            return []

        conversation = []

        for msg in self.messages:
            is_outgoing = msg.sender == user_id and msg.receiver == contact_id
            is_incoming = msg.sender == contact_id and msg.receiver == user_id

            if is_outgoing or is_incoming:
                decrypted = self.encryption.decrypt(msg.message_content)

                if is_outgoing:
                    conversation.append(f"You: {decrypted}")
                else:
                    conversation.append(f"{msg.sender}: {decrypted}")

        return conversation

    def get_sent_messages(self, user_id: str, contact_id: str) -> list:
        sent = []
        for msg in self.messages:
            if msg.sender == user_id and msg.receiver == contact_id:
                decrypted = self.encryption.decrypt(msg.message_content)
                sent.append(f"You: {decrypted}")
        return sent

    def receive_messages(self, user_id: str, contact_id: str) -> list:
        received = []
        for msg in self.messages:
            if msg.sender == contact_id and msg.receiver == user_id:
                decrypted = self.encryption.decrypt(msg.message_content)
                received.append(f"{msg.sender}: {decrypted}")
        return received
