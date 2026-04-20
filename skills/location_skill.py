import requests
from core import state_manager
from core import location_helper

def handle(command, speak):
    location_keywords = ["where am i", "my location", "what is my city", "where are we", "current location"]
    if not any(k in command for k in location_keywords):
        return False

    speak("Triangulating your precise tactical coordinates...")
    
    # Use centralized helper
    success, town = location_helper.sync_location()
    
    if success:
        lat, lon = state_manager.current_lat, state_manager.current_lon
        report = f"My hardware sensors indicate you are precisely at {town}. "
        report += f"Coordinates: {lat}, {lon}."
        speak(report)
        state_manager.add_to_chat("SEVEN", f"--- PRECISION GPS DATA ---\nArea: {town}\nLat/Lon: {lat}, {lon}")
        return True

    # Fallback to IP if GPS fails
    try:
        response = requests.get("http://ip-api.com/json/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data["status"] == "success":
                city = data.get("city", "Unknown City")
                report = f"I'm using your IP-based location as a fallback. You appear to be near {city}."
                speak(report)
            else:
                speak("I'm having trouble with all my positioning sensors.")
    except Exception as e:
        print(f"[Location Error] {e}")
        speak("I encountered an error during triangulation.")
    
    return True
