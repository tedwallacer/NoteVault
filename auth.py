from flask import Flask, request, jsonify, make_response
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from functools import wraps
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Initialize a basic in-memory "database"
in_memory_db = {
    "users": [],
    "notes": []
}

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Decorator to enforce token authentication on protected routes
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('X-Access-Token')

        if not token:
            return jsonify({'error': 'Token is missing!'}), 401

        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = next(
                (user for user in in_memory_db["users"] if user['username'] == payload['username']), 
                None
            )

            if not current_user:
                return jsonify({'error': 'User not found'}), 401
        except Exception as err:
            return jsonify({'error': str(err)}), 401

        return f(current_user, *args, **kwargs)

    return decorated

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    if any(user['username'] == data['username'] for user in in_memory_db["users"]):
        return jsonify({'error': 'Username already taken'}), 409

    hashed_pwd = generate_password_hash(data['password'], method='sha256')
    in_memory_db["users"].append({'username': data['username'], 'password': hashed_pwd})

    return jsonify({'message': 'User successfully registered'}), 201

@app.route('/login', methods=['POST'])
def login():
    credentials = request.get_json()

    if not credentials or not credentials.get('username') or not credentials.get('password'):
        return make_response('Authentication Failed', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})

    user = next(
        (u for u in in_memory_db["users"] if u['username'] == credentials.get('username')), 
        None
    )

    if not user or not check_password_hash(user['password'], credentials.get('password')):
        return make_response('Authentication Failed', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})

    token = jwt.encode(
        {'username': user['username'], 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)},
        app.config['SECRET_KEY']
    )

    return jsonify({'token': token})

@app.route('/users', methods=['GET'])
@token_required
def list_users(current_user):
    user_list = [{'username': user['username']} for user in in_memory_db["users"]]
    return jsonify({'users': user_list})

@app.route('/notes', methods=['POST'])
@token_required
def add_note(current_user):
    note_info = request.get_json()
    note = {
        "username": current_user['username'],
        "title": note_info["title"],
        "content": note_info["content"]
    }
    in_memory_db["notes"].append(note)
    return jsonify({'message': 'Note successfully added', 'note': note}), 201

@app.route('/notes', methods=['GET'])
@token_required
def get_notes(current_user):
    user_notes = [note for note in in_memory_db["notes"] if note["username"] == current_user['username']]
    return jsonify({"user_notes": user_notes})

@app.route('/notes/<title>', methods=['PUT'])
@token_required
def edit_note(current_user, title):
    note_found = next(
        (note for note in in_memory_db["notes"] 
         if note["username"] == current_user['username'] and note["title"] == title), 
        None
    )

    if not note_found:
        return jsonify({'error': 'Note not found'}), 404

    note_content = request.get_json()
    note_found['content'] = note_content['content']
    return jsonify({'message': 'Note successfully updated'})

@app.route('/notes/<title>', methods=['DELETE'])
@token_required
def delete_note(current_user, title):
    in_memory_db["notes"] = [
        note for note in in_memory_db["notes"] 
        if not (note["username"] == current_user['username'] and note["title"] == title)
    ]
    return jsonify({'message': 'Note successfully deleted'})

if __name__ == '__main__':
    app.run(debug=True)