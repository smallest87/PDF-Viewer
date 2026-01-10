import tkinter as tk
from tkinter import ttk

class ToolbarComponent(ttk.Frame):
    """Komponen navigasi dan kontrol fungsionalitas atas"""
    def __init__(self, parent, main_view):
        super().__init__(parent, padding=5)
        self.view = main_view
        self.controller = main_view.controller
        self._build_ui()

    def _build_ui(self):
        # Tombol Operasi File & Ekspor
        ttk.Button(self, text="Open", command=self.view._on_open).pack(side=tk.LEFT)
        ttk.Button(self, text="Export CSV", command=self.view._on_export_csv).pack(side=tk.LEFT, padx=5)
        
        ttk.Separator(self, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Kontrol Navigasi Halaman
        ttk.Button(self, text="<", command=lambda: self.controller.change_page(-1)).pack(side=tk.LEFT)
        self.pg_ent = ttk.Entry(self, width=5, justify="center")
        self.pg_ent.pack(side=tk.LEFT, padx=5)
        self.pg_ent.bind("<Return>", lambda e: self.controller.jump_to_page(int(self.pg_ent.get())))
        
        self.lbl_total = ttk.Label(self, text="/ 0")
        self.lbl_total.pack(side=tk.LEFT)
        ttk.Button(self, text=">", command=lambda: self.controller.change_page(1)).pack(side=tk.LEFT)
        
        ttk.Separator(self, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Kontrol Toggle Layer (Binding ke variabel di main_view)
        self.text_toggle = ttk.Checkbutton(
            self, text="Text Layer", 
            variable=self.view.text_layer_var, 
            command=lambda: self.controller.toggle_text_layer(self.view.text_layer_var.get()),
            state="disabled"
        )
        self.text_toggle.pack(side=tk.LEFT)
        
        self.csv_toggle = ttk.Checkbutton(
            self, text="CSV Text Overlay", 
            variable=self.view.csv_overlay_var, 
            command=lambda: self.controller.toggle_csv_layer(self.view.csv_overlay_var.get()),
            state="disabled"
        )
        self.csv_toggle.pack(side=tk.LEFT, padx=5)

        # Kontrol Zoom
        ttk.Button(self, text="Zoom +", command=lambda: self.controller.set_zoom("in")).pack(side=tk.RIGHT)
        ttk.Button(self, text="Zoom -", command=lambda: self.controller.set_zoom("out")).pack(side=tk.RIGHT)