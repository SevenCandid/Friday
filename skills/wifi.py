import subprocess
import os

def handle(command, speak):
    # Detect WiFi-related keywords
    if "wifi" not in command and "network" not in command:
        return False

    # 1. Turn WiFi ON
    if "on" in command or "enable" in command:
        try:
            # Note: This command typically requires Admin privileges
            subprocess.run(['netsh', 'interface', 'set', 'interface', 'Wi-Fi', 'admin=enabled'], check=True, capture_output=True)
            speak("WiFi has been turned on.")
        except subprocess.CalledProcessError:
            speak("I couldn't enable WiFi. I might need administrator privileges to do that.")
        return True

    # 2. Turn WiFi OFF
    if "off" in command or "disable" in command:
        try:
            subprocess.run(['netsh', 'interface', 'set', 'interface', 'Wi-Fi', 'admin=disabled'], check=True, capture_output=True)
            speak("WiFi has been turned off.")
        except subprocess.CalledProcessError:
            speak("I couldn't disable WiFi. I might need administrator privileges to do that.")
        return True

    # 3. List Networks
    if "show" in command or "list" in command or "available" in command:
        try:
            import state_manager
            result = subprocess.run(['netsh', 'wlan', 'show', 'networks'], check=True, capture_output=True, text=True)
            
            # Clean up the output to show just SSIDs for the chat window
            lines = result.stdout.split('\n')
            ssids = [line.split(':')[-1].strip() for line in lines if "SSID" in line and line.split(':')[-1].strip()]
            
            if ssids:
                list_msg = "Available Networks:\n" + "\n".join([f"• {s}" for s in ssids])
                state_manager.add_to_chat("Friday", list_msg)
                speak("I have listed available WiFi networks on your screen. You can connect manually.")
            else:
                speak("I couldn't find any available WiFi networks.")
        except Exception as e:
            print(f"[WiFi Error] {e}")
            speak("I'm sorry, I couldn't scan for networks right now.")
        return True

    return False
