import PyInstaller.__main__
import os
import shutil

def build():
    print("--- Friday Executable Builder ---")
    
    # 1. Clean previous builds
    try:
        if os.path.exists("build"): shutil.rmtree("build")
        if os.path.exists("dist"): shutil.rmtree("dist")
    except Exception as e:
        print(f"[Build Warning] Could not fully clean previous build folders: {e}")
        print("Continuing anyway... (this is usually fine if you closed Friday.exe)")

    # 2. Define the PyInstaller command
    PyInstaller.__main__.run([
        'main.py',                     # Entry point
        '--name=Friday',               # Name of the .exe
        '--onedir',                    # Bundle into a single folder (stable for plugins)
        '--windowed',                  # No console window
        '--additional-hooks-dir=hooks', # Use our fixed hooks to prevent crashes
        
        # Add Data Folders
        '--add-data=skills;skills',
        '--add-data=vosk-model-small-en-us-0.15;vosk-model-small-en-us-0.15',
        '--add-data=personality.py;.',
        
        # Hidden imports (libraries PyInstaller might miss)
        '--hidden-import=pycaw',
        '--hidden-import=comtypes',
        '--hidden-import=psutil',
        '--hidden-import=screen_brightness_control',
        '--hidden-import=pygetwindow',
        '--hidden-import=pytesseract',
        '--hidden-import=PIL',
        '--hidden-import=importlib.metadata',
        '--hidden-import=winsound',
        '--collect-all=webrtcvad',     # FIX: Collects webrtcvad even if metadata is missing
        '--collect-all=vosk',          # FIX: Collects Vosk DLLs and internal files
        '--collect-all=pyttsx3',       # FIX: Ensures speech engine is fully bundled
        '--collect-all=pygetwindow',   # FIX: Ensures window tracking is bundled
        
        '--noconfirm',                 # Overwrite existing dist
        '--clean'                      # Clean cache before build
    ])

    print("\n--- Build Complete! ---")
    print("Your executable is located in: dist/Friday/Friday.exe")
    print("Note: Make sure to copy your 'piper' folder into 'dist/Friday/' if you want neural voice support.")

if __name__ == "__main__":
    build()
