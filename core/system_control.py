import os
import subprocess
from .speech import speak
from .voice import listen

def open_chrome():
    """Opens Google Chrome."""
    try:
        os.system("start chrome")
        return True
    except Exception as e:
        print(f"[System Error] Failed to open Chrome: {e}")
        return False

def open_vscode():
    """Opens Visual Studio Code."""
    try:
        os.system("start code")
        return True
    except Exception as e:
        print(f"[System Error] Failed to open VS Code: {e}")
        return False

def open_clock():
    """Opens the Windows Clock app."""
    try:
        os.system("start ms-clock:")
        return True
    except Exception as e:
        print(f"[System Error] Failed to open Clock: {e}")
        return False

def open_file_explorer():
    """Opens the Windows File Explorer."""
    try:
        subprocess.Popen("explorer.exe")
        return True
    except Exception as e:
        print(f"[System Error] Failed to open File Explorer: {e}")
        return False

def lock_pc():
    """Locks the Windows PC."""
    try:
        os.system("rundll32.exe user32.dll,LockWorkStation")
        return True
    except Exception as e:
        print(f"[System Error] Failed to lock PC: {e}")
        return False

def shutdown_pc():
    """Sets a pending action to shut down the PC."""
    from . import state_manager
    def _execute():
        speak("Goodbye.")
        os.system("shutdown /s /t 1")
    state_manager.pending_action = _execute
    state_manager.pending_action_text = "shutdown the computer"
    speak("Are you sure you want to shut down the computer?")
    return True

def restart_pc():
    """Sets a pending action to restart the PC."""
    from . import state_manager
    def _execute():
        speak("See you in a moment.")
        os.system("shutdown /r /t 1")
    state_manager.pending_action = _execute
    state_manager.pending_action_text = "restart the computer"
    speak("Are you sure you want to restart the computer?")
    return True
