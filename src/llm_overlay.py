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


class Theme:
    BG = "#1e1e1e"
    CONTENT_BG = "#252526"
    BAR_BG = "#333333"
    BUTTON_BG = "#444343"
    RECORD_BG = "#5a5a5a"
    CARD_BG = "#2d2d2d"
    FG = "white"
    MUTED_FG = "#b3b3b3"


class ResizableWindowMixin:

    EDGE_SIZE = 4

    MIN_WIDTH = 200
    MIN_HEIGHT = 150

    def _init_drag_state(self):
        self.drag_data = {"x": 0, "y": 0}
        self.resize_edges = ""

    def _bind_drag(self, widget):
        widget.bind("<Button-1>", self.start_drag)
        widget.bind("<B1-Motion>", self.do_drag)

    def start_drag(self, event):
        """Initialize window drag operation."""
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y

    def do_drag(self, event):
        """Handle window dragging."""
        x = self.winfo_x() + (event.x - self.drag_data["x"])
        y = self.winfo_y() + (event.y - self.drag_data["y"])
        self.geometry(f"+{x}+{y}")

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



class LLMWindow(tk.Toplevel, ResizableWindowMixin):

    MIN_WIDTH = 320
    MIN_HEIGHT = 380

    FONT = ("Segoe UI", 10)
    FONT_BOLD = ("Segoe UI", 10, "bold")
    FONT_ITALIC = ("Segoe UI", 10, "italic")

    def __init__(self, master, model, model_name="AI"):
        super().__init__(master)

        self.model = model
        self.model_name = model_name or "AI"
        self._busy = False
        self._reply_queue = None
        self._stream_started = False
        self.recorder = SpeakerRecorder()
        self._recording_ui = False
        self._init_drag_state()

        self.title("LLM")
        self.geometry("450x600+500+150")
        self.configure(bg=Theme.BG)

        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.92)

        self._build_chrome()
        self._build_input()
        self._build_chat()

        make_window_invisible(self)

        self._insert_message("How can I help you today?", is_user=False)

    def _build_chrome(self):
        main_container = tk.Frame(self, bg=Theme.BG)
        main_container.pack(fill=tk.BOTH, expand=True)

        left_edge = tk.Frame(main_container, width=self.EDGE_SIZE, bg=Theme.BG, cursor="size_we")
        left_edge.pack(side=tk.LEFT, fill=tk.Y)
        self._bind_resize_edge(left_edge, "w")

        right_edge = tk.Frame(main_container, width=self.EDGE_SIZE, bg=Theme.BG, cursor="size_we")
        right_edge.pack(side=tk.RIGHT, fill=tk.Y)
        self._bind_resize_edge(right_edge, "e")

        inner_container = tk.Frame(main_container, bg=Theme.BG)
        inner_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        top_edge = tk.Frame(inner_container, height=self.EDGE_SIZE, bg=Theme.BG, cursor="size_ns")
        top_edge.pack(fill=tk.X, side=tk.TOP)
        self._bind_resize_edge(top_edge, "n")

        title_bar = tk.Frame(inner_container, bg=Theme.BAR_BG, height=28)
        title_bar.pack(fill=tk.X, side=tk.TOP)
        title_bar.pack_propagate(False)

        title_label = tk.Label(title_bar, text=f" {self.model_name} ", bg=Theme.BAR_BG, fg=Theme.FG, font=self.FONT_BOLD)
        title_label.pack(side=tk.LEFT, padx=4)

        close_btn = tk.Button(
            title_bar, text=" X ", bg=Theme.BUTTON_BG, fg=Theme.FG, bd=0,
            activebackground=Theme.BAR_BG, activeforeground=Theme.FG, command=self.destroy,
        )
        close_btn.pack(side=tk.RIGHT, padx=4)

        self._bind_drag(title_bar)
        self._bind_drag(title_label)

        bottom_edge = tk.Frame(inner_container, bg=Theme.BG, height=self.EDGE_SIZE + 6, cursor="size_nw_se")
        bottom_edge.pack(fill=tk.X, side=tk.BOTTOM)
        self._bind_resize_edge(bottom_edge, "se")

        self.content_frame = tk.Frame(inner_container, bg=Theme.CONTENT_BG)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def _build_input(self):
        input_frame = tk.Frame(self.content_frame, bg=Theme.CONTENT_BG)
        input_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=5)

        self.prompt_entry = tk.Entry(
            input_frame, bg=Theme.BAR_BG, fg=Theme.FG, insertbackground=Theme.FG,
            bd=0, font=self.FONT, relief=tk.FLAT,
            highlightthickness=1, highlightbackground=Theme.BUTTON_BG, highlightcolor=Theme.MUTED_FG,
        )
        self.prompt_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6), ipady=8)
        self.prompt_entry.bind("<Return>", self.send_message)
        self.prompt_entry.focus_set()

        self.send_btn = tk.Button(
            input_frame, text="Send", bg=Theme.BUTTON_BG, fg=Theme.FG, bd=0, font=self.FONT,
            activebackground=Theme.BAR_BG, activeforeground=Theme.FG, command=self.send_message, cursor="hand2"
        )
        self.send_btn.pack(side=tk.RIGHT, ipadx=12, ipady=4)

        self.record_btn = tk.Button(
            input_frame, text="Record", bg=Theme.BUTTON_BG, fg=Theme.FG, bd=0, font=self.FONT,
            activebackground=Theme.BAR_BG, activeforeground=Theme.FG, command=self.toggle_record,cursor="hand2"
        )
        self.record_btn.pack(side=tk.RIGHT, padx=(0, 6), ipadx=10, ipady=4)

    def _build_chat(self):
        chat_frame = tk.Frame(self.content_frame, bg=Theme.CONTENT_BG)
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(5, 0))

        self.chat_display = tk.Text(
            chat_frame, bg=Theme.CONTENT_BG, fg=Theme.FG, bd=0, wrap=tk.WORD,
            font=self.FONT, state=tk.NORMAL, padx=6, pady=6, highlightthickness=0,cursor="arrow"
        )

        scrollbar = tk.Scrollbar(
            chat_frame, command=self.chat_display.yview, bg=Theme.BAR_BG,
            troughcolor=Theme.CONTENT_BG, activebackground=Theme.BUTTON_BG,
            highlightthickness=0, bd=0, width=10,
        )
        self.chat_display.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.chat_display.bind("<Key>", self._readonly_key)
        self.chat_display.bind("<Button-2>", lambda e: "break")

        self.chat_display.tag_configure(
            "user_label", font=self.FONT_BOLD, foreground=Theme.FG, background=Theme.CARD_BG,
            lmargin1=90, lmargin2=90, rmargin=12, spacing1=10,
        )
        self.chat_display.tag_configure(
            "user_body", foreground=Theme.FG, background=Theme.CARD_BG,
            lmargin1=90, lmargin2=90, rmargin=12, spacing3=8,
        )
        self.chat_display.tag_configure(
            "ai_label", font=self.FONT_BOLD, foreground=Theme.MUTED_FG, background=Theme.BG,
            lmargin1=12, lmargin2=12, rmargin=90, spacing1=10,
        )
        self.chat_display.tag_configure(
            "ai_body", foreground=Theme.FG, background=Theme.BG,
            lmargin1=12, lmargin2=12, rmargin=90, spacing3=8,
        )
        self.chat_display.tag_configure(
            "thinking", font=self.FONT_ITALIC, foreground=Theme.MUTED_FG, background=Theme.CONTENT_BG,
            lmargin1=12, lmargin2=12, spacing1=8, spacing3=8,
        )
        self.chat_display.tag_configure(
            "status", font=self.FONT_ITALIC, foreground=Theme.MUTED_FG, background=Theme.CONTENT_BG,
            lmargin1=12, lmargin2=12, spacing1=8, spacing3=8,
        )
        self.chat_display.tag_configure("sel", background="#4a5a6a", foreground=Theme.FG)
        self.chat_display.tag_raise("sel")

    def _at_bottom(self):
        return self.chat_display.yview()[1] >= 0.995

    def _readonly_key(self, event):
        # Allow Ctrl+C / Ctrl+A, selection and navigation keys; block all editing.
        if event.state & 0x4 and event.keysym.lower() in ("c", "a"):
            return None
        if event.keysym in ("Shift_L", "Shift_R", "Control_L", "Control_R",
                            "Left", "Right", "Up", "Down", "Home", "End", "Prior", "Next"):
            return None
        return "break"

    def _insert_message(self, text, is_user):
        label_tag = "user_label" if is_user else "ai_label"
        body_tag = "user_body" if is_user else "ai_body"
        label = "You" if is_user else self.model_name

        stick = self._at_bottom()
        self.chat_display.insert(tk.END, f" {label} \n", label_tag)
        self.chat_display.insert(tk.END, f" {text} \n", body_tag)
        self.chat_display.insert(tk.END, "\n")
        if stick:
            self.chat_display.see(tk.END)

    def _show_thinking(self):
        stick = self._at_bottom()
        self.chat_display.insert(tk.END, f"{self.model_name} is thinking...", "thinking")
        if stick:
            self.chat_display.see(tk.END)

    def _hide_thinking(self):
        ranges = self.chat_display.tag_ranges("thinking")
        if not ranges:
            return
        self.chat_display.delete(ranges[0], ranges[1])

    def send_message(self, event=None):
        if self._busy:
            return

        user_text = self.prompt_entry.get().strip()
        if not user_text:
            return

        self.prompt_entry.delete(0, tk.END)
        self.send_text(user_text)

    def send_text(self, user_text):
        if self._busy or not user_text:
            return

        self._busy = True
        self._stream_started = False
        self._reply_queue = queue.Queue()
        self._insert_message(user_text, is_user=True)
        self.prompt_entry.configure(state=tk.DISABLED)
        self.send_btn.configure(state=tk.DISABLED)
        self._show_thinking()

        threading.Thread(target=self._stream_worker, args=(user_text,), daemon=True).start()
        self.after(80, self._poll_queue)

    def toggle_record(self):
        if self._recording_ui:
            self._recording_ui = False
            self.recorder.stop()
            self.record_btn.configure(text="Transcribing...", state=tk.DISABLED)
            self._show_transcribing()
        else:
            self._recording_ui = True
            self.recorder.start()
            self.record_btn.configure(text="Stop", bg=Theme.RECORD_BG)
            self.after(200, self._poll_speech)

    def _show_transcribing(self):
        stick = self._at_bottom()
        self.chat_display.insert(tk.END, "Transcribing audio...", "status")
        if stick:
            self.chat_display.see(tk.END)

    def _hide_transcribing(self):
        ranges = self.chat_display.tag_ranges("status")
        if not ranges:
            return
        self.chat_display.delete(ranges[0], ranges[1])

    def _poll_speech(self):
        if not self.winfo_exists():
            return

        try:
            while True:
                kind, payload = self.recorder.results.get_nowait()
                if kind == "done":
                    self._on_transcript(payload)
                    return
                if kind == "error":
                    self._on_speech_error(payload)
                    return
        except queue.Empty:
            pass

        self.after(200, self._poll_speech)

    def _on_transcript(self, text):
        self._hide_transcribing()
        self._reset_record_btn()

        if not text:
            return

        if self._busy:
            existing = self.prompt_entry.get().strip()
            self.prompt_entry.delete(0, tk.END)
            self.prompt_entry.insert(0, f"{existing} {text}" if existing else text)
        else:
            self.send_text(text)

    def _on_speech_error(self, message):
        self._hide_transcribing()
        self._reset_record_btn()
        self._insert_message(f"[Recording error: {message}]", is_user=False)

    def _reset_record_btn(self):
        self._recording_ui = False
        self.record_btn.configure(text="Record", bg=Theme.BUTTON_BG, state=tk.NORMAL)

    def destroy(self):
        self.recorder.abort()
        super().destroy()

    def _stream_worker(self, prompt):
        try:
            for chunk in self.model.generate_content(prompt, stream=True):
                try:
                    text = chunk.text
                except Exception:
                    continue
                if text:
                    self._reply_queue.put(text)
        except Exception as e:
            self._reply_queue.put(f"[Error connecting to {self.model_name}: {e}]")
        finally:
            self._reply_queue.put(None)

    def _poll_queue(self):
        if not self.winfo_exists() or self._reply_queue is None:
            return

        try:
            while True:
                item = self._reply_queue.get_nowait()
                if item is None:
                    self._end_stream()
                    return
                self._append_stream_chunk(item)
        except queue.Empty:
            pass

        self.after(80, self._poll_queue)

    def _append_stream_chunk(self, text):
        stick = self._at_bottom()

        if not self._stream_started:
            self._stream_started = True
            self._hide_thinking()
            self.chat_display.insert(tk.END, f" {self.model_name} \n", "ai_label")
            self.chat_display.insert(tk.END, f" {text}", "ai_body")
        else:
            self.chat_display.insert(tk.END, text, "ai_body")

        if stick:
            self.chat_display.see(tk.END)

    def _end_stream(self):
        if self._stream_started:
            stick = self._at_bottom()
            self.chat_display.insert(tk.END, " \n", "ai_body")
            self.chat_display.insert(tk.END, "\n")
            if stick:
                self.chat_display.see(tk.END)
        else:
            self._hide_thinking()
            self._insert_message("[No response received]", is_user=False)

        self._reply_queue = None
        self.prompt_entry.configure(state=tk.NORMAL)
        self.send_btn.configure(state=tk.NORMAL)
        self.prompt_entry.focus_set()
        self._busy = False