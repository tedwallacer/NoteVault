from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet
import os
import base64
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY').encode()
SALT = os.getenv('SALT').encode()

class NoteVault:
    _fernet_instance = None

    @classmethod
    def get_fernet_instance(cls):
        if cls._fernet_instance is None:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=SALT,
                iterations=390000,
                backend=default_backend()
            )
            key = base64.urlsafe_b64encode(kdf.derive(SECRET_KEY))
            cls._fernet_instance = Fernet(key)
        return cls._fernet_instance

    @staticmethod
    def encrypt_message(message):
        fernet = NoteVault.get_fernet_instance()
        encrypted_message = fernet.encrypt(message.encode())
        return encrypted_message.decode()

    @staticmethod
    def decrypt_message(encrypted_message):
        fernet = NoteVault.get_fernet_instance()
        decrypted_message = fernet.decrypt(encrypted_message.encode())
        return decrypted_message.decode()

if __name__ == "__main__":
    test_message = "This is a test"
    encrypted = NoteVault.encrypt_message(test_message)
    print(f"Encrypted: {encrypted}")
    
    decrypted = NoteVault.decrypt_message(encrypted)
    print(f"Decrypted: {decrypted}")