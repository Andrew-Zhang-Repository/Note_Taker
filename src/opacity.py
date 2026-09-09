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

class OpacityManager:
    def __init__(self, root_app, store):
        self.root = root_app
        self.store = store
        self._opacity_save_timer = None

        self.root.bind_all("<Control-Up>", self.increase_opacity)
        self.root.bind_all("<Control-Down>", self.decrease_opacity)

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
            self.queue_opacity_save(new_alpha, win_type)

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
            self.queue_opacity_save(new_alpha, win_type)

    def queue_opacity_save(self, new_alpha, win_type):
        if self._opacity_save_timer is not None:
            self.root.after_cancel(self._opacity_save_timer)
            
        self._opacity_save_timer = self.root.after(1000, lambda: self.save_opacity_to_disk(new_alpha, win_type))
        
    def save_opacity_to_disk(self, new_alpha, win_type):

        settings = self.store.config_settings
        if "ui_settings" not in settings:
            self.store.config_settings["ui_settings"] = {}
        if win_type not in self.store.config_settings["ui_settings"]:
            self.store.config_settings["ui_settings"][win_type] = {}
            
        self.store.config_settings["ui_settings"][win_type]["opacity"] = new_alpha
        self.store.atomic_save(settings, self.store.config_path)