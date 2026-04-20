# SEVEN — User Guide
### Your Personal AI Assistant for Windows
**Version 1.0** · Created by Frank Bediako

---

## What is SEVEN?

SEVEN is a voice-controlled AI assistant that runs locally on your Windows PC. She can manage your system, search the web, remember things about you, control your apps, and keep you informed — all through natural voice commands or typed input.

**Key Features:**
- 🎙️ Voice-activated with the wake word **"SEVEN"**
- 🧠 Long-term memory that remembers facts about you
- 🌍 Real-time weather monitoring with rain alerts
- 🔍 Deep web research with multi-source intelligence reports
- 📱 Remote access from your phone via the Mobile HUD
- 🖥️ Full system monitoring (CPU, RAM, Battery, WiFi)

---

## Getting Started

### Requirements
- Windows 10 or 11
- A working microphone
- [Ollama](https://ollama.com) installed and running (for AI features)
- Internet connection (for weather, news, and web search)

### First Launch
1. Run `SEVEN.exe` (or `python main.py` if running from source)
2. The **Neural Intelligence HUD** window will appear
3. Wait for the startup greeting — SEVEN will announce herself
4. You're ready to go!

### Setting Up Ollama (Required for AI)
SEVEN uses a local AI model for smart responses. To set it up:
1. Download and install [Ollama](https://ollama.com)
2. Open a terminal and run: `ollama pull llama3.2:1b`
3. Keep Ollama running in the background
4. SEVEN will automatically connect to it

> **Without Ollama:** SEVEN still works for basic commands (time, volume, apps, etc.), but smart features like memory recall and web research summaries won't be available.

---

## How to Talk to SEVEN

### Wake Word
Say **"SEVEN"** followed by your command. For example:
- *"SEVEN, what time is it?"*
- *"SEVEN, open Chrome"*
- *"SEVEN, research Python programming"*

### Follow-Up Mode
After SEVEN responds, she stays listening for **10 seconds**. During this window, you can give follow-up commands without saying her name again:
- You: *"SEVEN, what's the weather?"*
- SEVEN: *"There's an 80% chance of rain..."*
- You: *"Thank you"* (no need to say "SEVEN" again)

### Typed Commands
You can also type commands directly into the input box at the bottom of the HUD and click **EXECUTE** or press **Enter**.

---

## Command Reference

### 🕐 Time & Date
| Say this | What happens |
|---|---|
| *"What time is it?"* | Tells you the current time |
| *"What's the date?"* | Tells you today's date |

### 🔊 Volume Control
| Say this | What happens |
|---|---|
| *"Set volume to 50"* | Sets volume to 50% |
| *"Mute"* | Mutes the system |
| *"Unmute"* | Restores the volume |
| *"Volume up"* / *"Louder"* | Increases volume by 10% |
| *"Volume down"* / *"Quieter"* | Decreases volume by 10% |

### 💡 Brightness
| Say this | What happens |
|---|---|
| *"Set brightness to 70"* | Sets screen brightness to 70% |
| *"Dim the screen"* | Lowers brightness |
| *"Full brightness"* | Sets brightness to 100% |

### 📂 File Management
| Say this | What happens |
|---|---|
| *"Open my downloads folder"* | Opens the Downloads folder |
| *"Open my desktop"* | Opens the Desktop folder |
| *"Open my documents"* | Opens the Documents folder |
| *"Create a file named report"* | Creates `report.txt` on your Desktop |
| *"Write a note meeting at 3pm"* | Saves a note to `SEVEN_Mission_Notes.txt` |
| *"Find file homework"* | Searches Desktop, Downloads, and Documents for matching files |

### 🚀 App Launcher
| Say this | What happens |
|---|---|
| *"Open Chrome"* | Launches Google Chrome |
| *"Open VS Code"* | Launches Visual Studio Code |
| *"Open Discord"* | Launches Discord |
| *"List my apps"* | Shows all indexed applications in the HUD |
| *"Close Chrome"* | Closes Google Chrome |

> **Tip:** SEVEN automatically discovers installed apps. If she can't find one, try using its full name.

### 🌍 Weather
| Say this | What happens |
|---|---|
| *"What's the weather?"* | Gives you the current forecast for your location |
| *"Will it rain today?"* | Checks rain probability |

SEVEN also **proactively alerts** you if there's a high chance of rain — you don't even need to ask!

### 📰 News
| Say this | What happens |
|---|---|
| *"Give me the news"* | Reads top headlines |
| *"What's happening in Ghana?"* | Ghana-specific news briefing |
| *"Tech news"* | Technology headlines |

### 🔍 Web Research
| Say this | What happens |
|---|---|
| *"Research Python 3.13 features"* | Searches 5 sources and synthesizes a tactical report |
| *"Search best laptops 2026"* | Web search with AI summary |
| *"What is quantum computing?"* | Academic lookup via Wikipedia |
| *"Who is Elon Musk?"* | Wikipedia knowledge brief |
| *"Look up Ghana's population"* | General web intelligence |

> **Deep Research Mode:** When you say "research", SEVEN pulls data from the top 5 search results, cross-references them, and gives you a structured multi-source report — not just a single snippet.

### 🧠 Memory
| Say this | What happens |
|---|---|
| *"Remember my name is Frank"* | Saves your name (and personalizes greetings) |
| *"Remember I like Python"* | Stores the fact permanently |
| *"Remember my birthday is June 5th"* | Stores the fact permanently |
| *"What is my name?"* | Recalls from stored memory |
| *"What do I like?"* | Recalls from stored memory |
| *"What do you know about me?"* | Full memory report displayed in HUD |
| *"Forget the last thing"* | Deletes the most recent fact |
| *"Forget about Python"* | Deletes all facts containing "Python" |
| *"Forget everything"* | Wipes all stored memories |

### 📍 Location
| Say this | What happens |
|---|---|
| *"Where am I?"* | Uses GPS to detect your current location |

### 📸 Screenshots
| Say this | What happens |
|---|---|
| *"Take a screenshot"* | Captures and saves to Desktop as `seven_screenshot.png` |

### 🔋 System Status
| Say this | What happens |
|---|---|
| *"Battery status"* | Reports current battery percentage |
| *"System status"* | Reports CPU and RAM usage |

### 📶 WiFi
| Say this | What happens |
|---|---|
| *"Scan for WiFi"* | Lists available networks in the HUD |
| *"WiFi status"* | Shows current connection |

### ⏰ Alarms
| Say this | What happens |
|---|---|
| *"Set an alarm for 7:30 AM"* | Creates a daily alarm |

### 🤫 Stealth Mode
| Say this | What happens |
|---|---|
| *"Stealth mode"* | SEVEN stops speaking but still shows HUD alerts |
| *"Normal mode"* | Restores voice output |

You can also toggle Stealth Mode using the **STEALTH** button at the bottom of the HUD.

### 💬 General Chat
| Say this | What happens |
|---|---|
| *"Hello"* | Friendly greeting (personalized if she knows your name) |
| *"How are you?"* | Status check |
| *"Who are you?"* | Identity response |
| *"Who created you?"* | Creator information |
| *"What can you do?"* | Feature overview |
| *"Thank you"* | You're welcome! |

---

## The HUD (Heads-Up Display)

### Desktop HUD
The main window shows:
- **Header** — System name, status indicator, and Remote Link
- **Listening Wave** (🟢 Green) — Reacts to your voice in real-time
- **Talking Wave** (🔵 Cyan) — Pulses when SEVEN speaks
- **Sensor Grid** — Live CPU, RAM, Battery, WiFi, Disk, and Process count
- **Chat Terminal** — Full conversation history
- **Input Console** — Type commands, toggle Stealth Mode, or stop SEVEN mid-sentence

### Remote HUD (Mobile Access)
Access SEVEN from your phone on the same WiFi network:
1. Click the **REMOTE** link in the header (it auto-copies to clipboard)
2. Open that URL in your phone's browser
3. You can now read SEVEN's responses and send commands from your phone

---

## System Tray
When you close the HUD window, SEVEN doesn't quit — she minimizes to the **System Tray** (bottom-right of your taskbar). 

- **Double-click** the tray icon to bring the HUD back
- **Right-click** → **Exit SEVEN** to fully shut down

---

## Proactive Features

SEVEN doesn't just wait for commands. She actively monitors your environment:

| Feature | What she does |
|---|---|
| **Rain Alert** | Checks weather every 15 minutes and warns you about rain |
| **Low Battery** | Warns at 30% and auto-dims your screen at 20% |
| **Morning Briefing** | On first launch, gives you weather, news, and system status |
| **Location Sync** | Auto-detects your location for accurate weather |

---

## Configuration

SEVEN's settings are stored in `config.json` in the app directory:

```json
{
    "ai": {
        "ollama_url": "http://localhost:11434/api/generate",
        "model": "llama3.2:1b",
        "temperature": 0.3
    },
    "voice": {
        "piper_exe": "piper/piper.exe",
        "model": "piper/en_US-amy-low.onnx"
    },
    "user": {
        "city": "Accra"
    },
    "system": {
        "cpu_warning_threshold": 85,
        "battery_warning_threshold": 20,
        "auto_start": true
    }
}
```

### What you can customize:
- **`model`** — Change the AI model (try `"phi3"` or `"mistral"` for different personalities)
- **`city`** — Your default city for weather (auto-updates when GPS detects your location)
- **`auto_start`** — Set to `false` if you don't want SEVEN to launch with Windows
- **`temperature`** — Lower = more focused responses, higher = more creative

---

## Troubleshooting

| Problem | Solution |
|---|---|
| SEVEN doesn't respond to voice | Check that your microphone is enabled in Windows Settings |
| "Ollama is offline" errors | Make sure Ollama is running (`ollama serve` in terminal) |
| Weather shows wrong location | Say *"Where am I?"* to refresh GPS, or edit `city` in `config.json` |
| Voice sounds robotic | Install Piper for neural voice (see developer docs) |
| Remote HUD won't load | Make sure your phone is on the same WiFi as your PC |
| SEVEN takes too long to respond | AI processing depends on your hardware — a GPU helps significantly |
| Commands not recognized | Speak clearly and start with **"SEVEN"** — she listens for that wake word |

---

## Tips for Best Experience

1. **Speak clearly** — SEVEN uses speech recognition, so clear pronunciation helps
2. **Use the wake word** — Always start with "SEVEN" when she's in standby
3. **Check the HUD** — Long responses (research reports, news) appear in the chat terminal
4. **Train her memory** — The more facts you teach her, the more personalized she becomes
5. **Keep Ollama running** — Most smart features require the local AI to be active
6. **Use Stealth Mode** — In meetings or quiet environments, she'll still work but stay silent

---

## Privacy & Security

- 🔒 **All AI processing is local** — Your conversations never leave your computer
- 🔒 **No cloud accounts required** — SEVEN runs entirely on your machine
- 🔒 **Memory is local** — Stored facts are in a local SQLite database on your PC
- 🔒 **Weather & Search** — These use public APIs (Open-Meteo, DuckDuckGo) with no personal data sent

---

*Built with ❤️ in Ghana by Frank Bediako*
*SEVEN v1.0 — Your Tactical AI Companion*
