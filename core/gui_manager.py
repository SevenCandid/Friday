import tkinter as tk
from tkinter import scrolledtext
import threading
import time
import random
from datetime import datetime
import psutil
import math
from . import state_manager
import pystray
from PIL import Image
from .path_helper import get_resource_path

class SevenHUD:
    """Premium Sci-Fi HUD with Neural Wave and Clean Class Logic."""
    def __init__(self, on_ready, stop_cb, manual_cb):
        self.root = tk.Tk()
        self.root.title("SEVEN v1.0 | Neural Intelligence HUD")
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
            "seven": "#00f2ff",
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

        # 2. DUAL NEURAL WAVE VISUALIZER
        wave_panel = tk.Frame(self.root, bg=self.colors["bg"])
        wave_panel.pack(fill="x", padx=15, pady=(10, 5))

        # --- Listening Wave (User Voice) ---
        listen_frame = tk.Frame(wave_panel, bg="#0d1117", highlightbackground="#00ff88", highlightthickness=1)
        listen_frame.pack(fill="x", pady=(0, 4))
        tk.Label(listen_frame, text="🎙️ LISTENING", font=("Consolas", 8, "bold"),
                 bg="#0d1117", fg="#00ff88").pack(anchor="w", padx=8, pady=(4, 0))
        self.listen_canvas = tk.Canvas(listen_frame, height=50, bg="#0d1117", highlightthickness=0)
        self.listen_canvas.pack(fill="x", padx=4, pady=(0, 4))

        # --- Talking Wave (SEVEN Voice) ---
        talk_frame = tk.Frame(wave_panel, bg="#0d1117", highlightbackground="#00d2ff", highlightthickness=1)
        talk_frame.pack(fill="x", pady=(4, 0))
        tk.Label(talk_frame, text="🔊 SEVEN", font=("Consolas", 8, "bold"),
                 bg="#0d1117", fg="#00d2ff").pack(anchor="w", padx=8, pady=(4, 0))
        self.talk_canvas = tk.Canvas(talk_frame, height=50, bg="#0d1117", highlightthickness=0)
        self.talk_canvas.pack(fill="x", padx=4, pady=(0, 4))

        # State for wave animation
        self._wave_phase = 0.0
        self._talk_intensity = 0.0
        self._talk_bars = [0.0] * 40
        self._animate_dual_wave()

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
        self.chat.tag_config("seven", foreground=self.colors["seven"], spacing1=4)
        self.chat.tag_bind("seven", "<Button-1>", lambda e: None)

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
        tag = "user" if sender == "User" else "seven"
        sender_name = sender
        
        self.chat.insert("end", f"--- {sender_name} @ {time_str} ---\n", "meta")
        self.chat.insert("end", f"{text}\n\n", tag)
        self.chat.see("end")
        self.chat.config(state="disabled")

    def _animate_dual_wave(self):
        """Renders both the Listening and Talking waves at ~25fps."""
        self._wave_phase += 0.08
        phase = self._wave_phase

        # ─── LISTENING WAVE (reactive to mic energy) ───
        self.listen_canvas.delete("all")
        lw = self.listen_canvas.winfo_width() or 660
        lh = 50
        mid_y = lh / 2
        energy = min(state_manager.audio_energy, 1.5)
        reactivity = 0.3 + (energy * 3.0)

        # Background glow wave
        pts_bg = []
        for x in range(0, lw, 4):
            y = mid_y + (math.sin(x * 0.015 - phase * 0.7) * 8 + math.sin(x * 0.04 - phase) * 5) * reactivity
            pts_bg.extend([x, y])
        if len(pts_bg) >= 4:
            self.listen_canvas.create_line(pts_bg, fill="#004d33", smooth=True, width=1)

        # Main voice wave
        pts_main = []
        for x in range(0, lw, 4):
            y = mid_y + (math.sin(x * 0.025 + phase) * 12 + math.sin(x * 0.07 + phase * 1.3) * 6) * reactivity
            pts_main.extend([x, y])
        if len(pts_main) >= 4:
            self.listen_canvas.create_line(pts_main, fill="#00ff88", smooth=True, width=2)

        # Energy indicator bar
        bar_w = int(lw * min(energy, 1.0))
        if bar_w > 0:
            self.listen_canvas.create_rectangle(0, lh - 3, bar_w, lh, fill="#00ff88", outline="")

        # ─── TALKING WAVE (neural pulse bars) ───
        self.talk_canvas.delete("all")
        tw = self.talk_canvas.winfo_width() or 660
        th = 50
        is_talking = state_manager.is_speaking
        num_bars = len(self._talk_bars)
        bar_width = max(tw // num_bars, 2)
        gap = 2

        # Animate bar heights
        for i in range(num_bars):
            if is_talking:
                # Generate lively, semi-random bar heights when speaking
                target = 0.3 + 0.7 * abs(math.sin(phase * 2.5 + i * 0.8)) * random.uniform(0.5, 1.0)
                self._talk_bars[i] += (target - self._talk_bars[i]) * 0.35
            else:
                # Decay to a gentle idle pulse
                idle = 0.08 + 0.05 * abs(math.sin(phase * 0.5 + i * 0.3))
                self._talk_bars[i] += (idle - self._talk_bars[i]) * 0.15

        for i, h in enumerate(self._talk_bars):
            x1 = i * bar_width + gap
            x2 = x1 + bar_width - gap
            bar_h = int(h * (th - 6))
            y1 = (th - bar_h) // 2
            y2 = y1 + bar_h

            # Color gradient: cyan when idle, bright cyan-white when talking
            if is_talking:
                intensity = int(min(h * 255, 255))
                color = f"#{intensity:02x}ff{255:02x}"
            else:
                color = "#1a3a4a"

            self.talk_canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")

        self.root.after(40, self._animate_dual_wave)

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
    SevenHUD(on_ready, stop_cb, manual_cb)
