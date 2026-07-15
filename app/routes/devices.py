"""
Device Setup page route and device management APIs.
"""
import sqlite3
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from app.database import get_db
from app.services.serial_service import serial_manager

devices_bp = Blueprint('devices', __name__)


@devices_bp.route('/devices')
def devices_page():
    if 'user' not in session:
        return redirect(url_for('auth.index'))
    return render_template('devices.html', user=session['user'])


# ── API: List all devices ──
@devices_bp.route('/api/devices', methods=['GET'])
def get_devices():
    bound_only = request.args.get('bound_only', 'false').lower() == 'true'
    conn = get_db()
    cursor = conn.cursor()
    if bound_only:
        cursor.execute("SELECT * FROM devices WHERE is_bound = 1 ORDER BY registered_at DESC")
    else:
        cursor.execute("SELECT * FROM devices ORDER BY registered_at DESC")
    devices_list = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(devices_list)


# ── API: Add a new device ──
@devices_bp.route('/api/devices', methods=['POST'])
def add_device():
    data = request.json
    device_id = data.get('id', '').strip().upper()
    name = data.get('name', '').strip()
    lat = data.get('lat', 0.0)
    lon = data.get('lon', 0.0)

    if not device_id or not name:
        return jsonify({'success': False, 'error': 'Device ID and name are required'})

    user_email = session.get('user', {}).get('email', '')

    conn = get_db()
    cursor = conn.cursor()
    try:
        initial_status = 'online' if (lat != 0.0 or lon != 0.0) else 'offline'
        cursor.execute('''
            INSERT INTO devices (id, name, lat, lon, status, registered_by, active, is_bound)
            VALUES (?, ?, ?, ?, ?, ?, 1, 1)
        ''', (device_id, name, lat, lon, initial_status, user_email))
        conn.commit()
        
        if serial_manager.is_connected and serial_manager.trx_id:
            from app.services.lora_protocol import LoRaProtocol
            serial_manager.send(LoRaProtocol.build_bind(serial_manager.trx_id, device_id, True))
                
        conn.close()
        return jsonify({'success': True, 'message': f'Device {name} registered and bind command sent'})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'success': False, 'error': f'Device ID {device_id} already exists'})


# ── API: Update device ──
@devices_bp.route('/api/devices/<device_id>', methods=['PUT'])
def update_device(device_id):
    data = request.json
    conn = get_db()
    cursor = conn.cursor()

    lat = data.get('lat')
    lon = data.get('lon')
    name = data.get('name')

    if lat is not None and lon is not None:
        cursor.execute('UPDATE devices SET lat=?, lon=?, last_gps_time=datetime("now") WHERE id=?',
                        (lat, lon, device_id))
    if name is not None:
        cursor.execute('UPDATE devices SET name=? WHERE id=?', (name, device_id))

    conn.commit()
    conn.close()
    return jsonify({'success': True})


# ── API: Delete device ──
@devices_bp.route('/api/devices/<device_id>', methods=['DELETE'])
def delete_device(device_id):
    conn = get_db()
    conn.execute("DELETE FROM devices WHERE id = ?", (device_id,))
    conn.execute("DELETE FROM gps_logs WHERE device_id = ?", (device_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Device deleted'})


# ── API: Bind device ──
@devices_bp.route('/api/devices/<device_id>/bind', methods=['POST'])
def bind_device(device_id):
    device_id = device_id.strip().upper()
    
    success, message = serial_manager.bind_buoy(device_id, True)
    if success:
        conn = get_db()
        conn.execute("UPDATE devices SET is_bound = 1 WHERE id = ?", (device_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Successfully bound to device'})
    else:
        return jsonify({'success': False, 'error': message})


# ── API: Unbind device ──
@devices_bp.route('/api/devices/<device_id>/unbind', methods=['POST'])
def unbind_device(device_id):
    device_id = device_id.strip().upper()

    success, message = serial_manager.bind_buoy(device_id, False)
    if success:
        conn = get_db()
        conn.execute("UPDATE devices SET is_bound = 0 WHERE id = ?", (device_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Successfully unbound device'})
    else:
        return jsonify({'success': False, 'error': message})


# ── API: Update buoy location via LoRa ──
@devices_bp.route('/api/devices/<device_id>/update-location', methods=['POST'])
def update_buoy_location(device_id):
    device_id = device_id.strip().upper()
    success, result = serial_manager.update_buoy_location(device_id)

    if success:
        return jsonify({
            'success': True,
            'lat': result['lat'],
            'lon': result['lon'],
            'has_fix': result.get('has_fix', False),
            'is_cached': result.get('is_cached', False),
        })
    else:
        # Get DB location as fallback
        conn = get_db()
        cursor = conn.cursor()

        # Update status based on the error
        new_status = 'offline'
        if 'has no lock' in result:
            new_status = 'warning'
        
        cursor.execute("UPDATE devices SET status=? WHERE id=?", (new_status, device_id))
        conn.commit()

        cursor.execute("SELECT lat, lon, last_gps_time FROM devices WHERE id=?", (device_id,))
        row = cursor.fetchone()
        conn.close()

        fallback = {}
        if row:
            fallback = {'lat': row['lat'], 'lon': row['lon'], 'last_gps_time': row['last_gps_time']}

        return jsonify({
            'success': False,
            'error': result,
            'fallback': fallback
        })

@devices_bp.route('/api/devices/<device_id>/check-live', methods=['GET'])
def check_live_location(device_id):
    device_id = device_id.strip().upper()
    success, result = serial_manager.poll_live_location(device_id)
    
    if success:
        # Prevent 0.0 from being treated as live
        if result.get('lat', 0.0) != 0.0 or result.get('lon', 0.0) != 0.0:
            return jsonify({
                'success': True,
                'lat': result['lat'],
                'lon': result['lon']
            })
            
    return jsonify({
        'success': False,
        'error': 'Live location not locked yet or timeout'
    })


# ── API: Get device history trail ──
@devices_bp.route('/api/devices/<device_id>/history', methods=['POST', 'GET'])
def get_history(device_id):
    device_id = device_id.strip().upper()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT lat, lon, timestamp FROM gps_logs WHERE device_id = ? ORDER BY timestamp DESC", (device_id,))
    rows = cursor.fetchall()
    conn.close()
    
    # Group by hour (YYYY-MM-DD HH) and keep only the latest (first encountered since ordered DESC)
    history = []
    seen_hours = set()
    
    for r in rows:
        ts = r['timestamp']
        if not ts:
            continue
            
        # Extract date and hour "YYYY-MM-DD HH"
        hour_key = ts[:13] 
        
        if hour_key not in seen_hours:
            seen_hours.add(hour_key)
            # Use the actual point, but optionally we could override 'time': f"{hour_key}:00:00"
            history.append({'lat': r['lat'], 'lon': r['lon'], 'time': ts})
            
    return jsonify({'success': True, 'history': history})

# ── API: Set LED Color ──
@devices_bp.route('/api/devices/<device_id>/led', methods=['POST'])
def set_led(device_id):
    color_hex = request.json.get('color', '#0000ff') # default blue
    color_hex = color_hex.lstrip('#')
    off_time = request.json.get('off_time', None)
    is_on = request.json.get('is_on', True) # Default to True
    
    try:
        r = int(color_hex[0:2], 16)
        g = int(color_hex[2:4], 16)
        b = int(color_hex[4:6], 16)
    except:
        r, g, b = 0, 0, 255
        
    success, msg = serial_manager.set_led(device_id.strip().upper(), r, g, b, off_time, is_on)
    
    if success:
        conn = get_db()
        is_on_int = 1 if is_on else 0
        conn.execute("UPDATE devices SET led_color = ?, led_is_on = ? WHERE id = ?", (f'#{color_hex}', is_on_int, device_id.strip().upper()))
        conn.commit()
        conn.close()
        
    return jsonify({'success': success, 'message': msg, 'color': f'#{color_hex}', 'is_on': is_on})

# ── API: Toggle GPS Power ──
@devices_bp.route('/api/devices/<device_id>/gps-power', methods=['POST'])
def toggle_gps_power(device_id):
    state = request.json.get('state', False)
    success, msg = serial_manager.toggle_gps_power(device_id.strip().upper(), state)
    return jsonify({'success': success, 'message': msg})



# ── API: Read buoyancy device ID from USB ──
@devices_bp.route('/api/devices/read-id', methods=['POST'])
def read_device_id():
    data = request.json
    port = data.get('port', '')

    if not port:
        return jsonify({'success': False, 'error': 'No COM port specified'})

    success, result = serial_manager.read_device_id(port)
    if success:
        return jsonify({'success': True, 'device_id': result})
    else:
        return jsonify({'success': False, 'error': result})


# ── API: Stats ──
@devices_bp.route('/api/stats', methods=['GET'])
def get_stats():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM devices WHERE is_bound = 1")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM devices WHERE status = 'online' AND is_bound = 1")
    active = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM devices WHERE status = 'offline' AND is_bound = 1")
    lost = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM devices WHERE status = 'warning' AND is_bound = 1")
    warning = cursor.fetchone()[0]

    conn.close()
    return jsonify({
        'total_buoys': total, 
        'active_buoys': active, 
        'signal_lost': lost,
        'warning_buoys': warning
    })


# ── API: OTA Flash Buoy via WiFi ──
@devices_bp.route('/api/devices/<device_id>/ota-update', methods=['POST'])
def flash_buoy_ota(device_id):
    device_id = device_id.strip().upper()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT ip_address FROM devices WHERE id=?", (device_id,))
    row = cursor.fetchone()
    conn.close()

    if not row or not row['ip_address'] or row['ip_address'] == '0.0.0.0':
        # Fallback to mDNS hostname
        ip_address = f"oceanbuoy-{device_id}.local"
        print(f"[OTA] IP not in database. Falling back to mDNS: {ip_address}")
    else:
        ip_address = row['ip_address']
    
    import os
    import tempfile
    import requests
    
    bin_path = os.path.join(tempfile.gettempdir(), 'buoy_firmware.bin')
    if not os.path.exists(bin_path):
        # Fallback to local PlatformIO build for testing
        local_build_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'Buoyancy', '.pio', 'build', 'esp32dev', 'firmware.bin'))
        if os.path.exists(local_build_path):
            bin_path = local_build_path
            print(f"[OTA] Using local firmware build for testing: {bin_path}")
        else:
            return jsonify({'success': False, 'error': 'Firmware update not downloaded yet, and no local build found.'})
        
    try:
        url = f"http://{ip_address}/update"
        with open(bin_path, 'rb') as f:
            files = {'update': f}
            response = requests.post(url, files=files, timeout=30)
            
        if response.status_code == 200 and "OK" in response.text:
            return jsonify({'success': True, 'message': 'Firmware flashed successfully! Buoy is rebooting.'})
        else:
            return jsonify({'success': False, 'error': f'Flash failed: {response.text}'})
    except Exception as e:
        return jsonify({'success': False, 'error': f'Could not reach Buoy over WiFi: {str(e)}'})
