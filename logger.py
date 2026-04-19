import sys
import os
import datetime

LOG_FILE = "friday.log"

class LoggerWriter:
    """
    A custom file-like object that writes standard output to both 
    the original console and a persistent log file.
    """
    def __init__(self, original_stream, log_file):
        self.original_stream = original_stream
        self.log_file = log_file

    def write(self, message):
        # Always write to the original stream (console if visible)
        self.original_stream.write(message)
        
        # Only log non-empty, non-whitespace strings to avoid bloating
        if message.strip():
            timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
            try:
                with open(self.log_file, "a", encoding="utf-8") as f:
                    # Check if the message already has a bracketed prefix to avoid double-prefixing
                    if message.strip().startswith("["):
                        f.write(f"{timestamp} {message}\n")
                    else:
                        f.write(f"{timestamp} [System] {message}\n")
            except Exception:
                pass # Fail silently if file is locked

    def flush(self):
        self.original_stream.flush()

def init_logger():
    """
    Hooks into sys.stdout and sys.stderr.
    Must be called at the very start of main.py.
    """
    # Create the log file if it doesn't exist, and write a startup header
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write("\n" + "="*50 + "\n")
        f.write(f" Friday System Initialized : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*50 + "\n")

    # Replace standard streams
    sys.stdout = LoggerWriter(sys.stdout, LOG_FILE)
    sys.stderr = LoggerWriter(sys.stderr, LOG_FILE)
