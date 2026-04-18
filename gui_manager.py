import tkinter as tk
from tkinter import scrolledtext
import threading
import time
from datetime import datetime
import psutil
import math

class FridayHUD:
    def __init__(self, on_ready_callback, stop_callback, manual_command_callback):
        self.on_ready_callback = on_ready_callback
        self.stop_callback = stop_callback
        self.manual_command_callback = manual_command_callback
        
        self.root = tk.Tk()
        self.root.title("FRIDAY | Neural Link")
        self.root.geometry("450x700")
        self.root.configure(bg="#0a0a12")
        self.root.overrideredirect(True) # Borderless Sci-Fi look
        
        self._setup_ui()
        self._start_monitors()
        self._poll_queue() # Start listening for messages
        
        # Signal that the GUI is ready
        self.root.after(1000, lambda: self.on_ready_callback())
        self.root.mainloop()

    def _poll_queue(self):
        """Checks the state_manager queue for new messages to display."""
        import state_manager
        try:
            while not state_manager.chat_queue.empty():
                msg = state_manager.chat_queue.get_nowait()
                self.update_chat(msg["sender"], msg["text"])
                state_manager.chat_queue.task_done()
            
            # Update status label from state_manager
            self.status_label.config(text=state_manager.status.upper())
        except:
            pass
        self.root.after(200, self._poll_queue)

    def _setup_ui(self):
        # 1. Header
        header = tk.Frame(self.root, bg="#161625", height=40)
        header.pack(fill="x")
        tk.Label(header, text="SYSTEM CORE: FRIDAY", font=("Segoe UI Semibold", 9), bg="#161625", fg="#00f2ff").pack(side="left", padx=15)
        self.status_label = tk.Label(header, text="STANDBY", font=("Consolas", 8), bg="#161625", fg="#555555")
        self.status_label.pack(side="right", padx=15)

        # 2. Neural Wave Visualizer
        self.canvas = tk.Canvas(self.root, height=60, bg="#0a0a12", highlightthickness=0)
        self.canvas.pack(fill="x")
        self._animate_wave(0)

        # 3. Tactical Sensors
        sensor_frame = tk.Frame(self.root, bg="#0a0a12", pady=10)
        sensor_frame.pack(fill="x")
        
        self.sensors = {}
        fields = [("CPU", "#00f2ff"), ("RAM", "#f1c40f"), ("DSK", "#e74c3c"), ("PWR", "#2ecc71")]
        for name, color in fields:
            lbl = tk.Label(sensor_frame, text=f"{name}: --", font=("Consolas", 8, "bold"), bg="#0a0a12", fg=color)
            lbl.pack(side="left", expand=True)
            self.sensors[name] = lbl

        # 4. Chat Area
        self.chat_area = scrolledtext.ScrolledText(self.root, bg="#0d0d17", fg="#e0e0e0", font=("Consolas", 10), 
                                                 state="disabled", relief="flat", padx=15, pady=15, insertbackground="#00f2ff")
        self.chat_area.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.chat_area.tag_config("header", font=("Consolas", 8, "bold"), foreground="#555555")
        self.chat_area.tag_config("user_msg", foreground="#ffffff")
        self.chat_area.tag_config("friday_msg", foreground="#00f2ff")

        # 5. Input Area
        input_frame = tk.Frame(self.root, bg="#0a0a12", pady=10)
        input_frame.pack(fill="x")
        
        self.entry = tk.Entry(input_frame, bg="#161625", fg="#00f2ff", font=("Consolas", 10), relief="flat", insertbackground="#00f2ff")
        self.entry.pack(side="left", fill="x", expand=True, padx=(15, 5), pady=5, ipady=3)
        self.entry.bind("<Return>", lambda e: self._on_send())

        # Silence Button
        tk.Button(input_frame, text="⏹", font=("Consolas", 10, "bold"), bg="#440000", fg="white", 
                  relief="flat", padx=10, command=self.stop_callback).pack(side="left", padx=2)
        
        # Execute Button
        tk.Button(input_frame, text="EXECUTE", font=("Consolas", 8, "bold"), bg="#161625", fg="#00f2ff", 
                  relief="flat", padx=15, command=self._on_send).pack(side="left", padx=(2, 15))

    def _on_send(self):
        text = self.entry.get().strip()
        if text:
            self.stop_callback() # Stop speech on new command
            self.entry.delete(0, tk.END)
            self.manual_command_callback(text)

    def update_chat(self, sender, text):
        self.chat_area.config(state="normal")
        timestamp = datetime.now().strftime("%H:%M")
        tag = "user_msg" if sender == "User" else "friday_msg"
        
        self.chat_area.insert("end", f"[{timestamp}] {sender}:\n", "header")
        self.chat_area.insert("end", f"{text}\n\n", tag)
        self.chat_area.see("end")
        self.chat_area.config(state="disabled")

    def set_status(self, status):
        self.status_label.config(text=status.upper())

    def _animate_wave(self, phase):
        self.canvas.delete("all")
        width = 450
        mid_y = 30
        points = []
        for x in range(0, width, 5):
            y = mid_y + math.sin(x * 0.02 + phase) * 15 + math.sin(x * 0.05 + phase * 1.5) * 5
            points.extend([x, y])
        self.canvas.create_line(points, fill="#00f2ff", smooth=True, width=2)
        self.root.after(50, lambda: self._animate_wave(phase + 0.1))

    def _start_monitors(self):
        def update_sensors():
            while True:
                try:
                    cpu = psutil.cpu_percent()
                    ram = psutil.virtual_memory().percent
                    pwr = psutil.sensors_battery().percent if psutil.sensors_battery() else 100
                    
                    self.sensors["CPU"].config(text=f"CPU: {cpu}%")
                    self.sensors["RAM"].config(text=f"RAM: {ram}%")
                    self.sensors["PWR"].config(text=f"PWR: {pwr}%")
                except: pass
                time.sleep(2)
        threading.Thread(target=update_sensors, daemon=True).start()

# For backward compatibility if needed, but we should use the class
def init_gui(on_ready, stop_cb, manual_cb):
    return FridayHUD(on_ready, stop_cb, manual_cb)
