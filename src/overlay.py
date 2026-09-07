import tkinter as tk
from tkinter import ttk
from notes_store import note_store
from tkinter import simpledialog, messagebox
from capture import make_window_invisible
import threading
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

class OverlayWindow(tk.Tk):

    EDGE_SIZE = 4

    MIN_WIDTH = 200
    MIN_HEIGHT = 150

    # Position margins
    SCREEN_MARGIN = 20
    TASKBAR_HEIGHT = 60

    # Nudge distance in pixels
    NUDGE_DISTANCE = 20

    
    def __init__(self):
        super().__init__()

        
        self.drag_data = {"x": 0, "y": 0}
        self.title("Overlay")
        self.geometry("400x500+100+100")
        self.configure(bg="#1e1e1e")
    

        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.85)

        self.move_window()
        self._offsetx = 0
        self._offsety = 0

        make_window_invisible(self)
 
    
    def start_move(self, event):
        """Records the exact point the user clicked inside the title bar."""
        self._offsetx = event.x
        self._offsety = event.y

    def do_move(self, event):
        """Calculates the new position and moves the window."""
        x = self.winfo_pointerx() - self._offsetx
        y = self.winfo_pointery() - self._offsety
        
        # Move the window
        self.geometry(f"+{x}+{y}")

    #Adjustable window

    def move_window(self):

    

        self.main_container = tk.Frame(self, bg="#1e1e1e")
        self.main_container.pack(fill=tk.BOTH, expand=True)


        self.left_edge = tk.Frame(self.main_container, width=self.EDGE_SIZE, bg="#1e1e1e", cursor="size_we")
        self.left_edge.pack(side=tk.LEFT, fill=tk.Y)
        self._bind_resize_edge(self.left_edge, "w")
        
        self.left_edge = tk.Frame(self.main_container, width=self.EDGE_SIZE, bg="#1e1e1e")
        self.left_edge.pack(side=tk.LEFT, fill=tk.Y)
        self._bind_resize_edge(self.left_edge, "w")

        self.right_edge = tk.Frame(self.main_container, width=self.EDGE_SIZE, bg="#1e1e1e", cursor="size_we")
        self.right_edge.pack(side=tk.RIGHT, fill=tk.Y)
        self._bind_resize_edge(self.right_edge, "e")

        self.right_edge = tk.Frame(self.main_container, width=self.EDGE_SIZE, bg="#1e1e1e")
        self.right_edge.pack(side=tk.RIGHT, fill=tk.Y)
        self._bind_resize_edge(self.right_edge, "e")

        self.inner_container = tk.Frame(self.main_container, bg="#1e1e1e")
        self.inner_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.top_edge = tk.Frame(self.inner_container, height=self.EDGE_SIZE, bg="#1e1e1e")
        self.top_edge.pack(fill=tk.X, side=tk.TOP)
        self._bind_resize_edge(self.top_edge, "n")

        self.top_edge = tk.Frame(self.inner_container, height=self.EDGE_SIZE, bg="#1e1e1e", cursor="size_ns")
        self.top_edge.pack(fill=tk.X, side=tk.TOP)
        self._bind_resize_edge(self.top_edge, "n")

        self.title_frame = tk.Frame(self.inner_container, bg="#1e1e1e", height=25)
        self.title_frame.pack(fill=tk.X, side=tk.TOP)
        self.title_frame.pack_propagate(False)

        self.title_bar = tk.Frame(self.inner_container, bg="#1e1e1e", relief="raised", bd=0)
        self.title_bar.pack(fill="x", side="top")


        self.title_frame.bind("<Button-1>", self.start_drag)
        self.title_frame.bind("<B1-Motion>", self.do_drag)
   

        self.resize_frame = tk.Frame(self.inner_container, bg="#1e1e1e", height=10)
        self.resize_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.resize_frame = tk.Frame(self.inner_container, bg="#1e1e1e", height=self.EDGE_SIZE, cursor="size_ns")
        self.resize_frame.pack(fill=tk.X, side=tk.BOTTOM)

     
        # Bind resize events (bottom/southeast)
        self.resize_frame.bind("<Button-1>", self.start_resize)
        self.resize_frame.bind("<B1-Motion>", self.do_resize)
        self.close_btn = tk.Button(self.title_bar, text=" X ", bg="#333333", fg="white", bd=0, command=self.destroy)
        self.close_btn.pack(side="right", padx=4)
        self.content_frame = tk.Frame(self.inner_container, bg="#252526") # Slightly lighter so you can see it
        self.content_frame.pack(expand=True, fill="both", padx=5, pady=5)
     



        self.notes_ui_management()


    def start_drag(self, event):
        """Initialize window drag operation."""
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y

    def do_drag(self, event):
        """Handle window dragging."""
        x = self.winfo_x() + (event.x - self.drag_data["x"])
        y = self.winfo_y() + (event.y - self.drag_data["y"])
        self.geometry(f"+{x}+{y}")


    def start_resize(self, event):
        """Initialize window resize operation (for bottom resize bar)."""
        self.resize_edges = "se"  # Bottom bar = southeast resize
        self._start_edge_resize(event)

    def do_resize(self, event):
        """Handle window resizing (for bottom resize bar)."""
        self._do_edge_resize(event)

    def _start_edge_resize(self, event):
        """Initialize edge resize operation."""
        self.drag_data["x"] = event.x_root
        self.drag_data["y"] = event.y_root
        self.drag_data["width"] = self.winfo_width()
        self.drag_data["height"] = self.winfo_height()
        self.drag_data["win_x"] = self.winfo_x()
        self.drag_data["win_y"] = self.winfo_y()


    def _do_edge_resize(self, event):
        """Handle edge resize based on which edges are active."""
        if not self.resize_edges:
            return

        dx = event.x_root - self.drag_data["x"]
        dy = event.y_root - self.drag_data["y"]

        new_x = self.drag_data["win_x"]
        new_y = self.drag_data["win_y"]
        new_w = self.drag_data["width"]
        new_h = self.drag_data["height"]

        min_w, min_h = self.MIN_WIDTH, self.MIN_HEIGHT

        # Handle west (left) edge
        if "w" in self.resize_edges:
            potential_w = self.drag_data["width"] - dx
            if potential_w >= min_w:
                new_w = potential_w
                new_x = self.drag_data["win_x"] + dx

        # Handle east (right) edge
        if "e" in self.resize_edges:
            new_w = max(min_w, self.drag_data["width"] + dx)

        # Handle north (top) edge
        if "n" in self.resize_edges:
            potential_h = self.drag_data["height"] - dy
            if potential_h >= min_h:
                new_h = potential_h
                new_y = self.drag_data["win_y"] + dy

        # Handle south (bottom) edge
        if "s" in self.resize_edges:
            new_h = max(min_h, self.drag_data["height"] + dy)

        self.geometry(f"{new_w}x{new_h}+{new_x}+{new_y}")


    def _bind_resize_edge(self, frame: tk.Frame, edge: str) -> None:
        """Bind resize events to an edge frame."""
        def start(event):
            self.resize_edges = edge
            self._start_edge_resize(event)

        def drag(event):
            if self.resize_edges:
                self._do_edge_resize(event)

        def release(event):
            self.resize_edges = ""

        frame.bind("<Button-1>", start)
        frame.bind("<B1-Motion>", drag)
        frame.bind("<ButtonRelease-1>", release)

    def notes_ui_management(self):
        self.store = note_store()

        if self.store.config.get("types"):
            self.active_type = self.store.config["types"][0]
            
        self.current_notes = []
        self.active_note_id = None

        self.current_notes = []
        self.active_note_id = None

        top_bar = tk.Frame(self.content_frame, bg="#252526")
        top_bar.pack(fill=tk.X, pady=5)

        self.type_combo = ttk.Combobox(top_bar, values=self.store.config.get("types", []), state="readonly")
        self.type_combo.set(self.active_type)
        self.type_combo.pack(side=tk.LEFT, padx=5)
        self.type_combo.bind("<<ComboboxSelected>>", self.on_type_change)

        new_btn = tk.Button(top_bar, text="+ New Note", bg="#333333", fg="white", bd=0, command=self.create_new_note)
        new_btn.pack(side=tk.RIGHT, padx=5)

        self.note_listbox = tk.Listbox(self.content_frame, height=5, bg="#1e1e1e", fg="white", bd=0)
        self.note_listbox.pack(fill=tk.X, padx=5, pady=5)
        self.note_listbox.bind("<<ListboxSelect>>", self.on_note_select)



        
        self.delete_btn = tk.Button(top_bar, text="Delete", bg="#444343", fg="white", bd=0, command=self.delete_note)
        self.delete_btn.pack(side=tk.TOP, fill=tk.X, padx=5,pady=5)

        self.ai_btn = tk.Button(self.content_frame, text="Ask AI", bg="#737575", fg="white", bd=0, command=self.open_llm_window)
        self.ai_btn.pack(side=tk.BOTTOM, fill=tk.X, expand=True, padx=(2, 2))

        self.save_btn = tk.Button(self.content_frame, text="Save Note", bg="#444343", fg="white", bd=0, command=self.save_note)
        self.save_btn.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)

        self.editor = tk.Text(self.content_frame, bg="#1e1e1e", fg="white", bd=0, wrap=tk.WORD)
        self.editor.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

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
            self.store.delete_note(self.active_note_id,self.active_type)
            self.active_note_id = None
            self.editor.delete("1.0", tk.END)
            self.refresh_note_list()


    def open_llm_window(self):
        
        genai.configure(api_key=os.getenv("key"))
        model = genai.GenerativeModel(os.getenv("default_model"))

        llm_win = tk.Toplevel(self)
        llm_win.geometry("450x600+500+150")
        llm_win.configure(bg="#1e1e1e")
        llm_win.attributes("-topmost", True)
        llm_win.overrideredirect(True)

     
        make_window_invisible(llm_win)

    
        title_bar = tk.Frame(llm_win, bg="#333333", bd=0)
        title_bar.pack(fill=tk.X, side=tk.TOP)
        
        tk.Label(title_bar, text=" Gemini AI", bg="#333333", fg="white", font=("Arial", 10, "bold")).pack(side=tk.LEFT, pady=4, padx=4)
        tk.Button(title_bar, text=" X ", bg="#ff4c4c", fg="white", bd=0, command=llm_win.destroy).pack(side=tk.RIGHT, padx=4)

        def start_drag(event):
            llm_win._offsetx = event.x
            llm_win._offsety = event.y
            
        def do_drag(event):
            x = llm_win.winfo_pointerx() - llm_win._offsetx
            y = llm_win.winfo_pointery() - llm_win._offsety
            llm_win.geometry(f"+{x}+{y}")
            
        title_bar.bind("<ButtonPress-1>", start_drag)
        title_bar.bind("<B1-Motion>", do_drag)

        chat_display = tk.Text(llm_win, bg="#1e1e1e", fg="white", bd=0, wrap=tk.WORD, font=("Arial", 10))
        chat_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        chat_display.insert(tk.END, "Gemini: How can I help you today?\n\n")
        chat_display.config(state=tk.DISABLED)

        input_frame = tk.Frame(llm_win, bg="#252526")
        input_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=5)
        
        prompt_entry = tk.Entry(input_frame, bg="#333333", fg="white", bd=0, font=("Arial", 10))
        prompt_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5), ipady=8)
        
        def send_message(event=None):
            user_text = prompt_entry.get().strip()
            if not user_text:
                return
                
            chat_display.config(state=tk.NORMAL)
            chat_display.insert(tk.END, f"You: {user_text}\n\n")
            chat_display.see(tk.END) # Scroll to bottom
            chat_display.config(state=tk.DISABLED)
            
            prompt_entry.delete(0, tk.END)
            prompt_entry.config(state=tk.DISABLED)
            
        
            threading.Thread(target=fetch_gemini, args=(user_text,), daemon=True).start()

        def fetch_gemini(prompt):
            try:
                response = model.generate_content(prompt)
                reply = response.text
            except Exception as e:
                reply = f"[Error connecting to Gemini: {e}]"
                
            llm_win.after(0, lambda: update_ui(reply))

        def update_ui(reply_text):
            chat_display.config(state=tk.NORMAL)
            chat_display.insert(tk.END, f"Gemini: {reply_text}\n\n")
            chat_display.see(tk.END)
            chat_display.config(state=tk.DISABLED)
            
            prompt_entry.config(state=tk.NORMAL)
            prompt_entry.focus_set()

        prompt_entry.bind("<Return>", send_message)
        tk.Button(input_frame, text="Send", bg="#10a37f", fg="white", bd=0, command=send_message).pack(side=tk.RIGHT, ipady=3, ipadx=10)





if __name__ == "__main__":
    app = OverlayWindow()
    app.mainloop()