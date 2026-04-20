import os
from pathlib import Path

# --- Windows Folder Shortcuts ---
HOME_DIR = Path.home()

SHORTCUTS = {
    "desktop": HOME_DIR / "Desktop",
    "downloads": HOME_DIR / "Downloads",
    "documents": HOME_DIR / "Documents"
}

def open_folder(path_or_shortcut: str) -> bool:
    """
    Opens a folder in Windows File Explorer. 
    Accepts either a shortcut name ('desktop', 'downloads', 'documents') or a direct path string.
    """
    try:
        lookup = path_or_shortcut.lower().strip()
        
        # Resolve shortcut if provided, otherwise treat it as a direct path
        if lookup in SHORTCUTS:
            target_path = SHORTCUTS[lookup]
        else:
            target_path = Path(path_or_shortcut)
            
        if not target_path.exists():
            print(f"[File Error] Cannot open. The path '{target_path}' does not exist.")
            return False
            
        # os.startfile is the fastest, native way to open folders on Windows
        os.startfile(target_path)
        return True
        
    except Exception as e:
        print(f"[File Error] Failed to open folder: {e}")
        return False


def create_file(file_path: str, content: str = "") -> bool:
    """
    Creates a new text file at the specified path and writes initial content to it.
    If the file already exists, this will overwrite it.
    """
    try:
        path = Path(file_path)
        
        # Ensure the target directory exists before trying to create a file there
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # 'w' mode creates the file and writes the content
        with open(path, 'w', encoding='utf-8') as file:
            file.write(content)
        return True
        
    except Exception as e:
        print(f"[File Error] Failed to create file: {e}")
        return False


def write_file(file_path: str, content: str) -> bool:
    """
    Appends text to an existing file. 
    If the file does not exist, it will be automatically created.
    """
    try:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # 'a' mode appends to the file instead of overwriting it
        with open(path, 'a', encoding='utf-8') as file:
            file.write(content + "\n")
        return True
        
    except Exception as e:
        print(f"[File Error] Failed to write to file: {e}")
        return False


def read_file(file_path: str) -> str:
    """
    Reads all text from a file and returns it as a string.
    Returns None if the file doesn't exist or cannot be read.
    """
    try:
        path = Path(file_path)
        
        if not path.exists():
            print(f"[File Error] Cannot read. The file '{path}' does not exist.")
            return None
            
        # 'r' mode securely reads the file contents
        with open(path, 'r', encoding='utf-8') as file:
            return file.read()
            
    except Exception as e:
        print(f"[File Error] Failed to read file: {e}")
        return None
