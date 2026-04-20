import threading
import wikipedia
from duckduckgo_search import DDGS
from core import ai_layer

# Common Acronym Mapping for Disambiguation
KNOWLEDGE_MAP = {
    "uenr": "University of Energy and Natural Resources",
    "knust": "Kwame Nkrumah University of Science and Technology",
    "ug": "University of Ghana",
    "ucc": "University of Cape Coast",
    "legon": "University of Ghana, Legon",
    "gimpa": "Ghana Institute of Management and Public Administration"
}

def _academic_search(query, speak):
    """Mode A: KNOWLEDGE (Wikipedia Only)"""
    try:
        # 1. Translate Acronyms
        search_query = KNOWLEDGE_MAP.get(query.lower(), query)
        
        # 2. Try direct summary
        try:
            raw_summary = wikipedia.summary(search_query, sentences=3)
            summary = ai_layer.summarize(raw_summary)
            page = wikipedia.page(search_query)
            speak(f"Consulting Academic Databases for {search_query}.")
            return f"--- ACADEMIC BRIEF ---\nSource: Wikipedia\n\n• {summary}\n\nLink: {page.url}"
        except Exception:
            # 3. Fuzzy search fallback
            search_results = wikipedia.search(search_query)
            if search_results:
                best_match = search_results[0]
                raw_summary = wikipedia.summary(best_match, sentences=3)
                summary = ai_layer.summarize(raw_summary)
                page = wikipedia.page(best_match)
                return f"--- ACADEMIC BRIEF ---\nSource: Wikipedia (Fuzzy Match)\n\n• {summary}"
        
        return None
    except Exception:
        return None

def _web_intel_search(query, speak):
    """Mode C: SEARCH (Web Intel / DDG Multi-Source)"""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
            if results:
                speak(f"Synthesizing intelligence from multiple sources for {query}...")
                
                # Combine all snippets for the AI to analyze
                intelligence_pool = ""
                for i, r in enumerate(results):
                    intelligence_pool += f"[Source {i+1}]: {r.get('body', '')}\n"
                
                report = ai_layer.synthesize_research(query, intelligence_pool)
                
                # Add source links to the report
                links = "\n\nSources:\n" + "\n".join([f"- {r.get('href')}" for r in results[:3]])
                
                return f"--- MULTI-SOURCE BRIEF ---\n{report}{links}"
            else:
                return "I couldn't find any relevant intelligence on the web for that query."
    except Exception as e:
        print(f"[Explorer Error] {e}")
        return "I encountered an error while synthesizing web intelligence."

def handle(command, speak):
    cmd = command.lower().strip()
    
    # --- MODE C: SEARCH TRIGGER (HIGH PRIORITY) ---
    search_keywords = ["search", "research", "ressearch", "re-search", "look up", "find information on"]
    for kw in search_keywords:
        if cmd.startswith(kw):
            # Extract the query (remove the keyword and any leading space/punctuation)
            query = cmd.replace(kw, "", 1).strip(",.?! ")
            if query:
                def _search_thread():
                    result = _web_intel_search(query, speak)
                    if result:
                        speak(result)
                    else:
                        speak("I was unable to retrieve intelligence from the web.")
                threading.Thread(target=_search_thread, daemon=True).start()
                return True

    # --- MODE B: NEWS ROUTING (Strict) ---
    news_triggers = ["news", "headline", "headlines", "latest news", "update"]
    if any(t in cmd for t in news_triggers):
        # We explicitly return False here to let news_skill.py handle it
        print("[Explorer] Routing to News Mode.")
        return False

    # --- MODE A: KNOWLEDGE TRIGGER ---
    # PERSONAL FILTER: Skip if the user is asking about themselves (memory handles this)
    personal_words = ["my ", " my ", " i ", " me ", " me?", "do i", "am i"]
    if any(p in cmd for p in personal_words):
        return False

    knowledge_triggers = ["who is", "what is", "history of", "tell me about"]
    query = ""
    is_knowledge = False
    
    # LIVE DATA BLOCK: If user asks for price, weather, etc, skip Academic mode
    live_keywords = ["price", "weather", "score", "stock", "market", "exchange rate", "live"]
    if any(k in cmd for k in live_keywords):
        is_knowledge = False
    else:
        for t in knowledge_triggers:
            if t in cmd:
                query = cmd.split(t, 1)[-1].strip()
                is_knowledge = True
                break

    # --- MODE D: DIRECT ACRONYM MATCH ---
    if cmd in KNOWLEDGE_MAP:
        query = cmd
        is_knowledge = True
    
    if is_knowledge and query:
        def _knowledge_thread():
            from core import state_manager
            result = _academic_search(query, speak)
            if result:
                speak(result)
            else:
                speak(f"I couldn't find a verified academic entry for {query}. Should I try a general web search?")
                state_manager.pending_action = lambda: _web_intel_search(query, speak)
                state_manager.pending_action_text = f"web_search_{query}"
        
        threading.Thread(target=_knowledge_thread, daemon=True).start()
        return True

    return False
