import difflib
from . import skill_manager
from . import memory_manager
from . import state_manager
from . import ai_layer

# Intent Definitions (Clusters of related words)
INTENT_MAP = {
    "WEB_BROWSING": ["chrome", "internet", "google", "youtube", "web", "browser", "browse", "website"],
    "FILE_CONTROL": ["file", "folder", "document", "move", "search", "find", "locate", "path", "directory"],
    "SYSTEM_CONTROL": [
        "shutdown", "restart", "battery", "wifi", "volume", "brightness", 
        "power", "energy", "mute", "audio", "sound", "lock", "screen", "dim",
        "close", "kill", "terminate", "exit", "end", "monitor", "status", "cpu", "ram"
    ],
    "DESKTOP_CONTROL": [
        "scroll", "screenshot", "capture", "type", "click", "mouse", 
        "keyboard", "desktop", "minimize", "maximize", "window", "copy", "paste"
    ],
    "TIME": ["time", "date", "clock", "today", "day", "calendar"],
    "NEWS": ["news", "headline", "headlines", "update", "happening", "report", "briefing"],
    "SEARCH": ["search", "who", "what", "where", "how", "tell", "about", "look", "google", "find", "research"],
    "GENERAL_CHAT": ["seven", "hello", "hi", "hey", "thanks", "thank", "help", "who", "what", "how", "sup", "whats up"]
}

def _normalize_command(command):
    """Fixes common speech-to-text errors before processing."""
    corrections = {
        "wiffi": "wifi",
        "wify": "wifi",
        "hoping": "open",
        "frieze": "files",
        "bright heels": "brightness",
        "four pin": "open",
        "valence": "browser"
    }
    words = command.lower().split()
    cleaned_words = [corrections.get(w, w) for w in words]
    return " ".join(cleaned_words)

def _calculate_intent(command):
    """
    Calculates the most likely intent category based on word matches 
    and fuzzy string similarity.
    """
    words = command.lower().split()
    scores = {intent: 0 for intent in INTENT_MAP}
    
    for word in words:
        for intent, patterns in INTENT_MAP.items():
            # 1. Exact match (High weight)
            if word in patterns:
                scores[intent] += 10
            
            # 2. Fuzzy match (Low weight - handles distorted speech)
            fuzzy_matches = difflib.get_close_matches(word, patterns, n=1, cutoff=0.7)
            if fuzzy_matches:
                scores[intent] += 5

    # Find the intent with the highest score
    if not scores:
        return "GENERAL_CHAT", 0
        
    best_intent = max(scores, key=scores.get)
    return best_intent, scores[best_intent]

def process(command, response_callback):
    """
    The main intelligence entry point. Analyzes intent and routes 
    to the correct skills.
    """
    if not command:
        return False

    # 1. Normalize (Auto-Correct common errors)
    cmd = _normalize_command(command.lower().strip())
    
    # --- PROACTIVE RESPONSE HANDLING ---
    if state_manager.pending_action:
        if any(w in cmd for w in ["yes", "yeah", "sure", "do it", "please", "ok"]):
            action = state_manager.pending_action
            state_manager.pending_action = None
            state_manager.pending_action_text = None
            
            print(f"[Brain] Attempting to execute pending action: {action} (Type: {type(action)})")
            
            # SAFETY CHECK: Only call if it's actually a function/lambda
            if callable(action):
                try:
                    result = action()
                    if result:
                        response_callback(result)
                except Exception as e:
                    print(f"[Brain Error] Failed to execute pending action: {e}")
                    response_callback("I encountered an error while trying to perform that action.")
            else:
                print(f"[Brain Error] Pending action was not callable! Value: {action}")
            return True
        elif any(w in cmd for w in ["no", "nope", "nah", "stop", "cancel"]):
            state_manager.pending_action = None
            state_manager.pending_action_text = None
            response_callback("Understood. I'll remain silent.")
            return True
    
    # 2. Identify Intent
    intent, confidence = _calculate_intent(cmd)
    
    # 3. Apply Context (Memory)
    # If confidence is low, check if the last command was the same intent
    try:
        last_intent = memory_manager.get_last_intent()
        if confidence < 10 and last_intent and last_intent != "GENERAL_CHAT":
            # Boost confidence for follow-up actions in the same context
            if any(kw in cmd for kw in ["it", "them", "search", "open", "go"]):
                intent = last_intent
                confidence += 15
                print(f"[Brain] Applying Context: Boosted {intent} based on last interaction.")
    except:
        pass
    
    print(f"[Brain] Intent: {intent} (Confidence: {confidence})")

    # Wrapper to capture the response for memory
    def mem_callback(resp):
        memory_manager.add_interaction(cmd, resp, intent)
        response_callback(resp)

    # 4. Routing
    # If confidence is extremely low, it might be noise or general chat
    if confidence < 5:
        # Context Awareness: If the user says 'this' or 'here', or asks for an explanation/summary
        # and we have an active window, let the AI handle it with context.
        context_keywords = ["this", "here", "explain", "summarize", "about", "what"]
        if any(kw in cmd for kw in context_keywords) and ai_layer.is_available():
            response = ai_layer.process_with_context(cmd, state_manager.active_window)
            mem_callback(response)
            return True
            
        # Fallback to general skill processing (for chat, etc.)
        handled = skill_manager.execute_command(cmd, mem_callback)
        if not handled:
            mem_callback("I didn't fully understand that. Could you rephrase?")
        return True

    # Intent-based routing
    # The skill_manager still handles the execution, but the brain decides if it's worth trying
    handled = skill_manager.execute_command(cmd, mem_callback)
    
    if not handled:
        mem_callback("I detected your intent but I'm not sure how to perform that specific action yet.")
        
    return True
