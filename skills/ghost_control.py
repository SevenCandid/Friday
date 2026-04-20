import pyautogui
import time
import os
from core import state_manager

# Safety setting: Move mouse to corner to abort
pyautogui.FAILSAFE = True

def _execute_type(text):
    """Safely types the message into the active window."""
    time.sleep(1) # Final buffer
    pyautogui.write(text, interval=0.05)
    return f"Typing sequence complete: '{text}'"

def handle(command, speak):
    # 1. Scroll Control
    if "scroll down" in command:
        speak("Scrolling tactical display down.")
        time.sleep(0.5)
        pyautogui.scroll(-500)
        return True
    
    if "scroll up" in command:
        speak("Scrolling tactical display up.")
        time.sleep(0.5)
        pyautogui.scroll(500)
        return True

    # 2. Screenshot
    if "take a screenshot" in command or "capture screen" in command:
        speak("Capturing tactical display snapshot.")
        time.sleep(0.5)
        desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
        path = os.path.join(desktop, "friday_screenshot.png")
        pyautogui.screenshot(path)
        speak(f"Snapshot saved to your desktop as friday_screenshot.png.")
        return True

    # 3. Window Control
    if "minimize all" in command or "show desktop" in command:
        speak("Minimizing all windows.")
        pyautogui.hotkey('win', 'd')
        return True
        
    if "minimize window" in command or "minimize this" in command:
        speak("Minimizing active window.")
        pyautogui.hotkey('win', 'down')
        time.sleep(0.1)
        pyautogui.hotkey('win', 'down')
        return True
        
    if "maximize window" in command or "maximize this" in command:
        speak("Maximizing active window.")
        pyautogui.hotkey('win', 'up')
        return True
        
    # 4. Keyboard Macros
    if "copy that" in command or "copy this" in command:
        pyautogui.hotkey('ctrl', 'c')
        speak("Copied to clipboard.")
        return True
        
    if "paste that" in command or "paste this" in command or "paste it" in command:
        pyautogui.hotkey('ctrl', 'v')
        speak("Pasted.")
        return True
        
    if "press enter" in command or "hit enter" in command:
        pyautogui.press('enter')
        return True

    # 5. Typing Control
    if command.startswith("type "):
        text_to_type = command[5:].strip()
        if not text_to_type:
            return False
            
        speak(f"I am prepared to type: '{text_to_type}'. Shall I proceed?")
        
        # Use the state manager to wait for a 'Yes' confirmation
        state_manager.pending_action = lambda: _execute_type(text_to_type)
        state_manager.pending_action_text = "typing_confirmation"
        return True

    return False
