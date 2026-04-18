import psutil
import time
import threading
import observer
import memory_manager

# Cooldown timers to prevent spam (in seconds)
_cooldowns = {
    "high_cpu": 0,
    "low_battery": 0,
    "idle_check": 0
}

COOLDOWN_PERIOD = 600 # 10 minutes

def greet_user(speak):
    """Initial system check and randomized greeting."""
    import random
    
    greetings = [
        "Welcome back. I'm Friday, your personal assistant.",
        "Good to see you again. I'm Friday, your assistant.",
        "Hello again. Friday here, ready to help."
    ]
    
    try:
        batt = psutil.sensors_battery()
        cpu = psutil.cpu_percent()
        
        msg = random.choice(greetings) + " "
        
        if batt:
            msg += f"Your battery is at {int(batt.percent)} percent. "
        
        if cpu > 70:
            msg += "The system is running a bit hot, but otherwise stable."
        else:
            msg += "System status is optimal. Standing by."
            
        speak(msg)
    except Exception as e:
        print(f"[Sentinel Error] Greeting failed: {e}")

def _monitor_loop(speak):
    """Background loop to check system state and trigger proactive messages."""
    while True:
        try:
            current_time = time.time()
            
            # 1. Check CPU Usage
            cpu = psutil.cpu_percent(interval=1)
            if cpu > 85 and (current_time - _cooldowns["high_cpu"] > COOLDOWN_PERIOD):
                speak("Excuse me, I noticed your CPU usage is over 85 percent. You might want to check for background apps.")
                _cooldowns["high_cpu"] = current_time

            # 2. Check Battery
            batt = psutil.sensors_battery()
            if batt and batt.percent < 20 and not batt.power_plugged and (current_time - _cooldowns["low_battery"] > COOLDOWN_PERIOD):
                speak(f"Warning: Your battery has dropped to {int(batt.percent)} percent. Please connect a power source.")
                _cooldowns["low_battery"] = current_time

            # 3. Check Context (Observer Integration)
            active_app = observer.get_active_app()
            # This can be used for "Smart Suggestions" later
            # e.g. "I see you're using VS Code, should I open your task list?"
            
        except Exception as e:
            print(f"[Sentinel Error] Monitor loop hit a snag: {e}")
            
        time.sleep(60) # Check every minute

def start_sentinel(speak):
    """Launches the proactive monitoring thread."""
    thread = threading.Thread(target=_monitor_loop, args=(speak,), daemon=True)
    thread.start()
    print("[Sentinel] Proactive monitoring system online.")
