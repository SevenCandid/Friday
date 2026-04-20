import os
import threading
import time
import difflib
from pathlib import Path
import state_manager

# Internal index of apps
_app_index = {}
_last_scan = 0

def get_app_count():
    """Returns the number of indexed applications."""
    return len(_app_index)

def _scan_apps():
    """Background task to index installed applications."""
    global _app_index, _last_scan
    
    new_index = {}
    
    # Common locations for Start Menu shortcuts (.lnk files)
    search_paths = [
        os.path.join(os.environ["ProgramData"], "Microsoft", "Windows", "Start Menu", "Programs"),
        os.path.join(os.environ["AppData"], "Microsoft", "Windows", "Start Menu", "Programs"),
        os.path.join(os.path.expanduser("~"), "Desktop")
    ]

    for path in search_paths:
        if not os.path.exists(path): continue
        
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith(".lnk") or file.endswith(".exe"):
                    # Clean the name (e.g. "Google Chrome.lnk" -> "google chrome")
                    app_name = file.rsplit('.', 1)[0].lower()
                    full_path = os.path.join(root, file)
                    
                    # Store in index (don't overwrite if we already have it)
                    if app_name not in new_index:
                        new_index[app_name] = full_path
                        
    _app_index = new_index
    _last_scan = time.time()
    state_manager.app_count = len(_app_index)
    print(f"[App Launcher] Indexed {len(_app_index)} applications.")

def _background_refresher():
    """Periodically refreshes the app index in the background."""
    while True:
        _scan_apps()
        time.sleep(600) # Refresh every 10 minutes

# Start the initial scan and background thread immediately on import
threading.Thread(target=_background_refresher, daemon=True).start()

def handle(command, speak):
    import memory_manager
    
    # 1. Handle "How many apps"
    if "how many" in command and ("app" in command or "program" in command):
        count = get_app_count()
        speak(f"You have {count} applications indexed and ready for launch.")
        return True

    # 2. Handle "List Apps" command variants
    list_keywords = ["list my apps", "show available apps", "list all installed apps", "show all available apps", "list apps", "show apps", "what apps"]
    if any(k in command for k in list_keywords):
        all_apps = sorted(_app_index.keys())
        count = len(all_apps)
        if count == 0:
            speak("I haven't indexed any applications yet.")
            return True
        app_list_str = "\n".join([f"• {app.title()}" for app in all_apps])
        speak(f"I have indexed {count} applications. Displaying them in your tactical HUD now.")
        
        # We push the long list directly to the chat without speaking it (to avoid noise)
        import state_manager
        state_manager.add_to_chat("Friday", f"--- INDEXED APPLICATIONS ({count}) ---\n{app_list_str}")
        return True

    # 3. Handle Launching
    if "open" not in command and "launch" not in command:
        return False

    target_app = ""
    if "open" in command: target_app = command.split("open")[-1].strip()
    elif "launch" in command: target_app = command.split("launch")[-1].strip()

    if not target_app: return False

    # --- INTELLIGENT MATCHING ENGINE ---
    # Filter out installer/uninstaller/config shortcuts (never what the user wants)
    JUNK_WORDS = ["uninstall", "setup", "remove", "configuration", "config tools", "update", "repair"]

    # 1. Partial & Exact Match (against clean candidates only)
    candidates = [
        name for name in _app_index.keys()
        if target_app in name and not any(junk in name for junk in JUNK_WORDS)
    ]

    # 2. Fuzzy Match fallback
    if not candidates:
        all_clean = [n for n in _app_index.keys() if not any(j in n for j in JUNK_WORDS)]
        candidates = difflib.get_close_matches(target_app, all_clean, n=3, cutoff=0.5)

    # Also try with junk if still nothing
    if not candidates:
        candidates = difflib.get_close_matches(target_app, _app_index.keys(), n=3, cutoff=0.5)

    if not candidates:
        speak(f"I'm sorry, I couldn't find an application named {target_app}.")
        return True

    # 3. Exact match wins immediately — no need to ask
    if target_app in candidates:
        best_match = target_app
    else:
        # Use Memory to rank, then prefer shorter names (more specific)
        usage_data = memory_manager.get_memory("app_usage") or {}
        candidates.sort(key=lambda x: (-usage_data.get(x, 0), len(x)))

        # 4. If still ambiguous after ranking, ask — but only between top 2
        if len(candidates) > 1:
            top_usage = usage_data.get(candidates[0], 0)
            second_usage = usage_data.get(candidates[1], 0)
            if top_usage <= second_usage:
                options = " or ".join([c.title() for c in candidates[:2]])
                speak(f"Did you mean {options}?")
                return True

        best_match = candidates[0]
    try:
        os.startfile(_app_index[best_match])
        speak(f"Launching {best_match.title()}.")
        
        # Log Usage in Memory
        usage_data[best_match] = usage_data.get(best_match, 0) + 1
        memory_manager.set_memory("app_usage", usage_data)
        return True
    except Exception as e:
        print(f"[App Launcher Error] {e}")
        return False
