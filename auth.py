from flask import Flask, request, jsonify, make_response
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from functools import wraps
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Initialize a basic in-memory "database"
in_memory_db = {"users": [], "notes": []}


# Function to find user by username
def find_user_by_username(username):
    return next((user for user in in_memory_db["users"] if user['username'] == username), None)


# Decorator for token authentication
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('X-Access-Token')
        if not token:
            return jsonify({'error': 'Token is missing!'}), 401
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = find_user_by_username(payload['username'])
            if not current_user:
                return jsonify({'error': 'User not found'}), 401
        except Exception as err:
            return jsonify({'error': str(err)}), 401
        return f(current_user, *args, **kwargs)
    return decorated


# User registration
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if find_user_by_username(data['username']):
        return jsonify({'error': 'Username already taken'}), 409
    hashed_pwd = generate_password_hash(data['password'], method='sha256')
    in_memory_db["users"].append({'username': data['username'], 'password': hashed_pwd})
    return jsonify({'message': 'User successfully registered'}), 201


# User login
@app.route('/login', methods=['POST'])
def login():
    credentials = request.get_json()
    if not all(key in credentials for key in ('username', 'password')):
        return make_response('Authentication failed.', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})
    user = find_user_by_username(credentials.get('username'))
    if not user or not check_password_hash(user['password'], credentials.get('password')):
        return make_response('Authentication failed.', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})
    token = jwt.encode({'username': user['username'], 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])
    return jsonify({'token': token})


# List all users
@app.route('/users', methods=['GET'])
@token_required
def list_users(current_user):
    user_list = [{'username': user['username']} for user in in_memory_db["users"]]
    return jsonify({'users': user_list})


# Add a note
@app.route('/notes', methods=['POST'])
@token_required
def add_note(current_user):
    note_info = request.get_json()
    note = {"username": current_user['username'], "title": note_info["title"], "content": note_info["content"]}
    in_memory_db["notes"].append(note)
    return jsonify({'message': 'Note successfully added', 'note': note}), 201


# Get all notes for the current user
@app.route('/notes', methods=['GET'])
@token_required
def get_notes(current_user):
    user_notes = [note for note in in_memory_db["notes"] if note["username"] == current_user['username']]
    return jsonify({"user_notes": user_notes})


# Edit a specific note
@app.route('/notes/<title>', methods=['PUT'])
@token_required
def edit_note(current_user, title):
    note_found = next((note for note in in_memory_db["notes"] if note["username"] == current_user['username'] and note["title"] == title), None)
    if not note_found:
        return jsonify({'error': 'Note not found'}), 404
    note_content = request.get_json()
    note_found['content'] = note_content['content']
    return jsonify({'message': 'Note successfully updated'})


# Delete a specific note
@app.route('/notes/<title>', methods=['DELETE'])
@token_required
def delete_note(current_user, title):
    in_memory_db["notes"] = [note for note in in_memory_db["notes"] if not (note["username"] == current_user['username'] and note["title"] == title)]
    return jsonify({'message': 'Note successfully deleted'})


if __name__ == '__main__':
    app.run(debug=True)