"""
SQLite database initialization and helper functions.
"""
import sqlite3
from werkzeug.security import generate_password_hash
from app.config import DATABASE_PATH, SUPER_ADMIN, DEFAULT_SETTINGS


def get_db():
    """Get a database connection with Row factory."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Initialize database tables and seed data."""
    conn = get_db()
    cursor = conn.cursor()

    # ── Users table ──
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('super_admin','admin','user')),
            status TEXT DEFAULT 'Active',
            last_active TEXT DEFAULT 'Now',
            avatar TEXT NOT NULL,
            avatar_bg TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # ── Devices table ──
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS devices (
            id TEXT PRIMARY KEY,
            name TEXT,
            lat REAL DEFAULT 0.0,
            lon REAL DEFAULT 0.0,
            battery INTEGER DEFAULT 100,
            status TEXT DEFAULT 'offline',
            gps_status TEXT DEFAULT 'unknown',
            last_gps_time TEXT,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            registered_by TEXT,
            active INTEGER DEFAULT 1,
            is_cached INTEGER DEFAULT 0,
            is_bound INTEGER DEFAULT 1,
            led_color TEXT DEFAULT '#0000ff',
            sleep_mode TEXT DEFAULT 'Asleep'
        )
    ''')
    
    try:
        cursor.execute("ALTER TABLE devices ADD COLUMN is_cached INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE devices ADD COLUMN led_color TEXT DEFAULT '#0000ff'")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE devices ADD COLUMN is_bound INTEGER DEFAULT 1")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE devices ADD COLUMN sleep_mode TEXT DEFAULT 'Asleep'")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE devices ADD COLUMN is_bound INTEGER DEFAULT 1")
    except sqlite3.OperationalError:
        pass

    # ── GPS Logs table ──
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gps_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT,
            lat REAL NOT NULL,
            lon REAL NOT NULL,
            source TEXT DEFAULT 'live',
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # ── API Logs table ──
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT,
            ip_address TEXT,
            method TEXT,
            endpoint TEXT,
            payload TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # ── Settings table ──
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # ── Seed super admin if no users exist ──
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        hashed = generate_password_hash(SUPER_ADMIN['password'])
        cursor.execute('''
            INSERT INTO users (name, email, password, role, status, last_active, avatar, avatar_bg)
            VALUES (?, ?, ?, ?, 'Active', 'Now', ?, ?)
        ''', (
            SUPER_ADMIN['name'],
            SUPER_ADMIN['email'],
            hashed,
            SUPER_ADMIN['role'],
            SUPER_ADMIN['avatar'],
            SUPER_ADMIN['avatar_bg']
        ))

    # ── Seed default settings ──
    for key, value in DEFAULT_SETTINGS.items():
        cursor.execute('''
            INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)
        ''', (key, value))

    conn.commit()
    conn.close()
    print("[DB] Database initialized successfully")
