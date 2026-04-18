import pygetwindow as gw
import PIL.ImageGrab
import os

# Optional OCR library
try:
    import pytesseract
    # You may need to specify the path to your Tesseract-OCR executable here:
    # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    HAS_OCR = True
except ImportError:
    HAS_OCR = False

def get_active_app():
    """Returns the title of the currently focused window."""
    try:
        window = gw.getActiveWindow()
        if window:
            return window.title
        return "Unknown"
    except Exception as e:
        print(f"[Observer Error] Could not get active window: {e}")
        return "Desktop"

def observe_screen():
    """Captures the screen and returns a summary of the text (if OCR available)."""
    if not HAS_OCR:
        active = get_active_app()
        return f"I can see you are using {active}, but I need Tesseract-OCR installed to read the text for you."

    try:
        # Take a screenshot
        screenshot = PIL.ImageGrab.grab()
        
        # Perform OCR
        text = pytesseract.image_to_string(screenshot)
        
        # Clean up text (remove empty lines and junk)
        lines = [line.strip() for line in text.split('\n') if len(line.strip()) > 5]
        summary = " ".join(lines[:10]) # Get the first few meaningful lines
        
        active = get_active_app()
        if not summary:
            return f"You are currently using {active}, but the screen appears to be empty or mostly images."
            
        return f"You are using {active}. I can see text mentioning: {summary[:150]}..."
        
    except Exception as e:
        print(f"[Observer Error] Screen capture failed: {e}")
        return f"I'm having trouble seeing your screen right now, but you are focused on {get_active_app()}."
