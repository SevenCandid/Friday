import psutil
import threading
import datetime
import requests
import alarm_manager
import state_manager
from skills import news_skill
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


# ─────────────────────────────────────────────
# BOOT-TIME MORNING CHECK
# Only fires once per day, between 5am and 11am
# ─────────────────────────────────────────────
_briefing_done_date = None  # Tracks last run date


def should_run_briefing() -> bool:
    """Returns True if it's morning and the briefing hasn't run today."""
    global _briefing_done_date
    now = datetime.datetime.now()
    today = now.date()

    if _briefing_done_date == today:
        return False  # Already ran today

    return 5 <= now.hour < 11  # Morning window: 5am – 11am


def _mark_briefing_done():
    global _briefing_done_date
    _briefing_done_date = datetime.datetime.now().date()


# ─────────────────────────────────────────────
# WEATHER
# ─────────────────────────────────────────────

def _get_weather() -> str:
    city = config.get("user", "city")
    try:
        r = requests.get(f"https://wttr.in/{city}?format=%C,+%t", timeout=5)
        if r.status_code == 200:
            return r.text.strip()
    except Exception:
        pass
    return None


# ─────────────────────────────────────────────
# BRIEFING RUNNER
# ─────────────────────────────────────────────

def run_briefing(speak):
    """
    Runs the full morning briefing.
    Can be called manually (voice command) or automatically at boot.
    """
    speak("Initiating your morning briefing. Gathering data now.")

    def _thread():
        _mark_briefing_done()

        now = datetime.datetime.now()
        hour = now.hour
        if hour < 12:
            greeting = "Good morning."
        elif hour < 17:
            greeting = "Good afternoon."
        else:
            greeting = "Good evening."

        # ── 1. Weather ──────────────────────────────────────────
        weather = _get_weather()
        city = config.get("user", "city")
        weather_voice = (
            f"Today in {city}, the weather is {weather}."
            if weather else
            "I couldn't reach the weather service right now."
        )

        # ── 2. News (using smart summarizer) ────────────────────
        ghana_news  = news_skill._fetch_news(
            "https://news.google.com/rss/search?q=ghana", limit=2
        )
        global_news = news_skill._fetch_news(
            "https://news.google.com/rss", limit=1
        )

        # ── 3. System Status ────────────────────────────────────
        cpu  = psutil.cpu_percent(interval=0.5)
        ram  = psutil.virtual_memory().percent
        batt = psutil.sensors_battery()
        batt_str = f"{int(batt.percent)} percent" if batt else "Unknown"
        plugged  = batt and batt.power_plugged

        system_voice = f"Your system is at {cpu} percent CPU and {ram} percent RAM."
        if batt:
            system_voice += f" Battery is at {batt_str}"
            system_voice += ", and charging." if plugged else ", not plugged in."

        # ── 4. Active Alarms ────────────────────────────────────
        active_alarms = alarm_manager.get_active_alarms()
        if active_alarms:
            alarm_voice = f"You have {len(active_alarms)} active alarm{'s' if len(active_alarms) > 1 else ''} today."
        else:
            alarm_voice = "You have no alarms scheduled."

        # ── GUI: Rich Structured Display ────────────────────────
        gui = [
            "🌅 MORNING BRIEFING",
            f"📅 {now.strftime('%A, %d %B %Y  •  %H:%M')}",
            "",
        ]
        if weather:
            gui.append(f"🌦️  WEATHER: {weather}")
            gui.append("")

        if ghana_news or global_news:
            gui.append("📰 TOP HEADLINES:")
            for item in ghana_news:
                gui.append(f"  • {item['title']}")
                gui.append(f"      {item['summary']}")
            for item in global_news:
                gui.append(f"  • {item['title']}")
                gui.append(f"      {item['summary']}")
            gui.append("")

        gui.append(f"💻 SYSTEM:  CPU {cpu}%  •  RAM {ram}%  •  Battery {batt_str}")
        gui.append(f"⏰ ALARMS:  {alarm_voice}")

        state_manager.add_to_chat("Friday", "\n".join(gui))

        # ── VOICE: Natural, Sentence-by-Sentence ─────────────────
        speak(f"{greeting} I'm Friday. Here's your morning briefing.")
        speak(weather_voice)

        if ghana_news:
            speak("Today's top headline from Ghana:")
            speak(ghana_news[0]['summary'])

        if global_news:
            speak("Globally:")
            speak(global_news[0]['summary'])

        speak(system_voice)
        speak(alarm_voice)
        speak("That's your briefing. Have a productive day.")

    threading.Thread(target=_thread, daemon=True).start()


# ─────────────────────────────────────────────
# SKILL HANDLER (voice-triggered)
# ─────────────────────────────────────────────

def handle(command, speak):
    triggers = [
        "morning briefing", "daily briefing",
        "what's my day", "today's briefing",
        "morning report", "give me a briefing"
    ]
    if not any(t in command for t in triggers):
        return False

    run_briefing(speak)
    return True
