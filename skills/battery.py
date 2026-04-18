import psutil

def handle(command, speak):
    # Detect battery-related keywords
    if "battery" not in command:
        return False

    # Retrieve battery sensor data
    battery = psutil.sensors_battery()

    if battery is None:
        speak("Battery information is not available on this system.")
        return True

    percent = int(battery.percent)
    is_plugged = battery.power_plugged
    
    # Construct a natural response
    status = "currently charging" if is_plugged else "on battery power"
    
    # Optional: Add alert if low
    low_battery_warning = ""
    if percent < 20 and not is_plugged:
        low_battery_warning = " You might want to plug in your charger soon."

    response = f"Your battery is at {percent} percent and is {status}.{low_battery_warning}"
    speak(response)
    
    return True
