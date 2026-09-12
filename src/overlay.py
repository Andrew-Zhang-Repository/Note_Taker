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
from rich_text import RichTextMixin
from pathlib import Path
load_dotenv()





class OverlayWindow(tk.Toplevel, ResizableWindowMixin, RichTextMixin):

    # Position margins
    SCREEN_MARGIN = 20
    TASKBAR_HEIGHT = 60

    # Nudge distance in pixels
    NUDGE_DISTANCE = 20

    def __init__(self, master=None):
        super().__init__(master)

        self._init_drag_state()
        self.title("Overlay")
        self.geometry("400x500+100+100")
        self.configure(bg=Theme.BG)

        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-toolwindow", True)


        self.bind_all("<Control-Shift-X>", lambda event: self.quit_app())

        self.model = None
        self.model_name = None
        self.llm_win = None
        self.move_window()
        make_window_invisible(self)

    def quit_app(self):
        if self.master:
            self.master.destroy()
        else:
            self.destroy()

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
            activebackground=Theme.BUTTON_BG, activeforeground=Theme.FG, command=self.quit_app,
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


    def get_available_types(self):
        types = []
        if os.path.exists(self.store.types_dir):
            for filename in os.listdir(self.store.types_dir):
                if filename.endswith(".json"):
                    # Remove the ".json" part so it looks clean in the dropdown
                    types.append(filename[:-5]) 
        return types

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

        # Folders Toolbar
        folders_frame = tk.Frame(self.content_frame, bg=Theme.CONTENT_BG)
        folders_frame.pack(fill=tk.X, pady=(0, 5))

        self.type_combo = ttk.Combobox(folders_frame, values=self.get_available_types(), state="readonly")
        self.type_combo.set(self.active_type)
        self.type_combo.pack(side=tk.LEFT, padx=(0, 5), expand=True, fill=tk.X)
        self.type_combo.bind("<<ComboboxSelected>>", self.on_type_change)

        new_folder_btn = tk.Button(folders_frame, text="New Folder", bg=Theme.BUTTON_BG, fg=Theme.FG, bd=0, command=self.new_type, cursor="hand2")
        new_folder_btn.pack(side=tk.RIGHT)

        # Notes Toolbar
        notes_frame = tk.Frame(self.content_frame, bg=Theme.CONTENT_BG)
        notes_frame.pack(fill=tk.X, pady=(0, 5))

        new_btn = tk.Button(notes_frame, text="+ New Note", bg=Theme.BAR_BG, fg=Theme.FG, bd=0, command=self.create_new_note, cursor="hand2")
        new_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.delete_btn = tk.Button(notes_frame, text="Delete Note", bg=Theme.BUTTON_BG, fg=Theme.FG, bd=0, command=self.delete_note, cursor="hand2")
        self.delete_btn.pack(side=tk.LEFT)

        pop_out_btn = tk.Button(notes_frame, text="Pop Out", bg=Theme.BUTTON_BG, fg=Theme.FG, bd=0, command=self.pop_out_note, cursor="hand2")
        pop_out_btn.pack(side=tk.RIGHT)

        # Notes Listbox
        self.note_listbox = tk.Listbox(self.content_frame, height=5, bg=Theme.BG, fg=Theme.FG, bd=0)
        self.note_listbox.pack(fill=tk.X, pady=(0, 5))
        self.note_listbox.bind("<<ListboxSelect>>", self.on_note_select)

        # Bottom Actions Toolbar
        actions_frame = tk.Frame(self.content_frame, bg=Theme.CONTENT_BG)
        actions_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 0))

        self.ai_btn = tk.Button(actions_frame, text="Ask AI", bg="#737575", fg=Theme.FG, bd=0, command=self.open_llm_window, cursor="hand2")
        self.ai_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))

        delete_pics_btn = tk.Button(actions_frame, text="Clean Images", bg=Theme.BUTTON_BG, fg=Theme.FG, bd=0, command=self.wipe_all_pics, cursor="hand2")
        delete_pics_btn.pack(side=tk.RIGHT)

        # Text Editor
        self.editor = tk.Text(self.content_frame, bg=Theme.BG, fg=Theme.FG, bd=0, wrap=tk.WORD, insertbackground="white", state=tk.DISABLED)
        self._auto_save_timer = None
        self.editor.pack(fill=tk.BOTH, expand=True)
        self._init_rich_text(self.editor)


        text_color = settings.get("text_color", "#1e1e1e")
        self.ui_manager.apply_fg_recursively(self, text_color)

        self.refresh_note_list()

    def refresh_note_list(self):

        self.note_listbox.delete(0, tk.END)
        self.current_notes = self.store.read_note(self.active_type)

        for note in self.current_notes:
            self.note_listbox.insert(tk.END, note["title"])

    def _set_editor_enabled(self, enabled):
        self.editor.configure(state=tk.NORMAL if enabled else tk.DISABLED)

    def on_type_change(self, event):
        self.active_type = self.type_combo.get()
        self.rt_load("")
        self.active_note_id = None
        self._set_editor_enabled(False)
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

    def rt_notify_change(self):
        self.save_note()

    def on_note_select(self, event):
        selection = self.note_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        selected_note = self.current_notes[index]
        self.active_note_id = selected_note["id"]

        self.rt_load(selected_note["note_body"])
        self._set_editor_enabled(True)

    def save_note(self, event = None):
       
        if self._auto_save_timer is not None:
            self.after_cancel(self._auto_save_timer)
            
        self._auto_save_timer = self.after(1500, self.perform_auto_save)

    def perform_auto_save(self):
        if not self.active_note_id:
            return

        new_text = self.rt_get_text()
        self.store.update_note(self.active_note_id, self.active_type, new_text)

        for note in self.current_notes:
            if note["id"] == self.active_note_id:
                note["note_body"] = new_text
                break

    def new_type(self):

        confirm = simpledialog.askstring("New Category", "Enter New Type Name:")
        if confirm:
            success = self.store.create_new_type(confirm)

            if success:
                updated_types = self.get_available_types()
                self.type_combo["values"] = updated_types
                self.type_combo.set(success)
                self.active_type = success
                self.active_note_id = None
                self.rt_load("")
                self._set_editor_enabled(False)
                self.refresh_note_list() 
            else:
                messagebox.showerror("Error", f"Could not create '{success}'. It might already exist.")



    def delete_note(self):

        if not self.active_note_id:
            return

        confirm = messagebox.askyesno("Delete Note", "Are you sure you want to delete this note? This cannot be undone.")

        if confirm:
            self.store.delete_note(self.active_note_id, self.active_type)
            self.active_note_id = None
            self.rt_load("")
            self._set_editor_enabled(False)
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

    def wipe_all_pics(self):

        for file in self.store.image_dir.iterdir():
            if file.is_file() and file.suffix.lower()==".png":
                file.unlink()  
               


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    app = OverlayWindow(root)
    root.mainloop()
