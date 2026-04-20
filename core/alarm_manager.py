import threading
import time
import datetime
import winsound
import json
import os
import re
from . import state_manager
from . import utils
from .speech import speak

ALARM_FILE = utils.get_data_path("alarms.json")

# Internal state
_alarms = []
_alarm_state = "IDLE"  # IDLE, RINGING, SNOOZED
_ringing_thread = None
_current_ringing_alarm = None

def _load_alarms():
    """Loads alarms from the JSON file."""
    global _alarms
    if os.path.exists(ALARM_FILE):
        try:
            with open(ALARM_FILE, "r") as f:
                _alarms = json.load(f)
            print(f"[System] Loaded {len(_alarms)} alarms from storage.")
        except Exception as e:
            print(f"[System Error] Failed to load alarms: {e}")
            _alarms = []
    else:
        _alarms = []

def _save_alarms():
    """Saves alarms to the JSON file."""
    try:
        with open(ALARM_FILE, "w") as f:
            json.dump(_alarms, f, indent=4)
    except Exception as e:
        print(f"[System Error] Failed to save alarms: {e}")

def parse_time_string(time_string: str):
    """
    Parses a conversational time string.
    Returns (datetime_obj, type_str)
    """
    time_string = time_string.lower().strip()
    now = datetime.datetime.now()
    
    # Detect Recurrence
    alarm_type = "once"
    if "every day" in time_string or "daily" in time_string:
        alarm_type = "daily"
    elif "weekday" in time_string:
        alarm_type = "weekdays"
    else:
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        for day in days:
            if day in time_string:
                alarm_type = day
                break

    # 1. Handle relative time ("in 10 minutes")
    if "in" in time_string:
        words = time_string.split()
        for i, word in enumerate(words):
            if word.isdigit():
                amount = int(word)
                unit_str = " ".join(words[i:])
                if "minute" in unit_str or "min" in unit_str:
                    return now + datetime.timedelta(minutes=amount), "once"
                elif "hour" in unit_str or "hr" in unit_str:
                    return now + datetime.timedelta(hours=amount), "once"
                    
    # 2. Handle exact time using regex
    match = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(p\.m\.|a\.m\.|pm|am)?", time_string)
    if match:
        try:
            hour = int(match.group(1))
            minute = int(match.group(2)) if match.group(2) else 0
            ampm = match.group(3)
            
            if ampm:
                ampm = ampm.replace(".", "")
                if ampm == "pm" and hour < 12: hour += 12
                if ampm == "am" and hour == 12: hour = 0
                
            target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if target_time <= now and alarm_type == "once":
                target_time += datetime.timedelta(days=1)
                
            return target_time, alarm_type
        except: pass
            
    return None, None

def set_alarm(time_string: str, message: str = "") -> str:
    target_time, alarm_type = parse_time_string(time_string)
    if not target_time:
        return "I couldn't understand the time for that alarm."
        
    time_str = target_time.strftime("%H:%M")
    
    new_alarm = {
        "id": int(time.time()),
        "time": time_str,
        "type": alarm_type,
        "message": message,
        "active": True,
        "last_triggered": ""
    }
    
    _alarms.append(new_alarm)
    _save_alarms()
    
    friendly_time = target_time.strftime("%I:%M %p").lstrip("0")
    if alarm_type == "once":
        return f"Alarm set for {friendly_time}."
    else:
        return f"Alarm set for {friendly_time} {alarm_type}."

def list_alarms() -> str:
    active = [a for a in _alarms if a["active"]]
    if not active: return "You have no active alarms."
    
    resp = "You have the following alarms: "
    items = []
    for a in active:
        t = datetime.datetime.strptime(a["time"], "%H:%M")
        f_t = t.strftime("%I:%M %p").lstrip("0")
        items.append(f"{f_t} ({a['type']})")
    return resp + ", ".join(items)

def get_active_alarms():
    return [a for a in _alarms if a.get("active", False)]

def disable_all_alarms() -> str:
    for a in _alarms:
        a["active"] = False
    _save_alarms()
    return "All alarms have been disabled."

def cancel_alarm(time_string: str) -> str:
    global _alarm_state
    if _alarm_state == "RINGING":
        return stop_alarm()

    target_time, _ = parse_time_string(time_string)
    if not target_time: return "I couldn't identify which alarm to cancel."
    
    t_str = target_time.strftime("%H:%M")
    found = False
    for a in _alarms:
        if a["time"] == t_str and a["active"]:
            a["active"] = False
            found = True
    
    if found:
        _save_alarms()
        return f"Cancelled the {target_time.strftime('%I:%M %p')} alarm."
    return "I couldn't find an active alarm for that time."

def stop_alarm() -> str:
    global _alarm_state, _current_ringing_alarm
    if _alarm_state == "RINGING":
        _alarm_state = "IDLE"
        _current_ringing_alarm = None
        return "Alarm stopped."
    return "No alarm is currently ringing."

def snooze_alarm(duration_mins: int = 5) -> str:
    global _alarm_state, _current_ringing_alarm
    if _alarm_state == "RINGING" and _current_ringing_alarm:
        _alarm_state = "IDLE"
        snooze_time = datetime.datetime.now() + datetime.timedelta(minutes=duration_mins)
        new_alarm = {
            "id": int(time.time()),
            "time": snooze_time.strftime("%H:%M"),
            "type": "once",
            "message": f"Snooze: {_current_ringing_alarm.get('message', '')}",
            "active": True,
            "last_triggered": ""
        }
        _alarms.append(new_alarm)
        _current_ringing_alarm = None
        _save_alarms()
        return f"Snoozed for {duration_mins} minutes."
    return "There is no alarm to snooze."

def _ringing_behavior(alarm_msg: str):
    global _alarm_state
    cycle = 0
    while _alarm_state == "RINGING":
        try:
            frequency = min(1000 + (cycle * 200), 3000)
            beeps = min(2 + cycle, 5)
            
            for _ in range(beeps):
                if _alarm_state != "RINGING": break
                winsound.Beep(frequency, 300)
                time.sleep(0.1)
                
            if _alarm_state != "RINGING": break
            
            time.sleep(1)
            msg = alarm_msg if alarm_msg else "Wake up!"
            speak(f"Alarm ringing! {msg}")
            
            cycle += 1
            time.sleep(2)
        except: time.sleep(1)

def _check_alarms_loop():
    global _alarm_state, _current_ringing_alarm
    while True:
        try:
            if _alarm_state == "IDLE":
                now = datetime.datetime.now()
                time_now = now.strftime("%H:%M")
                date_now = now.strftime("%Y-%m-%d")
                is_weekday = now.weekday() < 5
                day_now = now.strftime("%A").lower()
                
                for a in _alarms:
                    if a["active"] and a["time"] == time_now and a["last_triggered"] != date_now:
                        should_trigger = False
                        if a["type"] == "once":
                            should_trigger = True
                            a["active"] = False
                        elif a["type"] == "daily":
                            should_trigger = True
                        elif a["type"] == "weekdays" and is_weekday:
                            should_trigger = True
                        elif a["type"] == day_now:
                            should_trigger = True
                        
                        if should_trigger:
                            a["last_triggered"] = date_now
                            _save_alarms()
                            _alarm_state = "RINGING"
                            _current_ringing_alarm = a
                            threading.Thread(target=_ringing_behavior, args=(a["message"],), daemon=True).start()
                            break
        except Exception as e:
            print(f"[Alarm Thread Error] {e}")
        time.sleep(1)

def start_background_manager():
    _load_alarms()
    threading.Thread(target=_check_alarms_loop, daemon=True).start()
    print("[System] Persistent Alarm Manager started.")
