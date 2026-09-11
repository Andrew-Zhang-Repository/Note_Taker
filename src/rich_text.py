import os
import re
import uuid
import tkinter as tk
from PIL import Image, ImageTk, ImageGrab


class RichTextMixin:

    UNDO_LIMIT = 100
    UNDO_DEBOUNCE_MS = 600

    def _init_rich_text(self, editor):
        self.rt_editor = editor
        self.inline_images = {}
        self._undo_stack = []
        self._redo_stack = []
        self._undo_timer = None
        self._baseline = (self.rt_get_text(), editor.index(tk.INSERT))

        editor.bind("<KeyRelease>", self._rt_on_key_release)
        editor.bind("<Control-v>", self.handle_paste)
        editor.bind("<Control-z>", self.undo_snapshot)
        editor.bind("<Control-y>", self.redo_snapshot)

    def rt_notify_change(self):
        pass

    def rt_get_text(self):
        raw = ""
        for key, value, index in self.rt_editor.dump("1.0", tk.END, text=True, image=True):
            if key == "text":
                raw += value
            elif key == "image":
                raw += f"[IMG:{value}]"
        return raw.strip()

    def rt_load(self, text_data):
        self._rt_render(text_data)
        self.rt_reset_undo()

    def _rt_render(self, text_data):
        prev_state = self.rt_editor.cget("state")
        self.rt_editor.configure(state=tk.NORMAL)

        self.rt_editor.delete("1.0", tk.END)
        self.inline_images.clear()

        parts = re.split(r'(\[IMG:.*?\])', text_data or "")

        for part in parts:
            if part.startswith("[IMG:") and part.endswith("]"):
                img_path = part[5:-1]
                if os.path.exists(img_path):
                    img = Image.open(img_path)
                    img.thumbnail((400, 400))
                    photo = ImageTk.PhotoImage(img)
                    self.inline_images[img_path] = photo
                    self.rt_editor.image_create(tk.END, image=photo, name=img_path)
            elif part:
                self.rt_editor.insert(tk.END, part)

        self.rt_editor.configure(state=prev_state)

    def rt_reset_undo(self):
        if self._undo_timer is not None:
            self.rt_editor.after_cancel(self._undo_timer)
            self._undo_timer = None
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._baseline = (self.rt_get_text(), self.rt_editor.index(tk.INSERT))

    def _rt_on_key_release(self, event=None):
        self._schedule_undo_snapshot()
        self.rt_notify_change()

    def _schedule_undo_snapshot(self):
        if self._undo_timer is not None:
            self.rt_editor.after_cancel(self._undo_timer)
        self._undo_timer = self.rt_editor.after(self.UNDO_DEBOUNCE_MS, self._commit_undo_snapshot)

    def _commit_undo_snapshot(self):
        self._undo_timer = None
        if not self.rt_editor.winfo_exists():
            return
        current = self.rt_get_text()
        if current == self._baseline[0]:
            return
        self._push_undo(self._baseline)
        self._baseline = (current, self.rt_editor.index(tk.INSERT))

    def _push_undo(self, state):
        self._undo_stack.append(state)
        if len(self._undo_stack) > self.UNDO_LIMIT:
            self._undo_stack.pop(0)
        self._redo_stack.clear()

    def _flush_pending_snapshot(self):
        if self._undo_timer is not None:
            self.rt_editor.after_cancel(self._undo_timer)
            self._commit_undo_snapshot()

    def undo_snapshot(self, event=None):
        self._flush_pending_snapshot()
        if not self._undo_stack:
            return "break"

        current = (self.rt_get_text(), self.rt_editor.index(tk.INSERT))
        state = self._undo_stack.pop()
        self._redo_stack.append(current)
        self._rt_restore(state)
        return "break"

    def redo_snapshot(self, event=None):
        self._flush_pending_snapshot()
        if not self._redo_stack:
            return "break"

        current = (self.rt_get_text(), self.rt_editor.index(tk.INSERT))
        state = self._redo_stack.pop()
        self._undo_stack.append(current)
        self._rt_restore(state)
        return "break"

    def _rt_restore(self, state):
        text, cursor = state
        self._rt_render(text)
        try:
            if self.rt_editor.compare(cursor, ">", "end-1c"):
                cursor = "end-1c"
            self.rt_editor.mark_set(tk.INSERT, cursor)
        except tk.TclError:
            pass
        self._baseline = (self.rt_get_text(), self.rt_editor.index(tk.INSERT))

    def handle_paste(self, event=None):
        try:
            clipboard_img = ImageGrab.grabclipboard()

            if clipboard_img and isinstance(clipboard_img, Image.Image):
                self._flush_pending_snapshot()
                self._push_undo(self._baseline)

                unique_name = f"img_{uuid.uuid4().hex}.png"
                local_path = os.path.join(str(self.store.image_dir), unique_name)
                clipboard_img.save(local_path)

                clipboard_img.thumbnail((400, 400))
                photo = ImageTk.PhotoImage(clipboard_img)
                self.inline_images[local_path] = photo

                self.rt_editor.image_create(tk.INSERT, image=photo, name=local_path)
                self._baseline = (self.rt_get_text(), self.rt_editor.index(tk.INSERT))

                self.rt_notify_change()
                return "break"

        except Exception as e:
            print("Paste error:", e)
