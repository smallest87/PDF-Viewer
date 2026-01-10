import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

class ViewportComponent(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#323639")
        self.tk_img = None
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.h_rule = tk.Canvas(self, height=25, bg="#e0e0e0", bd=0, highlightthickness=0)
        self.v_rule = tk.Canvas(self, width=25, bg="#e0e0e0", bd=0, highlightthickness=0)
        self.canvas = tk.Canvas(self, bg="#323639", bd=0, highlightthickness=0)
        
        self.h_rule.grid(row=0, column=1, sticky="ew")
        self.v_rule.grid(row=1, column=0, sticky="ns")
        self.canvas.grid(row=1, column=1, sticky="nsew")
        
        v_scr = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self._sync_v)
        v_scr.grid(row=1, column=2, sticky="ns")
        self.canvas.configure(yscrollcommand=v_scr.set)

    def _sync_v(self, *args):
        self.canvas.yview(*args)
        self.v_rule.yview(*args)