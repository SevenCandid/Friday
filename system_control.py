import os
import subprocess
from speech import speak
from voice import listen

def open_chrome():
    """Opens Google Chrome."""
    try:
        # On Windows, 'start chrome' uses the system's registered application path
        os.system("start chrome")
        return True
    except Exception as e:
        print(f"[System Error] Failed to open Chrome: {e}")
        return False

def open_vscode():
    """Opens Visual Studio Code."""
    try:
        # 'code' is the global command for VS Code
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
        # Subprocess is fast and clean for launching system executables
        subprocess.Popen("explorer.exe")
        return True
    except Exception as e:
        print(f"[System Error] Failed to open File Explorer: {e}")
        return False

def lock_pc():
    """Locks the Windows PC."""
    try:
        # The standard Windows DLL call to lock the workstation
        os.system("rundll32.exe user32.dll,LockWorkStation")
        return True
    except Exception as e:
        print(f"[System Error] Failed to lock PC: {e}")
        return False

def shutdown_pc():
    """Shuts down the PC, requiring voice confirmation for safety."""
    print("\n[System] Awaiting voice confirmation to SHUT DOWN...")
    speak("Are you sure you want to shut down the computer?")
    
    # Listen for the user's verbal confirmation
    confirm = listen(listen_timeout=10)
    
    if confirm and ("yes" in confirm or "sure" in confirm or "do it" in confirm):
        print("Initiating shutdown sequence...")
        os.system("shutdown /s /t 1")
        return True
    else:
        print("Shutdown aborted.")
        return False

def restart_pc():
    """Restarts the PC, requiring voice confirmation for safety."""
    print("\n[System] Awaiting voice confirmation to RESTART...")
    speak("Are you sure you want to restart the computer?")
    
    # Listen for the user's verbal confirmation
    confirm = listen(listen_timeout=10)
    
    if confirm and ("yes" in confirm or "sure" in confirm or "do it" in confirm):
        print("Initiating restart sequence...")
        os.system("shutdown /r /t 1")
        return True
    else:
        print("Restart aborted.")
        return False
