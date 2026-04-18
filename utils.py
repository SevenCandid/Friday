import os
import sys

def get_base_path():
    """Returns the base path for the application."""
    if hasattr(sys, '_MEIPASS'):
        # Running as a PyInstaller bundle
        return sys._MEIPASS
    else:
        # Running as a normal script
        return os.path.abspath(".")

def get_data_path(filename):
    """
    Returns the path for persistent data files.
    These should live in the same directory as the executable,
    NOT in the temporary _MEIPASS folder.
    """
    if hasattr(sys, '_MEIPASS'):
        # Get the directory where the .exe is located
        exe_dir = os.path.dirname(sys.executable)
        return os.path.join(exe_dir, filename)
    else:
        return os.path.join(os.path.abspath("."), filename)

def get_asset_path(filename):
    """
    Returns the path for internal assets (icons, sounds).
    These are extracted to the temporary _MEIPASS folder.
    """
    return os.path.join(get_base_path(), filename)
