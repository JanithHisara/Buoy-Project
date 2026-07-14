"""
Offline vector tile server from .mbtiles file.
"""
import sqlite3
from flask import Blueprint, Response
from app.config import MBTILES_PATH

tiles_bp = Blueprint('tiles', __name__)


@tiles_bp.route('/tiles/<int:z>/<int:x>/<int:y>.pbf')
def serve_tile(z, x, y):
    """Serve a vector tile from the mbtiles SQLite database."""
    try:
        conn = sqlite3.connect(MBTILES_PATH)
        cursor = conn.cursor()

        # TMS coordinate system Y-flip
        tms_y = (1 << z) - 1 - y

        cursor.execute(
            "SELECT tile_data FROM tiles WHERE zoom_level=? AND tile_column=? AND tile_row=?",
            (z, x, tms_y)
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            response = Response(row[0], mimetype='application/x-protobuf')
            response.headers['Content-Encoding'] = 'gzip'
            response.cache_control.max_age = 31536000
            response.cache_control.public = True
            return response
        else:
            return '', 204

    except Exception as e:
        print(f"[Tiles] Error: {e}")
        return '', 500
