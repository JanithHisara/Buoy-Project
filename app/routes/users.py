"""
Users management page and APIs.
"""
import random
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash
from app.database import get_db

users_bp = Blueprint('users', __name__)


@users_bp.route('/users')
def users_page():
    if 'user' not in session:
        return redirect(url_for('auth.index'))
    # Only admin and super_admin can see this page
    if session['user'].get('role') not in ('admin', 'super_admin'):
        return redirect(url_for('dashboard.dashboard'))
    return render_template('users.html', user=session['user'])


# ── API: List all users ──
@users_bp.route('/api/users', methods=['GET'])
def get_users():
    if 'user' not in session or session['user'].get('role') not in ('admin', 'super_admin'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, role, status, last_active, avatar, avatar_bg, created_at FROM users")
    users_list = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(users_list)


# ── API: Add user (super_admin only) ──
@users_bp.route('/api/users', methods=['POST'])
def add_user():
    if 'user' not in session or session['user'].get('role') != 'super_admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    data = request.json
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    role = data.get('role', 'user')

    if not name or not email or not password:
        return jsonify({'success': False, 'error': 'All fields are required'})

    if role not in ('admin', 'user'):
        return jsonify({'success': False, 'error': 'Invalid role'})

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    if cursor.fetchone():
        conn.close()
        return jsonify({'success': False, 'error': 'Email already registered'})

    avatar = "".join([p[0].upper() for p in name.split() if p])[:2] or "US"
    gradients = [
        "linear-gradient(135deg,#00d4ff,#0077ff)",
        "linear-gradient(135deg,#00e5b0,#0077ff)",
        "linear-gradient(135deg,#ff6b6b,#ff4757)",
        "linear-gradient(135deg,#ffb830,#ff6b6b)",
    ]
    avatar_bg = random.choice(gradients)
    hashed = generate_password_hash(password)

    try:
        cursor.execute('''
            INSERT INTO users (name, email, password, role, status, last_active, avatar, avatar_bg)
            VALUES (?, ?, ?, ?, 'Active', 'Now', ?, ?)
        ''', (name, email, hashed, role, avatar, avatar_bg))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': f'User {name} added'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'error': str(e)})


# ── API: Update user role (super_admin only) ──
@users_bp.route('/api/users/<int:user_id>/role', methods=['PUT'])
def update_role(user_id):
    if 'user' not in session or session['user'].get('role') != 'super_admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    if session['user'].get('id') == user_id:
        return jsonify({'success': False, 'error': 'Cannot modify your own role'})

    data = request.json
    role = data.get('role')
    if role not in ('admin', 'user', 'super_admin'):
        return jsonify({'success': False, 'error': 'Invalid role'})

    conn = get_db()
    conn.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Role updated'})


# ── API: Delete user (super_admin only) ──
@users_bp.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    if 'user' not in session or session['user'].get('role') != 'super_admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    if session['user'].get('id') == user_id:
        return jsonify({'success': False, 'error': 'Cannot delete your own account'})

    conn = get_db()
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'User deleted'})
