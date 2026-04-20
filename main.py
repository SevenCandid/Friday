import multiprocessing

if __name__ == '__main__':
    multiprocessing.freeze_support()

import time
import difflib
import threading
import sys

# Initialize the persistent file logger only in the main process
import logger
if multiprocessing.current_process().name == 'MainProcess':
    logger.init_logger()

import sentinel
import context_engine
import audio_manager
from voice import listen
import speech
import alarm_manager
import memory_manager
import battery_manager
import gui_manager
import state_manager
import skill_manager
import brain
import startup_manager
import observer
import web_bridge
from personality import get_response

def is_wake_word(text: str) -> bool:
    """
    Highly robust, lightweight wake word detection.
    """
    if not text:
        return False
        
    text = text.lower().strip()
    
    aliases = ["friday", "fryday", "friyday", "fry day", "hey friday", "hello friday", "hi friday", "okay friday", "hey", "hello", "hi"]
    if any(alias in text for alias in aliases):
        return True
        
    words = text.split()
    for word in words:
        if word.startswith("fri") or word.startswith("fry") or word.startswith("fra") or difflib.get_close_matches(word, ["friday"], n=1, cutoff=0.6):
            return True
            
    return False

def run_assistant():
    print("\nFriday is online and always listening...")
    state_manager.set_status("Wake word active")
    
    # Load Memory
    memory_manager.load_memory()
    
    # Load Skill Plugins
    skill_manager.load_skills()
    
    # System Init
    alarm_manager.start_background_manager()
    battery_manager.start_monitoring()
    startup_manager.manage_startup()
    observer.start_context_tracking()
    web_bridge.start_background_bridge()
    
    conversation_active = False

    while True:
        current_timeout = 30 if conversation_active else 5
        input_text = listen(listen_timeout=current_timeout)
        
        if input_text is None:
            if conversation_active:
                conversation_active = False
            continue
            
        if not input_text:
            continue
            
        if not conversation_active:
            print(f"[Standby] Heard: '{input_text}'")
            
        # Handle Command Execution via Skills
        if conversation_active:
            state_manager.set_status("Listening...")
            print(f"User: '{input_text}'")
            state_manager.add_to_chat("User", input_text)
            state_manager.set_status("Processing...")
            brain.process(input_text, speech.speak)
            continue
            
        # Handle Wake Word Detection
        if is_wake_word(input_text):
            audio_manager.play_chirp()
            
            # Remove the wake word and punctuation
            clean_command = input_text.lower()
            for wake in ["hey friday", "hello friday", "okay friday", "friday"]:
                if wake in clean_command:
                    clean_command = clean_command.replace(wake, "", 1)
            
            clean_command = clean_command.strip(",.?! ")
            
            handled = brain.process(clean_command, speech.speak)
            
            if not handled:
                wake_resp = get_response("wake")
                speech.speak(wake_resp)
            
            conversation_active = True
            state_manager.status = "Listening..."

if __name__ == "__main__":
    _ready_triggered = False

    def on_gui_ready():
        global _ready_triggered
        if _ready_triggered:
            return
        _ready_triggered = True
        
        # Start all subsystems after GUI is ready
        sentinel.greet_user(speech.speak)
        sentinel.start_sentinel(speech.speak)
        context_engine.start_context_engine(speech.speak)
        threading.Thread(target=run_assistant, daemon=True).start()

    def on_manual_command(text):
        """Handles commands typed into the GUI chat box."""
        state_manager.add_to_chat("User", text)
        brain.process(text, speech.speak)

    def on_exit():
        print("\nShutting down Friday...")

    try:
        gui_manager.init_gui(
            on_ready=on_gui_ready,
            stop_cb=speech.stop_speaking,
            manual_cb=on_manual_command
        )
    except KeyboardInterrupt:
        on_exit()
