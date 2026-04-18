import time
import threading
import psutil
import observer
import state_manager
import memory_manager
import os

# Cooldowns to prevent annoyance (5 minutes)
COOLDOWN = 300
_last_triggers = {}

def _execute_open_projects():
    """Example action: Open the user's coding folder."""
    # You can customize this path!
    project_path = os.path.expanduser("~/Documents")
    os.startfile(project_path)
    return "Opening your project folder now."

def _monitor_context(speak):
    """Background loop to detect activity patterns and suggest actions."""
    while True:
        try:
            current_time = time.time()
            active_app = observer.get_active_app().lower()
            cpu = psutil.cpu_percent()
            batt = psutil.sensors_battery()

            # 1. CODING CONTEXT
            if any(tech in active_app for tech in ["visual studio", "code", "pycharm", "sublime"]):
                if current_time - _last_triggers.get("coding", 0) > COOLDOWN:
                    speak("I see you're working on some code. Would you like me to open your project folder?")
                    state_manager.state.pending_action = _execute_open_projects
                    state_manager.state.pending_action_text = "coding_support"
                    _last_triggers["coding"] = current_time

            # 2. BROWSER CONTEXT (Heavy Load)
            elif "chrome" in active_app or "edge" in active_app:
                if cpu > 80 and (current_time - _last_triggers.get("heavy_browser", 0) > COOLDOWN):
                    speak("Your system is under heavy load while browsing. Should I help you close some background tasks?")
                    # Action could be a cleanup script
                    _last_triggers["heavy_browser"] = current_time

            # 3. LOW BATTERY + HEAVY APP
            if batt and batt.percent < 25 and not batt.power_plugged and cpu > 60:
                if current_time - _last_triggers.get("low_batt_heavy", 0) > COOLDOWN:
                    speak("Your battery is low and usage is high. Consider closing high-performance applications to save power.")
                    _last_triggers["low_batt_heavy"] = current_time

        except Exception as e:
            print(f"[Context Engine Error] {e}")
        
        time.sleep(30) # Check context every 30 seconds

def start_context_engine(speak):
    """Launches the situational awareness thread."""
    thread = threading.Thread(target=_monitor_context, args=(speak,), daemon=True)
    thread.start()
    print("[Context Engine] Situational awareness online.")
