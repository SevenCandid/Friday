import os
import sys
import wave
import subprocess
import threading
import queue
import time
import winsound
import state_manager

# Neural Voice Configuration
PIPER_EXE = "piper/piper.exe"
VOICE_MODEL = "piper/en_US-amy-low.onnx"
TEMP_WAV = "last_speech.wav"

# ---------------------------------------------------------------
# PERSISTENT TTS SERVER
# One long-lived subprocess. pyttsx3 runs on its OWN main thread.
# -u = unbuffered I/O so "done" signals arrive immediately.
# ---------------------------------------------------------------
_TTS_SERVER_SCRIPT = """
import pyttsx3, sys

e = pyttsx3.init()
for v in e.getProperty('voices'):
    if 'female' in v.name.lower() or 'zira' in v.name.lower():
        e.setProperty('voice', v.id)
        break
e.setProperty('rate', 175)

sys.stdout.write('ready\\n')
sys.stdout.flush()

while True:
    line = sys.stdin.readline()
    if not line:
        break
    text = line.strip()
    if text:
        e.say(text)
        e.runAndWait()
    sys.stdout.write('done\\n')
    sys.stdout.flush()
"""


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
        self._tts_done = threading.Event()

        self._start_tts_server()
        threading.Thread(target=self._worker, daemon=True, name="VoiceWorker").start()

    # ------------------------------------------------------------------
    # Persistent TTS Server
    # ------------------------------------------------------------------
    def _start_tts_server(self):
        try:
            self._tts_proc = subprocess.Popen(
                [sys.executable, "-u", "-c", _TTS_SERVER_SCRIPT],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                bufsize=1
            )
            threading.Thread(
                target=self._read_tts_output,
                daemon=True,
                name="TTS-Reader"
            ).start()
            print("[Speech] TTS server online.")
        except Exception as e:
            print(f"[Speech] TTS server failed: {e}")
            self._tts_proc = None

    def _read_tts_output(self):
        """Watches server stdout and fires _tts_done on each 'done' line."""
        try:
            while True:
                line = self._tts_proc.stdout.readline()
                if not line:
                    break
                if line.strip() == "done":
                    self._tts_done.set()
        except Exception:
            pass

    def _speak_via_server(self, text):
        """Send full text to TTS server, wait until completely spoken."""
        # Restart if crashed
        if not self._tts_proc or self._tts_proc.poll() is not None:
            self._start_tts_server()
            time.sleep(0.5)

        if not self._tts_proc:
            return

        try:
            # Replace any internal newlines so the server reads it as one line
            safe = text.replace("\n", " ").replace("\r", " ")
            self._tts_done.clear()
            self._tts_proc.stdin.write(safe + "\n")
            self._tts_proc.stdin.flush()

            # Wait for "done" — check stop every 50 ms
            while not self._tts_done.wait(timeout=0.05):
                if self._stop_event.is_set():
                    self._tts_proc.terminate()
                    self._tts_proc = None
                    return
                if self._tts_proc and self._tts_proc.poll() is not None:
                    break  # server died
        except Exception as e:
            print(f"[TTS Error] {e}")
            self._tts_proc = None

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
        if self._tts_proc and self._tts_proc.poll() is None:
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
