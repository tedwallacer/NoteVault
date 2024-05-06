import os
import sqlite3
from dotenv import load_dotenv
from cryptography.fernet import Fernet

load_dotenv()

DATABASE_PATH = os.getenv("DATABASE_PATH", "app.db")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

conn = sqlite3.connect(DATABASE_PATH)
cursor = conn.cursor()

class DatabaseManager:
    def __init__(self):
        self.initialize_database()

    @staticmethod
    def initialize_database():
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                note TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        conn.commit()

    @staticmethod
    def encrypt_data(data):
        fernet = Fernet(ENCRYPTION_KEY)
        encrypted_data = fernet.encrypt(data.encode())
        return encrypted_data

    @staticmethod
    def decrypt_data(encrypted_data):
        fernet = Fernet(ENCRYPTION_KEY)
        decrypted_data = fernet.decrypt(encrypted_data).decode()
        return decrypted_data

    def add_user(self, username, password):
        encrypted_password = self.encrypt_data(password)
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, encrypted_password))
        conn.commit()

    def add_note(self, user_id, note):
        encrypted_note = self.encrypt_data(note)
        cursor.execute("INSERT INTO notes (user_id, note) VALUES (?, ?)", (user_id, encrypted_note))
        conn.commit()

    def get_user_notes(self, user_id):
        cursor.execute("SELECT note FROM notes WHERE user_id=?", (user_id,))
        encrypted_notes = cursor.fetchall()
        decrypted_notes = [self.decrypt_data(note[0]) for note in encrypted_notes]
        return decrypted_notes

if __name__ == '__main__':
    db_manager = DatabaseManager()
    user_id_example = 1
    notes = db_manager.get_user_notes(user_id_example)
    print(notes)