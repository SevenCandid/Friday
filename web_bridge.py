import os
import threading
import socket
import json
import time
from flask import Flask, request, jsonify, render_template_string
import state_manager
import brain

app = Flask(__name__)

# Load the HTML template from the file
def get_template():
    try:
        with open("remote_hud.html", "r", encoding="utf-8") as f:
            return f.read()
    except:
        return "<h1>Friday Remote HUD: Error loading template.</h1>"

@app.route("/")
def index():
    return render_template_string(get_template())

@app.route("/command", methods=["POST"])
def receive_command():
    data = request.json
    cmd = data.get("command", "")
    if cmd:
        # We process the command through the brain
        # We'll use a dummy response callback to capture the reply
        replies = []
        def capture_reply(text):
            replies.append(text)
            state_manager.add_to_chat("Friday", text)

        # Log user command in desktop chat
        state_manager.add_to_chat("Remote User", cmd)
        
        # Process in a background thread to avoid blocking Flask
        threading.Thread(target=brain.process, args=(cmd, capture_reply), daemon=True).start()
        
        # Since brain.process is async, we can't get the reply immediately 
        # unless we wait or use a different flow. 
        # For now, we tell the phone "Transmitted" and let polling pick up the reply.
        return jsonify({"status": "Transmitted", "reply": "Processing..."})
    return jsonify({"status": "Error", "message": "No command provided"})

@app.route("/messages")
def get_messages():
    # Collect all messages currently in the remote queue
    msgs = []
    while not state_manager.remote_chat_queue.empty():
        msgs.append(state_manager.remote_chat_queue.get_nowait())
    return jsonify({"messages": msgs})

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def start_server():
    ip = get_local_ip()
    port = 5000
    print(f"\n[Web Bridge] --- REMOTE HUD ACTIVATED ---")
    print(f"[Web Bridge] URL: http://{ip}:{port}")
    print(f"[Web Bridge] Ensure your phone is on the same WiFi!")
    
    # Enable CORS for mobile browsers
    @app.after_request
    def add_header(response):
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response

    # Disable Flask logging for a cleaner console
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    
    try:
        app.run(host="0.0.0.0", port=port, threaded=True, debug=False)
    except Exception as e:
        print(f"[Web Bridge Error] Could not start server: {e}")

def start_background_bridge():
    threading.Thread(target=start_server, daemon=True, name="WebBridgeThread").start()

if __name__ == "__main__":
    start_server()
