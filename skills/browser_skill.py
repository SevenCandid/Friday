import webbrowser
import random
import sys
import os

# Add parent dir to path so we can import system_control if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import system_control

def handle(command, speak):
    # Chrome logic
    if ("open" in command or "launch" in command) and "chrome" in command:
        system_control.open_chrome()
        speak(random.choice(["Opening Chrome.", "Launching your browser.", "Sure, opening Chrome now."]))
        return True
        
    # YouTube logic
    if "youtube" in command:
        webbrowser.open("https://www.youtube.com")
        speak(random.choice(["Opening YouTube.", "Taking you to YouTube."]))
        return True
        
    return False
