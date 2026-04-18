import os
import shutil
import glob
from pathlib import Path
import random

def _find_on_system(filename):
    """Searches common user directories for a specific file."""
    search_dirs = [
        Path.home() / "Desktop",
        Path.home() / "Downloads",
        Path.home() / "Documents"
    ]
    
    matches = []
    for directory in search_dirs:
        if not directory.exists(): continue
        
        # Recursive search for the filename
        for root, dirs, files in os.walk(directory):
            # Avoid hidden/system folders
            if any(part.startswith('.') for part in root.split(os.sep)): continue
            
            for f in files:
                if filename.lower() in f.lower():
                    matches.append(os.path.join(root, f))
            
            if len(matches) > 10: break # Stop searching after 10 matches
            
    return matches

def handle(command, speak):
    # Detect File-related keywords
    file_keywords = ["file", "folder", "search", "find", "locate", "move", "open"]
    if not any(kw in command for kw in file_keywords):
        return False

    # 1. SEARCH / FIND
    if "find" in command or "search" in command or "locate" in command:
        target = command.split("file")[-1].strip() if "file" in command else command.split("locate")[-1].strip()
        if not target: return False
        
        speak(f"Searching for {target} on your system.")
        matches = _find_on_system(target)
        
        if matches:
            print(f"\n--- Found {len(matches)} matches for '{target}' ---")
            for i, m in enumerate(matches[:10]):
                print(f"[{i+1}] {m}")
            print("------------------------------------------\n")
            
            speak(f"I found {len(matches)} matches. I've listed them in the console. Opening the first one for you.")
            os.startfile(matches[0])
        else:
            speak(f"I'm sorry, I couldn't find any files matching {target} in your common folders.")
        return True

    # 2. OPEN
    if "open" in command:
        target = command.split("file")[-1].strip() if "file" in command else command.split("folder")[-1].strip()
        if not target: return False
        
        # Try as a direct path first
        if os.path.exists(target):
            os.startfile(target)
            speak(f"Opening {os.path.basename(target)}.")
            return True
        else:
            # Try to find it if it's just a name
            matches = _find_on_system(target)
            if matches:
                os.startfile(matches[0])
                speak(f"Opening {os.path.basename(matches[0])}.")
                return True
        return False

    # 3. MOVE
    if "move" in command and "to" in command:
        try:
            # Extract "move [file] to [folder]"
            parts = command.split("move")[-1].split("to")
            file_name = parts[0].replace("file", "").strip()
            folder_name = parts[1].strip()
            
            # Find the source file
            src_matches = _find_on_system(file_name)
            if not src_matches:
                speak(f"I couldn't locate the source file {file_name}.")
                return True
                
            src_path = src_matches[0]
            
            # Resolve destination folder
            dest_dir = Path.home() / "Desktop" / folder_name # Default to desktop subfolder
            if not dest_dir.exists():
                os.makedirs(dest_dir)
            
            dest_path = dest_dir / os.path.basename(src_path)
            
            shutil.move(src_path, dest_path)
            speak(f"Successfully moved {file_name} to your {folder_name} folder.")
            print(f"[File Move] {src_path} -> {dest_path}")
        except Exception as e:
            print(f"[Move Error] {e}")
            speak("I encountered an error while trying to move that file.")
        return True

    return False
