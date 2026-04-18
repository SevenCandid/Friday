import re
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

def _get_volume_control():
    """Universal method that handles both raw COM and wrapped pycaw objects."""
    try:
        devices = AudioUtilities.GetSpeakers()
        
        # Method A: Try standard Activate (on raw COM objects)
        if hasattr(devices, 'Activate'):
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        # Method B: Try accessing the internal device if it's a wrapper
        elif hasattr(devices, '_device') and hasattr(devices._device, 'Activate'):
            interface = devices._device.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        else:
            # Method C: Use the lowest-level enumerator as absolute fallback
            enumerator = AudioUtilities.GetDeviceEnumerator()
            device = enumerator.GetDefaultAudioEndpoint(0, 1)
            interface = device.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            
        return cast(interface, POINTER(IAudioEndpointVolume))
    except Exception as e:
        print(f"[Volume Error] All access methods failed: {e}")
        return None

def handle(command, speak):
    # Expanded keyword detection for more natural phrasing
    audio_keywords = ["volume", "mute", "sound", "audio", "louder", "quieter"]
    if not any(kw in command for kw in audio_keywords):
        return False
        
    volume = _get_volume_control()
    if not volume:
        # If we identified it's a volume command but can't access hardware, 
        # we still return True so other skills don't try to handle it.
        speak("I'm sorry, I'm having trouble accessing your speakers right now.")
        return True

    # 1. Mute / Unmute
    if "unmute" in command:
        volume.SetMute(0, None)
        speak("Audio unmuted.")
        return True
    elif "mute" in command:
        volume.SetMute(1, None)
        speak("System muted.")
        return True

    # 2. Absolute Volume (e.g., "Set volume to 50%")
    match = re.search(r"(\d+)%", command) or re.search(r"to (\d+)", command)
    if match:
        target_percent = int(match.group(1))
        # Clamp between 0 and 100
        target_percent = max(0, min(100, target_percent))
        volume.SetMasterVolumeLevelScalar(target_percent / 100.0, None)
        speak(f"Setting volume to {target_percent} percent.")
        return True

    # 3. Relative Volume (Increase/Decrease)
    current_vol = volume.GetMasterVolumeLevelScalar()
    
    if "increase" in command or "up" in command or "louder" in command:
        new_vol = min(1.0, current_vol + 0.1)
        volume.SetMasterVolumeLevelScalar(new_vol, None)
        speak(f"Increasing volume to {int(new_vol * 100)} percent.")
        return True
        
    if "decrease" in command or "down" in command or "lower" in command or "quieter" in command:
        new_vol = max(0.0, current_vol - 0.1)
        volume.SetMasterVolumeLevelScalar(new_vol, None)
        speak(f"Decreasing volume to {int(new_vol * 100)} percent.")
        return True

    return False
