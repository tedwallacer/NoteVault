from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from functools import wraps
from cryptography.fernet import Fernet
import os

app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your_secret_key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.String(1000), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

def generate_key():
    return Fernet.generate_key()

def encrypt_message(message):
    key = os.getenv('ENCRYPTION_KEY', generate_key())
    f = Fernet(key)
    encrypted_message = f.encrypt(message.encode())
    return encrypted_message

def decrypt_message(encrypted_message):
    key = os.getenv('ENCRYPTION_KEY')
    f = Fernet(key)
    decrypted_message = f.decrypt(encrypted_message).decode()
    return decrypted_message

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.filter_by(id=data['id']).first()
        except:
            return jsonify({'message': 'Token is invalid!'}), 401

        return f(current_user, *args, **kwargs)

    return decorated

@app.route('/user', methods=['POST'])
def create_user():
    data = request.get_json()

    hashed_password = generate_password_hash(data['password'], method='sha256')

    new_user = User(username=data['username'], password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'New user created!'})

@app.route('/login', methods=['POST'])
def login():
    auth = request.authorization

    if not auth or not auth.username or not auth.password:
        return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'})

    user = User.query.filter_by(username=auth.username).first()

    if not user:
        return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'})

    if check_password_hash(user.password, auth.password):
        token = jwt.encode({'id': user.id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])

        return jsonify({'token': token})

    return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'})

@app.route('/note', methods=['POST'])
@token_required
def create_note(current_user):
    data = request.get_json()

    encrypted_content = encrypt_message(data['content'])

    new_note = Note(title=data['title'], content=encrypted_content, user_id=current_user.id)
    db.session.add(new_note)
    db.session.commit()

    return jsonify({'message': 'Note created!'})

@app.route('/note', methods=['GET'])
@token_required
def get_all_notes(current_user):
    notes = Note.query.filter_by(user_id=current_user.id).all()

    output = []

    for note in notes:
        note_data = {}
        note_data['id'] = note.id
        note_data['title'] = note.title
        note_data['content'] = decrypt_message(note.content)
        output.append(note_data)

    return jsonify({'notes': output})

@app.route('/note/<note_id>', methods=['PUT'])
@token_required
def update_note(current_user, note_id):
    note = Note.query.filter_by(id=note_id, user_id=current_user.id).first()

    if not note:
        return jsonify({'message': 'No note found!'})

    data = request.get_json()
    note.title = data['title']
    note.content = encrypt_message(data['content'])
    db.session.commit()

    return jsonify({'message': 'Note item has been updated!'})

@app.route('/note/<note_id>', methods=['DELETE'])
@token_required
def delete_note(current_user, note_id):
    note = Note.query.filter_by(id=note_id, user_id=current_user.id).first()

    if not note:
        return jsonify({'message': 'No note found!'})

    db.session.delete(note)
    db.session.commit()

    return jsonify({'message': 'Note item deleted!'})

if __name__ == '__main__':
    app.run(debug=True)