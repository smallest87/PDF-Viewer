import tkinter as tk
from tkinter import ttk

class StatusBarComponent(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, relief=tk.SUNKEN, padding=(5, 2))
        
        self.lbl_status = ttk.Label(self, text="Status: -")
        self.lbl_status.pack(side=tk.LEFT, padx=5)
        
        self.lbl_dims = ttk.Label(self, text="Dimensi: -")
        self.lbl_dims.pack(side=tk.LEFT, padx=5)
        
        self.progress = ttk.Progressbar(self, orient=tk.HORIZONTAL, length=150, mode='determinate')
        self.progress.pack(side=tk.RIGHT, padx=10)
        
        self.lbl_zoom = ttk.Label(self, text="Zoom: 100%")
        self.lbl_zoom.pack(side=tk.RIGHT, padx=5)