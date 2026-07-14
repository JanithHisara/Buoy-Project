"""
Serial port and scan APIs.
"""
from flask import Blueprint, request, jsonify
from app.services.serial_service import serial_manager

serial_bp = Blueprint('serial', __name__)


# ── List available COM ports ──
@serial_bp.route('/api/ports', methods=['GET'])
def list_ports():
    ports = serial_manager.list_ports()
    return jsonify(ports)


# ── Connect to a COM port ──
@serial_bp.route('/api/connect', methods=['POST'])
def connect():
    data = request.json
    port = data.get('port', '')
    baud = data.get('baud_rate')

    if not port:
        return jsonify({'success': False, 'error': 'No port specified'})

    success, message = serial_manager.connect(port, baud)
    return jsonify({'success': success, 'message': message})


# ── Disconnect ──
@serial_bp.route('/api/disconnect', methods=['POST'])
def disconnect():
    serial_manager.disconnect()
    return jsonify({'success': True})


# ── Scan unbound buoys ──
@serial_bp.route('/api/scan_unbound', methods=['POST'])
def scan_unbound():
    success, message = serial_manager.scan_unbound()
    return jsonify({'success': success, 'message': message})

# ── Scan bound buoys ──
@serial_bp.route('/api/scan_bound', methods=['POST'])
def scan_bound():
    success, message = serial_manager.scan_bound()
    return jsonify({'success': success, 'message': message})


# ── Get scan/connection status ──
@serial_bp.route('/api/status', methods=['GET'])
def status():
    return jsonify(serial_manager.get_scan_status())


# ── Get GPS data points ──
@serial_bp.route('/api/gps', methods=['GET'])
def get_gps():
    with serial_manager.data_lock:
        points = serial_manager.gps_data.copy()
    return jsonify(points)


# ── Ping and test a specific buoy ──
@serial_bp.route('/api/ping_device', methods=['POST'])
def ping_device():
    data = request.json
    buoy_id = data.get('buoy_id')
    if not buoy_id:
        return jsonify({'success': False, 'error': 'No Buoy ID provided'})

    success_init, result_init = serial_manager.update_buoy_location(buoy_id)
    
    if success_init:
        # We got a GPS fix (cached or live)
        lat = result_init.get('lat', 0.0)
        lon = result_init.get('lon', 0.0)
        return jsonify({'success': True, 'status': 'success', 'lat': lat, 'lon': lon})
    else:
        # Check if it was a connection error
        if isinstance(result_init, str) and "no serial connection" in result_init.lower():
            return jsonify({'success': False, 'status': 'no_connection', 'message': 'Transceiver is not connected. Please connect the Transceiver COM port first.'})
        
        # Check if it responded but had no GPS
        if isinstance(result_init, str) and "responded" in result_init.lower():
            return jsonify({'success': True, 'status': 'success', 'lat': 0.0, 'lon': 0.0})
            
        # Otherwise, no response at all
        return jsonify({'success': False, 'status': 'no_response', 'message': 'Buoyancy is not responding'})

@serial_bp.route('/api/devices/<buoy_id>/update-location', methods=['POST'])
def update_location(buoy_id):
    success, result = serial_manager.update_buoy_location(buoy_id)
    if success:
        return jsonify({
            'success': True,
            'is_cached': True,
            'lat': result.get('lat', 0.0),
            'lon': result.get('lon', 0.0)
        })
    else:
        return jsonify({'success': False, 'error': result})


