from flask import Flask, request, jsonify, make_response
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from functools import wraps
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Initialize a simple in-memory "database"
mock_db = {
    "users": [],
    "notes": []
}

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

# Decorator to enforce token requirement on protected routes
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('x-access-tokens')

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = next((user for user in mock_db["users"] if user['username'] == data['username']), None)
            
            if not current_user:
                return jsonify({'message': 'User not found'}), 401
        except Exception as e:
            return jsonify({'message': str(e)}), 401

        return f(current_user, *args, **kwargs)

    return decorated

@app.route('/register', methods=['POST'])
def signup_user():
    data = request.get_json()

    if any(user['username'] == data['username'] for user in mock_db["users"]):
        return jsonify({'message': 'User already exists'}), 409

    hashed_password = generate_password_hash(data['password'], method='sha256')
    mock_db["users"].append({'username': data['username'], 'password': hashed_password})

    return jsonify({'message': 'Registered successfully'}), 201

@app.route('/login', methods=['POST'])
def login_user():
    auth = request.get_json()

    if not auth or not auth.get('username') or not auth.get('password'):
        return make_response('Could not verify', 401, {'Authentication': 'login required"'})

    user = next((user for user in mock_db["users"] if user['username'] == auth.get('username')), None)
    
    if not user or not check_password_hash(user['password'], auth.get('password')):
        return make_response('Could not verify', 401, {'Authentication': 'login required'})

    token = jwt.encode(
        {'username': user['username'], 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)},
        app.config['SECRET_KEY']
    )
    
    return jsonify({'token': token})

# Retrieve all users (token required)
@app.route('/users', methods=['GET'])
@token_required
def get_all_users(current_user):
    users_with_hidden_passwords = [{'username': user['username']} for user in mock_db["users"]]
    return jsonify({'users': users_with_hidden_passwords})

@app.route('/notes', methods=['POST'])
@token_required
def add_note(current_user):
    data = request.get_json()
    new_note = {
        "username": current_user['username'],
        "title": data["title"],
        "content": data["content"]
    }
    mock_db["notes"].append(new_note)
    return jsonify({'message': 'Note created successfully', 'note': new_note}), 201

@app.route('/notes', methods=['GET'])
@token_required
def get_notes(current_user):
    user_notes = [note for note in mock_db["notes"] if note["username"] == current_user['username']]
    return jsonify({"notes": user_notes})

@app.route('/notes/<title>', methods=['PUT'])
@token_required
def update_note(current_user, title):
    note = next((note for note in mock_db["notes"] if note["username"] == current_user['username'] and note["title"] == title), None)
    
    if not note:
        return jsonify({'message': 'No note found'}), 404
    
    data = request.get_json()
    note['content'] = data['content']
    return jsonify({'message': 'Note updated successfully'})

@app.route('/notes/<title>', methods=['DELETE'])
@token_required
def delete_note(current_user, title):
    mock_db["notes"] = [note for note in mock_db["notes"] if not (note["username"] == current_user['username'] and note["title"] == title)]
    return jsonify({'message': 'Note deleted successfully'})

if __name__ == '__main__':
    app.run(debug=True)