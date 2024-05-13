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
mock_database = {
    "users": [],
    "notes": []
}

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Decorator to enforce token requirement on protected routes
def token_authentication_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('X-Access-Token')

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            authenticated_data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            authenticated_user = next(
                (user for user in mock_database["users"] if user['username'] == authenticated_data['username']), 
                None
            )

            if not authenticated_user:
                return jsonify({'message': 'User not found'}), 401
        except Exception as error:
            return jsonify({'message': str(error)}), 401

        return func(authenticated_user, *args, **kwargs)

    return decorated_function

@app.route('/register', methods=['POST'])
def register_user():
    registration_data = request.get_json()

    if any(user['username'] == registration_data['username'] for user in mock_database["users"]):
        return jsonify({'message': 'User already exists'}), 409

    hashed_password = generate_password_hash(registration_data['password'], method='sha256')
    mock_database["users"].append({'username': registration_data['username'], 'password': hashed_password})

    return jsonify({'message': 'Registered successfully'}), 201

@app.route('/login', methods=['POST'])
def authenticate_user():
    login_credentials = request.get_json()

    if not login_credentials or not login_credentials.get('username') or not login_credentials.get('password'):
        return make_response('Could not verify', 401, {'Authentication': 'Login required"'})

    user = next(
        (user for user in mock_database["users"] if user['username'] == login_credentials.get('username')), 
        None
    )

    if not user or not check_password_hash(user['password'], login_credentials.get('password')):
        return make_response('Could not verify', 401, {'Authentication': 'Login required'})

    token = jwt.encode(
        {'username': user['username'], 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)},
        app.config['SECRET_KEY']
    )

    return jsonify({'token': token})

# Retrieve all users (token required)
@app.route('/users', methods=['GET'])
@token_authentication_required
def list_all_users(authenticated_user):
    users_list = [{'username': user['username']} for user in mock_database["users"]]
    return jsonify({'users': users_list})

@app.route('/notes', methods=['POST'])
@token_authentication_required
def create_note(authenticated_user):
    note_data = request.get_json()
    new_note = {
        "username": authenticated_user['username'],
        "title": note_data["title"],
        "content": note_data["content"]
    }
    mock_database["notes"].append(new_note)
    return jsonify({'message': 'Note created successfully', 'note': new_note}), 201

@app.route('/notes', methods=['GET'])
@token_authentication_required
def list_user_notes(authenticated_user):
    own_notes = [note for note in mock_database["notes"] if note["username"] == authenticated_user['username']]
    return jsonify({"notes": own_notes})

@app.route('/notes/<title>', methods=['PUT'])
@token_authentication_required
def update_user_note(authenticated_user, title):
    note_to_update = next(
        (note for note in mock_database["notes"] 
         if note["username"] == authenticated_user['username'] and note["title"] == title), 
        None
    )

    if not note_to_update:
        return jsonify({'message': 'No note found'}), 404

    update_content = request.get_json()
    note_to_update['content'] = update_content['content']
    return jsonify({'message': 'Note updated successfully'})

@app.route('/notes/<title>', methods=['DELETE'])
@token_authentication_required
def delete_user_note(authenticated_user, title):
    mock_database["notes"] = [
        note for note in mock_database["notes"] 
        if not (note["username"] == authenticated_user['username'] and note["title"] == title)
    ]
    return jsonify({'message': 'Note deleted successfully'})

if __name__ == '__main__':
    app.run(debug=True)