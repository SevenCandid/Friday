import observer

def handle(command, speak):
    # Detect vision-related keywords
    if "what am i doing" in command or "active app" in command or "current window" in command:
        app = observer.get_active_app()
        if app and app != "Unknown":
            speak(f"You are currently focused on {app}.")
        else:
            speak("You appear to be on your desktop or an unrecognized application.")
        return True

    if "what's on my screen" in command or "what do you see" in command or "read the screen" in command:
        speak("One moment, scanning your tactical display...")
        summary = observer.observe_screen()
        speak(summary)
        return True

    return False
