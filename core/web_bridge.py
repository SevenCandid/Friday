import os
import threading
import socket
import json
import time
from flask import Flask, request, jsonify, render_template_string
from . import state_manager
from . import brain

app = Flask(__name__)

# Load the HTML template from the root directory
def get_template():
    try:
        _ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        template_path = os.path.join(_ROOT_DIR, "remote_hud.html")
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    except:
        return "<h1>SEVEN Remote HUD: Error loading template.</h1>"

@app.route("/")
def index():
    return render_template_string(get_template())

@app.route("/command", methods=["POST"])
def receive_command():
    data = request.json
    cmd = data.get("command", "")
    if cmd:
        replies = []
        def capture_reply(text):
            replies.append(text)
            state_manager.add_to_chat("SEVEN", text)

        state_manager.add_to_chat("Remote User", cmd)
        threading.Thread(target=brain.process, args=(cmd, capture_reply), daemon=True).start()
        return jsonify({"status": "Transmitted", "reply": "Processing..."})
    return jsonify({"status": "Error", "message": "No command provided"})

@app.route("/messages")
def get_messages():
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
