"""
Authentication utilities: hashing, verification, session helpers.
"""
import hashlib
import os
import secrets
from database.models import get_db


def hash_password(password: str) -> str:
    """Hash a password with a random salt using SHA-256."""
    salt = secrets.token_hex(16)
    hashed = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}:{hashed}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a password against its stored hash."""
    try:
        salt, hashed = stored_hash.split(':', 1)
        check = hashlib.sha256((salt + password).encode()).hexdigest()
        return secrets.compare_digest(check, hashed)
    except Exception:
        return False


def register_user(username: str, email: str, password: str) -> dict:
    """Register a new user. Returns {'success': bool, 'message': str, 'user_id': int}"""
    if len(username) < 3:
        return {'success': False, 'message': 'Username must be at least 3 characters.'}
    if len(password) < 6:
        return {'success': False, 'message': 'Password must be at least 6 characters.'}
    if '@' not in email:
        return {'success': False, 'message': 'Invalid email address.'}

    colors = ['#6c63ff', '#ff6584', '#43e97b', '#fa8231', '#00b8d9',
              '#f7971e', '#ee0979', '#00c6ff', '#12c2e9', '#f64f59']
    avatar_color = secrets.choice(colors)

    conn = get_db()
    c = conn.cursor()
    try:
        pw_hash = hash_password(password)
        c.execute(
            'INSERT INTO users (username, email, password_hash, avatar_color) VALUES (?, ?, ?, ?)',
            (username.strip(), email.lower().strip(), pw_hash, avatar_color)
        )
        user_id = c.lastrowid
        # Create stats row for new user
        c.execute('INSERT INTO player_stats (user_id) VALUES (?)', (user_id,))
        conn.commit()
        return {'success': True, 'message': 'Account created!', 'user_id': user_id}
    except Exception as e:
        conn.rollback()
        if 'UNIQUE' in str(e):
            if 'username' in str(e):
                return {'success': False, 'message': 'Username already taken.'}
            return {'success': False, 'message': 'Email already registered.'}
        return {'success': False, 'message': 'Registration failed. Try again.'}
    finally:
        conn.close()


def login_user(username: str, password: str) -> dict:
    """Authenticate a user. Returns {'success': bool, 'message': str, 'user': dict}"""
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute('SELECT * FROM users WHERE username = ?', (username.strip(),))
        user = c.fetchone()
        if not user:
            return {'success': False, 'message': 'Invalid username or password.'}
        if not verify_password(password, user['password_hash']):
            return {'success': False, 'message': 'Invalid username or password.'}
        return {
            'success': True,
            'message': 'Login successful!',
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'avatar_color': user['avatar_color'],
            }
        }
    finally:
        conn.close()


def get_user_by_id(user_id: int) -> dict | None:
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute('SELECT id, username, email, avatar_color, created_at FROM users WHERE id = ?', (user_id,))
        row = c.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()
