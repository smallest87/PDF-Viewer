import tkinter as tk
from tkinter import ttk

class ToolbarComponent(tk.Frame):
    def __init__(self, parent, view):
        super().__init__(parent, bd=1, relief=tk.RAISED)
        self.view = view
        self._build_ui()

    def _build_ui(self):
        # --- FILE CONTROLS ---
        ttk.Button(self, text="Open PDF", command=self.view._on_open).pack(side=tk.LEFT, padx=5)
        ttk.Button(self, text="Export CSV", command=self.view._on_export_csv).pack(side=tk.LEFT, padx=2)
        
        self.btn_table = ttk.Button(self, text="📊 Table", command=self.view._on_view_csv_table)
        self.btn_table.pack(side=tk.LEFT, padx=5)
        self.btn_table.config(state=tk.DISABLED)

        ttk.Separator(self, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        # --- NAVIGATION ---
        ttk.Button(self, text="<<", command=lambda: self.view.controller.change_page(-1)).pack(side=tk.LEFT)
        
        self.pg_ent = tk.Entry(self, width=4, justify='center')
        self.pg_ent.pack(side=tk.LEFT, padx=2)
        self.pg_ent.bind("<Return>", lambda e: self.view.controller.jump_to_page(int(self.pg_ent.get())))
        
        self.lbl_total = tk.Label(self, text="/ 0")
        self.lbl_total.pack(side=tk.LEFT, padx=2)
        
        ttk.Button(self, text=">>", command=lambda: self.view.controller.change_page(1)).pack(side=tk.LEFT)

        ttk.Separator(self, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        # --- ZOOM & LAYERS ---
        ttk.Button(self, text="Zoom +", command=lambda: self.view.controller.set_zoom("in")).pack(side=tk.LEFT)
        ttk.Button(self, text="Zoom -", command=lambda: self.view.controller.set_zoom("out")).pack(side=tk.LEFT)
        
        self.text_toggle = tk.Checkbutton(self, text="Text Layer", variable=self.view.text_layer_var,
                                          command=lambda: self.view.controller.toggle_text_layer(self.view.text_layer_var.get()))
        self.text_toggle.pack(side=tk.LEFT, padx=5)

        self.csv_toggle = tk.Checkbutton(self, text="CSV Overlay", variable=self.view.csv_overlay_var,
                                         command=lambda: self.view.controller.toggle_csv_layer(self.view.csv_overlay_var.get()))
        self.csv_toggle.pack(side=tk.LEFT, padx=5)

        # --- LINE GROUPING CONTROLS (FITUR BARU) ---
        tk.Label(self, text=" | Grouping:").pack(side=tk.LEFT, padx=(10, 0))
        
        # Checkbox diikat langsung ke BooleanVar di Controller
        self.chk_group = tk.Checkbutton(
            self, 
            text="Line", 
            variable=self.view.controller.line_grouping_enabled_var,
            command=self.view.controller.toggle_line_grouping
        )
        self.chk_group.pack(side=tk.LEFT)
        self.chk_group.config(state=tk.DISABLED)

        tk.Label(self, text="Tol:").pack(side=tk.LEFT)
        
        # Entry untuk input toleransi sumbu
        self.ent_tolerance = tk.Entry(self, width=5)
        self.ent_tolerance.insert(0, "2.0")
        self.ent_tolerance.pack(side=tk.LEFT, padx=2)
        self.ent_tolerance.config(state=tk.DISABLED)
        
        # Bind event Enter untuk update nilai toleransi
        self.ent_tolerance.bind(
            "<Return>", 
            lambda e: self.view.controller.update_tolerance(self.ent_tolerance.get())
        )