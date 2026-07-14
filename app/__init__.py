"""
Flask application factory.
"""
from flask import Flask
from app.config import SECRET_KEY
from app.database import init_db


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__,
                static_folder='static',
                template_folder='templates')

    app.secret_key = SECRET_KEY

    # Cache map tiles aggressively and log API requests
    @app.after_request
    def after_request_handler(response):
        from flask import request as req, session
        from app.database import get_db
        
        # Cache tiles
        if req.path and req.path.startswith('/tiles/'):
            response.cache_control.max_age = 31536000
            response.cache_control.public = True
            return response
            
        # Ignore static files for logging
        if req.path and req.path.startswith('/static/'):
            return response

        # Log API access
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key='api_access_logs'")
            row = cursor.fetchone()
            if row and row['value'] == 'true':
                user_email = session.get('user', {}).get('email', 'anonymous')
                ip_addr = req.remote_addr
                method = req.method
                endpoint = req.path
                
                payload = ""
                if req.is_json and req.method in ['POST', 'PUT']:
                    # Exclude password fields from logs
                    data = dict(req.get_json(silent=True) or {})
                    if 'password' in data:
                        data['password'] = '***'
                    payload = str(data)[:500]
                    
                cursor.execute('''
                    INSERT INTO api_logs (user_email, ip_address, method, endpoint, payload)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_email, ip_addr, method, endpoint, payload))
                conn.commit()
            conn.close()
        except Exception as e:
            print(f"[Logging Error] {e}")

        return response

    # Initialize database
    init_db()

    # Register blueprints
    from app.routes import register_blueprints
    register_blueprints(app)

    # Start serial listener
    from app.services.serial_service import serial_manager
    serial_manager.start_listener()

    return app
