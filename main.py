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


from flask import Flask, render_template, jsonify, request, session
import serial.tools.list_ports
import serial
import threading
import time
import os
import random
from collections import deque

app = Flask(__name__)
app.secret_key = 'oceannav_secret_key_2025'
ser = None
gps_data = []
scanning = False
scan_complete = False
last_scan_time = 0
data_lock = threading.Lock()

# Mock users database
users_db = [
    {"id": 1, "name": "Admin Kumar", "email": "admin@oceannav.lk", "role": "admin", "status": "Active", "last_active": "Now", "avatar": "AK", "avatar_bg": "linear-gradient(135deg,#00d4ff,#0077ff)"},
    {"id": 2, "name": "Nimal Perera", "email": "nimal@oceannav.lk", "role": "user", "status": "Active", "last_active": "5m ago", "avatar": "NP", "avatar_bg": "linear-gradient(135deg,#00e5b0,#0077ff)"},
    {"id": 3, "name": "Sunil Ranaweera", "email": "sunil@oceannav.lk", "role": "user", "status": "Offline", "last_active": "2h ago", "avatar": "SR", "avatar_bg": "linear-gradient(135deg,#ff6b6b,#ff4757)"},
    {"id": 4, "name": "Kumari", "email": "kumari@oceannav.lk", "role": "user", "status": "Away", "last_active": "45m ago", "avatar": "KF", "avatar_bg": "linear-gradient(135deg,#ffb830,#ff6b6b)"}
]

# Mock devices database
devices_db = [
    {"id": "BUOY-Test", "port": "COM3", "version": "v2.4.1", "lat": 65.9271, "lon": 79.8612, "battery": 87, "signal": 80, "status": "online", "last_ping": "2s ago"},
    {"id": "BUOY-002", "port": "COM5", "version": "v2.4.1", "lat": 6.9345, "lon": 79.8650, "battery": 92, "signal": 100, "status": "online", "last_ping": "1s ago"},
    {"id": "BUOY-003", "port": "COM7", "version": "v2.3.0", "lat": 6.9102, "lon": 79.8580, "battery": 12, "signal": 20, "status": "offline", "last_ping": "42m ago"},
    {"id": "BUOY-004", "port": "COM9", "version": "v2.4.0", "lat": 6.9401, "lon": 79.8700, "battery": 34, "signal": 40, "status": "warning", "last_ping": "8s ago"},
    {"id": "BUOY-005", "port": "COM11", "version": "v2.4.1", "lat": 6.9180, "lon": 79.8620, "battery": 74, "signal": 75, "status": "online", "last_ping": "3s ago"},
    {"id": "BUOY-006", "port": "COM13", "version": "v2.4.1", "lat": 6.9520, "lon": 79.8750, "battery": 61, "signal": 85, "status": "online", "last_ping": "5s ago"}
]

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
    return render_template('devices.html', user=session['user'], devices=devices_db)

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
    if session['user']['role'] != 'admin':
        return render_template('dashboard.html', user=session['user'], error="Access denied")
    return render_template('users.html', user=session['user'], users=users_db)

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    role = data.get('role')
    name = data.get('name')
    
    if email and password:
        user = {
            'name': name or email.split('@')[0],
            'email': email,
            'role': role
        }
        session['user'] = user
        return jsonify({'success': True, 'user': user})
    return jsonify({'success': False, 'error': 'Invalid credentials'})

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user', None)
    return jsonify({'success': True})

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
    global ser
    
    port = request.json.get('port')
    
    if not port:
        return jsonify({"status": "error", "message": "No port provided"})
    
    try:
        if ser and ser.is_open:
            ser.close()
            print("Closed previous connection")
        
        ser = serial.Serial(port, 115200, timeout=1)
        print(f"Connected to {port}")
        
        return jsonify({"status": "connected", "port": port})
    
    except Exception as e:
        print("Connection error:", e)
        return jsonify({"status": "error", "message": str(e)})

# -------------------- SEND SCAN COMMAND --------------------
@app.route('/scan', methods=['GET', 'POST'])
def scan():
    global ser, scanning, scan_complete, gps_data, last_scan_time
    
    if not ser or not ser.is_open:
        return jsonify({"status": "no device", "error": "No serial connection"})
    
    try:
        # Clear previous data
        with data_lock:
            gps_data = []
            scanning = True
            scan_complete = False
        
        # Send command
        print("Sending: GPS")
        ser.write(b"GPS\n")
        ser.flush()
        
        last_scan_time = time.time()
        
        # Start reading thread
        def read_gps_data():
            global gps_data, scanning, scan_complete
            
            try:
                time.sleep(0.3)  # Give ESP32 time to respond
                points_collected = 0
                start_time = time.time()
                
                # Read for up to 3 seconds
                while time.time() - start_time < 3:
                    if ser.in_waiting > 0:
                        line = ser.readline().decode(errors="ignore").strip()
                        
                        if not line:
                            continue
                        
                        print(f"Received: {line}")
                        
                        # Parse comma-separated format: "lat,lon"
                        if "," in line and not line.startswith('{'):
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
                                        points_collected += 1
                                    
                                    print(f"Parsed {points_collected}: lat={lat}, lon={lon}")
                                    
                                except ValueError as e:
                                    print(f"Invalid numbers in: {line} - {e}")
                        
                        # Parse JSON format
                        elif line.startswith('[') and line.endswith(']'):
                            import json
                            try:
                                json_data = json.loads(line)
                                if isinstance(json_data, list):
                                    for item in json_data:
                                        if 'lat' in item and 'lon' in item:
                                            with data_lock:
                                                gps_data.append({
                                                    "lat": item['lat'],
                                                    "lon": item['lon']
                                                })
                                            points_collected += 1
                                    print(f"Parsed {len(json_data)} locations from JSON")
                            except Exception as e:
                                print(f"Failed to parse JSON: {e}")
                    
                    time.sleep(0.05)
                
                print(f"Scan complete! Collected {points_collected} GPS points")
                
            except Exception as e:
                print(f"Read error: {e}")
            finally:
                scanning = False
                scan_complete = True
        
        # Start reading thread
        thread = threading.Thread(target=read_gps_data)
        thread.daemon = True
        thread.start()
        
        return jsonify({"status": "sent", "message": "GPS command sent, collecting data..."})
        
    except Exception as e:
        print("Write error:", e)
        scanning = False
        return jsonify({"status": "error", "message": str(e)})

# -------------------- READ GPS DATA --------------------
@app.route('/gps', methods=['GET'])
def get_gps():
    global gps_data, scanning, scan_complete
    
    with data_lock:
        points = gps_data.copy()
    
    print(f"Returning {len(points)} GPS points")
    
    # Return just the array for compatibility with frontend
    return jsonify(points)

# -------------------- NEW ENDPOINT: ADD DEVICE WITH RANDOM LOCATION --------------------
@app.route('/gps/device_id', methods=['POST'])
def get_gps_for_device():
    """
    This endpoint is called when adding a new device.
    It generates a random GPS location (latitude and longitude)
    and returns it to the frontend.
    """
    data = request.json
    device_id = data.get('device_id')
    device_name = data.get('device_name')
    
    print(f"Adding new device: Name={device_name}, ID={device_id}")
    
    # Generate random GPS coordinates
    # Latitude range: -90 to 90 (using Sri Lanka / Indian Ocean region for relevance)
    # Longitude range: -180 to 180 (centered around Sri Lanka 79°E - 82°E)
    lat = round(random.uniform(5.5, 9.5), 6)      # Sri Lanka lat range approx 5.5°N to 9.5°N
    lon = round(random.uniform(79.5, 82.0), 6)     # Sri Lanka lon range approx 79.5°E to 82.0°E
    
    # Add some randomness to make it look realistic (ocean area around Sri Lanka)
    # Sometimes generate points in the open ocean for buoy simulation
    ocean_variant = random.choice([1, 2, 3])
    if ocean_variant == 1:
        # Deep ocean area (Bay of Bengal)
        lat = round(random.uniform(5.0, 15.0), 6)
        lon = round(random.uniform(80.0, 88.0), 6)
    elif ocean_variant == 2:
        # Arabian Sea side
        lat = round(random.uniform(5.0, 12.0), 6)
        lon = round(random.uniform(72.0, 78.0), 6)
    # else keep Sri Lankan coastal range
    
    print(f"Generated random location: lat={lat}, lon={lon}")
    
    # Return the coordinates to frontend
    return jsonify({
        'success': True,
        'lat': lat,
        'lon': lon,
        'message': f'GPS coordinates generated for {device_name}'
    })

# -------------------- API ROUTES --------------------
@app.route('/api/devices', methods=['GET'])
def get_devices():
    return jsonify(devices_db)

@app.route('/api/devices/<device_id>', methods=['PUT'])
def update_device(device_id):
    data = request.json
    for device in devices_db:
        if device['id'] == device_id:
            device.update(data)
            return jsonify({'success': True, 'device': device})
    return jsonify({'success': False, 'error': 'Device not found'})

@app.route('/connection-status', methods=['GET'])
def connection_status():
    global ser
    return jsonify({
        'connected': ser is not None and ser.is_open,
        'port': ser.port if ser and ser.is_open else None,
        'scanning': scanning,
        'gps_points': len(gps_data)
    })

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