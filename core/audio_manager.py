import winsound
import threading
import time

def play_chirp():
    """Plays a high-tech ascending chirp (Wake Word feedback)."""
    def _run():
        try:
            # Ascending frequency sweep
            for freq in range(800, 1600, 100):
                winsound.Beep(freq, 20)
        except:
            pass
    threading.Thread(target=_run, daemon=True).start()

def play_whoosh():
    """Plays a descending 'whoosh' sound (Minimize feedback)."""
    def _run():
        try:
            # Descending frequency sweep
            for freq in range(1200, 400, -100):
                winsound.Beep(freq, 30)
        except:
            pass
    threading.Thread(target=_run, daemon=True).start()

def play_notification():
    """Subtle double-ping for alerts."""
    def _run():
        try:
            winsound.Beep(1000, 50)
            time.sleep(0.05)
            winsound.Beep(1200, 50)
        except:
            pass
    threading.Thread(target=_run, daemon=True).start()
