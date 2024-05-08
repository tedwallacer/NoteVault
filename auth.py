from flask import Flask, request, jsonify, make_response
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from functools import wraps
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

mock_db = {
    "users": [],
    "notes": []  # Added to support notes functionality
}

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'x-access-tokens' in request.headers:
            token = request.headers['x-access-tokens']

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = [user for user in mock_db["users"] if user['username'] == data['username']]
            if not current_user:
                raise RuntimeError('User not found')
            current_user = current_user[0]
        except Exception as e:
            return jsonify({'message': str(e)}), 401

        return f(current_user, *args, **kwargs)

    return decorated

@app.route('/register', methods=['POST'])
def signup_user():
    data = request.get_json()

    existing_user = [user for user in mock_db["users"] if user['username'] == data['username']]
    if existing_user:
        return jsonify({'message': 'User already exists'}), 409

    hashed_password = generate_password_hash(data['password'], method='sha256')

    mock_db["users"].append({
        'username': data['username'],
        'password': hashed_password
    })

    return jsonify({'message': 'Registered successfully'}), 201

@app.route('/login', methods=['POST'])
def login_user():
    auth = request.get_json()

    if not auth or not auth.get('username') or not auth.get('password'):
        return make_response('Could not verify', 401, {'Authentication': 'login required"'})

    user = [user for user in mock_db["users"] if user['username'] == auth.get('username')]
    if not user:
        return make_response('Could not verify', 401, {'Authentication': 'login required'})

    if check_password_hash(user[0]['password'], auth.get('password')):
        token = jwt.encode({'username': user[0]['username'], 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])
        return jsonify({'token': token})

    return make_response('Could not verify', 401, {'Authentication': 'login required'})

@app.route('/users', methods=['GET'])
@token_required
def get_all_users(current_user):
    # Hide the passwords when listing users
    users_with_hidden_passwords = [{"username": user["username"]} for user in mock_db["users"]]
    return jsonify({'users': users_with_hidden_passwords})

@app.route('/notes', methods=['POST'])
@token_required
def add_note(current_user):
    data = request.get_json()
    new_note = {
        "username": current_user["username"],
        "title": data["title"],
        "content": data["content"]
    }
    mock_db["notes"].append(new_note)
    return jsonify({'message' : 'Note created successfully', 'note': new_note}), 201

@app.route('/notes', methods=['GET'])
@token_required
def get_notes(current_user):
    users_notes = [note for note in mock_db["notes"] if note["username"] == current_user["username"]]
    return jsonify({"notes": users_notes})

@app.route('/notes/<title>', methods=['PUT'])
@token_required
def update_note(current_user, title):
    notes = [note for note in mock_db["notes"] if note["username"] == current_user["username"] and note["title"] == title]
    if not notes:
        return jsonify({'message' : 'No note found'}), 404

    data = request.get_json()
    notes[0]['content'] = data['content']
    return jsonify({'message' : 'Note updated successfully'})

@app.route('/notes/<title>', methods=['DELETE'])
@token_required
def delete_note(current_user, title):
    global mock_db
    mock_db["notes"] = [note for note in mock_db["notes"] if not (note["username"] == current_user["username"] and note["title"] == title)]

    return jsonify({'message' : 'Note deleted successfully'})

if __name__ == '__main__':
    app.run(debug=True)