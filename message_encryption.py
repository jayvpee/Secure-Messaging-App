"""message_encryption.py
Very simple demo encryption for MVP use.
"""

class Encryption:
    def encrypt(self, plaintext: str) -> str:
        #basic Caesar-style shift for demo only
        return "".join(chr(ord(ch) + 1) for ch in plaintext)
    def decrypt(self, ciphertext: str) -> str:
        return "".join(chr(ord(ch) - 1) for ch in ciphertext)
