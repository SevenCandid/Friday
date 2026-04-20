import os
import sys
from . import config

def manage_startup():
    """Manages the Windows startup shortcut based on config settings."""
    if os.name != 'nt':
        return # Only for Windows
        
    try:
        auto_start = config.get("system", "auto_start")
    except:
        auto_start = True # Default to True
    
    # Path to the Windows startup folder
    startup_folder = os.path.join(os.getenv('APPDATA'), r'Microsoft\Windows\Start Menu\Programs\Startup')
    batch_path = os.path.join(startup_folder, "FridayAutoStart.bat")
    
    if auto_start:
        if not os.path.exists(batch_path):
            try:
                # Get the absolute path to the executable or script
                if getattr(sys, 'frozen', False):
                    target = sys.executable
                else:
                    target = os.path.abspath(sys.argv[0])

                # Create a .bat file to launch Friday
                with open(batch_path, 'w', encoding="utf-8") as f:
                    f.write(f'@echo off\n')
                    f.write(f'start "" "{target}"\n')
                
                print(f"[Startup] Created auto-start link at {batch_path}")
            except Exception as e:
                print(f"[Startup Error] Failed to create auto-start link: {e}")
    else:
        if os.path.exists(batch_path):
            try:
                os.remove(batch_path)
                print(f"[Startup] Disabled auto-start.")
            except Exception as e:
                print(f"[Startup Error] Failed to remove auto-start link: {e}")
