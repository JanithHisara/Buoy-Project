import os
import sys
import tempfile
import threading
import time
import subprocess
import requests
from app.version import __version__

# State variables
update_status = {
    'checking': False,
    'update_available': False,
    'downloading': False,
    'ready_to_install': False,
    'latest_version': None,
    'error': None,
    'download_progress': 0
}

UPDATE_FILE_PATH = os.path.join(tempfile.gettempdir(), 'OceanNav_Update_Installer.exe')
GITHUB_API_URL = "https://api.github.com/repos/JanithHisara/Buoy-Project/releases/latest"

def parse_version(v_str):
    """Convert version string like 'v1.1.0' or '1.1' into a tuple of ints for comparison."""
    clean = v_str.lower().replace('v', '')
    try:
        return tuple(map(int, clean.split('.')))
    except:
        return (0, 0, 0)

def check_for_updates():
    """Check GitHub for a new release and download it if available."""
    global update_status
    if update_status['checking'] or update_status['downloading'] or update_status['ready_to_install']:
        return

    update_status['checking'] = True
    update_status['error'] = None

    try:
        # Fetch latest release from GitHub
        response = requests.get(GITHUB_API_URL, timeout=10)
        if response.status_code == 200:
            data = response.json()
            remote_version_str = data.get('tag_name', '')
            remote_version = parse_version(remote_version_str)
            local_version = parse_version(__version__)

            if remote_version > local_version:
                # Update is available! Find the .exe asset and firmware bins
                assets = data.get('assets', [])
                exe_asset = next((a for a in assets if a.get('name', '').endswith('.exe')), None)
                buoy_bin = next((a for a in assets if 'buoy' in a.get('name', '').lower() and a.get('name', '').endswith('.bin')), None)
                trx_bin = next((a for a in assets if 'transmitter' in a.get('name', '').lower() and a.get('name', '').endswith('.bin')), None)
                
                if exe_asset:
                    update_status['latest_version'] = remote_version_str
                    update_status['update_available'] = True
                    download_url = exe_asset.get('browser_download_url')
                    _download_update(download_url)
                
                # Download Buoy Firmware if it exists
                if buoy_bin:
                    bin_url = buoy_bin.get('browser_download_url')
                    b_path = os.path.join(tempfile.gettempdir(), 'buoy_firmware.bin')
                    _download_firmware(bin_url, b_path)
                    update_status['buoy_bin_path'] = b_path
                    update_status['buoy_version'] = remote_version_str

                # Download Transmitter Firmware if it exists and flash it
                if trx_bin:
                    bin_url = trx_bin.get('browser_download_url')
                    t_path = os.path.join(tempfile.gettempdir(), 'transmitter_firmware.bin')
                    _download_firmware(bin_url, t_path)
                    _silent_flash_transmitter(t_path)

                if not exe_asset and not buoy_bin and not trx_bin:
                    update_status['error'] = "No executable or firmware found in the latest release."
            else:
                update_status['update_available'] = False
        else:
            update_status['error'] = f"GitHub API error: {response.status_code}"
            
    except Exception as e:
        update_status['error'] = str(e)
    finally:
        update_status['checking'] = False


def _download_update(url):
    """Downloads the update file in chunks to show progress."""
    global update_status
    update_status['downloading'] = True
    update_status['download_progress'] = 0

    try:
        response = requests.get(url, stream=True, timeout=15)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        # Remove old update file if exists
        if os.path.exists(UPDATE_FILE_PATH):
            try: os.remove(UPDATE_FILE_PATH)
            except: pass

        with open(UPDATE_FILE_PATH, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        update_status['download_progress'] = int((downloaded / total_size) * 100)

        # Download complete
        update_status['ready_to_install'] = True
        
    except Exception as e:
        update_status['error'] = f"Download failed: {str(e)}"
    finally:
        update_status['downloading'] = False


def start_update_checker():
    """Start the update checker in a background thread."""
    thread = threading.Thread(target=check_for_updates, daemon=True)
    thread.start()


def install_update_and_restart():
    """Launch the downloaded installer silently and exit the app."""
    if not update_status['ready_to_install'] or not os.path.exists(UPDATE_FILE_PATH):
        return False
        
    try:
        # Run Inno Setup installer silently
        # /VERYSILENT = No UI, /SUPPRESSMSGBOXES = No prompts, /FORCECLOSEAPPLICATIONS = Kills OceanNav.exe
        subprocess.Popen([UPDATE_FILE_PATH, "/VERYSILENT", "/SUPPRESSMSGBOXES", "/FORCECLOSEAPPLICATIONS"])
        
        # Exit the current Python process so the installer can overwrite the files
        os._exit(0)
    except Exception as e:
        update_status['error'] = f"Install failed: {str(e)}"
        return False

def _download_firmware(url, dest_path):
    """Downloads a firmware bin file."""
    try:
        response = requests.get(url, stream=True, timeout=15)
        response.raise_for_status()
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk: f.write(chunk)
    except Exception as e:
        print(f"[Updater] Failed to download firmware: {e}")

def _silent_flash_transmitter(bin_path):
    """Silently flashes the transmitter using esptool.py."""
    # Run in a background thread to not block the updater
    def flash():
        print("[Updater] Starting silent flash for Transmitter...")
        # Get the active serial port from the global serial_service
        try:
            from run import serial_service
            if serial_service and serial_service.is_connected:
                port = serial_service.port
                serial_service.disconnect() # Release the port
                time.sleep(1) # Give OS time to release
                
                # Assume standard esptool install in the environment
                cmd = [
                    sys.executable, "-m", "esptool", 
                    "--port", port, "--baud", "115200", 
                    "--before", "default_reset", "--after", "hard_reset", 
                    "write_flash", "-z", "0x10000", bin_path
                ]
                
                subprocess.run(cmd, check=True, capture_output=True)
                print("[Updater] Transmitter flash successful!")
                
                # Reconnect
                serial_service.connect(port)
        except Exception as e:
            print(f"[Updater] Flash failed: {e}")
            
    threading.Thread(target=flash, daemon=True).start()
