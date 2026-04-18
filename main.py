import time
import difflib
import threading
import sys
import sentinel
import context_engine
import audio_manager
from voice import listen
from speech import speak
import alarm_manager
import memory_manager
import battery_manager  # NEW: Battery monitor
import gui_manager
import state_manager
import skill_manager
import memory_manager
import brain  # NEW: Intelligence Layer
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
    
    # 0. Load Memory
    memory_manager.load_memory()
    
    # 1. Load the Skill Plugins
    skill_manager.load_skills()
    
    # 2. System Init
    alarm_manager.start_background_manager()
    battery_manager.start_monitoring() # Start the proactive monitor
    memory_manager.load_memory()
    
    conversation_active = False
    
    # Helper for skills to respond correctly
    def friday_respond(text):
        state_manager.add_to_chat("Friday", text)
        speak(text)

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
            
        # 3. Handle Command Execution via Skills
        if conversation_active:
            state_manager.set_status("Listening...")
            print(f"User: '{input_text}'")
            state_manager.add_to_chat("User", input_text)
            
            state_manager.set_status("Processing...")
            
            # Use the brain to understand intent and route to skills
            brain.process(input_text, friday_respond)
            continue
            
        # 4. Handle Wake Word Detection
        if is_wake_word(input_text):
            audio_manager.play_chirp() # Sound feedback
            
            # CLEANUP: Aggressively remove the wake word and punctuation
            clean_command = input_text.lower()
            for wake in ["hey friday", "hello friday", "okay friday", "friday"]:
                if wake in clean_command:
                    clean_command = clean_command.replace(wake, "", 1)
            
            # Remove leading commas or punctuation left by STT
            clean_command = clean_command.strip(",.?! ")
            
            handled = brain.process(clean_command, friday_respond)
            
            if not handled:
                wake_resp = get_response("wake")
                friday_respond(wake_resp)
            
            conversation_active = True
            state_manager.status = "Listening..."

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support() # FIX: Prevents multiple windows in compiled EXE
    
    _ready_triggered = False
    def friday_speak(text):
        """Unified speak function that updates GUI and Voice."""
        state_manager.add_to_chat("Friday", text)
        speak(text) # Reconnected to the correct speech engine

    _ready_triggered = False
    def on_gui_ready():
        global _ready_triggered
        if _ready_triggered: return
        _ready_triggered = True
        
        # This runs after the GUI initializes
        sentinel.greet_user(friday_speak)
        sentinel.start_sentinel(friday_speak)
        context_engine.start_context_engine(friday_speak)
        threading.Thread(target=run_assistant, daemon=True).start()

    def on_manual_command(text):
        """Handles commands typed into the GUI chat box."""
        state_manager.add_to_chat("User", text)
        
        # Define response helper for manual entry
        def manual_respond(resp_text):
            state_manager.add_to_chat("Friday", resp_text)
            speak(resp_text)
            
        brain.process(text, manual_respond)

    def on_exit():
        print("\nShutting down Friday...")

    import speech
    try:
        # Using the new, cleaner init_gui from the FridayHUD class
        gui_manager.init_gui(on_ready_callback=on_gui_ready, stop_callback=speech.stop_speaking, manual_command_callback=on_manual_command)
    except KeyboardInterrupt:
        on_exit()
