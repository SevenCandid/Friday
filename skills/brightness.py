import re

def handle(command, speak):
    # Detect brightness-related keywords
    if "brightness" not in command and "bright" not in command and "dim" not in command:
        return False

    try:
        import screen_brightness_control as sbc
        # Get current brightness
        current_brightness = sbc.get_brightness()
        if isinstance(current_brightness, list) and len(current_brightness) > 0:
            current_brightness = current_brightness[0]
        else:
            current_brightness = 50 # Default fallback
    except Exception as e:
        print(f"[Brightness Error] {e}")
        speak("I'm sorry, I couldn't access your display settings.")
        return True

    # 1. Absolute Brightness (e.g., "Set brightness to 70")
    match = re.search(r"(\d+)", command)
    if match and "to" in command:
        target = int(match.group(1))
        target = max(0, min(100, target))
        sbc.set_brightness(target)
        speak(f"Setting brightness to {target} percent.")
        return True

    # 2. Relative Brightness (Increase/Decrease)
    if "increase" in command or "up" in command or "brighter" in command:
        target = min(100, current_brightness + 10)
        sbc.set_brightness(target)
        speak(f"Increasing brightness to {target} percent.")
        return True
        
    if "decrease" in command or "down" in command or "dim" in command or "lower" in command:
        target = max(0, current_brightness - 10)
        sbc.set_brightness(target)
        speak(f"Dimming the screen to {target} percent.")
        return True

    return False
