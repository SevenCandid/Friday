import os
import subprocess
import threading
import queue
import time
import pyttsx3
import state_manager

# Config for High-Quality Neural Voice
PIPER_EXE = "piper/piper.exe"
VOICE_MODEL = "piper/en_US-amy-low.onnx"
TEMP_WAV = "last_speech.wav"

# Global queue for speech requests
_speech_queue = queue.Queue()

def _speak_pyttsx3(text):
    """Legacy/Fallback robotic voice."""
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        for voice in voices:
            if "zira" in voice.name.lower():
                engine.setProperty('voice', voice.id)
                break
        engine.setProperty('rate', 190)
        engine.say(text)
        engine.runAndWait()
        engine.stop()
        del engine
    except Exception as e:
        print(f"[Speech Error] pyttsx3 failed: {e}")

def _speak_piper(text):
    """High-quality neural voice using Piper."""
    try:
        # 1. Generate the WAV file
        process = subprocess.Popen(
            [PIPER_EXE, "-m", VOICE_MODEL, "-f", TEMP_WAV],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        process.communicate(input=text)
        
        # 2. Play the WAV file using Windows built-in player
        if os.path.exists(TEMP_WAV):
            import winsound
            winsound.PlaySound(TEMP_WAV, winsound.SND_FILENAME)
            return True
    except Exception as e:
        print(f"[Speech Error] Piper failed: {e}")
    return False

def _speech_worker():
    """Dedicated worker thread that handles speech requests."""
    while True:
        try:
            text = _speech_queue.get()
            if not text:
                _speech_queue.task_done()
                continue
            
            state_manager.set_speaking(True)
            
            # Try Piper first, fallback to pyttsx3
            if os.path.exists(PIPER_EXE) and os.path.exists(VOICE_MODEL):
                success = _speak_piper(text)
                if not success:
                    _speak_pyttsx3(text)
            else:
                _speak_pyttsx3(text)
                
            state_manager.set_speaking(False)
            _speech_queue.task_done()
            
        except Exception as e:
            print(f"[Speech System Error] {e}")
            state_manager.set_speaking(False)
            time.sleep(1)

# Start the speech worker thread
_worker_thread = threading.Thread(target=_speech_worker, daemon=True)
_worker_thread.start()

def speak(text):
    """Adds text to the speech queue. Thread-safe and non-blocking."""
    if not text:
        return
    print(f"Friday: {text}")
    _speech_queue.put(text)
