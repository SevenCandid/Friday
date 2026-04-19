import sys
import os
import random
import threading

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import memory_manager
import ltm_core
import ai_layer
from personality import get_response

def handle(command, speak):
    # Explicit Memory Feature Check
    if "do you have memory" in command:
        speak("Yes, I now have a long-term memory database. Tell me to 'remember that' something, and I will recall it later.")
        return True

    # Long-Term Memory: Save Fact
    if command.startswith("remember that ") or command.startswith("note that "):
        def _save_memory_thread():
            fact = ai_layer.extract_fact(command)
            if fact:
                ltm_core.save_fact(fact)
                speak("Got it, I've committed that to long-term memory.")
            else:
                speak("I didn't quite catch what you wanted me to remember.")
        threading.Thread(target=_save_memory_thread, daemon=True).start()
        return True
        
    # Long-Term Memory: Recall Fact
    memory_questions = ["what is my", "what are my", "do i ", "who am i", "do you remember", "what did i tell you"]
    if any(q in command for q in memory_questions):
        def _recall_memory_thread():
            facts = ltm_core.get_all_facts()
            answer = ai_layer.answer_from_memory(command, facts)
            speak(answer)
        threading.Thread(target=_recall_memory_thread, daemon=True).start()
        return True

    # Casual Chat / Greetings
    greetings = ["hello", "hi", "hey", "sup", "whats up"]
    if any(g in command for g in greetings) and len(command.split()) <= 2:
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
        speak("I can check the time, control your volume and brightness, manage files, open websites, and monitor your system. What would you like to do?")
        return True
    
    if "your name" in command or "who are you" in command:
        speak("I am Friday, your personal assistant.")
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

    return False
