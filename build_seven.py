import PyInstaller.__main__
import os
import shutil

def build():
    print("--- SEVEN v2.0 Executable Builder ---")
    
    # 0. Kill SEVEN if it's running (to avoid PermissionError)
    import subprocess
    try:
        subprocess.run(["taskkill", "/F", "/IM", "SEVEN.exe"], 
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        print("[Build] Terminated running SEVEN instance.")
    except:
        pass

    # 1. Clean previous builds
    try:
        if os.path.exists("build"): shutil.rmtree("build")
        if os.path.exists("dist"): shutil.rmtree("dist")
    except Exception as e:
        print(f"[Build Warning] Could not fully clean previous build folders: {e}")
        print("Continuing anyway... (this is usually fine if you closed the application)")

    # 2. Dynamically prepare data files
    datas = [
        ('core', 'core'),
        ('skills', 'skills'),
        ('vosk-model-small-en-us-0.15', 'vosk-model-small-en-us-0.15'),
        ('seven.ico', '.'),
    ]
    
    # Only add piper if the folder exists
    if os.path.exists("piper"):
        print("[Build] Found 'piper' folder. Bundling neural voice engine...")
        datas.append(('piper', 'piper'))
    else:
        print("[Build Warning] 'piper' folder not found. SEVEN will build in 'Lite Mode' (using SAPI5 fallback).")

    # 3. Define the PyInstaller command
    PyInstaller.__main__.run([
        'main.py',                     # Entry point
        '--name=SEVEN',                # Name of the .exe
        '--onedir',                    # Bundle into a single folder (stable for plugins)
        '--windowed',                  # No console window
        '--additional-hooks-dir=hooks', # Use fixed hooks to prevent crashes
        
        # Add Data Folders
        *[f'--add-data={src}{os.pathsep}{dst}' for src, dst in datas],
        '--icon=seven.ico',
        
        # Hidden imports (libraries PyInstaller might miss)
        '--hidden-import=pycaw',
        '--hidden-import=comtypes',
        '--hidden-import=psutil',
        '--hidden-import=screen_brightness_control',
        '--hidden-import=pygetwindow',
        '--hidden-import=pytesseract',
        '--hidden-import=PIL',
        '--hidden-import=flask',
        '--hidden-import=werkzeug',
        '--hidden-import=importlib.metadata',
        '--hidden-import=winsound',
        '--hidden-import=feedparser',
        '--hidden-import=duckduckgo_search',
        '--hidden-import=wikipedia',
        '--hidden-import=requests',
        '--hidden-import=html',
        '--hidden-import=sqlite3',
        '--hidden-import=pyautogui',
        '--hidden-import=pystray',
        '--hidden-import=faster_whisper',
        '--hidden-import=ctranslate2',
        '--hidden-import=webrtcvad',
        
        # Auto-collect critical binaries/data
        '--collect-all=webrtcvad',
        '--collect-all=vosk',
        '--collect-all=pyttsx3',
        '--collect-all=faster_whisper',
        '--collect-all=ctranslate2',
        
        '--noconfirm',                 # Overwrite existing dist
        '--clean'                      # Clean cache before build
    ])

    print("\n--- Build Complete! ---")
    print("Your executable is located in: dist/SEVEN/SEVEN.exe")
    print("Note: Ensure 'config.json' and your 'last_speech.wav' are in the root folder.")

if __name__ == "__main__":
    build()
