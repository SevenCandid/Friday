import feedparser
import threading

def _clean_summary(summary, length=150):
    """Truncates the summary to a clean 1-2 sentences."""
    if not summary:
        return "No summary available."
    
    # Remove HTML tags if any (very basic)
    import re
    clean = re.sub('<[^<]+?>', '', summary)
    
    if len(clean) > length:
        return clean[:length].strip() + "..."
    return clean.strip()

def fetch_news(url, limit=3):
    """Fetches and parses headlines from an RSS feed with a browser-like identity."""
    try:
        import requests
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        
        response = requests.get(url, headers=headers, timeout=10)
        feed = feedparser.parse(response.content)
        
        results = []
        for entry in feed.entries[:limit]:
            results.append({
                "title": entry.title,
                "summary": _clean_summary(entry.get("description", entry.get("summary", "")))
            })
        return results
    except Exception as e:
        print(f"[News Error] Failed to fetch from {url}: {e}")
        return []

def handle(command, speak):
    # Detect news-related keywords with flexible matching
    news_triggers = ["news", "headline", "headlines", "update"]
    if not any(t in command for t in news_triggers):
        return False

    speak("Acquiring latest intelligence feeds. Please stand by.")
    
    # URLs
    GHANA_RSS = "https://news.google.com/rss/search?q=ghana"
    GLOBAL_RSS = "https://news.google.com/rss"

    def _get_news_thread():
        ghana_news = fetch_news(GHANA_RSS, limit=3)
        global_news = fetch_news(GLOBAL_RSS, limit=2)

        if not ghana_news and not global_news:
            speak("I'm having trouble connecting to the news network right now. Please check your internet connection.")
            return

        # Prepare GUI Text
        gui_text = "📰 GHANA INTELLIGENCE:\n"
        voice_text = "Here are the top headlines for today. In Ghana: "
        
        for i, item in enumerate(ghana_news, 1):
            gui_text += f"{i}. {item['title']}\n   - {item['summary']}\n\n"
            voice_text += f"{item['title']}. "

        gui_text += "🌍 GLOBAL INTELLIGENCE:\n"
        voice_text += " Globally: "
        for i, item in enumerate(global_news, 1):
            gui_text += f"{i}. {item['title']}\n   - {item['summary']}\n\n"
            voice_text += f"{item['title']}. "

        # Push to GUI and Speak
        # Note: We use the speak callback which handles GUI updates in main.py
        speak(gui_text)
        
    threading.Thread(target=_get_news_thread, daemon=True).start()
    return True
