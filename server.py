from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from functools import wraps
from flask_caching import Cache
import os

app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your_default_secret_key_here')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site_database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["CACHE_TYPE"] = "SimpleCache"
app.config["CACHE_DEFAULT_TIMEOUT"] = 300

db = SQLAlchemy(app)
cache_manager = Cache(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(80), nullable=False)

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.String(1000), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

def verify_token(func):
    @wraps(func)
    def decorator(*args, **kwargs):
        authenticated_user = User.query.first()
        return func(authenticated_user, *args, **kwargs)
    return decorator

@app.route('/note', methods=['GET'])
@verify_token
def fetch_all_notes(authenticated_user):
    notes_cache_key = f"user_notes_{authenticated_user.id}"
    cached_notes = cache_manager.get(notes_cache_key)
    
    if not cached_notes:
        user_notes = Note.query.filter_by(user_id=authenticated_user.id).all()
        cache_manager.set(notes_cache_key, user_notes, timeout=60*5)
        cached_notes = user_notes
    
    notes_response = [{'id': note.id, 'title': note.title, 'content': note.content} for note in cached_notes]
    return jsonify({'notes': notes_response})

@app.route('/note', methods=['POST'])
@verify_token
def create_new_note(authenticated_user):
    note_data = request.get_json()
    notes_cache_key = f"user_notes_{authenticated_user.id}"
    
    note_instance = Note(title=note_data['title'], content=note_data['content'], user_id=authenticated_user.id)
    db.session.add(note_instance)
    db.session.commit()
    
    cache_manager.delete(notes_cache_key)
    return jsonify({'message': 'Note successfully created'}), 201

@app.route('/note/<int:note_id>', methods=['PUT'])
@verify_token
def update_existing_note(authenticated_user, note_id):
    received_data = request.get_json()
    notes_cache_key = f"user_notes_{authenticated_user.id}"
    
    target_note = Note.query.filter_by(id=note_id, user_id=authenticated_user.id).first()
    if target_note:
        target_note.title = received_data.get('title', target_note.title)
        target_note.content = received_data.get('content', target_note.content)
        db.session.commit()
        cache_manager.delete(notes_cache_key)
        return jsonify({'message': 'Note successfully updated'}), 200
    else:
        return jsonify({'message': 'Note not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)