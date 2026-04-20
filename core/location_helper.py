import subprocess
import requests
from . import state_manager

def get_device_location():
    """Attempts to get high-accuracy coordinates from the Windows Location Service."""
    try:
        ps_script = (
            "Add-Type -AssemblyName System.Device; "
            "$GeoWatcher = New-Object System.Device.Location.GeoCoordinateWatcher; "
            "$GeoWatcher.Start(); "
            "$timeout = 0; "
            "while (($GeoWatcher.Status -ne 'Ready') -and ($GeoWatcher.Permission -ne 'Denied') -and ($timeout -lt 50)) { "
            "  Start-Sleep -Milliseconds 100; $timeout++; "
            "}; "
            "$pos = $GeoWatcher.Position.Location; "
            "if ($pos.IsUnknown) { Write-Output 'UNKNOWN' } "
            "else { Write-Output \"$($pos.Latitude),$($pos.Longitude)\" }"
        )
        
        result = subprocess.check_output(
            ["powershell", "-Command", ps_script], 
            text=True, 
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
        ).strip()
        
        if result and "UNKNOWN" not in result and "," in result:
            lat, lon = result.split(",")
            return float(lat), float(lon)
    except Exception as e:
        print(f"[Location Helper Error] {e}")
    return None

def sync_location():
    """Performs a full GPS and reverse-geocode sync, updating the state manager."""
    coords = get_device_location()
    if coords:
        lat, lon = coords
        try:
            headers = {"User-Agent": "SEVEN-AI-Assistant"}
            res = requests.get(f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json", headers=headers)
            if res.status_code == 200:
                data = res.json()
                address = data.get("address", {})
                town = address.get("city") or address.get("town") or address.get("village") or "Unknown Area"
                
                state_manager.current_city = town
                state_manager.current_lat = lat
                state_manager.current_lon = lon
                return True, town
        except:
            pass
    return False, None
