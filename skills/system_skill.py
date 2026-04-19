import sys
import os
import random
import psutil

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import system_control

def handle(command, speak):
    # App Launching
    if ("open" in command or "launch" in command) and ("vscode" in command or "visual studio" in command or "code" in command):
        system_control.open_vscode()
        speak("Opening VS Code.")
        return True
        
    if ("open" in command or "launch" in command) and ("file explorer" in command or "explorer" in command):
        system_control.open_file_explorer()
        speak("Opening File Explorer.")
        return True
        
    if ("open" in command or "launch" in command) and "clock" in command:
        system_control.open_clock()
        speak("Opening the Windows Clock app.")
        return True
        
    # System Monitoring
    if any(k in command for k in ["monitor", "status", "cpu", "ram", "system"]):
        if "open" not in command and "launch" not in command:
            cpu = psutil.cpu_percent(interval=0.5)
            ram = psutil.virtual_memory().percent
            speak(f"Your CPU is currently at {cpu} percent, and RAM usage is at {ram} percent.")
            return True

    # Power Controls
    if "shutdown" in command or "shut down" in command or "turn off" in command:
        if system_control.shutdown_pc():
            speak("Goodbye.")
        else:
            speak("Okay, I will keep the computer running.")
        return True
        
    if "restart" in command:
        if system_control.restart_pc():
            speak("See you in a moment.")
        else:
            speak("Restart cancelled.")
        return True
        
    if "lock" in command and ("computer" in command or "pc" in command or "screen" in command):
        system_control.lock_pc()
        speak("Locking the computer.")
        return True
        
    return False
