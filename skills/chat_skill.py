"""
Chat Skill for SEVEN.
Handles conversational interactions, long-term memory operations,
and serves as the general AI fallback for unrecognized commands.
"""
import sys
import os
import random
import threading
import re

from core import memory_manager
from core import ltm_core
from core import ai_layer
from core import state_manager
from core.personality import get_response


def _extract_name(command):
    """Attempts to extract a name from commands like 'remember my name is Frank'."""
    patterns = [
        r"my name is (\w+)",
        r"call me (\w+)",
        r"i am (\w+)",
        r"i'm (\w+)",
        r"name is (\w+)"
    ]
    for pattern in patterns:
        match = re.search(pattern, command, re.IGNORECASE)
        if match:
            return match.group(1).capitalize()
    return None


def handle(command, speak):
    # ─── EXPLICIT MEMORY FEATURE CHECK ───
    if "do you have memory" in command:
        count = ltm_core.fact_count()
        speak(f"Yes, I have a long-term memory database with {count} facts stored. "
              "Tell me to remember something, and I'll recall it later.")
        return True

    # ─── LONG-TERM MEMORY: SAVE FACT ───
    remember_triggers = ["remember that ", "remember my ", "remember i ", "remember ", "note that "]
    if any(command.startswith(t) for t in remember_triggers):
        def _save_memory_thread():
            # Auto-detect and store the user's name
            name = _extract_name(command)
            if name:
                memory_manager.set_memory("user_name", name)
                print(f"[Memory] Auto-set user name: {name}")

            fact = ai_layer.extract_fact(command)
            if fact:
                ltm_core.save_fact(fact)
                speak("Got it, I've committed that to long-term memory.")
            else:
                speak("I didn't quite catch what you wanted me to remember.")
        threading.Thread(target=_save_memory_thread, daemon=True).start()
        return True
        
    # ─── LONG-TERM MEMORY: RECALL FACT ───
    memory_questions = [
        "what is my", "what are my", "what's my",
        "what do i", "what do you know", "what do you remember",
        "do i ", "do i like", "who am i",
        "do you remember", "what did i tell you",
        "tell me what you know", "list my memories",
        "show my memories", "what have i told you"
    ]
    if any(q in command for q in memory_questions) and "location" not in command:
        def _recall_memory_thread():
            facts = ltm_core.get_all_facts()
            if not facts:
                speak("I don't have any facts stored in my memory yet. "
                      "Tell me to remember something and I'll keep it safe.")
                return
            answer = ai_layer.answer_from_memory(command, facts)
            speak(answer)
        threading.Thread(target=_recall_memory_thread, daemon=True).start()
        return True

    # ─── LONG-TERM MEMORY: LIST ALL ───
    if any(t in command for t in ["all my memories", "everything you know", "memory report",
                                   "memory dump", "what do you know about me"]):
        def _list_memory_thread():
            facts = ltm_core.get_all_facts_with_ids()
            if not facts:
                speak("Your memory bank is empty. I haven't stored any facts yet.")
                return
            
            # Build a formatted list for the HUD
            lines = [f"📋 MEMORY REPORT ({len(facts)} facts stored)"]
            lines.append("─" * 40)
            for fact_id, fact, timestamp in facts:
                date = timestamp.split("T")[0] if "T" in timestamp else timestamp
                lines.append(f"[{fact_id}] {fact}  ({date})")
            
            state_manager.add_to_chat("SEVEN", "\n".join(lines))
            speak(f"I have {len(facts)} facts in my memory. I've displayed them in your HUD.")
        threading.Thread(target=_list_memory_thread, daemon=True).start()
        return True

    # ─── LONG-TERM MEMORY: FORGET ───
    if command.startswith("forget ") or "delete memory" in command or "erase memory" in command:
        def _forget_thread():
            # "forget everything" / "clear memory" / "erase all memories"
            if any(w in command for w in ["everything", "all", "clear", "erase all", "reset"]):
                ltm_core.clear_memory()
                memory_manager.set_memory("user_name", None)
                speak("I've wiped my entire memory. We're starting fresh.")
                return
            
            # "forget the last thing" / "forget that"
            if any(w in command for w in ["last", "that", "previous"]):
                deleted = ltm_core.delete_last_fact()
                if deleted:
                    speak(f"Done. I've forgotten: {deleted}")
                else:
                    speak("There's nothing in my memory to forget.")
                return
            
            # "forget about [keyword]" — search and delete matching facts
            keyword = command.replace("forget ", "").replace("about ", "").strip()
            if keyword:
                matches = ltm_core.search_facts(keyword)
                if matches:
                    for fact_id, fact_text in matches:
                        ltm_core.delete_fact_by_id(fact_id)
                    speak(f"Done. I've forgotten {len(matches)} fact(s) related to '{keyword}'.")
                else:
                    speak(f"I don't have any memories related to '{keyword}'.")
            else:
                speak("What would you like me to forget? You can say 'forget everything', "
                      "'forget the last thing', or 'forget about [topic]'.")
        threading.Thread(target=_forget_thread, daemon=True).start()
        return True

    # ─── CASUAL CHAT / GREETINGS ───
    greetings = ["hello", "hi", "hey", "sup", "whats up"]
    if any(g in command for g in greetings) and len(command.split()) <= 2:
        # Use the stored name for a personal touch
        name = memory_manager.get_memory("user_name")
        if name:
            speak(random.choice([
                f"Hello {name}! What can I do for you?",
                f"Hey {name}! Ready for your commands.",
                f"Hi {name}! How can I help you today?"
            ]))
        else:
            speak(random.choice([
                "Hello! I'm here and listening.",
                "Hi there! How can I help you today?",
                "Hey! What's on your mind?",
                "Hello! Ready for your commands."
            ]))
        return True
        
    if "thank you" in command or "thanks" in command:
        speak(random.choice(["You're very welcome.", "No problem at all!", "Happy to help!"]))
        return True
        
    if "what can you do" in command or "help" in command:
        speak("I can check the time, control your volume and brightness, manage files, "
              "research topics on the web, remember facts about you, open websites, "
              "and monitor your system. What would you like to do?")
        return True
    
    if "your name" in command or "who are you" in command:
        speak("I am SEVEN, your personal assistant.")
        return True

    # Creator / Origin Questions
    creator_keywords = ["who made you", "who created you", "who is your creator",
                        "who is your maker", "who developed you", "who is your developer"]
    if any(k in command for k in creator_keywords):
        from core import personality
        response = (f"I was created and developed by {personality.CREATOR_NAME}, "
                    f"also known as {personality.CREATOR_ALIAS}. "
                    f"He is a talented developer from {personality.CREATOR_LOCATION}.")
        speak(response)
        return True
        
    if "how are you" in command:
        speak("I'm fully operational and ready to assist you.")
        return True

    if "what are you doing" in command or "what're you doing" in command:
        speak(random.choice([
            "Just hanging out in your system tray, waiting for you!",
            "I'm currently monitoring your system and ready for commands.",
            "Just being your helpful assistant. What's on your mind?"
        ]))
        return True

    if "what's up" in command or "whats up" in command:
        speak("Not much, just here and ready to help. How about you?")
        return True

    # Skip AI fallback for system and location commands
    system_keywords = ["restart", "shutdown", "shut down", "turn off", "power", "log off"]
    location_keywords = ["location", "where am i", "where are we"]
    search_keywords = ["price", "who is", "what is", "where is", "how many", "score", "weather", "latest"]
    if any(kw in command for kw in search_keywords + system_keywords + location_keywords):
        return False

    if ai_layer.is_available():
        def _ai_chat_thread():
            response = ai_layer.process_with_context(command, state_manager.active_window)
            speak(response)
        
        threading.Thread(target=_ai_chat_thread, daemon=True).start()
        return True

    return False
