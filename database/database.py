import os
import sqlite3
from dotenv import load_dotenv
from cryptography.fernet import Fernet
from datetime import datetime

load_dotenv()

DATABASE_PATH = os.getenv("DATABASE_PATH", "app.db")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

conn = sqlite3.connect(DATABASE_PATH)
cursor = conn.cursor()

class DatabaseManager:
    def __init__(self):
        self._initialize_database()

    def _initialize_database(self):
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                note TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            );
        """)
        conn.commit()

    @staticmethod
    def _encrypt_data(data):
        fernet = Fernet(ENCRYPTION_KEY)
        return fernet.encrypt(data.encode())

    @staticmethod
    def _decrypt_data(encrypted_data):
        fernet = Fernet(ENCRYPTION_KEY)
        return fernet.decrypt(encrypted_data).decode()

    def add_user(self, username, password):
        encrypted_password = self._encrypt_data(password)
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, encrypted_password))
        conn.commit()
        self._log_activity(f"Added new user: {username}")

    def add_note(self, user_id, note):
        encrypted_note = self._encrypt_data(note)
        cursor.execute("INSERT INTO notes (user_id, note) VALUES (?, ?)", (user_id, encrypted_note))
        conn.commit()
        self._log_activity(f"Added new note for user_id: {user_id}")

    def get_user_notes(self, user_id):
        cursor.execute("SELECT id, note FROM notes WHERE user_id=?", (user_id,))
        
        encrypted_notes = cursor.fetchall()
        notes = [(note_id, self._decrypt_data(note)) for note_id, note in encrypted_notes]
        self._log_activity(f"Retrieved {len(notes)} notes for user_id: {user_id}")
        return notes

    def update_note(self, note_id, new_note):
        encrypted_note = self._encrypt_data(new_note)
        cursor.execute("UPDATE notes SET note = ? WHERE id = ?", (encrypted_note, note_id))
        conn.commit()
        self._log_activity(f"Updated note_id: {note_id}")

    @staticmethod
    def _log_activity(message):
        """
        Logs activity to the console with a timestamp.
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] {message}")

if __name__ == '__main__':
    db_manager = DatabaseManager()
    
    # Example usage
    user_id_example = 1
    note_id_to_update = 1
    new_note_content = "This is the updated content of the note."
    
    # Uncomment these as needed for your testing
    # db_manager.add_user("testUser", "password123")
    db_manager.update_note(note_id_to_update, new_note_content)
    notes = db_manager.get_user_notes(user_id_example)
    print(notes)