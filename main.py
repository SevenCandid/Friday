import multiprocessing

if __name__ == '__main__':
    multiprocessing.freeze_support()

import time
import difflib
import threading
import sys

# Initialize the persistent file logger from the core package
from core import logger
if multiprocessing.current_process().name == 'MainProcess':
    logger.init_logger()

from core import sentinel
from core import context_engine
from core import audio_manager
from core.voice import listen
from core import speech
from core import alarm_manager
from core import memory_manager
from core import battery_manager
from core import gui_manager
from core import state_manager
from core import skill_manager
from core import brain
from core import startup_manager
from core import observer
from core import web_bridge
from core import weather_manager
from core.personality import get_response

def is_wake_word(text: str) -> bool:
    """
    Highly robust, lightweight wake word detection.
    """
    if not text:
        return False
        
    text = text.lower().strip()
    
    aliases = ["seven", "hey seven", "hello seven", "hi seven", "okay seven", "hey", "hello", "hi", "heaven", "evan", "sven"]
    if any(alias in text for alias in aliases):
        return True
        
    words = text.split()
    for word in words:
        if word.startswith("sev") or word.startswith("sen") or difflib.get_close_matches(word, ["seven"], n=1, cutoff=0.6):
            return True
            
    return False

def run_assistant():
    print("\nSEVEN is online and always listening...")
    state_manager.set_status("Wake word active")
    
    # Load Memory
    memory_manager.load_memory()
    
    # Load Skill Plugins
    skill_manager.load_skills()
    
    # System Init
    alarm_manager.start_background_manager()
    battery_manager.start_monitoring()
    weather_manager.start_monitoring()
    startup_manager.manage_startup()
    observer.start_context_tracking()
    web_bridge.start_background_bridge()
    
    conversation_active = False
    last_interaction_time = 0
    FOLLOW_UP_TIMEOUT = 10 # 10 seconds for follow-up as requested

    while True:
        # Determine if we should be in active conversation or waiting for wake word
        current_time = time.time()
        if conversation_active and (current_time - last_interaction_time > FOLLOW_UP_TIMEOUT):
            print("[System] Follow-up window closed. Entering hibernation (Silent Mode)...")
            conversation_active = False
            state_manager.set_status("Wake word active")

        # Listen for input
        current_timeout = 30 if conversation_active else 5
        input_text = listen(listen_timeout=current_timeout)
        
        if input_text is None:
            continue
            
        if not input_text:
            continue
            
        # --- CASE 1: ACTIVE CONVERSATION (Follow-up Mode) ---
        if conversation_active:
            print(f"User: '{input_text}'")
            state_manager.add_to_chat("User", input_text)
            state_manager.set_status("Processing...")
            brain.process(input_text, speech.speak)
            last_interaction_time = time.time() # Reset follow-up timer
            continue
            
        # --- CASE 2: STANDBY (Listening for Wake Word 'SEVEN') ---
        if is_wake_word(input_text):
            audio_manager.play_chirp()
            
            # Remove the wake word and punctuation
            clean_command = input_text.lower()
            for wake in ["hey seven", "hello seven", "okay seven", "seven"]:
                if wake in clean_command:
                    clean_command = clean_command.replace(wake, "", 1)
            
            clean_command = clean_command.strip(",.?! ")
            
            # Reset timers and state
            conversation_active = True
            last_interaction_time = time.time()
            state_manager.set_status("Listening...")

            # If there was a command with the wake word, process it
            if clean_command:
                state_manager.add_to_chat("User", clean_command)
                brain.process(clean_command, speech.speak)
            else:
                # If just the wake word, give a friendly response
                wake_resp = get_response("wake")
                speech.speak(wake_resp)

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
