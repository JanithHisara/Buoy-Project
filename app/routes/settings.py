"""
Settings page route and APIs.
"""
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from app.database import get_db
from app.services.updater import update_status, install_update_and_restart

settings_bp = Blueprint('settings', __name__)


@settings_bp.route('/settings')
def settings_page():
    if 'user' not in session:
        return redirect(url_for('auth.index'))
    return render_template('settings.html', user=session['user'])


# ── Update API Endpoints ──

@settings_bp.route('/api/update_status', methods=['GET'])
def get_update_status():
    from app.version import __version__
    
    # Return a copy of the status plus the current version
    status_copy = update_status.copy()
    status_copy['current_version'] = __version__
    return jsonify(status_copy)


@settings_bp.route('/api/install_update', methods=['POST'])
def trigger_install_update():
    if update_status.get('ready_to_install'):
        install_update_and_restart()
        return jsonify({'status': 'ok', 'message': 'Installing update and restarting...'})
    return jsonify({'status': 'error', 'message': 'Update not ready'}), 400


# ── API: Get all settings ──
@settings_bp.route('/api/settings', methods=['GET'])
def get_settings():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM settings")
    settings = {row['key']: row['value'] for row in cursor.fetchall()}
    conn.close()
    return jsonify(settings)


# ── API: Update settings ──
@settings_bp.route('/api/settings', methods=['PUT'])
def update_settings():
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    for key, value in data.items():
        cursor.execute(
            'INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, datetime("now"))',
            (key, str(value))
        )
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Settings saved'})


# ── API: Export logs ──
@settings_bp.route('/api/logs/export', methods=['GET'])
def export_logs():
    import csv
    import io
    from flask import Response
    
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 403

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, user_email, ip_address, method, endpoint, payload FROM api_logs ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date & Time', 'User Email', 'IP Address', 'Method', 'Endpoint', 'Payload'])
    
    for row in rows:
        writer.writerow([
            row['timestamp'],
            row['user_email'],
            row['ip_address'],
            row['method'],
            row['endpoint'],
            row['payload']
        ])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=api_access_logs.csv"}
    )
