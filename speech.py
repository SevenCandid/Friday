import os
import sys
import wave
import subprocess
import threading
import queue
import multiprocessing
import time
import time
import winsound
import state_manager
import config

# Neural Voice Configuration
PIPER_EXE = config.get("voice", "piper_exe")
VOICE_MODEL = config.get("voice", "model")
TEMP_WAV = "last_speech.wav"

# ---------------------------------------------------------------
# PERSISTENT TTS WORKER (PyInstaller Safe)
# ---------------------------------------------------------------
def _tts_worker(in_q, out_q):
    """
    Runs in a completely separate process to prevent GUI freezing.
    Uses multiprocessing queues for safe communication in bundled .exe
    """
    import pyttsx3
    import time
    import comtypes
    
    try:
        # Initialize COM for SAPI5 in the child process
        comtypes.CoInitialize()
        
        engine = pyttsx3.init()
        # Set volume to maximum (1.0)
        engine.setProperty('volume', 1.0)
        
        # Set female voice if available
        voices = engine.getProperty('voices')
        for v in voices:
            if 'female' in v.name.lower() or 'zira' in v.name.lower():
                engine.setProperty('voice', v.id)
                break
        engine.setProperty('rate', 175)
        
        with open("tts_debug.log", "a") as f:
            f.write(f"TTS Worker Initialized Successfully at {time.ctime()}\n")
        
        out_q.put('ready')
        
        while True:
            text = in_q.get()
            if text is None:
                break
            
            text = text.strip()
            if text:
                try:
                    engine.say(text)
                    engine.runAndWait()
                except Exception as e:
                    # Log error to a file since stdout is None in --windowed
                    with open("tts_debug.log", "a") as f:
                        f.write(f"Speak Error: {e}\n")
            
            out_q.put('done')
            
    except Exception as e:
        with open("tts_debug.log", "a") as f:
            f.write(f"Initialization Error: {e}\n")
        out_q.put('error')



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
        self._tts_proc = None      # Persistent pyttsx3 server
        self._tts_in = None
        self._tts_out = None
        self._tts_done = threading.Event()

        # We DO NOT start the TTS server here to avoid multiprocessing crash at boot.
        # It will be lazily started in _speak_via_server.
        threading.Thread(target=self._worker, daemon=True, name="VoiceWorker").start()

    def _start_tts_server(self):
        """Starts a dedicated TTS thread with its own COM context for stability."""
        try:
            self._tts_queue = queue.Queue()
            self._tts_thread = threading.Thread(
                target=self._tts_worker_thread,
                daemon=True,
                name="TTS-Thread"
            )
            self._tts_thread.start()
            print("[Speech] High-stability TTS thread online.")
        except Exception as e:
            print(f"[Speech Error] Failed to start TTS thread: {e}")

    def _tts_worker_thread(self):
        """Dedicated thread for pyttsx3 to avoid GUI conflicts."""
        import pyttsx3
        import pythoncom
        
        try:
            # Initialize COM for SAPI5 in this thread
            pythoncom.CoInitialize()
            
            engine = pyttsx3.init()
            engine.setProperty('volume', 1.0)
            engine.setProperty('rate', 175)
            
            # Set female voice if available
            voices = engine.getProperty('voices')
            for v in voices:
                if 'female' in v.name.lower() or 'zira' in v.name.lower():
                    engine.setProperty('voice', v.id)
                    break

            while True:
                text = self._tts_queue.get()
                if text is None: break
                
                try:
                    engine.say(text)
                    engine.runAndWait()
                except:
                    pass
                
                self._tts_done.set()
                self._tts_queue.task_done()
                
        except Exception as e:
            print(f"[Speech Thread Error] {e}")

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
        threading.Thread(target=_one_shot, daemon=True).start()
        
        # Wait for speech to finish to maintain conversation flow
        self._tts_done.wait(timeout=10.0)

    # ------------------------------------------------------------------
    # Piper Neural Voice (Primary)
    # ------------------------------------------------------------------
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

            # Play asynchronously, wait for EXACT duration from WAV header
            duration = _get_wav_duration(TEMP_WAV)
            winsound.PlaySound(TEMP_WAV, winsound.SND_FILENAME | winsound.SND_ASYNC)

            deadline = time.time() + duration + 0.3  # small safety buffer
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

    # ------------------------------------------------------------------
    # Worker
    # ------------------------------------------------------------------
    def _worker(self):
        while True:
            text = self._queue.get()
            if not text:
                self._queue.task_done()
                continue

            # Clear stale stop signal before processing new speech
            self._stop_event.clear()
            state_manager.set_speaking(True)

            if not self._speak_piper(text):
                self._speak_via_server(text)

            state_manager.set_speaking(False)
            self._queue.task_done()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def speak(self, text):
        if text:
            print(f"Friday: {text}")
            state_manager.add_to_chat("Friday", text)
            self._queue.put(text)

    def stop(self):
        self._stop_event.set()
        if self._active_proc:
            try: self._active_proc.terminate()
            except: pass
        if self._tts_proc and self._tts_proc.is_alive():
            try: self._tts_proc.terminate()
            except: pass
            self._tts_proc = None
        while not self._queue.empty():
            try: self._queue.get_nowait(); self._queue.task_done()
            except: break
        winsound.PlaySound(None, winsound.SND_PURGE)
        state_manager.set_speaking(False)


# Module-level singleton
_engine = VoiceEngine()


def speak(text):
    _engine.speak(text)


def stop_speaking():
    _engine.stop()
