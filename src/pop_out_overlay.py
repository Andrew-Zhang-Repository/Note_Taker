import tkinter as tk
from capture import make_window_invisible
from llm_overlay import ResizableWindowMixin, Theme


class PopOutNote(tk.Toplevel,ResizableWindowMixin):
    def __init__(self, main_app, note_id, title, body, active_type,store,UIManager):
        super().__init__(main_app)
 
        self.main_app = main_app
        self.note_id = note_id
        self.active_type = active_type
        self.store = store
        self.UIManager = UIManager

        settings = self.store.config_settings.get("ui_settings", {}).get("popout", {})
        saved_opacity = settings.get("opacity", 0.85)
        self.attributes("-alpha", saved_opacity)
        self.win_type = "popout"

        
     
        self.geometry("320x260+500+200")
        self.configure(bg="#1e1e1e")
        self.attributes("-topmost", True)
        self.overrideredirect(True)
        self._init_drag_state()

        self.saved_bg = settings.get("bg_color", "#1e1e1e")
        make_window_invisible(self)

        self.build_ui(title, body)

    def build_ui(self, title, body):
       
        
        left_edge = tk.Frame(self, width=self.EDGE_SIZE, bg=Theme.BG, cursor="size_we")
        left_edge.pack(side=tk.LEFT, fill=tk.Y)
        self._bind_resize_edge(left_edge, "w")

        right_edge = tk.Frame(self, width=self.EDGE_SIZE, bg=Theme.BG, cursor="size_we")
        right_edge.pack(side=tk.RIGHT, fill=tk.Y)
        self._bind_resize_edge(right_edge, "e")


        bottom_edge = tk.Frame(self, bg=Theme.BG, height=self.EDGE_SIZE + 6, cursor="size_nw_se")
        bottom_edge.pack(fill=tk.X, side=tk.BOTTOM)
        self._bind_resize_edge(bottom_edge, "se")

        title_bar = tk.Frame(self, bg="#2d2d2d", height=24)
        title_bar.pack(fill=tk.X, side=tk.TOP)
        title_bar.pack_propagate(False)

        top_edge = tk.Frame(title_bar, height=4, bg="#2d2d2d", cursor="size_ns")
        top_edge.pack(fill=tk.X, side=tk.TOP)
        self._bind_resize_edge(top_edge, "n")

        title_label = tk.Label(
            title_bar, 
            text=f"{title}", 
            bg="#2d2d2d", 
            fg="#cccccc", 
            font=("Segoe UI", 9, "bold")
        )
        title_label.pack(side=tk.LEFT, padx=4)



        close_btn = tk.Button(title_bar, text="✕", bg="#2d2d2d", fg="white", bd=0, command=self.close_popout)
        close_btn.pack(side=tk.RIGHT, padx=4)

      
        title_bar.bind("<ButtonPress-1>", self.start_drag)
        title_bar.bind("<B1-Motion>", self.do_drag)
        title_label.bind("<ButtonPress-1>", self.start_drag)
        title_label.bind("<B1-Motion>", self.do_drag)



        

        self.pop_editor = tk.Text(
            self, 
            bg="#1e1e1e", 
            fg="white", 
            bd=0, 
            wrap=tk.WORD, 
            font=("Segoe UI", 10),
            insertbackground="white"
        )
        self.pop_editor.pack(fill=tk.BOTH, expand=True, padx=6, pady=(4, 0))
        self.pop_editor.insert(tk.END, body)

    
        self.pop_save_btn = tk.Button(self, text="Save", bg="#333333", fg="white", bd=0, command=self.save_popout)
        self.pop_save_btn.pack(side=tk.BOTTOM, fill=tk.X, padx=6, pady=4)

        self.recolor_widgets = [self, left_edge, right_edge, bottom_edge]

        self.UIManager.apply_bg(self, self.saved_bg)


    def start_drag(self, e):
        self._x = e.x
        self._y = e.y

    def do_drag(self, e):
        x = self.winfo_pointerx() - self._x
        y = self.winfo_pointery() - self._y
        self.geometry(f"+{x}+{y}")

  
    def save_popout(self):
        new_text = self.pop_editor.get("1.0", tk.END).strip()
        
  
        self.main_app.store.update_note(self.note_id, self.active_type, new_text)
        
        for n in self.main_app.current_notes:
            if n["id"] == self.note_id:
                n["note_body"] = new_text
                break
  
        if self.main_app.active_note_id == self.note_id:
            self.main_app.editor.delete("1.0", tk.END)
            self.main_app.editor.insert(tk.END, new_text)

    
        self.pop_save_btn.config(text="Saved!")
        self.after(1500, lambda: self.pop_save_btn.config(text="Save"))

    def close_popout(self):
        self.main_app.open_popouts.pop(self.note_id, None)
        self.destroy()


    