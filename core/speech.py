import os
import sys
import wave
import subprocess
import threading
import queue
import multiprocessing
import time
import winsound
from . import state_manager
from . import config

# Neural Voice Configuration
PIPER_EXE = config.get("voice", "piper_exe")
VOICE_MODEL = config.get("voice", "model")
TEMP_WAV = "last_speech.wav"

def _get_wav_duration(path):
    """Returns exact playback duration of a WAV file in seconds."""
    try:
        with wave.open(path, 'r') as wf:
            return wf.getnframes() / float(wf.getframerate())
    except Exception:
        return 3.0  # Safe fallback

class VoiceEngine:
    def __init__(self):
        self._queue = queue.Queue()
        self._stop_event = threading.Event()
        self._active_proc = None   # Piper process
        self._tts_done = threading.Event()

        threading.Thread(target=self._worker, daemon=True, name="VoiceWorker").start()

    def _speak_via_server(self, text):
        """One-Shot TTS: Initialize, speak, and close. Most reliable for Windows SAPI5."""
        def _one_shot():
            import pyttsx3
            import pythoncom
            try:
                pythoncom.CoInitialize()
                engine = pyttsx3.init()
                engine.setProperty('volume', 1.0)
                engine.setProperty('rate', 175)
                
                # Female voice selection
                voices = engine.getProperty('voices')
                for v in voices:
                    if 'female' in v.name.lower() or 'zira' in v.name.lower():
                        engine.setProperty('voice', v.id)
                        break
                
                engine.say(text)
                engine.runAndWait()
            except Exception as e:
                print(f"[One-Shot TTS Error] {e}")
            finally:
                self._tts_done.set()

        self._tts_done.clear()
        t = threading.Thread(target=_one_shot, daemon=True)
        t.start()
        t.join(timeout=15.0) # Wait for the current sentence to finish before next in queue

    def _speak_piper(self, text):
        if not os.path.exists(PIPER_EXE):
            return False
        try:
            self._active_proc = subprocess.Popen(
                [PIPER_EXE, "-m", VOICE_MODEL, "-f", TEMP_WAV],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                text=True
            )
            self._active_proc.communicate(input=text)
            self._active_proc = None

            if self._stop_event.is_set() or not os.path.exists(TEMP_WAV):
                return False

            duration = _get_wav_duration(TEMP_WAV)
            winsound.PlaySound(TEMP_WAV, winsound.SND_FILENAME | winsound.SND_ASYNC)

            deadline = time.time() + duration + 0.3
            while time.time() < deadline:
                if self._stop_event.is_set():
                    winsound.PlaySound(None, winsound.SND_PURGE)
                    return True
                time.sleep(0.05)
            return True
        except Exception as e:
            print(f"[Piper Error] {e}")
            self._active_proc = None
            return False

    def _worker(self):
        while True:
            text = self._queue.get()
            if not text:
                self._queue.task_done()
                continue

            self._stop_event.clear()
            state_manager.set_speaking(True)

            if not self._speak_piper(text):
                self._speak_via_server(text)

            state_manager.set_speaking(False)
            self._queue.task_done()

    def speak(self, text):
        if text:
            print(f"SEVEN: {text}")
            state_manager.add_to_chat("SEVEN", text)
            
            # Skip voice output if Stealth Mode is active
            if state_manager.quiet_mode:
                print(f"[Stealth Mode] Skipping voice queue for: {text}")
                return
                
            self._queue.put(text)

    def stop(self):
        self._stop_event.set()
        if self._active_proc:
            try: self._active_proc.terminate()
            except: pass
        winsound.PlaySound(None, winsound.SND_PURGE)
        state_manager.set_speaking(False)

# Module-level singleton
_engine = VoiceEngine()

def speak(text):
    _engine.speak(text)

def stop_speaking():
    _engine.stop()
