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
from llm_overlay import Theme, ResizableWindowMixin, LLMWindow
from pop_out_overlay import PopOutNote
from ui_manager import UIManager

load_dotenv()





class OverlayWindow(tk.Tk, ResizableWindowMixin):

    # Position margins
    SCREEN_MARGIN = 20
    TASKBAR_HEIGHT = 60

    # Nudge distance in pixels
    NUDGE_DISTANCE = 20

    def __init__(self):
        super().__init__()

        self._init_drag_state()
        self.title("Overlay")
        self.geometry("400x500+100+100")
        self.configure(bg=Theme.BG)

        self.overrideredirect(True)
        self.attributes("-topmost", True)

        self.model = None
        self.model_name = None
        self.llm_win = None
        self.move_window()

        make_window_invisible(self)

    def move_window(self):

        self.main_container = tk.Frame(self, bg=Theme.BG)
        self.main_container.pack(fill=tk.BOTH, expand=True)

        left_edge = tk.Frame(self.main_container, width=self.EDGE_SIZE, bg=Theme.BG, cursor="size_we")
        left_edge.pack(side=tk.LEFT, fill=tk.Y)
        self._bind_resize_edge(left_edge, "w")

        right_edge = tk.Frame(self.main_container, width=self.EDGE_SIZE, bg=Theme.BG, cursor="size_we")
        right_edge.pack(side=tk.RIGHT, fill=tk.Y)
        self._bind_resize_edge(right_edge, "e")

        self.inner_container = tk.Frame(self.main_container, bg=Theme.BG)
        self.inner_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        top_edge = tk.Frame(self.inner_container, height=self.EDGE_SIZE, bg=Theme.BG, cursor="size_ns")
        top_edge.pack(fill=tk.X, side=tk.TOP)
        self._bind_resize_edge(top_edge, "n")

        self.title_bar = tk.Frame(self.inner_container, bg=Theme.BG, height=28)
        self.title_bar.pack(fill=tk.X, side=tk.TOP)
        self.title_bar.pack_propagate(False)
        self._bind_drag(self.title_bar)

        self.close_btn = tk.Button(
            self.title_bar, text=" X ", bg=Theme.BAR_BG, fg=Theme.FG, bd=0,
            activebackground=Theme.BUTTON_BG, activeforeground=Theme.FG, command=self.destroy,
        )
        self.close_btn.pack(side=tk.RIGHT, padx=4, pady=2)

        resize_frame = tk.Frame(self.inner_container, bg=Theme.BG, height=self.EDGE_SIZE + 6, cursor="size_nw_se")
        resize_frame.pack(fill=tk.X, side=tk.BOTTOM)
        self._bind_resize_edge(resize_frame, "se")

        self.content_frame = tk.Frame(self.inner_container, bg=Theme.CONTENT_BG)
        self.content_frame.pack(expand=True, fill="both", padx=5, pady=5)

        self.recolor_widgets = [self, self.main_container, left_edge, right_edge,
                                self.inner_container, top_edge, resize_frame]

        self.notes_ui_management()

    def notes_ui_management(self):
        self.store = note_store()
        
        settings = self.store.config_settings.get("ui_settings", {}).get("main", {})
                
        saved_opacity = settings.get("opacity", 0.85)
        self.attributes("-alpha", saved_opacity)

        self.win_type = "main"
        self.ui_manager = UIManager(self, self.store)

        saved_bg = settings.get("bg_color", "#1e1e1e")
        self.ui_manager.apply_bg(self, saved_bg)

        

        if self.store.config.get("types"):
            self.active_type = self.store.config["types"][0]

        self.current_notes = []
        self.active_note_id = None

        top_bar = tk.Frame(self.content_frame, bg=Theme.CONTENT_BG)
        top_bar.pack(fill=tk.X, pady=5)

        self.type_combo = ttk.Combobox(top_bar, values=self.store.config.get("types", []), state="readonly")
        self.type_combo.set(self.active_type)
        self.type_combo.pack(side=tk.LEFT, padx=5)
        self.type_combo.bind("<<ComboboxSelected>>", self.on_type_change)

        new_btn = tk.Button(top_bar, text="+ New Note", bg=Theme.BAR_BG, fg=Theme.FG, bd=0, command=self.create_new_note,cursor="hand2")
        new_btn.pack(side=tk.RIGHT, padx=5)

        self.note_listbox = tk.Listbox(self.content_frame, height=5, bg=Theme.BG, fg=Theme.FG, bd=0)
        self.note_listbox.pack(fill=tk.X, padx=5, pady=5)
        self.note_listbox.bind("<<ListboxSelect>>", self.on_note_select)

        self.delete_btn = tk.Button(top_bar, text="Delete", bg=Theme.BUTTON_BG, fg=Theme.FG, bd=0, command=self.delete_note, cursor="hand2")
        self.delete_btn.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        self.ai_btn = tk.Button(self.content_frame, text="Ask AI", bg="#737575", fg=Theme.FG, bd=0, command=self.open_llm_window, cursor="hand2")
        self.ai_btn.pack(side=tk.BOTTOM, fill=tk.X, expand=True, padx=(2, 2))

        self.save_btn = tk.Button(self.content_frame, text="Save Note", bg=Theme.BUTTON_BG, fg=Theme.FG, bd=0, command=self.save_note, cursor="hand2")
        self.save_btn.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)

        self.save_btn = tk.Button(self.content_frame, text="Pop Out Note", bg=Theme.BUTTON_BG, fg=Theme.FG, bd=0, command=self.pop_out_note, cursor="hand2")
        self.save_btn.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        self.editor = tk.Text(self.content_frame, bg=Theme.BG, fg=Theme.FG, bd=0, wrap=tk.WORD, insertbackground="white")
        self.editor.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)


        text_color = settings.get("text_color", "#1e1e1e")
        self.ui_manager.apply_fg_recursively(self, text_color)
        
        self.refresh_note_list()

    def refresh_note_list(self):

        self.note_listbox.delete(0, tk.END)
        self.current_notes = self.store.read_note(self.active_type)

        for note in self.current_notes:
            self.note_listbox.insert(tk.END, note["title"])

    def on_type_change(self, event):
        self.active_type = self.type_combo.get()
        self.editor.delete("1.0", tk.END)
        self.active_note_id = None
        self.refresh_note_list()

    def create_new_note(self):

        note_title = simpledialog.askstring("New Note", "Enter a title for your new note:")

        # Search for duplicates
        if note_title:
            for note in self.current_notes:
                if note["title"].lower() == note_title.lower():
                    messagebox.showwarning("Duplicate Name", f"A note named '{note_title}' already exists in this folder.")
                    return

            self.store.add_note(self.active_type, note_title, "")
            self.refresh_note_list()

    def on_note_select(self, event):
        selection = self.note_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        selected_note = self.current_notes[index]
        self.active_note_id = selected_note["id"]

        self.editor.delete("1.0", tk.END)
        self.editor.insert(tk.END, selected_note["note_body"])

    def save_note(self):
        if not self.active_note_id:
            return

        new_text = self.editor.get("1.0", tk.END).strip()
        self.store.update_note(self.active_note_id, self.active_type, new_text)

        for note in self.current_notes:
            if note["id"] == self.active_note_id:
                note["note_body"] = new_text
                break

        self.save_btn.config(text="Saved!")
        self.after(2000, lambda: self.save_btn.config(text="Save Note"))

    def delete_note(self):

        if not self.active_note_id:
            return

        confirm = messagebox.askyesno("Delete Note", "Are you sure you want to delete this note? This cannot be undone.")

        if confirm:
            self.store.delete_note(self.active_note_id, self.active_type)
            self.active_note_id = None
            self.editor.delete("1.0", tk.END)
            self.refresh_note_list()

    def _get_model(self):
        if self.model is None:
            genai.configure(api_key=os.getenv("key"))
            self.model_name = os.getenv("default_model") or "AI"
            self.model = genai.GenerativeModel(self.model_name)
        return self.model

    def open_llm_window(self):
        if self.llm_win is not None and self.llm_win.winfo_exists():
            self.llm_win.lift()
            self.llm_win.focus_force()
            return

        self._get_model()
        self.llm_win = LLMWindow(self, self.model,self.store, self.ui_manager, self.model_name)


    def pop_out_note(self):
        if not getattr(self, 'open_popouts', None):
            self.open_popouts = {} 

        if not self.active_note_id:
            return

        note_id = self.active_note_id

        if note_id in self.open_popouts and self.open_popouts[note_id].winfo_exists():
            self.open_popouts[note_id].lift()
            return

        selected_note = next((n for n in self.current_notes if n["id"] == note_id), None)
        if not selected_note:
            return

        pop_win = PopOutNote(
            main_app=self, 
            note_id=note_id, 
            title=selected_note['title'], 
            body=selected_note.get("note_body", ""), 
            active_type=self.active_type,
            store = self.store,
            UIManager = self.ui_manager
        )
        
        self.open_popouts[note_id] = pop_win


if __name__ == "__main__":
    app = OverlayWindow()
    app.mainloop()
