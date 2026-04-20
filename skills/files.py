import os
import shutil
from pathlib import Path
from core import state_manager
from core import file_manager

def _find_on_system(filename):
    """Searches common user directories for a specific file with a depth limit."""
    search_dirs = [
        Path.home() / "Desktop",
        Path.home() / "Downloads",
        Path.home() / "Documents"
    ]
    
    matches = []
    MAX_DEPTH = 2
    
    for directory in search_dirs:
        if not directory.exists(): continue
        base_depth = str(directory).count(os.sep)
        for root, dirs, files in os.walk(directory):
            current_depth = root.count(os.sep)
            if current_depth - base_depth > MAX_DEPTH:
                del dirs[:]
                continue
            if any(part.startswith('.') for part in root.split(os.sep)): continue
            for f in files:
                if filename.lower() in f.lower():
                    matches.append(os.path.join(root, f))
            if len(matches) > 10: break
    return matches

def handle(command, speak):
    cmd = command.lower().strip()
    
    # 0. Strict Keywords to avoid hijacking
    file_keywords = ["file", "folder", "document", "directory", "note", "desktop", "download"]
    if not any(kw in cmd for kw in file_keywords):
        return False

    # 1. SEARCH / FIND
    if any(k in cmd for k in ["find", "search", "locate"]):
        target = cmd.split("file")[-1].strip() if "file" in cmd else cmd.split("folder")[-1].strip()
        if not target or target == cmd: return False
        
        speak(f"Triangulating {target} on your local system...")
        matches = _find_on_system(target)
        if matches:
            speak(f"I found {len(matches)} matches. Opening the most relevant one.")
            os.startfile(matches[0])
            return True
        else:
            speak(f"I couldn't locate any files matching {target} in your common directories.")
            return True

    # 2. OPEN FOLDERS
    folder_map = {"download": "downloads", "desktop": "desktop", "document": "documents"}
    for kw, path_key in folder_map.items():
        if "open" in cmd and kw in cmd:
            file_manager.open_folder(path_key)
            speak(f"Opening your {kw} directory.")
            return True

    # 3. CREATE / WRITE
    if "create" in cmd and "file" in cmd:
        filename = "SEVEN_Tactical_File"
        if "named" in cmd: filename = cmd.split("named")[-1].strip()
        filepath = file_manager.SHORTCUTS["desktop"] / f"{filename}.txt"
        if file_manager.create_file(str(filepath), "Initialized by SEVEN.\n"):
            speak(f"I have deployed the file '{filename}' to your desktop.")
        return True

    if "note" in cmd and ("write" in cmd or "add" in cmd or "save" in cmd):
        content = cmd.split("note")[-1].strip()
        filepath = file_manager.SHORTCUTS["desktop"] / "SEVEN_Mission_Notes.txt"
        if file_manager.write_file(str(filepath), f"- {content}\n"):
            speak("Note captured and saved to your Mission Notes on the desktop.")
        return True

    return False
