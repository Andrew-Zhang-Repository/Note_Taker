import tkinter as tk

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
     

        # Bottom bar with font size controls
        self.bottom_bar = tk.Frame(self.inner_container, bg="#333333", height=30)
        self.bottom_bar.pack(fill=tk.X, side=tk.BOTTOM)
        self.bottom_bar.pack_propagate(False)

        # Font size controls container (centered)
        font_controls = tk.Frame(self.bottom_bar, bg="#333333")
        font_controls.pack(side=tk.LEFT, padx=8)


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



if __name__ == "__main__":
    app = OverlayWindow()
    app.mainloop()