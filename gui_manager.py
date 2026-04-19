import tkinter as tk
from tkinter import scrolledtext
import threading
import time
from datetime import datetime
import psutil
import math
import state_manager

class FridayHUD:
    """Premium Sci-Fi HUD with Neural Wave and Clean Class Logic."""
    def __init__(self, on_ready, stop_cb, manual_cb):
        self.root = tk.Tk()
        self.root.title("FRIDAY v2.0 | Neural Intelligence HUD")
        self.root.geometry("600x850")
        self.root.configure(bg="#0a0a12")
        # self.root.overrideredirect(True) # Removed to restore Max/Min/X buttons
        
        self.stop_cb = stop_cb
        self.manual_cb = manual_cb
        
        self._init_styles()
        self._build_ui()
        self._start_loops(on_ready)
        
    def _init_styles(self):
        # Premium Sci-Fi Palette
        self.colors = {
            "bg": "#0a0a12",
            "panel": "#161625",
            "accent": "#00f2ff", # Cyber Cyan
            "glow": "#00d4ff",
            "text": "#e0e0e0",
            "user": "#ffffff",
            "friday": "#00f2ff",
            "stop": "#440000",
            "warn": "#f1c40f"
        }
        self.font_header = ("Orbitron", 9, "bold") # Assuming Orbitron is available or falls back
        self.font_main = ("Consolas", 10)
        self.font_sensor = ("Consolas", 8, "bold")

    def _build_ui(self):
        # 1. Holographic Header
        header = tk.Frame(self.root, bg=self.colors["panel"], height=45)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        tk.Label(header, text="SYSTEM CORE: FRIDAY v2.0", font=("Segoe UI Semibold", 9), 
                 bg=self.colors["panel"], fg=self.colors["accent"]).pack(side="left", padx=15)
        
        self.status_label = tk.Label(header, text="STANDBY", font=self.font_sensor, 
                                   bg=self.colors["panel"], fg="#555555")
        self.status_label.pack(side="right", padx=15)

        # 2. NEURAL WAVE VISUALIZER (The "Wow" Factor)
        self.canvas = tk.Canvas(self.root, height=60, bg=self.colors["bg"], highlightthickness=0)
        self.canvas.pack(fill="x", pady=5)
        self._animate_wave(0)

        # 3. Tactical Sensor Grid (Full 6-Sensor Suite)
        sensor_frame = tk.Frame(self.root, bg=self.colors["bg"], pady=5)
        sensor_frame.pack(fill="x")
        
        self.sensor_labels = {}
        # Hardware Row
        row1 = tk.Frame(sensor_frame, bg=self.colors["bg"])
        row1.pack(fill="x")
        h_fields = [("CPU", self.colors["accent"]), ("RAM", self.colors["warn"]), ("PWR", "#2ecc71")]
        for name, color in h_fields:
            lbl = tk.Label(row1, text=f"{name}: --", font=self.font_sensor, bg=self.colors["bg"], fg=color)
            lbl.pack(side="left", expand=True)
            self.sensor_labels[name] = lbl

        # Intelligence Row
        row2 = tk.Frame(sensor_frame, bg=self.colors["bg"])
        row2.pack(fill="x")
        i_fields = [("NET", "#9b59b6"), ("APPS", "#e67e22"), ("DSK", "#e74c3c")]
        for name, color in i_fields:
            lbl = tk.Label(row2, text=f"{name}: --", font=self.font_sensor, bg=self.colors["bg"], fg=color)
            lbl.pack(side="left", expand=True)
            self.sensor_labels[name] = lbl

        # 4. Neural Chat Terminal
        self.chat = scrolledtext.ScrolledText(self.root, bg="#0d0d17", fg=self.colors["text"], 
                                             font=self.font_main, state="disabled", relief="flat", 
                                             padx=15, pady=15, insertbackground=self.colors["accent"])
        self.chat.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.chat.tag_config("meta", foreground="#555555", font=("Consolas", 8))
        self.chat.tag_config("user", foreground=self.colors["user"], spacing1=2)
        self.chat.tag_config("friday", foreground=self.colors["friday"], spacing1=2)

        # 5. Tactical Input Console
        input_frame = tk.Frame(self.root, bg=self.colors["bg"], pady=15)
        input_frame.pack(fill="x")
        
        self.entry = tk.Entry(input_frame, bg=self.colors["panel"], fg=self.colors["accent"], 
                             font=self.font_main, relief="flat", insertbackground=self.colors["accent"],
                             highlightthickness=1, highlightbackground="#333344")
        self.entry.pack(side="left", fill="x", expand=True, padx=(15, 5), ipady=5)
        self.entry.bind("<Return>", lambda e: self._handle_send())

        # STOP (SILENCE) BUTTON
        tk.Button(input_frame, text="⏹", bg=self.colors["stop"], fg="white", 
                  activebackground="#ff0000", relief="flat", padx=12, font=self.font_main,
                  command=self.stop_cb).pack(side="left", padx=2)
        
        # EXECUTE BUTTON
        tk.Button(input_frame, text="EXECUTE", bg=self.colors["accent"], fg="black", 
                  activebackground="#ffffff", relief="flat", font=self.font_sensor, 
                  padx=15, command=self._handle_send).pack(side="left", padx=(2, 15))

    def _handle_send(self):
        text = self.entry.get().strip()
        if text:
            self.stop_cb()
            self.entry.delete(0, tk.END)
            self.manual_cb(text)

    def _add_message(self, sender, text):
        self.chat.config(state="normal")
        time_str = datetime.now().strftime("%H:%M")
        tag = "user" if sender == "User" else "friday"
        
        self.chat.insert("end", f"--- {sender} @ {time_str} ---\n", "meta")
        self.chat.insert("end", f"{text}\n\n", tag)
        self.chat.see("end")
        self.chat.config(state="disabled")

    def _animate_wave(self, phase):
        """Neural Wave animation loop."""
        self.canvas.delete("all")
        width = 450
        mid_y = 30
        points = []
        for x in range(0, width, 5):
            y = mid_y + math.sin(x * 0.03 + phase) * 15 + math.sin(x * 0.07 + phase * 1.2) * 6
            points.extend([x, y])
        self.canvas.create_line(points, fill=self.colors["accent"], smooth=True, width=2)
        self.root.after(50, lambda: self._animate_wave(phase + 0.12))

    def _start_loops(self, on_ready):
        # Hardware Monitor
        def sensor_loop():
            while True:
                try:
                    # Intelligence Calculations: Deep Network Scan
                    net_info = "OFFLINE"
                    try:
                        import subprocess
                        # Using Windows native 'netsh' to get the SSID
                        results = subprocess.check_output(["netsh", "wlan", "show", "interfaces"], 
                                                        text=True, stderr=subprocess.DEVNULL)
                        for line in results.split("\n"):
                            if "SSID" in line and "BSSID" not in line:
                                net_info = line.split(":")[1].strip()
                                break
                        if net_info == "OFFLINE":
                            # Check for Ethernet/Generic connection
                            import socket
                            socket.create_connection(("8.8.8.8", 53), timeout=1)
                            net_info = "CONNECTED"
                    except:
                        net_info = "DISCONNECTED"
                    
                    app_count = len(psutil.pids())

                    stats = {
                        "CPU": f"{psutil.cpu_percent()}%",
                        "RAM": f"{psutil.virtual_memory().percent}%",
                        "DSK": f"{psutil.disk_usage('/').percent}%",
                        "PWR": f"{psutil.sensors_battery().percent if psutil.sensors_battery() else 100}%",
                        "NET": net_info,
                        "APPS": str(app_count)
                    }
                    for k, v in stats.items():
                        self.sensor_labels[k].config(text=f"{k}: {v}")
                except: pass
                time.sleep(2)
        
        # State Queue Polling
        def state_loop():
            while not state_manager.chat_queue.empty():
                msg = state_manager.chat_queue.get_nowait()
                self._add_message(msg["sender"], msg["text"])
            self.status_label.config(text=state_manager.status.upper())
            self.root.after(200, state_loop)

        threading.Thread(target=sensor_loop, daemon=True).start()
        self.root.after(200, state_loop)
        self.root.after(1000, on_ready)
        self.root.mainloop()

def init_gui(on_ready, stop_cb, manual_cb):
    FridayHUD(on_ready, stop_cb, manual_cb)
