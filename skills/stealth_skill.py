from core import state_manager

def handle(command, speak):
    # Triggers for entering Stealth Mode
    stealth_on = [
        "stealth mode", "quiet mode", "meeting mode", 
        "go silent", "be quiet", "stop talking",
        "we are in a meeting", "lecture mode", "church mode"
    ]
    
    # Triggers for exiting Stealth Mode
    stealth_off = [
        "normal mode", "standard mode", "talk to me",
        "exit stealth", "end quiet mode", "you can speak",
        "meeting is over"
    ]

    # --- ENABLE STEALTH ---
    if any(t in command for t in stealth_on):
        state_manager.quiet_mode = True
        speak("Understood. Entering Stealth Mode. I will communicate via HUD notifications only.")
        return True

    # --- DISABLE STEALTH ---
    if any(t in command for t in stealth_off):
        state_manager.quiet_mode = False
        speak("Stealth Mode deactivated. I am now authorized for voice communication.")
        return True

    return False
