from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet, InvalidToken
import os
import base64
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')
SALT = os.getenv('SALT')

if SECRET_KEY is None or SALT is None:
    raise ValueError("SECRET_KEY or SALT is not set in environment variables.")

SECRET_KEY = SECRET_KEY.encode()
SALT = SALT.encode()

class NoteVault:
    _fernet_instance = None

    @classmethod
    def get_fernet_instance(cls):
        if cls._fernet_instance is None:
            try:
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=SALT,
                    iterations=390000,
                    backend=default_backend()
                )
                key = base64.urlsafe_b64encode(kdf.derive(SECRET_KEY))
                cls._fernet_instance = Fernet(key)
            except Exception as e:
                raise RuntimeError("Failed to create Fernet instance: " + str(e))
        return cls._fernet_instance

    @staticmethod
    def encrypt_message(message):
        try:
            fernet = NoteVault.get_fernet_instance()
            encrypted_message = fernet.encrypt(message.encode())
            return encrypted_message.decode()
        except Exception as e:
            raise RuntimeError("Encryption failed: " + str(e))

    @staticmethod
    def decrypt_message(encrypted_message):
        try:
            fernet = NoteVault.get_fernet_instance()
            decrypted_message = fernet.decrypt(encrypted_message.encode())
            return decrypted_message.decode()
        except InvalidToken:
            raise RuntimeError("Decryption failed: The provided token is invalid or corrupted.")
        except Exception as e:
            raise RuntimeError("An unexpected error occurred during decryption: " + str(e))

if __name__ == "__main__":
    test_message = "This is a test"
    try:
        encrypted = NoteVault.encrypt_message(test_message)
        print(f"Encrypted: {encrypted}")
        
        decrypted = NoteVault.decrypt_message(encrypted)
        print(f"Decrypted: {decrypted}")
    except RuntimeError as e:
        print(e)