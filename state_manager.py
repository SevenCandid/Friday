import queue

# Global state variables
status = "Idle"
alarm_ringing = False
is_speaking = False
pending_action = None       # Stores the function to execute on 'Yes'
pending_action_text = None  # Stores the label for the pending action

# Thread-safe queue for chat messages
# Format: {"sender": "User/Friday", "text": "..."}
chat_queue = queue.Queue()

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
    """Adds a message to the chat queue for the GUI to pick up."""
    chat_queue.put({"sender": sender, "text": text})
