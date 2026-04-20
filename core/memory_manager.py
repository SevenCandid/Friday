import json
import os
import collections
from pathlib import Path

# Paths
_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEMORY_FILE = os.path.join(_ROOT_DIR, "memory.json")

# Internal memory state
# Long-term: Persisted to JSON
_long_term = {
    "user_name": None,
    "preferences": {},
    "frequent_actions": {},
    "total_interactions": 0
}

# Short-term: Last 20 interactions in RAM
_short_term = collections.deque(maxlen=20)

def load_memory():
    """Loads long-term memory from JSON file."""
    global _long_term
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, 'r') as f:
                _long_term.update(json.load(f))
        except Exception as e:
            print(f"[Memory Error] Could not load memory: {e}")

def save_memory():
    """Saves long-term memory to JSON file."""
    try:
        with open(MEMORY_FILE, 'w') as f:
            json.dump(_long_term, f, indent=4)
    except Exception as e:
        print(f"[Memory Error] Could not save memory: {e}")

def add_interaction(command, response, intent=None):
    """Logs a new interaction into both short and long term memory."""
    # Add to RAM
    _short_term.append({
        "command": command,
        "response": response,
        "intent": intent,
        "timestamp": os.times()[4]
    })
    
    # Update stats
    _long_term["total_interactions"] += 1
    
    # Track frequent actions
    if intent:
        _long_term["frequent_actions"][intent] = _long_term["frequent_actions"].get(intent, 0) + 1
    
    # Save every 5 interactions to avoid excessive disk I/O
    if _long_term["total_interactions"] % 5 == 0:
        save_memory()

def get_last_intent():
    """Returns the intent of the very last successful command."""
    if _short_term:
        return _short_term[-1].get("intent")
    return None

def get_memory(key):
    """Retrieves a specific value from long-term memory."""
    return _long_term.get(key)

def set_memory(key, value):
    """Sets a specific value in long-term memory and saves."""
    _long_term[key] = value
    save_memory()
