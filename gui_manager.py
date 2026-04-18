import tkinter as tk
from tkinter import messagebox, scrolledtext
import threading
import pystray
from PIL import Image, ImageDraw
import sys
import os
import winreg
import state_manager
import memory_manager
import datetime
import psutil
import subprocess
import re

# Internal state
_root = None
_status_label = None
_chat_area = None
_input_field = None
_icon = None

# Dashboard Labels
_cpu_label = None
_ram_label = None
_disk_label = None
_battery_label = None
_net_label = None 
_apps_label = None # NEW: Apps indexed label

def _get_network_info():
    """Retrieves the current network name (WiFi or Ethernet)."""
    try:
        import subprocess
        # Try WiFi first
        result = subprocess.check_output("netsh wlan show interfaces", shell=True, stderr=subprocess.DEVNULL).decode()
        for line in result.split("\n"):
            if " SSID" in line and " BSSID" not in line:
                return line.split(":")[1].strip()
        
        # Fallback to general network interfaces if no WiFi
        import psutil
        addrs = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
        for interface, snics in addrs.items():
            if stats.get(interface) and stats[interface].isup and "Loopback" not in interface:
                return interface[:15] # Return first 15 chars of interface name
                
        return "Disconnected"
    except:
        return "Offline"

def _get_color(value):
    """Returns color based on resource usage percentage."""
    if value < 60: return "#2ecc71" # Green
    if value < 85: return "#f39c12" # Orange
    return "#e74c3c" # Red

def _update_dashboard():
    """Polls system stats and updates dashboard labels."""
    try:
        if _root is None: return

        # 1. CPU
        try:
            cpu = psutil.cpu_percent()
            _cpu_label.config(text=f"CPU: {cpu}%", fg=_get_color(cpu))
        except: pass

        # 2. RAM
        try:
            ram = psutil.virtual_memory().percent
            _ram_label.config(text=f"RAM: {ram}%", fg=_get_color(ram))
        except: pass

        # 3. Disk
        try:
            disk = psutil.disk_usage('/').percent
            _disk_label.config(text=f"Disk: {disk}%", fg=_get_color(disk))
        except: pass

        # 4. Battery
        try:
            batt = psutil.sensors_battery()
            if batt:
                b_text = f"Batt: {int(batt.percent)}%"
                if batt.power_plugged: b_text += " ⚡"
                _battery_label.config(text=b_text, fg=_get_color(100 - batt.percent if not batt.power_plugged else 0))
        except: pass

        # 5. Network (Moved up for priority)
        try:
            ssid = _get_network_info()
            _net_label.config(text=f"Net: {ssid}", fg="#2ecc71" if ssid != "Disconnected" and ssid != "Offline" else "#e74c3c")
        except: pass

        # 6. Apps Indexed
        try:
            from skills import app_launcher
            count = app_launcher.get_app_count()
            _apps_label.config(text=f"Apps: {count}")
        except:
            if _apps_label: _apps_label.config(text="Apps: 0")
            
    except Exception as e:
        print(f"[GUI Dashboard Error] {e}")
        
    # Schedule next update in 2 seconds
    if _root:
        _root.after(2000, _update_dashboard)

def set_autostart(enabled=True):
    """Sets or removes Friday from the Windows Registry startup key."""
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        if enabled:
            if hasattr(sys, '_MEIPASS'):
                # When running as EXE
                app_path = f'"{sys.executable}"'
            else:
                # When running as script (console mode)
                # We use the absolute path to main.py to ensure it works from any directory
                script_path = os.path.abspath(sys.modules['__main__'].__file__)
                app_path = f'"{sys.executable}" "{script_path}"'
            
            winreg.SetValueEx(key, "FridayAssistant", 0, winreg.REG_SZ, app_path)
            print(f"[System] Autostart enabled: {app_path}")
        else:
            try:
                winreg.DeleteValue(key, "FridayAssistant")
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
    except Exception as e:
        print(f"[System Error] Failed to set autostart: {e}")

def create_tray_icon(show_callback, hide_callback, exit_callback):
    """Creates a system tray icon with Show/Hide/Exit options."""
    image = Image.new('RGBA', (64, 64), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((8, 8, 56, 56), fill=(70, 130, 180), outline=(255, 255, 255))
    
    menu = pystray.Menu(
        pystray.MenuItem("Show Window", show_callback),
        pystray.MenuItem("Hide Window", hide_callback),
        pystray.MenuItem("Exit", exit_callback)
    )
    
    icon = pystray.Icon("Friday", image, "Friday Assistant", menu)
    return icon

def _poll_status():
    """Continuously polls state_manager for status updates."""
    if _status_label:
        current_status = state_manager.status
        if state_manager.alarm_ringing:
            current_status = "ALARM RINGING!"
            _status_label.config(fg="red")
        else:
            _status_label.config(fg="#555555")
        _status_label.config(text=current_status)
    
    # Also poll the chat queue here
    _poll_chat()
    
    if _root:
        _root.after(100, _poll_status)

def _poll_chat():
    """Pulls messages from state_manager and displays them in the UI."""
    try:
        while True:
            msg = state_manager.chat_queue.get_nowait()
            display_message(msg['sender'], msg['text'])
    except:
        pass

def display_message(sender, text):
    """Formats and displays a message in the chat area."""
    if not _chat_area:
        return
    
    _chat_area.config(state=tk.NORMAL)
    timestamp = datetime.datetime.now().strftime("%H:%M")
    
    if sender == "User":
        tag = "user_msg"
        header = f"[{timestamp}] You:\n"
    else:
        tag = "friday_msg"
        header = f"[{timestamp}] Friday:\n"
    
    _chat_area.insert(tk.END, header, "header")
    _chat_area.insert(tk.END, f"{text}\n\n", tag)
    _chat_area.see(tk.END)
    _chat_area.config(state=tk.DISABLED)

def start_gui(on_ready_callback, on_exit_callback, manual_command_callback):
    """Initializes the Sci-Fi HUD interface."""
    global _root, _status_label, _chat_area, _input_field, _icon
    
    _root = tk.Tk()
    _root.title("FRIDAY | Neural Link")
    _root.geometry("450x650")
    _root.configure(bg="#0a0a12") # Deep Space Background
    
    # Window protocols
    def hide_window():
        _root.withdraw()
    def show_window():
        _root.deiconify()
        _root.lift()
    _root.protocol("WM_DELETE_WINDOW", hide_window)
    
    # Header - Holographic Style
    header_frame = tk.Frame(_root, bg="#161625", height=50)
    header_frame.pack(fill=tk.X)
    header_frame.pack_propagate(False)
    
    tk.Label(header_frame, text="SYSTEM CORE: FRIDAY", font=("Segoe UI Semibold", 10), bg="#161625", fg="#00f2ff").pack(side=tk.LEFT, padx=15)
    _status_label = tk.Label(header_frame, text="STANDBY", font=("Consolas", 9), bg="#161625", fg="#555555")
    _status_label.pack(side=tk.RIGHT, padx=15)
    
    # Dashboard Panel (Two-Row Sci-Fi Layout)
    dash_frame_1 = tk.Frame(_root, bg="#0a0a12", height=25)
    dash_frame_1.pack(fill=tk.X, pady=(10, 2))
    
    dash_frame_2 = tk.Frame(_root, bg="#0a0a12", height=25)
    dash_frame_2.pack(fill=tk.X, pady=(0, 10))
    
    global _cpu_label, _ram_label, _disk_label, _battery_label, _net_label, _apps_label
    font_style = ("Consolas", 8, "bold")
    
    # Row 1: Hardware HUD
    _cpu_label = tk.Label(dash_frame_1, text="CPU: --%", font=font_style, bg="#0a0a12", fg="#00f2ff")
    _cpu_label.pack(side=tk.LEFT, expand=True)
    
    _ram_label = tk.Label(dash_frame_1, text="RAM: --%", font=font_style, bg="#0a0a12", fg="#f1c40f")
    _ram_label.pack(side=tk.LEFT, expand=True)
    
    _disk_label = tk.Label(dash_frame_1, text="DSK: --%", font=font_style, bg="#0a0a12", fg="#e67e22")
    _disk_label.pack(side=tk.LEFT, expand=True)
    
    _battery_label = tk.Label(dash_frame_1, text="PWR: --%", font=font_style, bg="#0a0a12", fg="#e74c3c")
    _battery_label.pack(side=tk.LEFT, expand=True)

    # Row 2: Intelligence HUD
    _net_label = tk.Label(dash_frame_2, text="NET: OFFLINE", font=font_style, bg="#0a0a12", fg="#00f2ff")
    _net_label.pack(side=tk.LEFT, expand=True)
    
    _apps_label = tk.Label(dash_frame_2, text="APPS: --", font=font_style, bg="#0a0a12", fg="#9b59b6")
    _apps_label.pack(side=tk.LEFT, expand=True)
    
    # Chat Display Area - Terminal Style
    _chat_area = scrolledtext.ScrolledText(_root, bg="#0d0d17", fg="#e0e0e0", font=("Consolas", 10), state=tk.DISABLED, relief=tk.FLAT, padx=15, pady=15, insertbackground="#00f2ff")
    _chat_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
    
    # Chat Styling Tags
    _chat_area.tag_config("header", font=("Consolas", 8, "bold"), foreground="#555555")
    _chat_area.tag_config("user_msg", foreground="#ffffff", spacing1=2, lmargin1=10, lmargin2=10)
    _chat_area.tag_config("friday_msg", foreground="#00f2ff", spacing1=2, lmargin1=10, lmargin2=10)

    # Input Area - Tactical Entry
    input_frame = tk.Frame(_root, bg="#0a0a12", pady=10)
    input_frame.pack(fill=tk.X)
    
    _input_field = tk.Entry(input_frame, bg="#161625", fg="#00f2ff", font=("Consolas", 10), relief=tk.FLAT, insertbackground="#00f2ff")
    _input_field.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(15, 5), pady=5, ipady=3)
    
    def on_send():
        text = _input_field.get().strip()
        if text:
            _input_field.delete(0, tk.END)
            manual_command_callback(text)
            
    send_btn = tk.Button(input_frame, text="EXECUTE", font=("Consolas", 8, "bold"), bg="#161625", fg="#00f2ff", activebackground="#00f2ff", activeforeground="#0a0a12", relief=tk.FLAT, padx=15, command=on_send)
    send_btn.pack(side=tk.RIGHT, padx=(5, 15))
    
    _input_field.bind("<Return>", lambda e: on_send())

    # Tray Initialization
    def exit_all():
        if _icon: _icon.stop()
        _root.destroy()
        on_exit_callback()
        os._exit(0)

    _icon = create_tray_icon(show_window, hide_window, exit_all)
    threading.Thread(target=_icon.run, daemon=True).start()

    # STARTUP SEQUENCE
    try:
        set_autostart(True) # Ensure Friday wakes up with Windows
    except:
        pass
        
    # We no longer withdraw() here so the window opens visibly as requested
    _root.deiconify()
    _root.lift()
    _root.focus_force()
    
    _root.after(100, _poll_status)
    _root.after(500, _update_dashboard)
    _root.after(1000, on_ready_callback) # Signal that we are ready to greet
    
    _root.mainloop()
