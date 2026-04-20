import psutil
import time
import threading
from .speech import speak
from . import state_manager

# State tracking to prevent spamming
_alert_30_triggered = False
_alert_20_triggered = False
_last_plugged_state = None

def _monitor_loop():
    """Background loop that checks battery levels and charger state."""
    global _alert_30_triggered, _alert_20_triggered, _last_plugged_state
    
    # Initialize the state on first run
    initial_battery = psutil.sensors_battery()
    if initial_battery:
        _last_plugged_state = initial_battery.power_plugged

    while True:
        try:
            battery = psutil.sensors_battery()
            
            if battery:
                percent = battery.percent
                is_plugged = battery.power_plugged
                
                # 1. Detect Charger Plug/Unplug
                if _last_plugged_state is not None and is_plugged != _last_plugged_state:
                    if is_plugged:
                        speak("Power levels stabilizing. Charger connected.")
                        state_manager.add_to_chat("System", "⚡ CHARGER CONNECTED")
                    else:
                        speak("Sir, the charger has been disconnected. We are on battery power.")
                        state_manager.add_to_chat("System", "🔋 ON BATTERY POWER")
                    _last_plugged_state = is_plugged

                # 2. Critical Alert (Below 20%)
                if percent <= 20 and not is_plugged:
                    if not _alert_20_triggered:
                        speak("Warning. Battery critically low. I am dimming the tactical display to conserve power.")
                        state_manager.add_to_chat("SEVEN", "⚠️ CRITICAL POWER: DIMMING DISPLAY")
                        
                        # Auto-dim screen
                        try:
                            import screen_brightness_control as sbc
                            sbc.set_brightness(10)
                        except:
                            pass
                            
                        _alert_20_triggered = True
                
                # 3. Low Battery Alert (Below 30%)
                elif percent <= 30 and not is_plugged:
                    if not _alert_30_triggered:
                        speak(f"Sir, battery is at {int(percent)} percent. Please consider a power source.")
                        state_manager.add_to_chat("SEVEN", f"🔋 LOW BATTERY: {int(percent)}%")
                        _alert_30_triggered = True
                        _alert_20_triggered = False # Reset critical if we hovered back up slightly
                
                # Reset triggers if we are charging or above thresholds
                if is_plugged or percent > 35:
                    if _alert_30_triggered or _alert_20_triggered:
                        print("[Battery] Thresholds reset (Charging or high level)")
                    _alert_30_triggered = False
                    _alert_20_triggered = False
            
        except Exception as e:
            print(f"[Battery Monitor Error] {e}")
            
        # Check every 10 seconds for charger state, levels can be slower but charger needs to be fast
        time.sleep(10)

def start_monitoring():
    """Initializes and starts the background battery monitoring thread."""
    monitor_thread = threading.Thread(target=_monitor_loop, daemon=True, name="BatteryMonitorThread")
    monitor_thread.start()
    print("[System] Proactive Battery Monitor activated.")
