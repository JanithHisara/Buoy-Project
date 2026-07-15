"""
OceanNav Buoy Navigation System — Entry Point
"""
import os
import sys

# Add the project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

app = create_app()

if __name__ == '__main__':
    print("=" * 50)
    print("  OceanNav Buoy Navigation System")
    print("=" * 50)
    print(f"  Server: http://localhost:5000")
    print(f"  Press CTRL+C to stop")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
