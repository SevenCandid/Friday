import tkinter as tk
from tkinter import scrolledtext
import threading
import time
from datetime import datetime
import psutil
import math
from . import state_manager
import pystray
from PIL import Image
from .path_helper import get_resource_path

class FridayHUD:
    """Premium Sci-Fi HUD with Neural Wave and Clean Class Logic."""
    def __init__(self, on_ready, stop_cb, manual_cb):
        self.root = tk.Tk()
        self.root.title("SEVEN v2.0 | Neural Intelligence HUD")
        self.root.geometry("700x900")
        self.root.configure(bg="#0f0f17")
        
        self.stop_cb = stop_cb
        self.manual_cb = manual_cb
        
        self._init_styles()
        self._build_ui()
        self._setup_tray()
        
        # Override the X button to minimize to tray
        self.root.protocol("WM_DELETE_WINDOW", self._hide_window)
        
        self._start_loops(on_ready)
        
    def _init_styles(self):
        # Premium Sci-Fi Palette
        self.colors = {
            "bg": "#0f0f17",
            "panel": "#1a1a2e",
            "accent": "#00f2ff", # Cyber Cyan
            "glow": "#00e5ff",
            "text": "#e0e0e0",
            "user": "#ffffff",
            "friday": "#00f2ff",
            "stop": "#550000",
            "warn": "#f39c12"
        }
        self.font_header = ("Orbitron", 11, "bold") 
        self.font_main = ("Consolas", 12)
        self.font_sensor = ("Consolas", 10, "bold")

    def _build_ui(self):
        # 1. Holographic Header
        header = tk.Frame(self.root, bg=self.colors["panel"], height=55)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        tk.Label(header, text="SYSTEM CORE: SEVEN v2.0", font=self.font_header, 
                 bg=self.colors["panel"], fg=self.colors["accent"]).pack(side="left", padx=20)
        
        self.status_label = tk.Label(header, text="STANDBY", font=self.font_sensor, 
                                   bg=self.colors["panel"], fg="#555555")
        self.status_label.pack(side="right", padx=15)
        
        # Remote Link Info
        from . import web_bridge
        remote_url = f"http://{web_bridge.get_local_ip()}:5000"
        link_lbl = tk.Label(header, text=f"REMOTE: {remote_url}", font=self.font_sensor, 
                            bg=self.colors["panel"], fg="#3498db", cursor="hand2")
        link_lbl.pack(side="right", padx=20)
        
        def copy_link(event):
            self.root.clipboard_clear()
            self.root.clipboard_append(remote_url)
            self._add_message("System", "Remote link copied to clipboard.")
            self.status_label.config(text="LINK COPIED", fg=self.colors["accent"])
            self.root.after(2000, lambda: self.status_label.config(text="STANDBY", fg="#555555"))

        link_lbl.bind("<Button-1>", copy_link)

        # 2. NEURAL WAVE VISUALIZER
        self.canvas = tk.Canvas(self.root, height=70, bg=self.colors["bg"], highlightthickness=0)
        self.canvas.pack(fill="x", pady=10)
        self._animate_wave(0)

        # 3. Tactical Sensor Grid
        sensor_frame = tk.Frame(self.root, bg=self.colors["bg"], pady=10)
        sensor_frame.pack(fill="x", padx=20)
        
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
        i_fields = [("NET", "#9b59b6"), ("APPS", "#e67e22"), ("PROCS", "#f1c40f"), ("DSK", "#e74c3c")]
        for name, color in i_fields:
            lbl = tk.Label(row2, text=f"{name}: --", font=self.font_sensor, bg=self.colors["bg"], fg=color)
            lbl.pack(side="left", expand=True)
            self.sensor_labels[name] = lbl

        # 4. Neural Chat Terminal
        self.chat = scrolledtext.ScrolledText(self.root, bg="#12121c", fg=self.colors["text"], 
                                             font=self.font_main, state="disabled", relief="flat", 
                                             padx=20, pady=20, insertbackground=self.colors["accent"])
        
        self.chat.tag_config("meta", foreground="#777777", font=("Consolas", 10))
        self.chat.tag_config("user", foreground=self.colors["user"], spacing1=4)
        self.chat.tag_config("friday", foreground=self.colors["friday"], spacing1=4)
        self.chat.tag_bind("friday", "<Button-1>", lambda e: None) # Placeholder for Seven

        # 5. Tactical Input Console
        input_frame = tk.Frame(self.root, bg=self.colors["bg"], pady=20, padx=20)
        input_frame.pack(side="bottom", fill="x")
        
        self.chat.pack(side="top", fill="both", expand=True, padx=20, pady=10)
        
        self.entry = tk.Entry(input_frame, bg=self.colors["panel"], fg=self.colors["accent"], 
                             font=self.font_main, relief="flat", insertbackground=self.colors["accent"],
                             highlightthickness=1, highlightbackground="#333344", highlightcolor=self.colors["accent"])
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 10), ipady=8)
        self.entry.bind("<Return>", lambda e: self._handle_send())

        # STOP BUTTON
        tk.Button(input_frame, text="⏹", bg=self.colors["stop"], fg="white", 
                  activebackground="#ff0000", relief="flat", padx=15, pady=5, font=self.font_main,
                  command=self.stop_cb).pack(side="left", padx=5)
        
        # STEALTH TOGGLE
        self.stealth_btn = tk.Button(input_frame, text="STEALTH: OFF", bg=self.colors["panel"], fg="#777777", 
                                   activebackground=self.colors["accent"], relief="flat", font=self.font_sensor, 
                                   padx=15, pady=5, command=self._toggle_stealth)
        self.stealth_btn.pack(side="left", padx=5)
        
        # EXECUTE BUTTON
        tk.Button(input_frame, text="EXECUTE", bg=self.colors["accent"], fg="black", 
                  activebackground="#ffffff", relief="flat", font=self.font_sensor, 
                  padx=20, pady=5, command=self._handle_send).pack(side="left")

    def _toggle_stealth(self):
        state_manager.quiet_mode = not state_manager.quiet_mode
        self._update_stealth_ui()
        status = "ENABLED" if state_manager.quiet_mode else "DISABLED"
        self._add_message("System", f"Stealth Mode {status}.")

    def _update_stealth_ui(self):
        if state_manager.quiet_mode:
            self.stealth_btn.config(text="STEALTH: ON", bg=self.colors["accent"], fg="black")
            self.status_label.config(text="STEALTH ACTIVE", fg=self.colors["accent"])
        else:
            self.stealth_btn.config(text="STEALTH: OFF", bg=self.colors["panel"], fg="#777777")
            self.status_label.config(text="STANDBY", fg="#555555")

    def _setup_tray(self):
        """Initializes the System Tray icon."""
        try:
            icon_path = get_resource_path("seven.ico")
            image = Image.open(icon_path)
            
            menu = (
                pystray.MenuItem("Show HUD", self._show_window, default=True),
                pystray.MenuItem("Exit SEVEN", self._quit_app)
            )
            self.tray_icon = pystray.Icon("SEVEN", image, "SEVEN AI Assistant", menu)
            threading.Thread(target=self.tray_icon.run, daemon=True, name="TrayThread").start()
        except Exception as e:
            print(f"[GUI] System Tray failed to initialize: {e}")

    def _hide_window(self):
        self.root.withdraw()

    def _show_window(self, icon=None, item=None):
        self.root.after(0, self.root.deiconify)
        self.root.after(0, self.root.lift)
        self.root.after(0, self.root.focus_force)

    def _quit_app(self, icon=None, item=None):
        if hasattr(self, 'tray_icon') and self.tray_icon:
            self.tray_icon.stop()
        self.root.quit()
        self.root.destroy()
        import os
        os._exit(0)

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
        sender_name = "SEVEN" if sender == "Friday" else sender
        
        self.chat.insert("end", f"--- {sender_name} @ {time_str} ---\n", "meta")
        self.chat.insert("end", f"{text}\n\n", tag)
        self.chat.see("end")
        self.chat.config(state="disabled")

    def _animate_wave(self, phase):
        self.canvas.delete("all")
        width = 700
        mid_y = 35
        reactivity = 1.0 + (state_manager.audio_energy * 2.5)
        points_main = []
        points_bg = []
        
        for x in range(0, width, 5):
            y1 = mid_y + (math.sin(x * 0.02 + phase) * 18 + math.sin(x * 0.06 + phase * 1.2) * 8) * reactivity
            points_main.extend([x, y1])
            y2 = mid_y + (math.sin(x * 0.015 - phase) * 12 + math.sin(x * 0.04 - phase * 0.8) * 10) * reactivity
            points_bg.extend([x, y2])
            
        self.canvas.create_line(points_bg, fill="#005577", smooth=True, width=1.5)
        self.canvas.create_line(points_main, fill=self.colors["accent"], smooth=True, width=3)
        self.canvas.create_line(points_main, fill=self.colors["accent"], smooth=True, width=3)
        self.canvas.create_line(points_main, fill=self.colors["accent"], smooth=True, width=3)
        
        self.root.after(40, lambda: self._animate_wave(phase + 0.1))

    def _start_loops(self, on_ready):
        def sensor_loop():
            while True:
                try:
                    net_info = "OFFLINE"
                    try:
                        import subprocess
                        creationflags = 0
                        if hasattr(subprocess, 'CREATE_NO_WINDOW'):
                            creationflags = subprocess.CREATE_NO_WINDOW
                        results = subprocess.check_output(["netsh", "wlan", "show", "interfaces"], 
                                                        text=True, stderr=subprocess.DEVNULL, creationflags=creationflags)
                        for line in results.split("\n"):
                            if "SSID" in line and "BSSID" not in line:
                                net_info = line.split(":")[1].strip()
                                break
                        if net_info == "OFFLINE":
                            import socket
                            socket.create_connection(("8.8.8.8", 53), timeout=1)
                            net_info = "CONNECTED"
                    except:
                        net_info = "DISCONNECTED"
                    
                    app_count = state_manager.app_count
                    proc_count = len(psutil.pids())

                    stats = {
                        "CPU": f"{psutil.cpu_percent()}%",
                        "RAM": f"{psutil.virtual_memory().percent}%",
                        "DSK": f"{psutil.disk_usage('/').percent}%",
                        "PWR": f"{psutil.sensors_battery().percent if psutil.sensors_battery() else 100}%",
                        "NET": net_info,
                        "APPS": str(app_count),
                        "PROCS": str(proc_count)
                    }
                    for k, v in stats.items():
                        self.sensor_labels[k].config(text=f"{k}: {v}")
                except: pass
                time.sleep(2)
        
        def state_loop():
            while not state_manager.chat_queue.empty():
                msg = state_manager.chat_queue.get_nowait()
                self._add_message(msg["sender"], msg["text"])
            self.status_label.config(text=state_manager.status.upper())
            self._update_stealth_ui()
            self.root.after(200, state_loop)

        threading.Thread(target=sensor_loop, daemon=True).start()
        self.root.after(200, state_loop)
        self.root.after(1000, on_ready)
        self.root.mainloop()

def init_gui(on_ready, stop_cb, manual_cb):
    FridayHUD(on_ready, stop_cb, manual_cb)
