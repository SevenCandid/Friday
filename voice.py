import os
import sys

# --- WINDOWS DLL REPAIR ---
# faster-whisper/ctranslate2 often fails to find its DLLs on Windows.
# This block manually adds the site-packages path to the DLL search path.
if sys.platform == "win32":
    import site
    packages_paths = site.getsitepackages()
    for path in packages_paths:
        ct_path = os.path.join(path, "ctranslate2")
        if os.path.exists(ct_path):
            try:
                os.add_dll_directory(ct_path)
            except:
                pass

import json
import queue
import threading
import collections
import time
import numpy as np
import pyaudio
import state_manager
import webrtcvad # Requires: pip install webrtcvad
from vosk import Model, KaldiRecognizer
from faster_whisper import WhisperModel

# --- CONFIGURATION ---
VOSK_MODEL_PATH = "vosk-model-small-en-us-0.15"
WHISPER_MODEL_SIZE = "tiny"

# Audio parameters
SAMPLE_RATE = 16000
CHUNK_DURATION_MS = 30 # 30ms frames for VAD
CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_DURATION_MS / 1000) 
BUFFER_SECONDS = 7
ENERGY_THRESHOLD = 80  # Lowered even further for maximum sensitivity
DEBUG_VOICE = False    # Set to True to see energy levels in console

# Global state
_audio_buffer = collections.deque(maxlen=(SAMPLE_RATE // CHUNK_SIZE) * BUFFER_SECONDS)
_vosk_model = None
_whisper_model = None
_pyaudio = None
_stream = None
_vad = webrtcvad.Vad(1) # Mode 1: Less aggressive filtering (0-3)
_failed_init = False

def _process_audio(data):
    """Applies normalization and noise gating to raw audio bytes."""
    audio_np = np.frombuffer(data, dtype=np.int16)
    
    # Calculate Energy (RMS)
    rms = np.sqrt(np.mean(audio_np.astype(np.float32)**2))
    
    if DEBUG_VOICE and rms > 50:
        print(f"[Debug] Energy: {int(rms)}")

    if rms < ENERGY_THRESHOLD:
        return None, 0
    
    # Normalize Volume (Gain boost for quiet speech)
    max_val = np.max(np.abs(audio_np))
    if max_val > 0:
        audio_np = (audio_np.astype(np.float32) / max_val * 32767).astype(np.int16)
        
    return audio_np.tobytes(), rms

def _initialize_engines():
    """Initializes Vosk and Whisper engines in the background."""
    global _vosk_model, _whisper_model, _failed_init
    
    if _failed_init:
        return

    try:
        if not os.path.exists(VOSK_MODEL_PATH):
            print(f"\n[Voice Warning] Vosk model not found at '{VOSK_MODEL_PATH}'.")
            print("[Action Required] Please download the model from https://alphacephei.com/vosk/models and unzip it here.")
            _failed_init = True
            return

        print("[Voice] Loading Offline Engines (Vosk + Whisper)...")
        _vosk_model = Model(VOSK_MODEL_PATH)
        # Use CPU only as requested, tiny model for speed
        _whisper_model = WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")
        print("[Voice] Offline Engines Ready.")
    except Exception as e:
        print(f"[Voice Error] Engine initialization failed: {e}")

def _get_whisper_transcription(raw_audio_chunks):
    """Processes the buffered audio using Whisper for high accuracy."""
    if not _whisper_model:
        return None
    
    try:
        # Convert byte chunks to a single float32 numpy array
        audio_data = b"".join(raw_audio_chunks)
        audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
        
        segments, _ = _whisper_model.transcribe(audio_np, beam_size=5)
        text = " ".join([segment.text for segment in segments]).strip()
        return text.lower()
    except Exception as e:
        print(f"[Voice Error] Whisper failed: {e}")
        return None

def listen(listen_timeout=5, phrase_time_limit=5):
    """
    Offline hybrid listener.
    Uses Vosk for real-time short commands.
    Escalates to Whisper for longer/complex phrases.
    """
    global _pyaudio, _stream, _vosk_model, _failed_init
    
    # Initialize engines on first run
    if not _vosk_model and not _failed_init:
        _initialize_engines()
    
    if _failed_init or not _vosk_model:
        time.sleep(1) # Prevent high CPU usage in fail state
        return None

    if not _pyaudio:
        print("[Voice] Activating High-Quality VAD & Noise Gate...")
        _pyaudio = pyaudio.PyAudio()
        _stream = _pyaudio.open(format=pyaudio.paInt16, channels=1, rate=SAMPLE_RATE, input=True, frames_per_buffer=CHUNK_SIZE)

    recognizer = KaldiRecognizer(_vosk_model, SAMPLE_RATE)
    
    start_time = time.time()
    
    # Capture loop
    while True:
        try:
            if listen_timeout and (time.time() - start_time > listen_timeout):
                return None

            raw_data = _stream.read(CHUNK_SIZE, exception_on_overflow=False)
            
            if state_manager.is_speaking:
                _audio_buffer.clear()
                continue

            # 1. Pre-process (Energy Gate & Normalization)
            clean_data, rms = _process_audio(raw_data)
            if clean_data is None:
                continue

            # 2. VAD (Voice Activity Detection)
            try:
                is_speech = _vad.is_speech(raw_data, SAMPLE_RATE)
            except:
                is_speech = True # Fallback to true if VAD fails on a chunk

            if not is_speech:
                continue

            _audio_buffer.append(clean_data)

            if recognizer.AcceptWaveform(clean_data):
                result = json.loads(recognizer.Result())
                vosk_text = result.get("text", "").lower().strip()
                
                if not vosk_text or len(vosk_text.split()) < 2:
                    # Filter out single-word garbage or noise
                    continue
                
                # POWER KEYWORDS
                power_keywords = [
                    "open", "launch", "time", "date", "alarm", "set", 
                    "who", "what", "how", "hello", "hi", "hey", "friday",
                    "thanks", "thank", "stop", "snooze", "cancel",
                    "write", "read", "create"
                ]
                
                word_count = len(vosk_text.split())
                has_keyword = any(kw in vosk_text for kw in power_keywords)
                
                # Decision Logic
                if word_count <= 4 and has_keyword:
                    return vosk_text
                else:
                    whisper_text = _get_whisper_transcription(list(_audio_buffer))
                    if whisper_text and len(whisper_text.split()) >= 2:
                        return whisper_text
                    return None # Discard garbage transcription
                    
        except Exception as e:
            print(f"[Voice Error] {e}")
            return None
