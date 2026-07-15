"""
Authentication routes: login, signup, logout.
"""
import random
from flask import Blueprint, render_template, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from app.database import get_db

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
def index():
    if 'user' in session:
        return render_template('dashboard.html', user=session['user'])
    return render_template('login.html')


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email', '').strip()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'success': False, 'error': 'Email and password are required'})

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, email, password, role, status, avatar, avatar_bg FROM users WHERE email = ?",
        (email,)
    )
    row = cursor.fetchone()

    if row:
        user = dict(row)
        if check_password_hash(user['password'], password):
            user.pop('password')
            # Update last active
            cursor.execute("UPDATE users SET last_active = 'Now', status = 'Active' WHERE id = ?", (user['id'],))
            conn.commit()
            conn.close()
            session['user'] = user
            return jsonify({'success': True, 'user': user})
        else:
            conn.close()
            return jsonify({'success': False, 'error': 'Incorrect password'})

    conn.close()
    return jsonify({'success': False, 'error': 'Account not found. Please sign up first.'})


@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.json
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')

    if not name or not email or not password:
        return jsonify({'success': False, 'error': 'All fields are required'})

    if len(password) < 6:
        return jsonify({'success': False, 'error': 'Password must be at least 6 characters'})

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    if cursor.fetchone():
        conn.close()
        return jsonify({'success': False, 'error': 'Email is already registered'})

    # Generate avatar
    avatar = "".join([p[0].upper() for p in name.split() if p])[:2] or "US"
    gradients = [
        "linear-gradient(135deg,#00d4ff,#0077ff)",
        "linear-gradient(135deg,#00e5b0,#0077ff)",
        "linear-gradient(135deg,#ff6b6b,#ff4757)",
        "linear-gradient(135deg,#ffb830,#ff6b6b)",
        "linear-gradient(135deg,#a855f7,#6366f1)",
        "linear-gradient(135deg,#06b6d4,#3b82f6)",
    ]
    avatar_bg = random.choice(gradients)
    hashed = generate_password_hash(password)

    try:
        cursor.execute('''
            INSERT INTO users (name, email, password, role, status, last_active, avatar, avatar_bg)
            VALUES (?, ?, ?, 'user', 'Active', 'Now', ?, ?)
        ''', (name, email, hashed, avatar, avatar_bg))
        conn.commit()

        cursor.execute(
            "SELECT id, name, email, role, status, avatar, avatar_bg FROM users WHERE email = ?",
            (email,)
        )
        user = dict(cursor.fetchone())
        session['user'] = user
        conn.close()
        return jsonify({'success': True, 'user': user})

    except Exception as e:
        conn.close()
        print(f"[Auth] Signup error: {e}")
        return jsonify({'success': False, 'error': 'Registration failed'})


@auth_bp.route('/logout', methods=['POST'])
def logout():
    if 'user' in session:
        # Update last active
        try:
            conn = get_db()
            conn.execute(
                "UPDATE users SET last_active = datetime('now'), status = 'Offline' WHERE email = ?",
                (session['user'].get('email', ''),)
            )
            conn.commit()
            conn.close()
        except:
            pass
    session.pop('user', None)
    return jsonify({'success': True})
