"""
Application configuration constants.
"""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Database
DATABASE_PATH = os.path.join(BASE_DIR, 'oceannav.db')

# Map tiles
MBTILES_PATH = os.path.join(BASE_DIR, 'srilanka map', 'osm-2020-02-10-v3.11_asia_sri-lanka.mbtiles')

# Flask
SECRET_KEY = 'oceannav_secret_key_2025_buoyancy'

# Serial defaults
DEFAULT_BAUD_RATE = 115200
SERIAL_TIMEOUT = 1

# Hardcoded Super Admin
SUPER_ADMIN = {
    'name': 'Super Admin',
    'email': 'superadmin@oceannav.lk',
    'password': 'superadmin123',
    'role': 'super_admin',
    'avatar': 'SA',
    'avatar_bg': 'linear-gradient(135deg,#7b2cbf,#3c096c)'
}

# Default settings
DEFAULT_SETTINGS = {
    'auto_scan_gps': 'true',
    'auto_connect_startup': 'true',
    'baud_rate': '115200',
    'show_buoy_trails': 'true',
    'auto_center_gps': 'false',
    'default_zoom': '13',
    'low_battery_alert': 'true',
    'low_battery_threshold': '20',
    'gps_drift_alert': 'false',
    'gps_drift_distance': '500',
    'two_factor_auth': 'false',
    'session_timeout': '300',
    'api_access_logs': 'true',
}
