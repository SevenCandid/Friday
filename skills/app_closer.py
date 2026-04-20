import psutil
import difflib

# Common spoken names → actual process executable names
PROCESS_ALIASES = {
    "chrome": "chrome.exe",
    "google chrome": "chrome.exe",
    "firefox": "firefox.exe",
    "mozilla": "firefox.exe",
    "edge": "msedge.exe",
    "microsoft edge": "msedge.exe",
    "spotify": "Spotify.exe",
    "discord": "Discord.exe",
    "notepad": "notepad.exe",
    "notepad++": "notepad++.exe",
    "word": "WINWORD.EXE",
    "microsoft word": "WINWORD.EXE",
    "excel": "EXCEL.EXE",
    "microsoft excel": "EXCEL.EXE",
    "powerpoint": "POWERPNT.EXE",
    "teams": "Teams.exe",
    "microsoft teams": "Teams.exe",
    "zoom": "Zoom.exe",
    "vlc": "vlc.exe",
    "paint": "mspaint.exe",
    "calculator": "CalculatorApp.exe",
    "explorer": "explorer.exe",
    "file explorer": "explorer.exe",
    "task manager": "Taskmgr.exe",
    "vs code": "Code.exe",
    "visual studio code": "Code.exe",
    "pycharm": "pycharm64.exe",
    "obs": "obs64.exe",
    "steam": "steam.exe",
    "whatsapp": "WhatsApp.exe",
    "telegram": "Telegram.exe",
    "ollama": "ollama.exe",
    "ollama app": "ollama app.exe",
    "friday": "Friday.exe",
    "main": "Friday.exe"
}

CLOSE_TRIGGERS = [
    "close", "shut down", "shutdown", "kill", "terminate",
    "exit", "quit", "stop", "end", "force close"
]


def _get_running_processes():
    """Returns a dict of {lowercase_name: [Popen objects]} for all running processes."""
    procs = {}
    for p in psutil.process_iter(['pid', 'name']):
        try:
            name = p.info['name'].lower()
            procs.setdefault(name, []).append(p)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return procs


def _find_and_kill(target_name):
    """
    Finds and terminates a process by spoken name.
    Returns (success: bool, message: str)
    """
    running = _get_running_processes()

    # 1. Check aliases first (spoken name → exe name)
    exe_name = PROCESS_ALIASES.get(target_name.lower())
    if exe_name and exe_name.lower() in running:
        procs = running[exe_name.lower()]
        for p in procs:
            try:
                p.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return True, f"{target_name.title()} has been closed."

    # 2. Direct partial match against running process names
    matches = [name for name in running if target_name.lower() in name]
    if matches:
        best = matches[0]
        for p in running[best]:
            try:
                p.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return True, f"Closed {best.replace('.exe', '').title()}."

    # 3. Fuzzy match (handles typos/close pronunciations)
    fuzzy = difflib.get_close_matches(target_name.lower(), running.keys(), n=1, cutoff=0.6)
    if fuzzy:
        best = fuzzy[0]
        for p in running[best]:
            try:
                p.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return True, f"Closed {best.replace('.exe', '').title()}."

    return False, f"I couldn't find a running application named {target_name}."


def handle(command, speak):
    import re
    cmd = command.lower().strip()

    # Detect a close trigger using word boundaries to avoid matching 'end' in 'friends'
    trigger_used = None
    for t in CLOSE_TRIGGERS:
        if re.search(rf'\b{re.escape(t)}\b', cmd):
            trigger_used = t
            break
            
    if not trigger_used:
        return False

    # Extract the app name (everything after the trigger word)
    # e.g. "close chrome" → "chrome", "shut down spotify" → "spotify"
    parts = cmd.split(trigger_used, 1)
    if len(parts) < 2:
        return False

    target = parts[1].strip()

    # --- CONTEXTUAL 'THIS' LOGIC ---
    if target == "this" or not target:
        from core import state_manager
        active_title = state_manager.active_window.lower()
        
        # Try to find a match for the active window title in our aliases
        matched_alias = None
        for alias, exe in PROCESS_ALIASES.items():
            if alias in active_title:
                matched_alias = alias
                break
        
        if matched_alias:
            target = matched_alias
        else:
            # If no alias match, try to use the first word of the window title
            # (e.g. "Notepad - file.txt" -> "Notepad")
            target = active_title.split("-")[-1].strip() if "-" in active_title else active_title.split()[0]
            print(f"[App Closer] No alias for '{active_title}', trying generic: '{target}'")

    # Filter out generic filler words that aren't app names
    filler = ["the", "app", "application", "program", "window", "it", "that"]
    for word in filler:
        target = target.replace(word, "").strip()

    if not target:
        speak("Which application would you like me to close?")
        return True

    success, message = _find_and_kill(target)
    speak(message)
    return True
