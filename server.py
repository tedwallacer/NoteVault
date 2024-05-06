from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from functools import wraps
from flask_caching import Cache
import os

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

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        current_user = User.query.first()
        return f(current_user, *args, **kwargs)
    return decorated

@app.route('/note', methods=['GET'])
@token_required
def get_all_notes(current_user):
    cache_key = f"user_notes_{current_user.id}"
    notes = cache.get(cache_key)
    
    if not notes:
        notes = Note.query.filter_by(user_id=current_user.id).all()
        cache.set(cache_key, notes, timeout=60*5)
    
    output = [{'id': note.id, 'title': note.title, 'content': note.content} for note in notes]
    return jsonify({'notes': output})

@app.route('/note', methods=['POST'])
@token_required
def create_note(current_user):
    data = request.get_json()
    cache_key = f"user_notes_{current_user.id}"
    
    new_note = Note(title=data['title'], content=data['content'], user_id=current_user.id)
    db.session.add(new_note)
    db.session.commit()
    
    cache.delete(cache_key)
    return jsonify({'message': 'Note created'}), 201

@app.route('/note/<int:note_id>', methods=['PUT'])
@token_required
def update_note(current_user, note_id):
    data = request.get_json()
    cache_key = f"user_notes_{current_user.id}"
    
    note = Note.query.filter_by(id=note_id, user_id=current_user.id).first()
    if note:
        note.title = data.get('title', note.title)
        note.content = data.get('content', note.content)
        db.session.commit()
        cache.delete(cache_key)
        return jsonify({'message': 'Note updated'}), 200
    else:
        return jsonify({'message': 'Note not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)