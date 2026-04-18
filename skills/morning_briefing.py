import psutil
import threading
import requests
import os
from skills import news_skill
import alarm_manager
import state_manager

def get_weather():
    """Fetches a simple weather summary for Ghana (or current location)."""
    try:
        # Using wttr.in for a lightweight, keyless weather check
        response = requests.get("https://wttr.in/Accra?format=%C+%t", timeout=5)
        if response.status_code == 200:
            return response.text.strip()
        return "Unknown"
    except:
        return "Offline"

def handle(command, speak):
    # Detect briefing-related keywords
    brief_keywords = ["morning briefing", "daily briefing", "what's my day like", "morning report"]
    if not any(k in command for k in brief_keywords):
        return False

    speak("Initiating daily briefing protocol. Gathering local and global data...")

    def _briefing_thread():
        # 1. Weather
        weather = get_weather()
        weather_voice = f"Today in Accra, it is {weather}." if weather != "Offline" else "I couldn't reach the weather service."
        
        # 2. News
        ghana_news = news_skill.fetch_news("https://news.google.com/rss/search?q=ghana", limit=2)
        global_news = news_skill.fetch_news("https://news.google.com/rss", limit=2)
        
        # 3. System
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        batt = psutil.sensors_battery()
        batt_text = f"{int(batt.percent)}%" if batt else "Unknown"

        # 4. Alarms
        active_alarms = alarm_manager.get_active_alarms() # Assuming this exists
        alarm_text = "You have no active alarms." if not active_alarms else f"You have {len(active_alarms)} alarms scheduled."

        # Prepare GUI Output
        gui_output = "🌅 MORNING BRIEFING\n\n"
        gui_output += f"🌦️ WEATHER: {weather}\n\n"
        
        gui_output += "📰 TOP HEADLINES:\n"
        for item in ghana_news:
            gui_output += f"• {item['title']}\n"
        
        gui_output += f"\n💻 SYSTEM STATUS:\n"
        gui_output += f"• CPU: {cpu}% | RAM: {ram}%\n"
        gui_output += f"• Battery: {batt_text}\n\n"
        
        gui_output += f"⏰ REMINDERS:\n{alarm_text}"

        # Prepare Voice Output
        voice_output = f"Good morning. I'm Friday, your personal assistant. {weather_voice} "
        if ghana_news:
            voice_output += f"Today's top headline is: {ghana_news[0]['title']}. "
        voice_output += f"Your system is running at {cpu} percent CPU, and battery is at {batt_text}. {alarm_text} Have a productive day."

        # Output
        speak(gui_output) # Push full structured text to GUI
        # The speak call in main.py will handle the voice part

    threading.Thread(target=_briefing_thread, daemon=True).start()
    return True
