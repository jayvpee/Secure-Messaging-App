"""message_encryption.py
Implements Session Key generation and message encryption.
"""

import os
import base64
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

class Encryption:
    def __init__(self):
        # Generate local identity key
        self.private_key = x25519.X25519PrivateKey.generate()
        self.public_key = self.private_key.public_key()
        
        public_bytes = self.public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        self.public_key_b64 = base64.urlsafe_b64encode(public_bytes).decode('utf-8')

    def get_public_key_b64(self) -> str:
        return self.public_key_b64

    def generate_session_key(self) -> bytes:
        """Generates a cryptographically secure 32-byte session key."""
        return os.urandom(32)

    def wrap_session_key(self, session_key: bytes, receiver_pub_key_b64: str) -> str:
        """Encrypts the session key using X25519 asymmetric flow so it can be safely sent."""
        receiver_pub_bytes = base64.urlsafe_b64decode(receiver_pub_key_b64.encode('utf-8'))
        receiver_public_key = x25519.X25519PublicKey.from_public_bytes(receiver_pub_bytes)

        ephemeral_private_key = x25519.X25519PrivateKey.generate()
        ephemeral_public_bytes = ephemeral_private_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw
        )

        shared_secret = ephemeral_private_key.exchange(receiver_public_key)

        salt = os.urandom(16)
        wrap_key = HKDF(
            algorithm=hashes.SHA256(), length=32, salt=salt, info=b'session-key-wrap'
        ).derive(shared_secret)

        nonce = os.urandom(16)
        cipher = Cipher(algorithms.AES(wrap_key), modes.CTR(nonce))
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(session_key) + encryptor.finalize()

        payload = ephemeral_public_bytes + salt + nonce + ciphertext
        return base64.urlsafe_b64encode(payload).decode('utf-8')

    def unwrap_session_key(self, wrapped_key_b64: str) -> bytes:
        """Decrypts the session key using the local private key."""
        payload = base64.urlsafe_b64decode(wrapped_key_b64.encode('utf-8'))

        ephemeral_public_bytes = payload[:32]
        salt = payload[32:48]
        nonce = payload[48:64]
        ciphertext = payload[64:]

        ephemeral_public_key = x25519.X25519PublicKey.from_public_bytes(ephemeral_public_bytes)
        shared_secret = self.private_key.exchange(ephemeral_public_key)

        wrap_key = HKDF(
            algorithm=hashes.SHA256(), length=32, salt=salt, info=b'session-key-wrap'
        ).derive(shared_secret)

        cipher = Cipher(algorithms.AES(wrap_key), modes.CTR(nonce))
        decryptor = cipher.decryptor()
        return decryptor.update(ciphertext) + decryptor.finalize()

    def encrypt_message(self, plaintext: str, session_key: bytes) -> str:
        """Encrypts a message using the active AES session key."""
        nonce = os.urandom(16)
        cipher = Cipher(algorithms.AES(session_key), modes.CTR(nonce))
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(plaintext.encode('utf-8')) + encryptor.finalize()
        
        # Only need to send the nonce and the ciphertext now
        payload = nonce + ciphertext
        return base64.urlsafe_b64encode(payload).decode('utf-8')

    def decrypt_message(self, ciphertext_b64: str, session_key: bytes) -> str:
        """Decrypts a message using the active AES session key."""
        payload = base64.urlsafe_b64decode(ciphertext_b64.encode('utf-8'))
        nonce = payload[:16]
        ciphertext = payload[16:]

        cipher = Cipher(algorithms.AES(session_key), modes.CTR(nonce))
        decryptor = cipher.decryptor()
        plaintext_bytes = decryptor.update(ciphertext) + decryptor.finalize()
        return plaintext_bytes.decode('utf-8')