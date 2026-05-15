import os
import math
import requests

def deg2num(lat, lon, zoom):
    lat_rad = math.radians(lat)
    n = 2 ** zoom
    x = int((lon + 180) / 360 * n)
    y = int((1 - math.log(math.tan(lat_rad) + 1 / math.cos(lat_rad)) / math.pi) / 2 * n)
    return x, y

def download_tiles(lat_min, lat_max, lon_min, lon_max, zoom_levels, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    for zoom in zoom_levels:
        x_min, y_max = deg2num(lat_min, lon_min, zoom)
        x_max, y_min = deg2num(lat_max, lon_max, zoom)

        print(f"\nZoom {zoom} downloading...")

        for x in range(x_min, x_max + 1):
            for y in range(y_min, y_max + 1):

                path = f"{output_dir}/{zoom}/{x}/{y}.png"
                os.makedirs(os.path.dirname(path), exist_ok=True)

                if not os.path.exists(path):
                    url = f"https://tile.openstreetmap.org/{zoom}/{x}/{y}.png"
                    try:
                        r = requests.get(url, timeout=10, headers={
                            "User-Agent": "OceanNav System"
                        })

                        if r.status_code == 200:
                            with open(path, "wb") as f:
                                f.write(r.content)

                    except Exception as e:
                        print("Error:", e)

# Sri Lanka region
download_tiles(
    lat_min=5.9, lat_max=9.9,
    lon_min=79.5, lon_max=81.9,
    zoom_levels=[8, 9, 10, 11],
    output_dir="static/tiles/sri_lanka"
)