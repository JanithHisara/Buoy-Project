import os
import math
import time
import random
import requests
import threading
from concurrent.futures import ThreadPoolExecutor

def deg2num(lat, lon, zoom):
    lat_rad = math.radians(lat)
    n = 2 ** zoom
    x = int((lon + 180) / 360 * n)
    y = int((1 - math.log(math.tan(lat_rad) + 1 / math.cos(lat_rad)) / math.pi) / 2 * n)
    return x, y

def estimate_tiles(lat_min, lat_max, lon_min, lon_max, zoom_levels):
    total_tiles = 0
    zoom_details = []
    
    for zoom in zoom_levels:
        x_min, y_max = deg2num(lat_min, lon_min, zoom)
        x_max, y_min = deg2num(lat_max, lon_max, zoom)
        
        x_count = max(1, abs(x_max - x_min) + 1)
        y_count = max(1, abs(y_max - y_min) + 1)
        tiles_in_zoom = x_count * y_count
        total_tiles += tiles_in_zoom
        zoom_details.append((zoom, tiles_in_zoom, x_count, y_count))
        
    return total_tiles, zoom_details

def download_tiles(lat_min, lat_max, lon_min, lon_max, zoom_levels, style_choice, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    
    style_urls = {
        "standard": "https://basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png",
        "dark": "https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png",
        "satellite": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        "topo": "https://tile.opentopomap.org/{z}/{x}/{y}.png"
    }
    
    url_template = style_urls.get(style_choice, style_urls["standard"])
    print(f"\n[INFO] Starting download for style: {style_choice.upper()}")
    print(f"[INFO] Saving tiles to: {output_dir}")
    
    headers = {
        "User-Agent": "OceanNav System Offline Map Downloader/2.0 (contact@oceannav.lk)"
    }
    
    total_tiles, _ = estimate_tiles(lat_min, lat_max, lon_min, lon_max, zoom_levels)
    
    # Pre-build list of all tile tasks
    tasks = []
    for zoom in zoom_levels:
        x_min, y_max = deg2num(lat_min, lon_min, zoom)
        x_max, y_min = deg2num(lat_max, lon_max, zoom)
        
        x_range = range(min(x_min, x_max), max(x_min, x_max) + 1)
        y_range = range(min(y_min, y_max), max(y_min, y_max) + 1)
        
        for x in x_range:
            for y in y_range:
                tasks.append((zoom, x, y))
                
    success_count = 0
    skipped_count = 0
    error_count = 0
    tiles_processed = 0
    lock = threading.Lock()
    
    def download_single_tile(task):
        nonlocal success_count, skipped_count, error_count, tiles_processed
        zoom, x, y = task
        
        # Save locally as standard z/x/y structure
        path = os.path.join(output_dir, str(zoom), str(x), f"{y}.png")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        if os.path.exists(path) and os.path.getsize(path) > 100:
            with lock:
                skipped_count += 1
                tiles_processed += 1
                percent = (tiles_processed / total_tiles) * 100
                print(f"[{percent:.1f}%] Saved tile {zoom}/{x}/{y} ({success_count} downloaded, {skipped_count} skipped)    ", end="\r")
            return
            
        # Format URL
        url = url_template.format(z=zoom, x=x, y=y)
            
        # Retry logic
        downloaded = False
        for attempt in range(3):
            try:
                r = requests.get(url, timeout=10, headers=headers)
                if r.status_code == 200:
                    if len(r.content) > 100:
                        with open(path, "wb") as f:
                            f.write(r.content)
                        downloaded = True
                        break
                elif r.status_code == 404:
                    break
            except Exception:
                pass
            
            # Short sleep before retry
            time.sleep(0.5 + random.random() * 0.5)
            
        with lock:
            tiles_processed += 1
            if downloaded:
                success_count += 1
            else:
                error_count += 1
                
            percent = (tiles_processed / total_tiles) * 100
            print(f"[{percent:.1f}%] Saved tile {zoom}/{x}/{y} ({success_count} downloaded, {skipped_count} skipped)    ", end="\r")

    print(f"\n[INFO] Starting parallel download using 12 threads...")
    
    with ThreadPoolExecutor(max_workers=12) as executor:
        executor.map(download_single_tile, tasks)
        
    print(f"\n\n[COMPLETED] Download process finished!")
    print(f" -> Successfully downloaded: {success_count} tiles")
    print(f" -> Already existed (skipped): {skipped_count} tiles")
    print(f" -> Errors/failed downloads: {error_count} tiles")

def main():
    print("=" * 60)
    print("      OceanNav Offline Map Tile Downloader v2.0")
    print("=" * 60)
    
    # 1. Choose style
    print("\nSelect Map Style:")
    print("  [1] CartoDB Light (Standard Light Map)")
    print("  [2] CartoDB Dark Matter (Recommended - Dark Theme Match)")
    print("  [3] Esri World Imagery (Satellite Map)")
    print("  [4] OpenTopoMap (Topographical/Terrain Map)")
    
    style_map = {"1": "standard", "2": "dark", "3": "satellite", "4": "topo"}
    choice = input("Enter choice (1-4, default 2): ").strip()
    style = style_map.get(choice, "dark")
    
    # 2. Choose Region / Coordinates
    print("\nSelect Region Boundary:")
    print("  [1] Colombo & Coastline (Operational Buoys Area - Recommended for high zooms)")
    print("  [2] Entire Sri Lanka Waters (Broad coverage - recommended up to zoom 12 only)")
    print("  [3] Custom Coordinates")
    
    region_choice = input("Enter choice (1-3, default 1): ").strip()
    if region_choice == "2":
        lat_min, lat_max = 5.9, 9.9
        lon_min, lon_max = 79.5, 81.9
        region_name = "sri_lanka"
    elif region_choice == "3":
        try:
            lat_min = float(input("Min Latitude (e.g. 6.8): "))
            lat_max = float(input("Max Latitude (e.g. 7.0): "))
            lon_min = float(input("Min Longitude (e.g. 79.8): "))
            lon_max = float(input("Max Longitude (e.g. 79.9): "))
            region_name = "custom"
        except ValueError:
            print("Invalid inputs, defaulting to Colombo.")
            lat_min, lat_max = 6.85, 7.05
            lon_min, lon_max = 79.78, 79.92
            region_name = "colombo"
    else:
        lat_min, lat_max = 6.85, 7.05
        lon_min, lon_max = 79.78, 79.92
        region_name = "colombo"
        
    # 3. Choose Zooms
    print("\nSelect Zoom Levels:")
    print("  [1] Quick broad view (zooms 8 - 11) - ~50 tiles")
    print("  [2] Detailed operational view (zooms 12 - 15) - ~300 tiles")
    print("  [3] Complete coverage (zooms 8 - 16) - ~600 tiles (Recommended)")
    print("  [4] Custom Zoom Levels (comma separated list, e.g. 8,10,12,13)")
    
    zoom_choice = input("Enter choice (1-4, default 3): ").strip()
    if zoom_choice == "1":
        zoom_levels = list(range(8, 12))
    elif zoom_choice == "2":
        zoom_levels = list(range(12, 16))
    elif zoom_choice == "4":
        try:
            zoom_levels = [int(z.strip()) for z in input("Enter zooms: ").split(",") if z.strip()]
        except ValueError:
            print("Invalid inputs, defaulting to 8-16.")
            zoom_levels = list(range(8, 17))
    else:
        zoom_levels = list(range(8, 17))
        
    # 4. Estimation & Confirmation
    total_tiles, details = estimate_tiles(lat_min, lat_max, lon_min, lon_max, zoom_levels)
    print("\n" + "-" * 50)
    print(f"Summary of request:")
    print(f" -> Style: {style.upper()}")
    print(f" -> Coordinates: Lat ({lat_min} to {lat_max}), Lon ({lon_min} to {lon_max})")
    print(f" -> Zooms: {zoom_levels}")
    print(f" -> Total estimated tiles to check/download: {total_tiles}")
    print(f" -> Approx. storage needed: {(total_tiles * 25) / 1024:.2f} MB")
    print("-" * 50)
    
    # Adjust output directory based on style
    output_dir = f"static/tiles/{style}"
    
    confirm = input("\nProceed with download? (y/n, default y): ").strip().lower()
    if confirm == "" or confirm.startswith("y"):
        download_tiles(lat_min, lat_max, lon_min, lon_max, zoom_levels, style, output_dir)
    else:
        print("Download cancelled.")

if __name__ == "__main__":
    main()