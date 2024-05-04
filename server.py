pip install Flask-Caching
```

```python
from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from functools import wraps
from cryptography.fernet import Fernet
import os
from flask_caching import Cache

app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your_secret_key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["CACHE_TYPE"] = "SimpleCache"  
app.config["CACHE_DEFAULT_TIMEOUT"] = 300  

db = SQLAlchemy(app)
cache = Cache(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.String(1000), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@app.route('/note', methods=['GET'])
@token_required
def get_all_notes(current_user):
    cache_key = f"user_notes_{current_user.id}"
    notes = cache.get(cache_key)
    
    if not notes:
        notes = Note.query.filter_by(user_id=current_user.id).all()
        cache.set(cache_key, notes)
    
    output = []

    for note in notes:
        note_data = {}
        note_data['id'] = note.id
        note_data['title'] = note.title
        note_data['content'] = decrypt_message(note.content)
        output.append(note_data)

    return jsonify({'notes': output})

@app.route('/note', methods=['POST'])
@token_required
def create_note(current_user):
    data = request.get_json()
    cache_key = f"user_notes_{current_user.id}"
    cache.delete(cache_key)
    
@app.route('/note/<note_id>', methods=['PUT'])
@token_required
def update_note(current_user, note_id):
    cache_key = f"user_notes_{current_user.id}"
    cache.delete(cache_key)

if __name__ == '__main__':
    app.run(debug=True)