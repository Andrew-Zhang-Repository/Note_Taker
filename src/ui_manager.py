import tkinter as tk
from tkinter import ttk
from notes_store import note_store
from speech_capture import SpeakerRecorder
from tkinter import simpledialog, messagebox
from capture import make_window_invisible
import threading
import queue
import google.generativeai as genai
import os
from dotenv import load_dotenv



load_dotenv()

class UIManager:
    def __init__(self, root_app, store):
        self.root = root_app
        self.store = store
        self._save_timers = {}

        self.text_colors = ["white", "#10a37f", "#ffd700", "#00ffff", "#ff99cc"]

        self.root.bind_all("<Control-Shift-T>", self.cycle_text_color)

        self.bg_colors = ["#1e1e1e", "#000000", "#111b21", "#1e1b2e", "#faf9fc", "#f81414"]
        self.root.bind_all("<Control-Shift-U>", self.increase_opacity)
        self.root.bind_all("<Control-Shift-D>", self.decrease_opacity)
        self.root.bind_all("<Control-b>", self.cycle_bg_color) 

    def cycle_bg_color(self, event=None):
        if not event: return
        target_win = event.widget.winfo_toplevel()
        win_type = getattr(target_win, "win_type", "main")

        settings = self.store.config_settings.get("ui_settings", {}).get(win_type, {})
        current_bg = settings.get("bg_color", "#1e1e1e")

        try:
            next_index = (self.bg_colors.index(current_bg) + 1) % len(self.bg_colors)
        except ValueError:
            next_index = 0
        new_bg = self.bg_colors[next_index]

        self.apply_bg(target_win, new_bg)
        self.save_setting_to_disk(win_type, "bg_color", new_bg)

    def apply_bg(self, target_win, color):
        for widget in getattr(target_win, "recolor_widgets", []):
            try:
                if widget.winfo_exists():
                    widget.config(bg=color)
            except tk.TclError:
                pass

    def increase_opacity(self, event=None):
        if not event: return
        target_win = event.widget.winfo_toplevel()
        try: current_alpha = float(target_win.attributes("-alpha"))
        except: current_alpha = 1.0 

        if current_alpha < 1.0:
            new_alpha = round(current_alpha + 0.05, 2)
            if new_alpha > 1.0: new_alpha = 1.0
            target_win.attributes("-alpha", new_alpha)
            
            win_type = getattr(target_win, "win_type", "main")
            self.queue_save(win_type, "opacity", new_alpha)

    def decrease_opacity(self, event=None):
        if not event: return
        target_win = event.widget.winfo_toplevel()
        try: current_alpha = float(target_win.attributes("-alpha"))
        except: current_alpha = 1.0
            
        if current_alpha > 0.2:
            new_alpha = round(current_alpha - 0.05, 2)
            if new_alpha < 0.2: new_alpha = 0.2
            target_win.attributes("-alpha", new_alpha)
            
            win_type = getattr(target_win, "win_type", "main")
            self.queue_save(win_type, "opacity", new_alpha)

    def queue_save(self, win_type, setting_key, value):
        timer_id = f"{win_type}_{setting_key}"
        if timer_id in self._save_timers:
            self.root.after_cancel(self._save_timers[timer_id])
            
        self._save_timers[timer_id] = self.root.after(
            1000, lambda: self.save_setting_to_disk(win_type, setting_key, value)
        )
        
    def save_setting_to_disk(self, win_type, setting_key, value):
        settings = self.store.config_settings
        if "ui_settings" not in settings: settings["ui_settings"] = {}
        if win_type not in settings["ui_settings"]: settings["ui_settings"][win_type] = {}
            
        settings["ui_settings"][win_type][setting_key] = value
        self.store.atomic_save(settings, self.store.config_path)


    def cycle_text_color(self, event=None):
        if not event: return
        target_win = event.widget.winfo_toplevel()
        win_type = getattr(target_win, "win_type", "main")
        settings = self.store.config_settings.get("ui_settings", {}).get(win_type, {})
        current_fg = settings.get("text_color", "white")

        try:
            next_index = (self.text_colors.index(current_fg) + 1) % len(self.text_colors)
        except ValueError:
            next_index = 0
        new_fg = self.text_colors[next_index]

        self.apply_fg_recursively(target_win, new_fg)
        self.save_setting_to_disk(win_type, "text_color", new_fg)

        return "break"

    def apply_fg_recursively(self, widget, color):
        try:
          
            if widget.winfo_class() == 'Text':
                widget.config(fg=color,insertbackground=color)
        except:
            pass
        for child in widget.winfo_children():
            if child.winfo_class() == 'Toplevel':
                continue
            self.apply_fg_recursively(child, color)