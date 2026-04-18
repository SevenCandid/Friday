import sys
import os
import re

# Add parent dir to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import alarm_manager

def handle(command, speak):
    # 1. Stop / Silence Alarm
    if "stop" in command or "cancel" in command or "end" in command or "off" in command or "silence" in command:
        if "alarm" in command or alarm_manager._alarm_state == "RINGING":
            speak(alarm_manager.stop_alarm())
            return True
            
    # 2. Snooze Alarm
    if "snooze" in command:
        if "alarm" in command or alarm_manager._alarm_state == "RINGING":
            duration = 5
            match = re.search(r"(\d+)", command)
            if match:
                duration = int(match.group(1))
            speak(alarm_manager.snooze_alarm(duration))
            return True

    # 3. Set Alarm
    if "set" in command and "alarm" in command:
        time_str = ""
        if "for" in command:
            time_str = command.split("for")[-1].strip()
        elif "in" in command:
            time_str = "in " + command.split("in ")[-1].strip()
        elif "at" in command:
            time_str = command.split("at")[-1].strip()
        speak(alarm_manager.set_alarm(time_str))
        return True
        
    # 4. Cancel Specific Alarm
    if "cancel" in command and "alarm" in command:
        time_str = ""
        if "for" in command:
            time_str = command.split("for")[-1].strip()
        elif "at" in command:
            time_str = command.split("at")[-1].strip()
        speak(alarm_manager.cancel_alarm(time_str))
        return True
        
    # 5. List/Show Alarms
    if "alarm" in command and ("list" in command or "what" in command or "show" in command or "open" in command):
        speak(alarm_manager.list_alarms())
        return True
        
    # 6. Disable All
    if "disable" in command and "all" in command and "alarm" in command:
        speak(alarm_manager.disable_all_alarms())
        return True
        
    return False
