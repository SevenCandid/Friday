import datetime
import random

def handle(command, speak):
    if "time" in command:
        current_time = datetime.datetime.now().strftime("%I:%M %p")
        if current_time.startswith("0"):
            current_time = current_time[1:]
        prefix = random.choice(["It is", "The time is", "Right now, it's"])
        speak(f"{prefix} {current_time}.")
        return True
        
    if "date" in command:
        current_date = datetime.datetime.now().strftime("%B %d, %Y")
        prefix = random.choice(["Today is", "It's", "The date is"])
        speak(f"{prefix} {current_date}.")
        return True
        
    return False
