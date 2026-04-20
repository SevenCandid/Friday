import os
import sys
from .path_helper import get_resource_path

# --- WINDOWS DLL REPAIR ---
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
from . import state_manager
import webrtcvad 
from vosk import Model, KaldiRecognizer
from faster_whisper import WhisperModel

# --- CONFIGURATION ---
VOSK_MODEL_PATH = get_resource_path("vosk-model-small-en-us-0.15")
WHISPER_MODEL_SIZE = "tiny"

# Audio parameters
SAMPLE_RATE = 16000
CHUNK_DURATION_MS = 30 # 30ms frames for VAD
CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_DURATION_MS / 1000) 
BUFFER_SECONDS = 10   # Catch longer commands
ENERGY_THRESHOLD = 300 # Increased for silent background
DEBUG_VOICE = False    # Set to True to see energy levels in console

# Global state
_audio_buffer = collections.deque(maxlen=(SAMPLE_RATE // CHUNK_SIZE) * BUFFER_SECONDS)
_vosk_model = None
_whisper_model = None
_pyaudio = None
_stream = None
_vad = webrtcvad.Vad(3) # Mode 3: Most aggressive filtering (0-3) for silence
_failed_init = False

def _process_audio(data):
    """Applies normalization and noise gating to raw audio bytes."""
    audio_np = np.frombuffer(data, dtype=np.int16)
    
    # Calculate Energy (RMS)
    rms = np.sqrt(np.mean(audio_np.astype(np.float32)**2))
    
    # Push normalized energy to state manager for visual reactivity
    state_manager.audio_energy = min(1.0, rms / 800.0) 
    
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
        
        # --- DEVICE SCANNER ---
        print("[Voice] Scanning for audio input devices...")
        for i in range(_pyaudio.get_device_count()):
            info = _pyaudio.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                print(f"  - [Device {i}] {info['name']}")

        _stream = _pyaudio.open(
            format=pyaudio.paInt16, 
            channels=1, 
            rate=SAMPLE_RATE, 
            input=True, 
            frames_per_buffer=4000 # Increased for stability
        )

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
                state_manager.audio_energy *= 0.8 # Decay for smoothness
                continue

            # 2. VAD (Voice Activity Detection)
            try:
                is_speech = _vad.is_speech(raw_data, SAMPLE_RATE)
            except:
                is_speech = True # Fallback to true if VAD fails on a chunk

            if not is_speech:
                continue

            _audio_buffer.append(clean_data)

            # --- IMPROVED WAKE WORD DETECTION ---
            partial_data = json.loads(recognizer.PartialResult())
            partial_text = partial_data.get("partial", "").lower()
            
            if recognizer.AcceptWaveform(clean_data):
                result = json.loads(recognizer.Result())
                vosk_text = result.get("text", "").lower().strip()
                
                if not vosk_text:
                    continue

                if "seven" in vosk_text or "seven" in partial_text:
                    cmd = vosk_text.replace("seven", "").strip()
                    if not cmd:
                        return "seven" 
                    return cmd 
                
                # High-accuracy fallback for potential commands
                whisper_text = _get_whisper_transcription(list(_audio_buffer))
                if whisper_text and "seven" in whisper_text:
                    return whisper_text
                return None 
                    
        except Exception as e:
            print(f"[Voice Error] {e}")
            return None
