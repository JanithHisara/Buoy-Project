"""
Blueprint registration for all routes.
"""


def register_blueprints(app):
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.live_map import live_map_bp
    from app.routes.devices import devices_bp
    from app.routes.users import users_bp
    from app.routes.settings import settings_bp
    from app.routes.serial_api import serial_bp
    from app.routes.tiles import tiles_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(live_map_bp)
    app.register_blueprint(devices_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(serial_bp)
    app.register_blueprint(tiles_bp)
