from flask import Flask, request, jsonify, send_from_directory, session
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from mysql.connector import Error
import os
from datetime import datetime

# ==================== CONFIG ====================
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "your_password",
    "database": "import_export"
}

app = Flask(__name__, static_folder='.', static_url_path='')
app.secret_key = os.environ.get('SECRET_KEY', 'change-me-please')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'


# ==================== DB HELPERS ====================
def get_db():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Error as e:
        print('[ERROR] MySQL Connection Failed:', e)
        return None


def query_user_by_email(email):
    conn = get_db()
    if not conn:
        return None, 'Database connection failed'
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        return user, None
    except Error as e:
        return None, str(e)


def create_user(name, email, password):
    conn = get_db()
    if not conn:
        return None, 'Database connection failed'
    try:
        password_hash = generate_password_hash(password)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO users (name, email, password_hash, role, created_at) VALUES (%s, %s, %s, %s, %s)',
            (name, email, password_hash, 'user', datetime.utcnow())
        )
        conn.commit()
        user_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return user_id, None
    except Error as e:
        return None, str(e)


def sanitize_user_record(user):
    if not user:
        return None
    return {
        'user_id': user.get('user_id'),
        'name': user.get('name'),
        'email': user.get('email'),
        'role': user.get('role')
    }


# ==================== ROUTES ====================
@app.route('/')
def home():
    return send_from_directory('.', 'index.html')


@app.route('/index.html')
def index_html():
    return send_from_directory('.', 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)


@app.route('/api/user', methods=['GET'])
def get_user():
    user = session.get('user')
    if user:
        return jsonify({'logged_in': True, 'user': user})
    return jsonify({'logged_in': False, 'user': None})


@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json(force=True)
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'success': False, 'message': 'Email and password are required.'}), 400

    user, error = query_user_by_email(email)
    if error:
        return jsonify({'success': False, 'message': error}), 500
    if not user:
        return jsonify({'success': False, 'message': 'Invalid email or password.'}), 401

    password_hash = user.get('password_hash', '')
    password_matches = False
    try:
        password_matches = check_password_hash(password_hash, password)
    except Exception:
        password_matches = False

    if not password_matches and password != password_hash:
        return jsonify({'success': False, 'message': 'Invalid email or password.'}), 401

    session['user'] = sanitize_user_record(user)
    session.permanent = True
    return jsonify({'success': True, 'message': 'Login successful.', 'user': session['user']})


@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json(force=True)
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    confirm = data.get('confirm_password', '')

    if not name or not email or not password or not confirm:
        return jsonify({'success': False, 'message': 'All fields are required.'}), 400
    if password != confirm:
        return jsonify({'success': False, 'message': 'Passwords do not match.'}), 400
    if len(password) < 6:
        return jsonify({'success': False, 'message': 'Password must be at least 6 characters.'}), 400

    existing_user, error = query_user_by_email(email)
    if error:
        return jsonify({'success': False, 'message': error}), 500
    if existing_user:
        return jsonify({'success': False, 'message': 'An account with that email already exists.'}), 409

    user_id, error = create_user(name, email, password)
    if error:
        return jsonify({'success': False, 'message': error}), 500

    return jsonify({'success': True, 'message': 'Registration successful. Please log in.'})


@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('user', None)
    return jsonify({'success': True, 'message': 'Logged out successfully.'})


# ==================== RUN ====================
if __name__ == '__main__':
    print('=' * 60)
    print('  IndiaTradeHub - Login/Register Server')
    print('=' * 60)
    print('\n[SERVER] Main site:  http://127.0.0.1:5000/')
    print('=' * 60 + '\n')
    app.run(debug=True, port=5000)

