"""message_encryption.py
Implements hybrid flow AES-CTR encryption using X25519 and HKDF.
"""

import os
import base64
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

class Encryption:
    def __init__(self):
        # To maintain the `encrypt(plaintext: str)` signature, we simulate
        # the receiver's identity by holding a static "receiver" keypair in this instance.
        self.receiver_private_key = x25519.X25519PrivateKey.generate()
        self.receiver_public_key = self.receiver_private_key.public_key()

    def key_agreement(self, private_key, peer_public_key) -> bytes:
        """Derives the shared secret using X25519 public and private keys."""
        return private_key.exchange(peer_public_key)

    def derive_key(self, shared_secret: bytes, salt: bytes) -> bytes:
        """Strengthens the raw shared secret into a 32-byte AES key using HKDF."""
        return HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            info=b'message-encryption',
        ).derive(shared_secret)

    def direct_encrypt(self, key: bytes, nonce: bytes, plaintext_bytes: bytes) -> bytes:
        """Encrypts data using AES-CTR stream cipher."""
        cipher = Cipher(algorithms.AES(key), modes.CTR(nonce))
        encryptor = cipher.encryptor()
        return encryptor.update(plaintext_bytes) + encryptor.finalize()

    def direct_decrypt(self, key: bytes, nonce: bytes, ciphertext_bytes: bytes) -> bytes:
        """Decrypts data using AES-CTR stream cipher."""
        cipher = Cipher(algorithms.AES(key), modes.CTR(nonce))
        decryptor = cipher.decryptor()
        return decryptor.update(ciphertext_bytes) + decryptor.finalize()

    def encrypt(self, plaintext: str) -> str:
        # 1. Generate an ephemeral (temporary) keypair for the sender
        ephemeral_private_key = x25519.X25519PrivateKey.generate()
        ephemeral_public_key = ephemeral_private_key.public_key()

        # Get raw 32 bytes of the public key to send with the message
        ephemeral_public_bytes = ephemeral_public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )

        # 2. Key Agreement: Combine sender's private key with receiver's public key
        shared_secret = self.key_agreement(ephemeral_private_key, self.receiver_public_key)

        # 3. Key Derivation: Generate salt and create the AES key
        salt = os.urandom(16)
        aes_key = self.derive_key(shared_secret, salt)

        # 4. Direct Encryption: Generate a unique nonce and encrypt
        nonce = os.urandom(16)
        ciphertext = self.direct_encrypt(aes_key, nonce, plaintext.encode('utf-8'))

        # Pack metadata and ciphertext together:
        # Public Key (32 bytes) + Salt (16 bytes) + Nonce (16 bytes) + Ciphertext
        payload = ephemeral_public_bytes + salt + nonce + ciphertext

        # Return as a URL-safe Base64 string for easy storage/transmission
        return base64.urlsafe_b64encode(payload).decode('utf-8')

    def decrypt(self, ciphertext_str: str) -> str:
        # Decode the Base64 string back into raw bytes
        payload = base64.urlsafe_b64decode(ciphertext_str.encode('utf-8'))

        # Unpack the fixed-length metadata
        ephemeral_public_bytes = payload[:32]
        salt = payload[32:48]
        nonce = payload[48:64]
        ciphertext = payload[64:]

        # Reconstruct the sender's public key object
        ephemeral_public_key = x25519.X25519PublicKey.from_public_bytes(ephemeral_public_bytes)

        # 1. Key Agreement: Combine receiver's private key with sender's public key
        shared_secret = self.key_agreement(self.receiver_private_key, ephemeral_public_key)

        # 2. Key Derivation: Re-derive the AES key using the same salt
        aes_key = self.derive_key(shared_secret, salt)

        # 3. Direct Decryption: Reverse the AES-CTR cipher
        plaintext_bytes = self.direct_decrypt(aes_key, nonce, ciphertext)

        return plaintext_bytes.decode('utf-8')
