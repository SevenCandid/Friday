import threading
from core import ai_layer
from core import state_manager

def handle(command, speak):
    """
    Analyzes the user's command for live search intent.
    If triggered, it fetches real-time data from the web and provides a summarized answer.
    """
    # 1. Identify Search Intent (Only for LIVE data)
    search_keywords = [
        "search", "research", "price", "stock", "score", "how many", "look up",
        "weather", "latest", "current", "how much", "find"
    ]
    
    is_search = any(kw in command for kw in search_keywords)
    
    # Also trigger if it ends in a question mark or starts with a question word
    if not is_search:
        question_words = ["who", "what", "where", "when", "why", "how"]
        is_search = any(command.startswith(w) for w in question_words)

    if not is_search:
        return False

    # 2. Extract and Clean Query
    query = command
    # Remove search triggers for the actual query
    for kw in ["search", "research", "find out", "look up", "tell me about"]:
        if query.startswith(kw):
            query = query.replace(kw, "", 1).strip()
            break
    
    # Remove filler words for a cleaner search
    filler = ["the", "a", "an", "of", "about", "is", "for", "me", "what", "who", "where"]
    query_words = [w for w in query.replace("?", "").split() if w.lower() not in filler]
    clean_query = " ".join(query_words)

    if not clean_query:
        speak("What would you like me to search for?")
        return True

    speak(f"Searching for {clean_query}...")

    def _search_thread():
        try:
            from duckduckgo_search import DDGS
            results = []
            
            with DDGS() as ddgs:
                # Use a very simple search - often more reliable
                for r in ddgs.text(clean_query, max_results=3):
                    results.append(r)
                
            if not results:
                # Try one more time with the raw query
                with DDGS() as ddgs:
                    for r in ddgs.text(query, max_results=3):
                        results.append(r)

            if not results:
                # Last resort: Try news
                with DDGS() as ddgs:
                    for r in ddgs.news(clean_query, max_results=3):
                        results.append(r)

            if not results:
                speak("I searched the web but couldn't find a direct answer. I might be having trouble reaching the live network.")
                return

            # Format results for the AI to summarize
            context = "\n".join([f"- {r['title']}: {r['body']}" for r in results])
            prompt = f"The user asked: '{query}'. Based on these search results, provide a concise, natural answer as Friday:\n\n{context}"
            
            if ai_layer.is_available():
                response = ai_layer.process_with_context(prompt, "Web Search Results")
                speak(response)
            else:
                # Fallback if AI is offline: just read the first title
                speak(f"I found some information. {results[0]['title']}. Would you like me to open the full results in your browser?")
                state_manager.pending_action = lambda: os.system(f"start https://duckduckgo.com/?q={query.replace(' ', '+')}")
                state_manager.pending_action_text = "open the search results"

        except Exception as e:
            print(f"[Search Error] {e}")
            speak("I encountered an error while trying to search the web.")

    threading.Thread(target=_search_thread, daemon=True).start()
    return True
