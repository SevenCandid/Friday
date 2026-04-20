import requests
import time
import threading
from . import config
from . import state_manager
from . import location_helper
from .speech import speak

# State to prevent spamming
_last_rain_alert = 0
_ALERT_COOLDOWN = 14400 # 4 hours

def _weather_monitor():
    """Background loop to check for rain and extreme weather."""
    global _last_rain_alert
    
    while True:
        try:
            # PROACTIVE: Always sync location first to ensure the background check is accurate
            location_helper.sync_location()
            
            city = state_manager.current_city
            lat, lon = state_manager.current_lat, state_manager.current_lon
            
            url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=precipitation_probability_max&timezone=auto"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                rain_prob = data["daily"]["precipitation_probability_max"][0]
                
                current_time = time.time()
                
                # Proactive Rain Alert
                if rain_prob >= 50 and (current_time - _last_rain_alert > _ALERT_COOLDOWN):
                    msg = f"Sir, I've detected a {rain_prob} percent chance of rain in {city} today. You might want to keep an umbrella handy."
                    speak(msg)
                    state_manager.add_to_chat("SEVEN", f"🌩️ WEATHER ALERT: {rain_prob}% RAIN PROBABILITY")
                    _last_rain_alert = current_time
            
        except Exception as e:
            print(f"[Weather Monitor Error] {e}")
            
        # Check every hour
        time.sleep(3600)

def start_monitoring():
    """Initializes and starts the proactive weather monitoring thread."""
    thread = threading.Thread(target=_weather_monitor, daemon=True, name="WeatherMonitorThread")
    thread.start()
    print("[System] Proactive Weather Monitoring activated.")
