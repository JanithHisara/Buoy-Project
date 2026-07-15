"""
Serial port management service.
Handles ESP32 transceiver connection and background data listener.
"""
import serial
import serial.tools.list_ports
import threading
import time
import sqlite3
from app.config import DATABASE_PATH, DEFAULT_BAUD_RATE, SERIAL_TIMEOUT
from app.services.lora_protocol import LoRaProtocol


class SerialManager:
    """Manages serial connection to ESP32 transceiver."""

    def __init__(self):
        self.ser = None
        self.connected_port = None
        self.trx_id = "000000000000"
        self.data_lock = threading.Lock()
        self.update_lock = threading.Lock()
        self.running = False

        # Scan state
        self.scanning = False
        self.scan_complete = False
        self.scan_start_time = 0

        # Response tracking
        self.gps_data = []
        self.latest_buoy_gps = {}          # {buoy_id: {lat, lon, timestamp, has_fix, is_cached}}
        self.latest_buoy_history = {}      # {buoy_id: [{'lat', 'lon'}, ...]}
        self.device_responded = {}          # {buoy_id: timestamp}
        self.scan_responded_buoys = []      # buoy IDs that responded to last scan
        self.last_buoy_id = None

        # Device ID reader
        self.reading_device_id = False
        self.detected_device_id = None

        self._listener_thread = None

    @property
    def is_connected(self):
        return self.ser is not None and self.ser.is_open

    def list_ports(self):
        """List available COM ports."""
        try:
            ports = serial.tools.list_ports.comports()
            return [p.device for p in ports]
        except Exception as e:
            print(f"[Serial] Error listing ports: {e}")
            return []

    def connect(self, port, baud_rate=None):
        """Connect to a serial port."""
        if baud_rate is None:
            baud_rate = DEFAULT_BAUD_RATE

        try:
            if self.ser and self.ser.is_open:
                self.ser.close()

            with self.data_lock:
                self.gps_data = []
                self.scan_responded_buoys = []

            self.ser = serial.Serial(port, baud_rate, timeout=SERIAL_TIMEOUT)
            self.connected_port = port

            # Reset ESP32 to capture TRX ID from boot
            self.ser.dtr = False
            self.ser.rts = True   # EN=LOW (Reset)
            time.sleep(0.1)
            self.ser.dtr = False
            self.ser.rts = False  # EN=HIGH, IO0=HIGH (Boot to App)
            time.sleep(0.6)

            print(f"[Serial] Connected to {port}")
            return True, f"Connected to {port}"

        except Exception as e:
            print(f"[Serial] Connection error: {e}")
            return False, str(e)

    def disconnect(self):
        """Disconnect from serial port."""
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.ser = None
        self.connected_port = None
        print("[Serial] Disconnected")

    def send(self, data):
        """Send data to serial port."""
        if not self.is_connected:
            return False
        try:
            self.ser.write(data.encode())
            self.ser.flush()
            print(f"[Serial] Sent: {data.strip()}")
            return True
        except Exception as e:
            print(f"[Serial] Send error: {e}")
            return False

    def _send_fast_sequence(self, buoy_id, commands, timeout_per_cmd=3.0):
        """Send a sequence of commands, waiting for a response before sending the next one."""
        for cmd in commands:
            start_time = time.time()
            
            self.send(cmd)
            
            while time.time() - start_time < timeout_per_cmd:
                with self.data_lock:
                    resp_time = self.device_responded.get(buoy_id, 0)
                    if resp_time > start_time:
                        break
                time.sleep(0.05)
            # Small buffer to ensure response text is fully read and processed,
            # and to allow LoRa modules to turnaround from TX to RX.
            time.sleep(0.5)

    def scan_unbound(self):
        """Send SCAN command to discover unbound buoys."""
        if not self.is_connected:
            return False, "No serial connection"

        with self.data_lock:
            self.gps_data = []
            self.scanning = True
            self.scan_complete = False
            self.scan_responded_buoys = []
            self.scan_start_time = time.time()

        cmd = LoRaProtocol.build_scan_all(self.trx_id)
        self.send(cmd)

        def finish_scan():
            time.sleep(15.0)
            with self.data_lock:
                self.scanning = False
                self.scan_complete = True
            print("[Serial] Unbound Scan completed")

        threading.Thread(target=finish_scan, daemon=True).start()
        return True, "Unbound Scan started"

    def scan_bound(self):
        """Send SCAN commands individually to all bound buoys."""
        if not self.is_connected:
            return False, "No serial connection"

        with self.data_lock:
            self.gps_data = []
            self.scanning = True
            self.scan_complete = False
            self.scan_responded_buoys = []
            self.scan_start_time = time.time()

        import sqlite3
        from app.database import DATABASE_PATH
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM devices WHERE is_bound = 1")
        bound_buoys = [row[0] for row in cursor.fetchall()]
        conn.close()

        if not bound_buoys:
            with self.data_lock:
                self.scanning = False
                self.scan_complete = True
            return True, "No bound buoys to scan"

        # Build individual commands
        commands = [LoRaProtocol.build_scan_one(self.trx_id, b_id) for b_id in bound_buoys]
        
        def do_scan():
            for cmd in commands:
                self.send(cmd)
                time.sleep(1.0) # Small delay to avoid collisions
            
            time.sleep(5.0) # Wait for remaining responses
            with self.data_lock:
                self.scanning = False
                self.scan_complete = True
            self._mark_unresponsive_devices()
            print("[Serial] Bound Scan completed")
            
        threading.Thread(target=do_scan, daemon=True).start()
        return True, "Bound Scan started"

    def request_gps(self, buoy_id):
        """Request GPS info from a specific buoy."""
        if not self.is_connected:
            return False, "No serial connection"

        # Clear previous data for this buoy
        with self.data_lock:
            if buoy_id in self.latest_buoy_gps:
                del self.latest_buoy_gps[buoy_id]
            if buoy_id in self.device_responded:
                del self.device_responded[buoy_id]

        # Send GPS on + GPS info commands fast
        cmds = [
            LoRaProtocol.build_gps_on(self.trx_id, buoy_id),
            LoRaProtocol.build_gps_info(self.trx_id, buoy_id)
        ]
        self._send_fast_sequence(buoy_id, cmds)

        return True, "GPS request sent"

    def update_buoy_location(self, buoy_id):
        """
        Request updated location from a buoy.
        Returns (success, data_dict_or_error_string).
        """
        if not self.is_connected:
            return False, "No serial connection"

        with self.update_lock:
            # Clear cache
            with self.data_lock:
                if buoy_id in self.latest_buoy_gps:
                    del self.latest_buoy_gps[buoy_id]
                if buoy_id in self.device_responded:
                    del self.device_responded[buoy_id]

            # Send commands fast (AT+CGPS=1 followed by AT+CGPSINFO)
            cmds = [
                LoRaProtocol.build_gps_on(self.trx_id, buoy_id),
                LoRaProtocol.build_gps_info(self.trx_id, buoy_id)
            ]
            self._send_fast_sequence(buoy_id, cmds)

            # Wait for response (up to 12 seconds)
            start = time.time()
            while time.time() - start < 12.0:
                with self.data_lock:
                    if buoy_id in self.latest_buoy_gps:
                        data = self.latest_buoy_gps[buoy_id].copy()
                        return True, data
                    if buoy_id in self.device_responded:
                        # Responded but no GPS yet, keep waiting
                        pass
                time.sleep(0.3)

            # Timeout — check if device at least responded
            with self.data_lock:
                responded = buoy_id in self.device_responded

            if responded:
                return False, "Device responded but GPS has no lock. Using last saved location."
            else:
                return False, "Buoyancy not in LoRa range. Showing database location."

    def update_buoy_history(self, buoy_id):
        """
        Request history trail (last 5 locations) from a buoy.
        Returns (success, history_list_or_error_string).
        """
        if not self.is_connected:
            return False, "No serial connection"

        with self.update_lock:
            # Clear cache
            with self.data_lock:
                if buoy_id in self.latest_buoy_history:
                    del self.latest_buoy_history[buoy_id]
                if buoy_id in self.device_responded:
                    del self.device_responded[buoy_id]

            # Send commands
            self.send(LoRaProtocol.build_gps_hist(self.trx_id, buoy_id))

            # Wait for response (up to 12 seconds)
            start = time.time()
            while time.time() - start < 12.0:
                with self.data_lock:
                    if buoy_id in self.latest_buoy_history:
                        data = self.latest_buoy_history[buoy_id].copy()
                        return True, data
                    if buoy_id in self.device_responded:
                        pass
                time.sleep(0.3)

            with self.data_lock:
                responded = buoy_id in self.device_responded

            if responded:
                return False, "Device responded but no history was retrieved."
            else:
                return False, "Buoyancy not in LoRa range."

    def bind_buoy(self, buoy_id, bind=True):
        """
        Send bind/unbind command and wait for response.
        Returns (success, message).
        """
        if not self.is_connected:
            return False, "No serial connection"

        with self.update_lock:
            with self.data_lock:
                if buoy_id in self.device_responded:
                    del self.device_responded[buoy_id]

            self.send(LoRaProtocol.build_bind(self.trx_id, buoy_id, bind))

            # Wait for response up to 5 seconds
            start = time.time()
            while time.time() - start < 5.0:
                with self.data_lock:
                    if buoy_id in self.device_responded:
                        return True, "Device responded successfully"
                time.sleep(0.1)

            return False, "Buoyancy did not respond (out of range or off)"

    def read_device_id(self, port, baud_rate=None):
        """
        Connect to a buoyancy device directly via USB to read its chip ID.
        Returns the 12-char hex device ID.
        """
        if baud_rate is None:
            baud_rate = DEFAULT_BAUD_RATE

        temp_ser = None
        try:
            temp_ser = serial.Serial(port, baud_rate, timeout=2)

            # Reset ESP32
            temp_ser.dtr = False
            temp_ser.rts = True   # EN=LOW (Reset)
            time.sleep(0.1)
            temp_ser.dtr = False
            temp_ser.rts = False  # EN=HIGH, IO0=HIGH (Boot to App)

            # Read boot output for up to 5 seconds
            start = time.time()
            while time.time() - start < 5.0:
                if temp_ser.in_waiting > 0:
                    line = temp_ser.readline().decode(errors='ignore').strip()
                    if line:
                        print(f"[DeviceID] Read: {line}")
                        # Look for BUOYANCY ID or TRX ID
                        if "BUOYANCY ID :" in line:
                            parts = line.split("BUOYANCY ID :")
                            if len(parts) > 1:
                                device_id = parts[1].strip().upper()
                                if len(device_id) == 12:
                                    return True, device_id
                        elif "TRX ID :" in line:
                            parts = line.split("TRX ID :")
                            if len(parts) > 1:
                                device_id = parts[1].strip().upper()
                                if len(device_id) == 12:
                                    return True, device_id
                time.sleep(0.1)

            return False, "Could not read device ID. Try again."

        except Exception as e:
            return False, str(e)
        finally:
            if temp_ser and temp_ser.is_open:
                temp_ser.close()

    def start_listener(self):
        """Start the background serial listener thread."""
        if self._listener_thread is None or not self._listener_thread.is_alive():
            self._listener_thread = threading.Thread(target=self._listener_loop, daemon=True)
            self._listener_thread.start()
            print("[Serial] Listener thread started")

    def _listener_loop(self):
        """Background loop that reads and parses serial data."""
        while True:
            try:
                if self.is_connected and self.ser.in_waiting > 0:
                    line = self.ser.readline().decode(errors='ignore').strip()
                    if line:
                        self._process_line(line)
                else:
                    time.sleep(0.1)
            except Exception as e:
                print(f"[Serial] Listener error: {e}")
                try:
                    if self.ser:
                        self.ser.close()
                except:
                    pass
                self.ser = None
                time.sleep(1.0)

    def _process_line(self, line):
        """Process a single line from serial."""
        print(f"[Serial] RX: {line}")

        # Detect Transceiver ID from boot
        if "TRX ID :" in line:
            parts = line.split("TRX ID :")
            if len(parts) > 1:
                self.trx_id = parts[1].strip().upper()
                print(f"[Serial] Transceiver ID: {self.trx_id}")
            return

        # Ignore Transceiver's serial echo
        if "Reveived via Serial :" in line:
            return

        # Parse header <TRX_ID,BUOY_ID>
        trx_id, buoy_id = LoRaProtocol.parse_header(line)
        if trx_id and buoy_id:
            self.last_buoy_id = buoy_id
            with self.data_lock:
                self.device_responded[buoy_id] = time.time()
                if buoy_id not in self.scan_responded_buoys:
                    self.scan_responded_buoys.append(buoy_id)

        # Parse +SCAN response
        if "+SCAN:" in line:
            resp = LoRaProtocol.parse_scan_response(line)
            if resp and resp.success:
                print(f"[Serial] Buoy discovered: {resp.buoy_id}")

        # Parse +CGPS response (Sleep/Awake Mode)
        if "+CGPS:" in line:
            bid = self.last_buoy_id
            if bid:
                sleep_mode = 'Asleep' if '+CGPS:0' in line else 'Awake'
                try:
                    conn = sqlite3.connect(DATABASE_PATH)
                    conn.execute("UPDATE devices SET sleep_mode=? WHERE id=?", (sleep_mode, bid))
                    conn.commit()
                    conn.close()
                except Exception as e:
                    print(f"[Serial] Error updating sleep mode: {e}")

        # Parse +CGPSINFO and +GPSLIVE responses
        if "+CGPSINFO:" in line or "+GPSLIVE:" in line:
            gps = LoRaProtocol.parse_gps_response(line)
            bid = self.last_buoy_id
            if gps and bid:
                with self.data_lock:
                    self.latest_buoy_gps[bid] = {
                        'lat': gps.latitude,
                        'lon': gps.longitude,
                        'has_fix': gps.has_fix,
                        'is_cached': gps.is_cached,
                        'satellites': gps.satellites,
                        'timestamp': time.time()
                    }

                # Save to database if valid fix
                if gps.has_fix:
                    with self.data_lock:
                        self.gps_data.append({'lat': gps.latitude, 'lon': gps.longitude})
                        if len(self.gps_data) > 100:
                            self.gps_data.pop(0)

                    try:
                        conn = sqlite3.connect(DATABASE_PATH)
                        cursor = conn.cursor()
                        source = 'cached' if gps.is_cached else 'live'
                        is_cached_int = 1 if gps.is_cached else 0
                        status_str = 'online'
                        last_gps_time_str = None
                        
                        if gps.year != 0 and gps.month != 0:
                            import datetime
                            try:
                                gps_dt_utc = datetime.datetime(gps.year, gps.month, gps.day, gps.hour, gps.minute, gps.second, tzinfo=datetime.timezone.utc)
                                diff = (datetime.datetime.now(datetime.timezone.utc) - gps_dt_utc).total_seconds()
                                
                                # If the location is older than 10 minutes, consider it a Last Save (cached)
                                if diff > 600:
                                    status_str = 'warning'
                                    is_cached_int = 1
                                else:
                                    status_str = 'online'
                                    is_cached_int = 0
                                
                                local_dt = gps_dt_utc.astimezone()
                                last_gps_time_str = local_dt.strftime("%Y-%m-%d %H:%M:%S")
                            except Exception:
                                pass
                        elif gps.is_cached:
                            status_str = 'warning'

                        if last_gps_time_str:
                            cursor.execute(
                                'INSERT INTO gps_logs (device_id, lat, lon, source, timestamp) VALUES (?,?,?,?,?)',
                                (bid, gps.latitude, gps.longitude, source, last_gps_time_str)
                            )
                            cursor.execute(
                                '''UPDATE devices SET lat=?, lon=?, status=?,
                                   gps_status='locked', last_gps_time=?,
                                   is_cached=?
                                   WHERE id=?''',
                                (gps.latitude, gps.longitude, status_str, last_gps_time_str, is_cached_int, bid)
                            )
                        else:
                            cursor.execute(
                                'INSERT INTO gps_logs (device_id, lat, lon, source, timestamp) VALUES (?,?,?,?, datetime("now", "localtime"))',
                                (bid, gps.latitude, gps.longitude, source)
                            )
                            cursor.execute(
                                '''UPDATE devices SET lat=?, lon=?, status=?,
                                   gps_status='locked', last_gps_time=datetime('now', 'localtime'),
                                   is_cached=?
                                   WHERE id=?''',
                                (gps.latitude, gps.longitude, status_str, is_cached_int, bid)
                            )
                        conn.commit()
                        conn.close()
                        
                        # Stop live broadcasting to preserve battery since UI now has the live location
                        if not gps.is_cached and "+GPSLIVE:" in line:
                            print(f"[Serial] Live lock achieved. Sending STOP command to {bid}.")
                            cmds = [ LoRaProtocol.build_stop_live(self.trx_id, bid) ]
                            threading.Thread(target=self._send_fast_sequence, args=(bid, cmds), daemon=True).start()
                            
                    except Exception as e:
                        print(f"[Serial] DB save error: {e}")
                else:
                    # GPS responded but no fix
                    try:
                        conn = sqlite3.connect(DATABASE_PATH)
                        cursor = conn.cursor()
                        cursor.execute(
                            "UPDATE devices SET status='warning', gps_status='no_lock' WHERE id=?",
                            (bid,)
                        )
                        conn.commit()
                        conn.close()
                    except Exception as e:
                        print(f"[Serial] DB warning update error: {e}")

        # Parse +CGPSHIST response
        if "+CGPSHIST:" in line:
            hist = LoRaProtocol.parse_gps_hist(line)
            bid = self.last_buoy_id
            if hist is not None and bid:
                with self.data_lock:
                    self.latest_buoy_history[bid] = hist

        # Parse +BIND response
        if "+BIND:" in line:
            resp = LoRaProtocol.parse_bind_response(line)
            if resp:
                print(f"[Serial] Bind response for {resp.buoy_id}: bound={resp.bound}")

    def _mark_unresponsive_devices(self):
        """After scan, mark devices that didn't respond as offline."""
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM devices WHERE active = 1")
            all_active = cursor.fetchall()
            for row in all_active:
                d_id = row[0]
                last_resp = self.device_responded.get(d_id, 0)
                if last_resp < self.scan_start_time:
                    cursor.execute(
                        "UPDATE devices SET status='offline', gps_status='unknown' WHERE id=?",
                        (d_id,)
                    )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[Serial] Error marking offline: {e}")

    def poll_live_location(self, buoy_id):
        """Actively ping the buoy for its live location (Master polling)"""
        if not self.is_connected or not self.trx_id:
            return False, "Gateway not connected"

        # Clear old GPS data for this buoy
        with self.data_lock:
            if buoy_id in self.latest_buoy_gps:
                del self.latest_buoy_gps[buoy_id]

        cmds = [
            LoRaProtocol.build_gps_info(self.trx_id, buoy_id)
        ]
        threading.Thread(target=self._send_fast_sequence, args=(buoy_id, cmds), daemon=True).start()

        # Wait max 3 seconds for response
        start = time.time()
        while time.time() - start < 3.0:
            with self.data_lock:
                if buoy_id in self.latest_buoy_gps:
                    data = self.latest_buoy_gps[buoy_id].copy()
                    del self.latest_buoy_gps[buoy_id]
                    return True, data
            time.sleep(0.3)
        return False, "Timeout waiting for live location"

    def set_led(self, buoy_id, r, g, b):
        """Set LED color of a buoy."""
        if not self.is_connected or not self.trx_id:
            return False, "Gateway not connected"

        with self.update_lock:
            cmd = LoRaProtocol.build_led_on(self.trx_id, buoy_id, r, g, b)
            self.send(cmd)
            return True, "LED color command sent"

    def toggle_gps_power(self, buoy_id, state):
        """Turn GPS power on or off."""
        if not self.is_connected or not self.trx_id:
            return False, "Gateway not connected"

        with self.update_lock:
            if state:
                cmd = LoRaProtocol.build_gps_on(self.trx_id, buoy_id)
            else:
                cmd = LoRaProtocol.build_gps_off(self.trx_id, buoy_id)
            
            self.send(cmd)
            return True, "GPS power command sent"

    def get_scan_status(self):
        """Get current scan status for the frontend."""
        with self.data_lock:
            return {
                'connected': self.is_connected,
                'port': self.connected_port,
                'scanning': self.scanning,
                'scan_complete': self.scan_complete,
                'trx_id': self.trx_id,
                'responded_buoys': list(self.scan_responded_buoys),
                'gps_points': len(self.gps_data)
            }


# Global singleton
serial_manager = SerialManager()
