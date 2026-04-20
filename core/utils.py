import os
import sys

def get_base_path():
    """Returns the base path for the application."""
    if hasattr(sys, '_MEIPASS'):
        # Running as a PyInstaller bundle
        return sys._MEIPASS
    else:
        # Running as a normal script - base is root (one level up from /core)
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_data_path(filename):
    """
    Returns the path for persistent data files.
    These should live in the same directory as the executable.
    """
    if hasattr(sys, '_MEIPASS'):
        # Get the directory where the .exe is located
        exe_dir = os.path.dirname(sys.executable)
        return os.path.join(exe_dir, filename)
    else:
        # Root is one level up from /core
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(root, filename)

def get_asset_path(filename):
    """
    Returns the path for internal assets (icons, sounds).
    """
    return os.path.join(get_base_path(), filename)
