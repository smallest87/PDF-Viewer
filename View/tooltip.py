import tkinter as tk


class TooltipManager:
    """Mengelola jendela pop-up balon teks untuk informasi hover"""

    def __init__(self, root):
        self.root = root
        self.tip_window = None

    def show(self, event, text, coords=None):
        """Menciptakan jendela tooltip dengan label koordinat terpisah"""
        if self.tip_window or not text:
            return
        self.tip_window = tw = tk.Toplevel(self.root)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{event.x_root+15}+{event.y_root+10}")

        display_text = f"Teks: {text}"
        if coords:
            # Berdasarkan urutan (x0, top, x1, bottom) dari Controller
            x0, top, x1, bottom = coords
            display_text += f"\nx0: {x0:.2f}"
            display_text += f"\nx1: {x1:.2f}"
            display_text += f"\ntop: {top:.2f}"
            display_text += f"\nbottom: {bottom:.2f}"

        tk.Label(
            tw,
            text=display_text,
            background="#ffffca",
            relief=tk.SOLID,
            borderwidth=1,
            font=("Arial", 9),
            padx=4,
            pady=2,
            justify="left",
        ).pack()

    def move(self, event):
        """Mengikuti pergerakan kursor"""
        if self.tip_window:
            self.tip_window.wm_geometry(f"+{event.x_root+15}+{event.y_root+10}")

    def hide(self):
        """Menghancurkan jendela tooltip"""
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None
