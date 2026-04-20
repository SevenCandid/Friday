import queue

# Global state variables
status = "Idle"
alarm_ringing = False
is_speaking = False
active_window = "Unknown"    # Tracks currently focused window
audio_energy = 0.0           # Real-time mic volume (0.0 to 1.0+)
pending_action = None       # Stores the function to execute on 'Yes'
pending_action_text = None  # Stores the label for the pending action
app_count = 0                # Number of indexed applications
quiet_mode = False           # If True, Friday skips voice output but still shows HUD alerts
current_city = "Accra"       # Default city
current_lat = 5.6037         # Default Accra Lat
current_lon = -0.1870        # Default Accra Lon

# Thread-safe queues for chat messages
chat_queue = queue.Queue()
remote_chat_queue = queue.Queue() # For the mobile HUD

def set_status(text):
    global status
    status = text

def set_alarm_ringing(active):
    global alarm_ringing
    alarm_ringing = active

def set_speaking(speaking):
    global is_speaking
    is_speaking = speaking

def add_to_chat(sender, text):
    """Adds a message to both the desktop and remote chat queues."""
    msg = {"sender": sender, "text": text}
    chat_queue.put(msg)
    remote_chat_queue.put(msg)
