import difflib
import skill_manager
import memory_manager

# Intent Definitions (Clusters of related words)
INTENT_MAP = {
    "WEB_BROWSING": ["chrome", "internet", "google", "youtube", "web", "browser", "browse", "website"],
    "FILE_CONTROL": ["file", "folder", "document", "move", "search", "find", "locate", "path", "directory"],
    "SYSTEM_CONTROL": [
        "shutdown", "restart", "battery", "wifi", "volume", "brightness", 
        "power", "energy", "mute", "audio", "sound", "lock", "screen", "dim"
    ],
    "TIME": ["time", "date", "clock", "today", "day", "calendar"],
    "GENERAL_CHAT": ["friday", "hello", "hi", "hey", "thanks", "thank", "help", "who", "what", "how", "sup", "whats up"]
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
    import state_manager
    if state_manager.state.pending_action:
        if any(w in cmd for w in ["yes", "yeah", "sure", "do it", "please", "ok"]):
            action = state_manager.state.pending_action
            state_manager.state.pending_action = None
            state_manager.state.pending_action_text = None
            result = action() # Execute the stored function
            response_callback(result)
            return True
        elif any(w in cmd for w in ["no", "nope", "nah", "stop", "cancel"]):
            state_manager.state.pending_action = None
            state_manager.state.pending_action_text = None
            response_callback("Understood. I'll remain silent.")
            return True
    
    # 2. Identify Intent
    intent, confidence = _calculate_intent(cmd)
    
    # 3. Apply Context (Memory)
    # If confidence is low, check if the last command was the same intent
    last_intent = memory_manager.get_last_intent()
    if confidence < 10 and last_intent and last_intent != "GENERAL_CHAT":
        # Boost confidence for follow-up actions in the same context
        if any(kw in cmd for kw in ["it", "them", "search", "open", "go"]):
            intent = last_intent
            confidence += 15
            print(f"[Brain] Applying Context: Boosted {intent} based on last interaction.")
    
    print(f"[Brain] Intent: {intent} (Confidence: {confidence})")

    # Wrapper to capture the response for memory
    def mem_callback(resp):
        memory_manager.add_interaction(cmd, resp, intent)
        response_callback(resp)

    # 4. Routing
    # If confidence is extremely low, it might be noise or general chat
    if confidence < 5:
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
