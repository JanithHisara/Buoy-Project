# from flask import Flask, render_template, jsonify, request
# import serial.tools.list_ports
# import serial

# app = Flask(__name__)
# ser = None


# # -------------------- UI --------------------
# @app.route("/")
# def index():
#     return render_template("index.html")

# @app.route("/map")
# def map_page():
#     return render_template("map.html")

# @app.route("/devices")
# def devices_page():
#     return render_template("devices.html")

# @app.route("/users")
# def users_page():
#     return render_template("users.html")

# @app.route("/settings")
# def settings_page():
#     return render_template("settings.html")


# # -------------------- LIST PORTS --------------------
# @app.route("/ports")
# def ports():
#     ports = serial.tools.list_ports.comports()
#     return jsonify([p.device for p in ports])


# # -------------------- CONNECT --------------------
# @app.route("/connect", methods=["POST"])
# def connect():
#     global ser

#     port = request.json.get("port")

#     if not port:
#         return jsonify({"status": "error", "message": "No port provided"})

#     try:
#         # Close previous connection
#         if ser and ser.is_open:
#             ser.close()
#             print("Closed previous connection")

#         # Open new connection
#         ser = serial.Serial(port, 115200, timeout=1)
#         print(f"Connected to {port}")

#         return jsonify({"status": "connected", "port": port})

#     except Exception as e:
#         print("Connection error:", e)
#         return jsonify({"status": "error", "message": str(e)})


# # -------------------- SEND SCAN COMMAND --------------------
# @app.route("/scan")
# def scan():
#     global ser

#     if ser and ser.is_open:
#         try:
#             print("Sending: Gps")
#             ser.write(b"Gps\n")
#             return jsonify({"status": "sent"})
#         except Exception as e:
#             print("Write error:", e)
#             return jsonify({"status": "error", "message": str(e)})

#     return jsonify({"status": "no device"})


# # -------------------- READ GPS DATA --------------------
# @app.route("/gps")
# def gps():
#     global ser
#     points = []

#     if ser and ser.is_open:
#         try:
#             while ser.in_waiting > 0:
#                 line = ser.readline().decode(errors="ignore").strip()

#                 if not line:
#                     continue

#                 print("Received:", line)

#                 # Expect: "lat,lon"
#                 if "," in line:
#                     parts = line.split(",")

#                     if len(parts) == 2:
#                         try:
#                             lat = float(parts[0])
#                             lon = float(parts[1])

#                             points.append({
#                                 "lat": lat,
#                                 "lon": lon
#                             })

#                         except ValueError:
#                             print("Invalid numbers:", line)

#         except Exception as e:
#             print("Read error:", e)

#     return jsonify(points)


# # -------------------- RUN SERVER --------------------
# if __name__ == "__main__":
#     print("Starting Flask server...")
#     app.run(debug=True)

##################################################################################################

# from flask import Flask, render_template, jsonify, request, session
# import serial
# import serial.tools.list_ports
# import threading
# import time
# import json
# import os

# app = Flask(__name__)
# app.secret_key = 'oceannav_secret_key_2025'

# # Global variables
# connected_port = None
# ser = None
# gps_data = []
# scanning = False
# serial_lock = threading.Lock()

# # Mock users database
# users_db = [
#     {"id": 1, "name": "Admin Kumar", "email": "admin@oceannav.lk", "role": "admin", "status": "Active", "last_active": "Now", "avatar": "AK", "avatar_bg": "linear-gradient(135deg,#00d4ff,#0077ff)"},
#     {"id": 2, "name": "Nimal Perera", "email": "nimal@oceannav.lk", "role": "user", "status": "Active", "last_active": "5m ago", "avatar": "NP", "avatar_bg": "linear-gradient(135deg,#00e5b0,#0077ff)"},
#     {"id": 3, "name": "Sunil Ranaweera", "email": "sunil@oceannav.lk", "role": "user", "status": "Offline", "last_active": "2h ago", "avatar": "SR", "avatar_bg": "linear-gradient(135deg,#ff6b6b,#ff4757)"},
#     {"id": 4, "name": "Kumari", "email": "kumari@oceannav.lk", "role": "user", "status": "Away", "last_active": "45m ago", "avatar": "KF", "avatar_bg": "linear-gradient(135deg,#ffb830,#ff6b6b)"}
# ]

# # Mock devices database
# devices_db = [
#     {"id": "BUOY-Test", "port": "COM3", "version": "v2.4.1", "lat": 65.9271, "lon": 79.8612, "battery": 87, "signal": 80, "status": "online", "last_ping": "2s ago"},
#     {"id": "BUOY-002", "port": "COM5", "version": "v2.4.1", "lat": 6.9345, "lon": 79.8650, "battery": 92, "signal": 100, "status": "online", "last_ping": "1s ago"},
#     {"id": "BUOY-003", "port": "COM7", "version": "v2.3.0", "lat": 6.9102, "lon": 79.8580, "battery": 12, "signal": 20, "status": "offline", "last_ping": "42m ago"},
#     {"id": "BUOY-004", "port": "COM9", "version": "v2.4.0", "lat": 6.9401, "lon": 79.8700, "battery": 34, "signal": 40, "status": "warning", "last_ping": "8s ago"},
#     {"id": "BUOY-005", "port": "COM11", "version": "v2.4.1", "lat": 6.9180, "lon": 79.8620, "battery": 74, "signal": 75, "status": "online", "last_ping": "3s ago"},
#     {"id": "BUOY-006", "port": "COM13", "version": "v2.4.1", "lat": 6.9520, "lon": 79.8750, "battery": 61, "signal": 85, "status": "online", "last_ping": "5s ago"}
# ]

# @app.route('/')
# def index():
#     return render_template('index.html')

# @app.route('/dashboard')
# def dashboard():
#     if 'user' not in session:
#         return render_template('index.html')
#     return render_template('dashboard.html', user=session['user'])

# @app.route('/devices')
# def devices():
#     if 'user' not in session:
#         return render_template('index.html')
#     return render_template('devices.html', user=session['user'], devices=devices_db)

# @app.route('/map')
# def map_page():
#     if 'user' not in session:
#         return render_template('index.html')
#     return render_template('map.html', user=session['user'])

# @app.route('/settings')
# def settings():
#     if 'user' not in session:
#         return render_template('index.html')
#     return render_template('settings.html', user=session['user'])

# @app.route('/users')
# def users():
#     if 'user' not in session:
#         return render_template('index.html')
#     if session['user']['role'] != 'admin':
#         return render_template('dashboard.html', user=session['user'], error="Access denied")
#     return render_template('users.html', user=session['user'], users=users_db)

# @app.route('/login', methods=['POST'])
# def login():
#     data = request.json
#     email = data.get('email')
#     password = data.get('password')
#     role = data.get('role')
#     name = data.get('name')
    
#     # Mock authentication - in production, validate properly
#     if email and password:
#         user = {
#             'name': name or email.split('@')[0],
#             'email': email,
#             'role': role
#         }
#         session['user'] = user
#         return jsonify({'success': True, 'user': user})
#     return jsonify({'success': False, 'error': 'Invalid credentials'})

# @app.route('/logout', methods=['POST'])
# def logout():
#     session.pop('user', None)
#     return jsonify({'success': True})

# @app.route('/ports', methods=['GET'])
# def get_ports():
#     try:
#         ports = serial.tools.list_ports.comports()
#         port_list = [port.device for port in ports]
#         if not port_list:
#             # Return mock ports for demo
#             port_list = ['COM3', 'COM5', 'COM7', 'COM9', 'COM11', 'COM13']
#         return jsonify(port_list)
#     except Exception as e:
#         print(f"Error listing ports: {e}")
#         # Return mock ports for demo
#         return jsonify(['COM3', 'COM5', 'COM7', 'COM9', 'COM11', 'COM13'])

# @app.route('/connect', methods=['POST'])
# def connect():
#     global ser, connected_port
#     port = request.json.get('port')
#     try:
#         with serial_lock:
#             if ser and ser.is_open:
#                 ser.close()
#             ser = serial.Serial(port, 115200, timeout=1)
#             connected_port = port
#             return jsonify({'success': True, 'message': f'Connected to {port}'})
#     except Exception as e:
#         print(f"Connection error: {e}")
#         return jsonify({'success': False, 'error': str(e), 'message': f'Simulated connection to {port}'})

# @app.route('/scan', methods=['GET', 'POST'])
# def scan():
#     global scanning
#     scanning = True
    
#     # Simulate GPS data collection
#     def collect_gps():
#         global gps_data, scanning
#         time.sleep(2)
#         gps_data = [
#             {"lat": 6, "lon": 79.8612},
#             {"lat": 6.9310, "lon": 79.8650},
#             {"lat": 6.9280, "lon": 79.8700},
#             {"lat": 6.9230, "lon": 79.8680}
#         ]
#         scanning = False
    
#     thread = threading.Thread(target=collect_gps)
#     thread.daemon = True
#     thread.start()
#     return jsonify({'success': True, 'message': 'GPS scan started'})

# @app.route('/gps', methods=['GET'])
# def get_gps():
#     global gps_data
#     data = gps_data.copy()
#     gps_data = []  # Clear after sending
#     return jsonify(data)

# @app.route('/api/devices', methods=['GET'])
# def get_devices():
#     return jsonify(devices_db)

# @app.route('/api/devices/<device_id>', methods=['PUT'])
# def update_device(device_id):
#     data = request.json
#     for device in devices_db:
#         if device['id'] == device_id:
#             device.update(data)
#             return jsonify({'success': True, 'device': device})
#     return jsonify({'success': False, 'error': 'Device not found'})

# @app.route('/api/scan-gps', methods=['POST'])
# def scan_gps():
#     """Real GPS scanning endpoint"""
#     global ser, scanning
#     if not ser or not ser.is_open:
#         return jsonify({'success': False, 'error': 'No serial connection'})
    
#     try:
#         with serial_lock:
#             ser.write(b'AT+GPS=1\r\n')
#             time.sleep(0.5)
#             response = ser.readline().decode('utf-8').strip()
#             return jsonify({'success': True, 'data': response})
#     except Exception as e:
#         return jsonify({'success': False, 'error': str(e)})

# if __name__ == '__main__':
#     # Create templates and static folders if they don't exist
#     os.makedirs('templates', exist_ok=True)
#     os.makedirs('static/css', exist_ok=True)
#     os.makedirs('static/js', exist_ok=True)
    
#     print("=" * 50)
#     print("OceanNav Buoy Navigation System")
#     print("=" * 50)
#     print("Server starting at: http://localhost:5000")
#     print("Press CTRL+C to stop the server")
#     print("=" * 50)
    
#     app.run(debug=True, host='0.0.0.0', port=5000)


#########################################################################


# from flask import Flask, render_template, jsonify, request, session
# import serial.tools.list_ports
# import serial
# import threading
# import time
# import os

# app = Flask(__name__)
# app.secret_key = 'oceannav_secret_key_2025'
# ser = None
# gps_data = []
# scanning = False

# # Mock users database
# users_db = [
#     {"id": 1, "name": "Admin Kumar", "email": "admin@oceannav.lk", "role": "admin", "status": "Active", "last_active": "Now", "avatar": "AK", "avatar_bg": "linear-gradient(135deg,#00d4ff,#0077ff)"},
#     {"id": 2, "name": "Nimal Perera", "email": "nimal@oceannav.lk", "role": "user", "status": "Active", "last_active": "5m ago", "avatar": "NP", "avatar_bg": "linear-gradient(135deg,#00e5b0,#0077ff)"},
#     {"id": 3, "name": "Sunil Ranaweera", "email": "sunil@oceannav.lk", "role": "user", "status": "Offline", "last_active": "2h ago", "avatar": "SR", "avatar_bg": "linear-gradient(135deg,#ff6b6b,#ff4757)"},
#     {"id": 4, "name": "Kumari", "email": "kumari@oceannav.lk", "role": "user", "status": "Away", "last_active": "45m ago", "avatar": "KF", "avatar_bg": "linear-gradient(135deg,#ffb830,#ff6b6b)"}
# ]

# # Mock devices database
# devices_db = [
#     {"id": "BUOY-Test", "port": "COM3", "version": "v2.4.1", "lat": 65.9271, "lon": 79.8612, "battery": 87, "signal": 80, "status": "online", "last_ping": "2s ago"},
#     {"id": "BUOY-002", "port": "COM5", "version": "v2.4.1", "lat": 6.9345, "lon": 79.8650, "battery": 92, "signal": 100, "status": "online", "last_ping": "1s ago"},
#     {"id": "BUOY-003", "port": "COM7", "version": "v2.3.0", "lat": 6.9102, "lon": 79.8580, "battery": 12, "signal": 20, "status": "offline", "last_ping": "42m ago"},
#     {"id": "BUOY-004", "port": "COM9", "version": "v2.4.0", "lat": 6.9401, "lon": 79.8700, "battery": 34, "signal": 40, "status": "warning", "last_ping": "8s ago"},
#     {"id": "BUOY-005", "port": "COM11", "version": "v2.4.1", "lat": 6.9180, "lon": 79.8620, "battery": 74, "signal": 75, "status": "online", "last_ping": "3s ago"},
#     {"id": "BUOY-006", "port": "COM13", "version": "v2.4.1", "lat": 6.9520, "lon": 79.8750, "battery": 61, "signal": 85, "status": "online", "last_ping": "5s ago"}
# ]

# # -------------------- UI ROUTES --------------------
# @app.route('/')
# def index():
#     return render_template('index.html')

# @app.route('/dashboard')
# def dashboard():
#     if 'user' not in session:
#         return render_template('index.html')
#     return render_template('dashboard.html', user=session['user'])

# @app.route('/devices')
# def devices():
#     if 'user' not in session:
#         return render_template('index.html')
#     return render_template('devices.html', user=session['user'], devices=devices_db)

# @app.route('/map')
# def map_page():
#     if 'user' not in session:
#         return render_template('index.html')
#     return render_template('map.html', user=session['user'])

# @app.route('/settings')
# def settings():
#     if 'user' not in session:
#         return render_template('index.html')
#     return render_template('settings.html', user=session['user'])

# @app.route('/users')
# def users():
#     if 'user' not in session:
#         return render_template('index.html')
#     if session['user']['role'] != 'admin':
#         return render_template('dashboard.html', user=session['user'], error="Access denied")
#     return render_template('users.html', user=session['user'], users=users_db)

# @app.route('/login', methods=['POST'])
# def login():
#     data = request.json
#     email = data.get('email')
#     password = data.get('password')
#     role = data.get('role')
#     name = data.get('name')
    
#     if email and password:
#         user = {
#             'name': name or email.split('@')[0],
#             'email': email,
#             'role': role
#         }
#         session['user'] = user
#         return jsonify({'success': True, 'user': user})
#     return jsonify({'success': False, 'error': 'Invalid credentials'})

# @app.route('/logout', methods=['POST'])
# def logout():
#     session.pop('user', None)
#     return jsonify({'success': True})

# # -------------------- LIST PORTS --------------------
# @app.route('/ports', methods=['GET'])
# def get_ports():
#     try:
#         ports = serial.tools.list_ports.comports()
#         port_list = [port.device for port in ports]
#         if not port_list:
#             port_list = ['COM3', 'COM5', 'COM7', 'COM9', 'COM11', 'COM13']
#         return jsonify(port_list)
#     except Exception as e:
#         print(f"Error listing ports: {e}")
#         return jsonify(['COM3', 'COM5', 'COM7', 'COM9', 'COM11', 'COM13'])

# # -------------------- CONNECT --------------------
# @app.route('/connect', methods=['POST'])
# def connect():
#     global ser
    
#     port = request.json.get('port')
    
#     if not port:
#         return jsonify({"status": "error", "message": "No port provided"})
    
#     try:
#         if ser and ser.is_open:
#             ser.close()
#             print("Closed previous connection")
        
#         ser = serial.Serial(port, 115200, timeout=1)
#         print(f"Connected to {port}")
        
#         return jsonify({"status": "connected", "port": port})
    
#     except Exception as e:
#         print("Connection error:", e)
#         return jsonify({"status": "error", "message": str(e)})

# # -------------------- SEND SCAN COMMAND --------------------
# @app.route('/scan', methods=['GET', 'POST'])
# def scan():
#     global ser, scanning, gps_data
    
#     if not ser or not ser.is_open:
#         return jsonify({"status": "no device", "error": "No serial connection"})
    
#     try:
#         print("Sending: GPS")
#         ser.write(b"GPS\n")
#         ser.flush()
        
#         # Start reading in background
#         scanning = True
#         gps_data = []
        
#         def read_gps_data():
#             global gps_data, scanning
#             time.sleep(0.5)  # Give ESP32 time to respond
            
#             try:
#                 # Read all available lines
#                 while ser.in_waiting > 0 and len(gps_data) < 10:
#                     line = ser.readline().decode(errors="ignore").strip()
                    
#                     if not line:
#                         continue
                    
#                     print("Received:", line)
                    
#                     # Parse comma-separated format: "lat,lon"
#                     if "," in line:
#                         parts = line.split(",")
#                         if len(parts) == 2:
#                             try:
#                                 lat = float(parts[0].strip())
#                                 lon = float(parts[1].strip())
                                
#                                 gps_data.append({
#                                     "lat": lat,
#                                     "lon": lon
#                                 })
#                                 print(f"Parsed: lat={lat}, lon={lon}")
                                
#                             except ValueError:
#                                 print("Invalid numbers:", line)
                    
#                     # Also handle JSON format if needed
#                     elif line.startswith('[') and line.endswith(']'):
#                         import json
#                         try:
#                             json_data = json.loads(line)
#                             if isinstance(json_data, list):
#                                 for item in json_data:
#                                     if 'lat' in item and 'lon' in item:
#                                         gps_data.append({
#                                             "lat": item['lat'],
#                                             "lon": item['lon']
#                                         })
#                                 print(f"Parsed {len(json_data)} locations from JSON")
#                         except:
#                             print("Failed to parse JSON")
                
#             except Exception as e:
#                 print("Read error:", e)
#             finally:
#                 scanning = False
        
#         # Start reading thread
#         thread = threading.Thread(target=read_gps_data)
#         thread.daemon = True
#         thread.start()
        
#         return jsonify({"status": "sent", "message": "GPS command sent"})
        
#     except Exception as e:
#         print("Write error:", e)
#         return jsonify({"status": "error", "message": str(e)})

# # -------------------- READ GPS DATA --------------------
# @app.route('/gps', methods=['GET'])
# def get_gps():
#     global gps_data, scanning
    
#     if scanning:
#         return jsonify({
#             "status": "scanning",
#             "message": "GPS scan in progress...",
#             "data": []
#         })
    
#     # Return collected GPS points
#     points = gps_data.copy()
    
#     # Clear after sending (optional - comment out if you want to keep data)
#     # gps_data = []
    
#     print(f"Returning {len(points)} GPS points")
#     return jsonify(points)

# # -------------------- API ROUTES --------------------
# @app.route('/api/devices', methods=['GET'])
# def get_devices():
#     return jsonify(devices_db)

# @app.route('/api/devices/<device_id>', methods=['PUT'])
# def update_device(device_id):
#     data = request.json
#     for device in devices_db:
#         if device['id'] == device_id:
#             device.update(data)
#             return jsonify({'success': True, 'device': device})
#     return jsonify({'success': False, 'error': 'Device not found'})

# @app.route('/connection-status', methods=['GET'])
# def connection_status():
#     global ser
#     return jsonify({
#         'connected': ser is not None and ser.is_open,
#         'port': ser.port if ser and ser.is_open else None,
#         'scanning': scanning,
#         'gps_points': len(gps_data)
#     })

# # -------------------- RUN SERVER --------------------
# if __name__ == '__main__':
#     os.makedirs('templates', exist_ok=True)
#     os.makedirs('static/css', exist_ok=True)
#     os.makedirs('static/js', exist_ok=True)
    
#     print("=" * 50)
#     print("OceanNav Buoy Navigation System")
#     print("=" * 50)
#     print("Server starting at: http://localhost:5000")
#     print("Press CTRL+C to stop the server")
#     print("=" * 50)
    
#     app.run(debug=True, host='0.0.0.0', port=5000)


from flask import Flask, render_template, jsonify, request, session, Response
import serial.tools.list_ports
import serial
import threading
import time
import os
import random
from collections import deque
import sqlite3

app = Flask(__name__)
app.secret_key = 'oceannav_secret_key_2025'

# Cache map tiles aggressively for high performance
@app.after_request
def add_header(response):
    if request.path and request.path.startswith('/static/tiles/'):
        response.cache_control.max_age = 31536000 # 1 year
        response.cache_control.public = True
    return response

ser = None
gps_data = []
scanning = False
scan_complete = False
last_scan_time = 0
device_located_flag = False
data_lock = threading.Lock()

# Real hardware tracking variables
connected_trx_id = "1234567890AB"
last_buoyancy_id = None
latest_buoy_gps = {}

def serial_listener_loop():
    global ser, gps_data, scanning, scan_complete, device_located_flag
    global connected_trx_id, last_buoyancy_id, latest_buoy_gps
    
    while True:
        try:
            if ser and ser.is_open:
                if ser.in_waiting > 0:
                    line = ser.readline().decode(errors="ignore").strip()
                    if line:
                        print(f"[Serial] Received: {line}")
                        
                        # Handle ESP32 "DEVICE_LOCATED" boot event
                        if "DEVICE_LOCATED" in line:
                            with data_lock:
                                device_located_flag = True
                            print("[Serial] Boot Event Detected: ESP32 Located!")
                            if last_buoyancy_id:
                                try:
                                    conn = sqlite3.connect(DATABASE)
                                    cursor = conn.cursor()
                                    cursor.execute('''
                                        UPDATE devices
                                        SET status = 'online', last_ping = 'Just now'
                                        WHERE id = ?
                                    ''', (last_buoyancy_id,))
                                    conn.commit()
                                    conn.close()
                                    print(f"[Serial] Marked device {last_buoyancy_id} as online via boot event")
                                except Exception as db_err:
                                    print("[Serial] Database error marking device online:", db_err)
                            
                        # Detect Transceiver ID from serial output
                        elif "TRX ID :" in line:
                            parts = line.split("TRX ID :")
                            if len(parts) > 1:
                                connected_trx_id = parts[1].strip().upper()
                                print(f"[Serial] Connected Transceiver ID: {connected_trx_id}")

                        # Detect Buoyancy ID header bracket format: e.g. <240ac4090b8c,240ac4090b8d>
                        elif line.startswith("<") and ">" in line:
                            header = line.replace("<", "").replace(">", "")
                            parts = header.split(",")
                            if len(parts) >= 2:
                                last_buoyancy_id = parts[1].strip().upper()
                                print(f"[Serial] Last Buoyancy ID set to: {last_buoyancy_id}")

                        # Handle +CGPSINFO data points
                        elif "+CGPSINFO:" in line:
                            parts = line.split("+CGPSINFO:")
                            if len(parts) > 1 and parts[1].strip():
                                coord_parts = parts[1].split(",")
                                if len(coord_parts) >= 2:
                                    try:
                                        lat = float(coord_parts[0].strip())
                                        lon = float(coord_parts[1].strip())
                                        
                                        # Save to latest buoy GPS cache (including 0.0 for fix status checks)
                                        if last_buoyancy_id:
                                            with data_lock:
                                                latest_buoy_gps[last_buoyancy_id] = {
                                                    "lat": lat,
                                                    "lon": lon,
                                                    "timestamp": time.time()
                                                }
                                                
                                        # Ensure valid GPS lock coordinates for map path and database logs
                                        if lat != 0.0 and lon != 0.0:
                                            with data_lock:
                                                gps_data.append({
                                                    "lat": lat,
                                                    "lon": lon
                                                })
                                                # Limit coordinates cache size
                                                if len(gps_data) > 100:
                                                    gps_data.pop(0)
                                                    
                                            # Save to SQLite DB
                                            try:
                                                conn = sqlite3.connect('oceannav.db')
                                                cursor = conn.cursor()
                                                cursor.execute('''
                                                    INSERT INTO gps_logs (device_id, lat, lon)
                                                    VALUES (?, ?, ?)
                                                ''', (last_buoyancy_id or ser.port, lat, lon))
                                                
                                                if last_buoyancy_id:
                                                    cursor.execute('''
                                                        UPDATE devices
                                                        SET lat = ?, lon = ?, status = 'online', last_ping = 'Just now'
                                                        WHERE id = ?
                                                    ''', (lat, lon, last_buoyancy_id))
                                                    
                                                conn.commit()
                                                conn.close()
                                            except Exception as db_err:
                                                print("[Serial] Database GPS save/update error:", db_err)
                                                
                                            print(f"[Serial] Parsed GPS coordinate: lat={lat}, lon={lon} for buoy={last_buoyancy_id}")
                                        else:
                                            print(f"[Serial] GPS module responded but has no satellite lock yet (lat=0.0, lon=0.0)")
                                    except ValueError:
                                        pass
                                    
                        # Handle original legacy simulated/fallback data points if they are direct coords
                        elif "," in line and not line.startswith("{"):
                            parts = line.split(",")
                            if len(parts) >= 2:
                                try:
                                    lat = float(parts[0].strip())
                                    lon = float(parts[1].strip())
                                    
                                    with data_lock:
                                        gps_data.append({
                                            "lat": lat,
                                            "lon": lon
                                        })
                                        if len(gps_data) > 100:
                                            gps_data.pop(0)
                                            
                                    try:
                                        conn = sqlite3.connect('oceannav.db')
                                        cursor = conn.cursor()
                                        cursor.execute('''
                                            INSERT INTO gps_logs (device_id, lat, lon)
                                            VALUES (?, ?, ?)
                                        ''', (ser.port, lat, lon))
                                        conn.commit()
                                        conn.close()
                                    except Exception as db_err:
                                        print("[Serial] Database GPS save error:", db_err)
                                        
                                    print(f"[Serial] Parsed direct GPS coordinate: lat={lat}, lon={lon}")
                                except ValueError:
                                    pass
            else:
                time.sleep(0.5)
        except Exception as e:
            print("[Serial] Reader error:", e)
            try:
                if ser:
                    ser.close()
            except:
                pass
            ser = None
            time.sleep(1.0)
        time.sleep(0.05)

# Spawn permanent background listener thread
listener_thread = threading.Thread(target=serial_listener_loop)
listener_thread.daemon = True
listener_thread.start()

DATABASE = 'oceannav.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        # Check if users table lacks password column or has old constraint
        cursor = conn.cursor()
        drop_table = False
        try:
            cursor.execute("SELECT password FROM users LIMIT 1")
            
            # Verify constraint allows super_admin
            cursor.execute("SAVEPOINT test_constraint")
            try:
                cursor.execute('''
                    INSERT INTO users (name, email, password, role, avatar, avatar_bg)
                    VALUES ('Test', 'test_dummy@gmail.com', 'pwd', 'super_admin', 'TS', 'bg')
                ''')
            except sqlite3.IntegrityError:
                drop_table = True
            finally:
                cursor.execute("ROLLBACK TO test_constraint")
        except sqlite3.OperationalError:
            # Table users might not exist or password column is missing
            drop_table = True
            
        if drop_table:
            print("Upgrading database: dropping users table to apply new role constraints and columns")
            conn.execute("DROP TABLE IF EXISTS users")

        # Create users table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('super_admin', 'admin', 'user')),
                status TEXT DEFAULT 'Active',
                last_active TEXT DEFAULT 'Now',
                avatar TEXT NOT NULL,
                avatar_bg TEXT NOT NULL
            )
        ''')
        
        # Create devices table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS devices (
                id TEXT PRIMARY KEY,
                port TEXT,
                version TEXT DEFAULT 'v2.4.1',
                lat REAL NOT NULL,
                lon REAL NOT NULL,
                battery INTEGER DEFAULT 100,
                signal INTEGER DEFAULT 100,
                status TEXT DEFAULT 'online',
                last_ping TEXT DEFAULT 'Just now',
                active INTEGER DEFAULT 1
            )
        ''')
        
        # Create gps_logs table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS gps_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT,
                lat REAL NOT NULL,
                lon REAL NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Seed users if empty
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            users_db = [
                {"name": "Super Admin", "email": "superadmin@oceannav.lk", "password": "password", "role": "super_admin", "status": "Active", "last_active": "Now", "avatar": "SA", "avatar_bg": "linear-gradient(135deg,#7b2cbf,#3c096c)"},
                {"name": "Admin Kumar", "email": "admin@oceannav.lk", "password": "password", "role": "admin", "status": "Active", "last_active": "Now", "avatar": "AK", "avatar_bg": "linear-gradient(135deg,#00d4ff,#0077ff)"}
            ]
            conn.executemany('''
                INSERT INTO users (name, email, password, role, status, last_active, avatar, avatar_bg)
                VALUES (:name, :email, :password, :role, :status, :last_active, :avatar, :avatar_bg)
            ''', users_db)
        
        
        conn.commit()

init_db()

# -------------------- UI ROUTES --------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return render_template('index.html')
    return render_template('dashboard.html', user=session['user'])

@app.route('/devices')
def devices():
    if 'user' not in session:
        return render_template('index.html')
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM devices")
    devices_list = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return render_template('devices.html', user=session['user'], devices=devices_list)

@app.route('/map')
def map_page():
    if 'user' not in session:
        return render_template('index.html')
    return render_template('map.html', user=session['user'])

@app.route('/settings')
def settings():
    if 'user' not in session:
        return render_template('index.html')
    return render_template('settings.html', user=session['user'])

@app.route('/users')
def users():
    if 'user' not in session:
        return render_template('index.html')
    if session['user']['role'] not in ('admin', 'super_admin'):
        return render_template('dashboard.html', user=session['user'], error="Access denied")
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT name, email, role, status, last_active, avatar, avatar_bg FROM users")
    users_list = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return render_template('users.html', user=session['user'], users=users_list)

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'success': False, 'error': 'Missing email or password'})
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT name, email, password, role, status, last_active, avatar, avatar_bg FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        user = dict(row)
        if user['password'] == password:
            user.pop('password')
            session['user'] = user
            return jsonify({'success': True, 'user': user})
        else:
            return jsonify({'success': False, 'error': 'Incorrect password'})
    return jsonify({'success': False, 'error': 'Account not found. Switch to Sign Up mode to register.'})

@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'user')
    
    if not name or not email or not password:
        return jsonify({'success': False, 'error': 'All fields are required'})
        
    if not email.endswith('@gmail.com'):
        return jsonify({'success': False, 'error': 'Please use a valid @gmail.com address'})
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    if cursor.fetchone():
        conn.close()
        return jsonify({'success': False, 'error': 'Email is already registered'})
        
    avatar = "".join([part[0].upper() for part in name.split() if part])[:2]
    if not avatar:
        avatar = "US"
        
    gradients = [
        "linear-gradient(135deg,#00d4ff,#0077ff)",
        "linear-gradient(135deg,#00e5b0,#0077ff)",
        "linear-gradient(135deg,#ff6b6b,#ff4757)",
        "linear-gradient(135deg,#ffb830,#ff6b6b)"
    ]
    avatar_bg = random.choice(gradients)
    
    try:
        cursor.execute('''
            INSERT INTO users (name, email, password, role, status, last_active, avatar, avatar_bg)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, email, password, role, 'Active', 'Now', avatar, avatar_bg))
        conn.commit()
        
        cursor.execute("SELECT name, email, role, status, last_active, avatar, avatar_bg FROM users WHERE email = ?", (email,))
        user = dict(cursor.fetchone())
        session['user'] = user
        success = True
    except Exception as e:
        print("Database error during signup:", e)
        success = False
    finally:
        conn.close()
        
    if success:
        return jsonify({'success': True, 'user': user})
    return jsonify({'success': False, 'error': 'Signup failed'})

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user', None)
    return jsonify({'success': True})

# -------------------- SUPER ADMIN APIS --------------------
@app.route('/api/users', methods=['POST'])
def api_add_user():
    if 'user' not in session or session['user']['role'] != 'super_admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
    data = request.json
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'user')
    
    if not name or not email or not password:
        return jsonify({'success': False, 'error': 'All fields are required'})
        
    if not email.endswith('@gmail.com') and not email.endswith('@oceannav.lk'):
        return jsonify({'success': False, 'error': 'Please use a valid @gmail.com or @oceannav.lk address'})
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    if cursor.fetchone():
        conn.close()
        return jsonify({'success': False, 'error': 'Email is already registered'})
        
    avatar = "".join([part[0].upper() for part in name.split() if part])[:2]
    if not avatar:
        avatar = "US"
        
    gradients = [
        "linear-gradient(135deg,#00d4ff,#0077ff)",
        "linear-gradient(135deg,#00e5b0,#0077ff)",
        "linear-gradient(135deg,#ff6b6b,#ff4757)",
        "linear-gradient(135deg,#ffb830,#ff6b6b)"
    ]
    avatar_bg = random.choice(gradients)
    
    try:
        cursor.execute('''
            INSERT INTO users (name, email, password, role, status, last_active, avatar, avatar_bg)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, email, password, role, 'Active', 'Now', avatar, avatar_bg))
        conn.commit()
        success = True
    except Exception as e:
        print("Database error during api signup:", e)
        success = False
    finally:
        conn.close()
        
    if success:
        return jsonify({'success': True, 'message': f'User {name} registered'})
    return jsonify({'success': False, 'error': 'Registration failed'})

@app.route('/api/users/<email>/role', methods=['PUT'])
def api_update_user_role(email):
    if 'user' not in session or session['user']['role'] != 'super_admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
    if session['user']['email'] == email:
        return jsonify({'success': False, 'error': 'Cannot modify your own role'})
        
    data = request.json
    role = data.get('role')
    if role not in ('admin', 'user', 'super_admin'):
        return jsonify({'success': False, 'error': 'Invalid role'})
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET role = ? WHERE email = ?", (role, email))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Role updated successfully'})

@app.route('/api/users/<email>', methods=['DELETE'])
def api_delete_user(email):
    if 'user' not in session or session['user']['role'] != 'super_admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
    if session['user']['email'] == email:
        return jsonify({'success': False, 'error': 'Cannot terminate your own account'})
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE email = ?", (email,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'User terminated successfully'})

# -------------------- STATS API --------------------
@app.route('/api/stats', methods=['GET'])
def get_stats():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM devices")
    total_buoys = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM devices WHERE status = 'online'")
    active_buoys = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM devices WHERE status IN ('offline', 'warning')")
    signal_lost = cursor.fetchone()[0]
    
    conn.close()
    
    return jsonify({
        'total_buoys': total_buoys,
        'active_buoys': active_buoys,
        'signal_lost': signal_lost
    })

# -------------------- LIST PORTS --------------------
@app.route('/ports', methods=['GET'])
def get_ports():
    try:
        ports = serial.tools.list_ports.comports()
        port_list = [port.device for port in ports]
        if not port_list:
            port_list = ['COM3', 'COM5', 'COM7', 'COM9', 'COM11', 'COM13']
        return jsonify(port_list)
    except Exception as e:
        print(f"Error listing ports: {e}")
        return jsonify(['COM3', 'COM5', 'COM7', 'COM9', 'COM11', 'COM13'])

# -------------------- CONNECT --------------------
@app.route('/connect', methods=['POST'])
def connect():
    global ser, device_located_flag, gps_data
    
    port = request.json.get('port')
    
    if not port:
        return jsonify({"status": "error", "message": "No port provided"})
    
    try:
        if ser and ser.is_open:
            ser.close()
            print("Closed previous connection")
        
        # Reset flags and data
        with data_lock:
            device_located_flag = False
            gps_data = []
            
        # Connect to serial port
        ser = serial.Serial(port, 115200, timeout=1)
        
        # Force ESP32 to reset by toggling DTR and RTS lines
        print(f"Resetting ESP32 on {port} to capture TRX ID...")
        ser.dtr = False
        ser.rts = True
        time.sleep(0.1)
        ser.dtr = True
        ser.rts = False
        time.sleep(0.6)  # Give ESP32 time to start boot sequence
        
        print(f"Connected to {port}")
        return jsonify({"status": "connected", "port": port})
    
    except Exception as e:
        print("Connection error:", e)
        return jsonify({"status": "error", "message": str(e)})

# -------------------- SEND SCAN COMMAND --------------------
@app.route('/scan', methods=['GET', 'POST'])
def scan():
    global ser, scanning, scan_complete, gps_data, last_scan_time, connected_trx_id
    
    if not ser or not ser.is_open:
        return jsonify({"status": "no device", "error": "No serial connection"})
        
    # Get device ID if provided in JSON payload
    device_id = None
    if request.is_json:
        device_id = request.json.get("device_id")
    elif request.method == 'POST' and request.values:
        device_id = request.values.get("device_id")
    elif request.method == 'GET' and request.args:
        device_id = request.args.get("device_id")
        
    if device_id:
        device_id = device_id.strip().upper()
    
    try:
        # Reset coordinate cache on start of new scan
        with data_lock:
            gps_data = []
            scanning = True
            scan_complete = False
            
        # Send command triggers to ESP32
        if device_id:
            print(f"Sending real hardware queries for scan of buoy: {device_id}")
            # Bind, turn on GPS, and request info
            ser.write(f"<{connected_trx_id},{device_id}>,AT+BIND=0\n".encode())
            time.sleep(1.2)
            ser.write(f"<{connected_trx_id},{device_id}>,AT+BIND=1\n".encode())
            time.sleep(1.2)
            ser.write(f"<{connected_trx_id},{device_id}>,AT+CGPS=1\n".encode())
            time.sleep(1.2)
            ser.write(f"<{connected_trx_id},{device_id}>,AT+CGPSINFO\n".encode())
        else:
            print("Sending general scan trigger command to ESP32...")
            ser.write(f"<{connected_trx_id},ALL>,AT+SCAN\n".encode())
            
        ser.flush()
        last_scan_time = time.time()
        
        # Simulation delay simulator trigger
        def finish_scanning():
            global scanning, scan_complete
            time.sleep(8.0)  # Wait 8 seconds for coordinates to collect due to delays
            with data_lock:
                scanning = False
                scan_complete = True
            print("Scan polling duration completed")
            
        threading.Thread(target=finish_scanning).start()
        
        return jsonify({"status": "sent", "message": "GPS command sent, collecting data..."})
        
    except Exception as e:
        print("Write error:", e)
        scanning = False
        return jsonify({"status": "error", "message": str(e)})

# -------------------- READ GPS DATA --------------------
@app.route('/gps', methods=['GET'])
def get_gps():
    global gps_data
    with data_lock:
        points = gps_data.copy()
    print(f"Returning {len(points)} GPS points")
    return jsonify(points)

# -------------------- NEW ENDPOINT: ADD DEVICE WITH RANDOM LOCATION --------------------
@app.route('/gps/device_id', methods=['POST'])
def get_gps_for_device():
    global ser, connected_trx_id, latest_buoy_gps
    data = request.json
    device_id = data.get('device_id')
    device_name = data.get('device_name')
    
    if device_id:
        device_id = device_id.strip().upper()
        
    print(f"Adding new device: Name={device_name}, ID={device_id}")
    
    # If serial is connected, send real commands to query physical hardware location
    if ser and ser.is_open:
        try:
            # Clear previous cache for this device
            with data_lock:
                if device_id and device_id in latest_buoy_gps:
                    del latest_buoy_gps[device_id]
            
            # Send bind, gps power on, and query commands
            print(f"Sending real hardware queries for device setup: {device_id}")
            ser.write(f"<{connected_trx_id},{device_id}>,AT+BIND=0\n".encode())
            time.sleep(1.2)
            ser.write(f"<{connected_trx_id},{device_id}>,AT+BIND=1\n".encode())
            time.sleep(1.2)
            ser.write(f"<{connected_trx_id},{device_id}>,AT+CGPS=1\n".encode())
            time.sleep(1.2)
            ser.write(f"<{connected_trx_id},{device_id}>,AT+CGPSINFO\n".encode())
            ser.flush()
            
            # Wait for coordinates to arrive (up to 10 seconds due to increased delays and hardware response times)
            start_time = time.time()
            lat, lon = None, None
            while time.time() - start_time < 10.0:
                with data_lock:
                    if device_id in latest_buoy_gps:
                        lat = latest_buoy_gps[device_id]['lat']
                        lon = latest_buoy_gps[device_id]['lon']
                        break
                time.sleep(0.2)
                
            if lat is not None and lon is not None:
                # If coordinates are 0.0, the hardware is connected but has no lock
                if lat == 0.0 and lon == 0.0:
                    return jsonify({
                        'success': False,
                        'error': 'GPS module connected but waiting for satellite lock (move outdoors / clear sky view required)'
                    })
                return jsonify({
                    'success': True,
                    'lat': lat,
                    'lon': lon,
                    'message': f'Real GPS coordinates retrieved for {device_name}'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Buoyancy hardware did not respond. Check LoRa range and power.'
                })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Serial communication error: {str(e)}'
            })
            
    return jsonify({
        'success': False,
        'error': 'No serial connection to Transceiver'
    })

# -------------------- API ROUTES --------------------
@app.route('/api/devices', methods=['GET'])
def get_devices():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM devices")
    devices_list = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(devices_list)

@app.route('/api/devices', methods=['POST'])
def add_device():
    data = request.json
    device_id = data.get('id')
    name = data.get('name')
    lat = data.get('lat')
    lon = data.get('lon')
    
    if not device_id or not name:
        return jsonify({'success': False, 'error': 'Missing device ID or name'})
        
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO devices (id, port, version, lat, lon, battery, signal, status, last_ping, active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (device_id, 'COM' + str(random.randint(3,15)), 'v2.4.1', lat, lon, 100, 100, 'online', 'Just now', 1))
        conn.commit()
        success = True
        error = None
    except sqlite3.IntegrityError:
        success = False
        error = f'Device with ID {device_id} already exists'
    finally:
        conn.close()
        
    if success:
        return jsonify({'success': True, 'message': f'Device {name} added'})
    else:
        return jsonify({'success': False, 'error': error})

@app.route('/api/devices/<device_id>', methods=['PUT'])
def update_device(device_id):
    data = request.json
    active = data.get('active')
    
    conn = get_db()
    cursor = conn.cursor()
    if active is not None:
        active_val = 1 if active else 0
        status_val = 'online' if active else 'offline'
        cursor.execute('''
            UPDATE devices SET active = ?, status = ? WHERE id = ?
        ''', (active_val, status_val, device_id))
    else:
        name = data.get('name')
        lat = data.get('lat')
        lon = data.get('lon')
        cursor.execute('''
            UPDATE devices SET lat = ?, lon = ? WHERE id = ?
        ''', (lat, lon, device_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/devices/<device_id>', methods=['DELETE'])
def delete_device(device_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM devices WHERE id = ?", (device_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Device deleted'})

@app.route('/connection-status', methods=['GET'])
def connection_status():
    global ser, scanning, gps_data, device_located_flag
    
    located = False
    with data_lock:
        if device_located_flag:
            located = True
            device_located_flag = False  # Reset flag so notification only fires once
            
    return jsonify({
        'connected': ser is not None and ser.is_open,
        'port': ser.port if ser and ser.is_open else None,
        'scanning': scanning,
        'gps_points': len(gps_data),
        'device_located': located
    })

# -------------------- OFFLINE VECTOR TILE SERVER --------------------
@app.route('/tiles/<int:z>/<int:x>/<int:y>.pbf')
def get_mbtiles_tile(z, x, y):
    try:
        db_path = os.path.join(app.root_path, 'sri_lanka.mbtiles', 'osm-2020-02-10-v3.11_asia_sri-lanka.mbtiles')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # TMS coordinate system Y-flip
        tms_y = (1 << z) - 1 - y
        
        cursor.execute("SELECT tile_data FROM tiles WHERE zoom_level=? AND tile_column=? AND tile_row=?", (z, x, tms_y))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            response = Response(row[0], mimetype='application/x-protobuf')
            response.headers['Content-Encoding'] = 'gzip'
            # Cache tiles for high performance
            response.cache_control.max_age = 31536000 # 1 year
            response.cache_control.public = True
            return response
        else:
            return '', 404
    except Exception as e:
        print(f"[Tiles] Error serving tile: {e}")
        return '', 500

# -------------------- RUN SERVER --------------------
if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    print("=" * 50)
    print("OceanNav Buoy Navigation System")
    print("=" * 50)
    print("Server starting at: http://localhost:5000")
    print("Press CTRL+C to stop the server")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)