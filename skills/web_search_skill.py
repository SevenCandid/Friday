import threading
from duckduckgo_search import DDGS
import ai_layer
import state_manager

def handle(command, speak):
    # 1. Identify Search Intent
    # Keywords that trigger a web search
    search_keywords = [
        "search", "find out", "who is", "what is", "where is", 
        "price of", "score", "how many", "tell me about", "look up",
        "weather in", "latest", "current"
    ]
    
    is_search = any(kw in command for kw in search_keywords)
    
    # Also trigger if it ends in a question mark or starts with a question word
    if not is_search:
        question_words = ["who", "what", "where", "when", "why", "how"]
        is_search = any(command.startswith(w) for w in question_words)

    if not is_search:
        return False

    # 2. Extract Query
    query = command
    for kw in search_keywords:
        if command.startswith(kw):
            query = command.replace(kw, "", 1).strip()
            break
    
    if not query:
        speak("What would you like me to search for?")
        return True

    speak(f"One moment, searching the live web for {query}...")

    def _search_thread():
        try:
            with DDGS() as ddgs:
                results = [r for r in ddgs.text(query, max_results=5)]
                
            if not results:
                speak("I searched the web but couldn't find any clear results for that.")
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
