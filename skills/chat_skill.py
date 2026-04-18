import sys
import os
import random

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import memory_manager
from personality import get_response

def handle(command, speak):
    # Name memory
    if "my name is" in command:
        name = command.split("is")[-1].strip().capitalize()
        memory_manager.set_memory("user_name", name)
        speak("Got it, I'll remember that.")
        return True
        
    if "remember" in command and "like" in command:
        thing = command.split("like")[-1].strip()
        memory_manager.set_memory("likes", thing)
        speak("Got it, I'll remember that.")
        return True
        
    if "what" in command and "my name" in command:
        name = memory_manager.get_memory("user_name")
        if name:
            speak(f"Your name is {name}.")
        else:
            speak("I don't know that yet.")
        return True
        
    if "what" in command and "do i like" in command:
        likes = memory_manager.get_memory("likes")
        if likes:
            speak(f"You like {likes}.")
        else:
            speak("I don't know that yet.")
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
