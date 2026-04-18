import psutil
import time
import threading
from speech import speak

# State tracking to prevent spamming the same alert
_alert_30_triggered = False
_alert_20_triggered = False

def _monitor_loop():
    """Background loop that checks battery levels every minute."""
    global _alert_30_triggered, _alert_20_triggered
    
    while True:
        try:
            battery = psutil.sensors_battery()
            
            if battery:
                percent = battery.percent
                is_plugged = battery.power_plugged
                
                # Critical Alert (Below 20%)
                if percent <= 20 and not is_plugged:
                    if not _alert_20_triggered:
                        speak("Warning. Battery critically low. Save your work immediately.")
                        _alert_20_triggered = True
                
                # Low Battery Alert (Below 30%)
                elif percent <= 30 and not is_plugged:
                    if not _alert_30_triggered:
                        speak("Your battery is below 30 percent. Please consider charging.")
                        _alert_30_triggered = True
                        _alert_20_triggered = False # Reset critical if we hovered back up slightly
                
                # Reset triggers if we are charging or above thresholds
                if is_plugged or percent > 35:
                    _alert_30_triggered = False
                    _alert_20_triggered = False
            
        except Exception as e:
            print(f"[Battery Monitor Error] {e}")
            
        # Wait 60 seconds before checking again
        time.sleep(60)

def start_monitoring():
    """Initializes and starts the background battery monitoring thread."""
    monitor_thread = threading.Thread(target=_monitor_loop, daemon=True)
    monitor_thread.start()
    print("[System] Proactive Battery Monitor started.")
