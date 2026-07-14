"""
LoRa AT command protocol builder and response parser.
Matches the firmware AT command format:
  Send:    <TRX_ID,BUOY_ID>,AT+COMMAND
  Receive: <TRX_ID,BUOY_ID>\r\n+COMMAND:data\r\nOK/ERROR\r\n
"""
import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class GPSData:
    """Parsed GPS data from +CGPSINFO response."""
    latitude: float = 0.0
    longitude: float = 0.0
    day: int = 0
    month: int = 0
    year: int = 0
    hour: int = 0
    minute: int = 0
    second: int = 0
    altitude: float = 0.0
    speed: float = 0.0
    course: float = 0.0
    satellites: int = 0
    hdop: float = 0.0
    is_cached: bool = False
    has_fix: bool = False


@dataclass
class ScanResponse:
    """Parsed SCAN response."""
    trx_id: str = ''
    buoy_id: str = ''
    success: bool = False


@dataclass
class BindResponse:
    """Parsed BIND response."""
    trx_id: str = ''
    buoy_id: str = ''
    bound: bool = False
    success: bool = False


class LoRaProtocol:
    """Builds AT commands and parses LoRa responses."""

    @staticmethod
    def build_scan_all(trx_id: str) -> str:
        """Build a SCAN command to discover all buoys."""
        return f"<{trx_id},ALL>,AT+SCAN\n"

    @staticmethod
    def build_scan_one(trx_id: str, buoy_id: str) -> str:
        """Build a SCAN command for a specific buoy."""
        return f"<{trx_id},{buoy_id}>,AT+SCAN\n"

    @staticmethod
    def build_bind(trx_id: str, buoy_id: str, bind: bool = True) -> str:
        """Build a BIND command."""
        val = '1' if bind else '0'
        return f"<{trx_id},{buoy_id}>,AT+BIND={val}\n"

    @staticmethod
    def build_gps_on(trx_id: str, buoy_id: str) -> str:
        """Build a CGPS power on command."""
        return f"<{trx_id},{buoy_id}>,AT+CGPS=1\n"

    @staticmethod
    def build_gps_off(trx_id: str, buoy_id: str) -> str:
        """Build a CGPS power off command."""
        return f"<{trx_id},{buoy_id}>,AT+CGPS=0\n"

    @staticmethod
    def build_gps_info(trx_id: str, buoy_id: str) -> str:
        """Build a CGPSINFO execute command to get GPS location."""
        return f"<{trx_id},{buoy_id}>,AT+CGPSINFO\n"

    @staticmethod
    def build_led_on(trx_id: str, buoy_id: str, r: int = 255, g: int = 255, b: int = 255) -> str:
        """Build an AT+LED=R,G,B command to turn on the LED."""
        return f"<{trx_id},{buoy_id}>,AT+LED={r},{g},{b}\n"

    @staticmethod
    def build_led_off(trx_id: str, buoy_id: str) -> str:
        """Build an AT+LED=0 command to turn off the LED."""
        return f"<{trx_id},{buoy_id}>,AT+LED=0\n"

    @staticmethod
    def build_get_battery(trx_id: str, buoy_id: str) -> str:
        """Build a BSOC command to get battery state of charge."""
        return f"<{trx_id},{buoy_id}>,AT+BSOC\n"

    @staticmethod
    def parse_header(line: str) -> tuple:
        """
        Parse the <TRX_ID,BUOY_ID> header from a response line.
        Returns (trx_id, buoy_id) or (None, None).
        """
        match = re.search(r'<([^,]+),([^>]+)>', line)
        if match:
            return match.group(1).strip().upper(), match.group(2).strip().upper()
        return None, None

    @staticmethod
    def parse_scan_response(line: str) -> Optional[ScanResponse]:
        """Parse a +SCAN: response line."""
        trx_id, buoy_id = LoRaProtocol.parse_header(line)
        if not trx_id:
            return None

        match = re.search(r'\+SCAN:(\S+)', line)
        if match:
            resp = ScanResponse()
            resp.trx_id = trx_id
            resp.buoy_id = buoy_id
            resp.success = 'OK' in line
            return resp
        return None

    @staticmethod
    def parse_bind_response(line: str) -> Optional[BindResponse]:
        """Parse a +BIND: response line."""
        trx_id, buoy_id = LoRaProtocol.parse_header(line)
        if not trx_id:
            return None

        match = re.search(r'\+BIND:(\S+)', line)
        if match:
            resp = BindResponse()
            resp.trx_id = trx_id
            resp.buoy_id = buoy_id
            data = match.group(1)
            resp.bound = data.startswith('1')
            resp.success = 'OK' in line
            return resp
        return None

    @staticmethod
    def parse_gps_response(line: str) -> Optional[GPSData]:
        """
        Parse a +CGPSINFO: or +GPSLIVE: response line.
        Format: +CGPSINFO:lat,lon,DD/MM/YYYY,HH:MM:SS,alt,speed,course,sats,hdop
        """
        match = re.search(r'\+(?:CGPSINFO|GPSLIVE):(.+)', line)
        if not match:
            return None

        data_str = match.group(1).strip()

        # Check for error messages
        if 'GPS TURNED OFF' in data_str or 'ERROR' in data_str:
            return None

        # Check for CACHED flag
        is_cached = 'CACHED' in data_str
        data_str = data_str.replace(',CACHED', '').replace(',LIVE', '')

        parts = data_str.split(',')
        if len(parts) < 2:
            return None

        gps = GPSData()
        gps.is_cached = is_cached

        try:
            gps.latitude = float(parts[0])
            gps.longitude = float(parts[1])
            gps.has_fix = (gps.latitude != 0.0 or gps.longitude != 0.0)

            if len(parts) >= 3:
                date_parts = parts[2].split('/')
                if len(date_parts) == 3:
                    gps.day = int(date_parts[0])
                    gps.month = int(date_parts[1])
                    gps.year = int(date_parts[2])

            if len(parts) >= 4:
                time_parts = parts[3].split(':')
                if len(time_parts) == 3:
                    gps.hour = int(time_parts[0])
                    gps.minute = int(time_parts[1])
                    gps.second = int(time_parts[2])

            if len(parts) >= 5:
                gps.altitude = float(parts[4])
            if len(parts) >= 6:
                gps.speed = float(parts[5])
            if len(parts) >= 7:
                gps.course = float(parts[6])
            if len(parts) >= 8:
                gps.satellites = int(parts[7])
            if len(parts) >= 9:
                gps.hdop = float(parts[8])

        except (ValueError, IndexError):
            pass

        return gps

    @staticmethod
    def is_ok_response(line: str) -> bool:
        """Check if line contains OK."""
        return 'OK' in line

    @staticmethod
    def is_error_response(line: str) -> bool:
        """Check if line contains ERROR."""
        return 'ERROR' in line

    @staticmethod
    def parse_gps_hist(line: str) -> Optional[list]:
        """
        Parse a +CGPSHIST: response line.
        Format: +CGPSHIST:lat0,lon0;lat1,lon1;...
        Returns a list of dicts: [{'lat': float, 'lon': float}, ...]
        """
        match = re.search(r'\+CGPSHIST:(.+)', line)
        if not match:
            return None

        data_str = match.group(1).strip()
        if 'ERROR' in data_str:
            return None

        history = []
        pairs = data_str.split(';')
        for pair in pairs:
            if ',' in pair:
                try:
                    lat_str, lon_str = pair.split(',')
                    lat = float(lat_str)
                    lon = float(lon_str)
                    import math
                    if not math.isnan(lat) and not math.isnan(lon):
                        # Filter out exactly 0.0 or near (0,0) which is Null Island (Africa) 
                        if abs(lat) > 0.01 or abs(lon) > 0.01:
                            history.append({'lat': lat, 'lon': lon})
                except ValueError:
                    continue
        return history
