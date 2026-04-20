import re
import threading
import html
import feedparser
from core import ai_layer

# ─────────────────────────────────────────────
# NEWS SOURCES
# ─────────────────────────────────────────────
GHANA_RSS  = "https://news.google.com/rss/search?q=ghana"
GLOBAL_RSS = "https://news.google.com/rss"

# ─────────────────────────────────────────────
# NOISE FILTERS
# ─────────────────────────────────────────────

# Source names to strip from summaries
SOURCE_NAMES = [
    "BBC", "CNN", "Reuters", "AFP", "AP", "Aljazeera", "Al Jazeera",
    "CitiNewsroom", "Citi Newsroom", "GhanaWeb", "MyJoyOnline", "Joy Online",
    "Graphic Online", "Daily Graphic", "Ghana News Agency", "GNA",
    "Pulse Ghana", "3News", "TV3", "UTV Ghana", "Peace FM",
    "Bloomberg", "Guardian", "Forbes", "CNBC", "Fox News", "NBC", "ABC News"
]

# Filler phrases that add no meaning
FILLER_PHRASES = [
    "click here to read more", "read more", "read full article",
    "continue reading", "see more", "learn more", "find out more",
    "for more information", "according to reports", "it is reported that",
    "it has been reported", "sources say", "sources have said",
    "the report says", "according to", "as reported by",
]

# Words that make a sentence more informative (scoring boost)
INFORMATIVE_SIGNALS = [
    # Numbers / quantities
    r'\d+', r'\d+%', r'\$\d+', r'billion', r'million', r'thousand',
    # Actions / events
    'announced', 'launched', 'signed', 'arrested', 'killed', 'died',
    'elected', 'appointed', 'resigned', 'fired', 'won', 'lost',
    'increased', 'decreased', 'dropped', 'rose', 'surged', 'collapsed',
    'approved', 'rejected', 'passed', 'banned', 'lifted',
    'deployed', 'invaded', 'attacked', 'rescued', 'released',
]


# ─────────────────────────────────────────────
# STEP 1 & 2: COMBINE + CLEAN TEXT
# ─────────────────────────────────────────────

def _clean_text(raw: str) -> str:
    """Strips HTML, entities, source names, and filler from raw text."""
    if not raw:
        return ""

    # Decode HTML entities (&nbsp; &amp; etc.)
    text = html.unescape(raw)

    # Remove HTML tags
    text = re.sub(r'<[^>]+?>', '', text)

    # Remove URLs
    text = re.sub(r'https?://\S+', '', text)

    # Remove source names (case-insensitive)
    for source in SOURCE_NAMES:
        text = re.sub(re.escape(source), '', text, flags=re.IGNORECASE)

    # Remove filler phrases
    for phrase in FILLER_PHRASES:
        text = re.sub(re.escape(phrase), '', text, flags=re.IGNORECASE)

    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    # Remove leading punctuation artifacts (e.g. "- Ghana")
    text = re.sub(r'^[\-–—,.:;]+\s*', '', text)

    return text


# ─────────────────────────────────────────────
# STEP 3 & 4: SPLIT + SCORE SENTENCES
# ─────────────────────────────────────────────

def _score_sentence(sentence: str) -> int:
    """Score a sentence by how informative it is."""
    score = 0
    s = sentence.lower()

    # Reward length (not too short, not too long)
    words = len(sentence.split())
    if 8 <= words <= 30:
        score += 5
    elif words < 5:
        score -= 10  # Too short = useless fragment

    # Reward informative signals
    for signal in INFORMATIVE_SIGNALS:
        if re.search(signal, s):
            score += 3

    # Penalise questions (usually not news statements)
    if sentence.strip().endswith('?'):
        score -= 5

    return score


def _best_sentence(text: str) -> str:
    """Splits text into sentences and returns the most informative one."""
    # Split on sentence-ending punctuation
    sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

    if not sentences:
        return text[:200].strip()

    if len(sentences) == 1:
        return sentences[0]

    # Score and pick the best
    scored = [(s, _score_sentence(s)) for s in sentences]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[0][0]


# ─────────────────────────────────────────────
# STEP 5: TRIM TO VOICE-FRIENDLY LENGTH
# ─────────────────────────────────────────────

def _trim_to_voice(text: str, max_words: int = 30) -> str:
    """Ensures the summary is short enough for natural spoken delivery."""
    words = text.split()
    if len(words) <= max_words:
        return text
    # Cut at the last complete sentence within the limit
    trimmed = ' '.join(words[:max_words])
    last_punct = max(trimmed.rfind('.'), trimmed.rfind('!'), trimmed.rfind('?'))
    if last_punct > 0:
        return trimmed[:last_punct + 1]
    return trimmed + '.'


# ─────────────────────────────────────────────
# MAIN SUMMARIZER
# ─────────────────────────────────────────────

def _summarize(title: str, raw_description: str) -> str:
    """
    Combines title + description, cleans, picks the best sentence,
    and returns a clean, voice-optimised summary.
    """
    combined = f"{title}. {raw_description}"
    cleaned  = _clean_text(combined)

    if not cleaned:
        best = _clean_text(title)
    else:
        best = _best_sentence(cleaned)
        best = _trim_to_voice(best)
        
    return ai_layer.rewrite(best)


# ─────────────────────────────────────────────
# RSS FETCHER
# ─────────────────────────────────────────────

def _fetch_news(url: str, limit: int = 3) -> list:
    """Fetches RSS feed and returns summarised news items."""
    try:
        import requests
        headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            )
        }
        response = requests.get(url, headers=headers, timeout=10)
        feed = feedparser.parse(response.content)

        results = []
        for entry in feed.entries[:limit]:
            title = getattr(entry, 'title', '')
            raw   = entry.get('description', entry.get('summary', ''))
            summary = _summarize(title, raw)
            results.append({'title': title, 'summary': summary})

        return results
    except Exception as e:
        print(f"[News Error] {e}")
        return []


# ─────────────────────────────────────────────
# SKILL HANDLER
# ─────────────────────────────────────────────

def handle(command, speak):
    triggers = ["news", "headline", "headlines", "update", "briefing"]
    if not any(t in command for t in triggers):
        return False

    speak("Acquiring and summarising the latest intelligence. Stand by.")

    def _news_thread():
        ghana_news  = _fetch_news(GHANA_RSS,  limit=3)
        global_news = _fetch_news(GLOBAL_RSS, limit=2)

        if not ghana_news and not global_news:
            speak("I'm unable to reach the news network right now. Please check your connection.")
            return

        # ── GUI Display (rich, formatted) ──────────────────────────
        gui_lines = ["📰 GHANA INTELLIGENCE:"]
        for i, item in enumerate(ghana_news, 1):
            gui_lines.append(f"{i}. {item['title']}")
            gui_lines.append(f"   — {item['summary']}\n")

        gui_lines.append("🌍 GLOBAL INTELLIGENCE:")
        for i, item in enumerate(global_news, 1):
            gui_lines.append(f"{i}. {item['title']}")
            gui_lines.append(f"   — {item['summary']}\n")

        from core import state_manager
        state_manager.add_to_chat("Friday", "\n".join(gui_lines))

        # ── Voice Delivery (natural, spoken) ───────────────────────
        voice_parts = ["Here's your intelligence briefing."]

        if ghana_news:
            voice_parts.append("In Ghana:")
            for item in ghana_news:
                voice_parts.append(item['summary'])

        if global_news:
            voice_parts.append("Globally:")
            for item in global_news:
                voice_parts.append(item['summary'])

        voice_parts.append("That's all for now.")

        # Speak each part naturally with a brief pause between items
        for part in voice_parts:
            speak(part)

    threading.Thread(target=_news_thread, daemon=True).start()
    return True
