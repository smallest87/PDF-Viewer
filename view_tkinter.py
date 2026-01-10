import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from PIL import Image, ImageTk
import os
from interface import PDFViewInterface

class TkinterPDFView(PDFViewInterface):
    def __init__(self, root, controller_class):
        self.root = root
        self.base_title = "Modular PDF Viewer Pro"
        self.root.title(self.base_title)
        self.controller = controller_class(self)
        self.tk_img = None
        self.text_layer_var = tk.BooleanVar(value=False)
        self.csv_overlay_var = tk.BooleanVar(value=False)
        self.tip_window = None
        self._setup_ui()

    def _setup_ui(self):
        tbar = ttk.Frame(self.root, padding=5); tbar.pack(side=tk.TOP, fill=tk.X)
        ttk.Button(tbar, text="Open", command=self._on_open).pack(side=tk.LEFT)
        ttk.Button(tbar, text="Export CSV", command=self._on_export_csv).pack(side=tk.LEFT, padx=5)
        ttk.Separator(tbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        ttk.Button(tbar, text="<", command=lambda: self.controller.change_page(-1)).pack(side=tk.LEFT)
        self.pg_ent = ttk.Entry(tbar, width=5, justify="center"); self.pg_ent.pack(side=tk.LEFT, padx=5)
        self.pg_ent.bind("<Return>", lambda e: self.controller.jump_to_page(int(self.pg_ent.get())))
        self.lbl_total = ttk.Label(tbar, text="/ 0"); self.lbl_total.pack(side=tk.LEFT)
        ttk.Button(tbar, text=">", command=lambda: self.controller.change_page(1)).pack(side=tk.LEFT)
        
        ttk.Separator(tbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        self.text_toggle = ttk.Checkbutton(tbar, text="Text Layer", variable=self.text_layer_var, command=lambda: self.controller.toggle_text_layer(self.text_layer_var.get()), state="disabled")
        self.text_toggle.pack(side=tk.LEFT)
        
        self.csv_toggle = ttk.Checkbutton(tbar, text="CSV Text Overlay", variable=self.csv_overlay_var, command=lambda: self.controller.toggle_csv_layer(self.csv_overlay_var.get()), state="disabled")
        self.csv_toggle.pack(side=tk.LEFT, padx=5)

        ttk.Button(tbar, text="Zoom +", command=lambda: self.controller.set_zoom("in")).pack(side=tk.RIGHT)
        ttk.Button(tbar, text="Zoom -", command=lambda: self.controller.set_zoom("out")).pack(side=tk.RIGHT)

        # Status Bar
        self.status_bar = ttk.Frame(self.root, relief=tk.SUNKEN, padding=(5, 2)); self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.lbl_sandwich_status = ttk.Label(self.status_bar, text="Status: -"); self.lbl_sandwich_status.pack(side=tk.LEFT, padx=5)
        self.lbl_page_dims = ttk.Label(self.status_bar, text="Dimensi: -"); self.lbl_page_dims.pack(side=tk.LEFT, padx=5)
        self.progress = ttk.Progressbar(self.status_bar, orient=tk.HORIZONTAL, length=150, mode='determinate'); self.progress.pack(side=tk.RIGHT, padx=10)
        self.lbl_zoom_info = ttk.Label(self.status_bar, text="Zoom: 100%"); self.lbl_zoom_info.pack(side=tk.RIGHT, padx=5)

        # Viewport
        container = tk.Frame(self.root, bg="#323639"); container.pack(fill=tk.BOTH, expand=True)
        container.grid_columnconfigure(1, weight=1); container.grid_rowconfigure(1, weight=1)
        self.h_rule = tk.Canvas(container, height=25, bg="#e0e0e0", bd=0, highlightthickness=0)
        self.v_rule = tk.Canvas(container, width=25, bg="#e0e0e0", bd=0, highlightthickness=0)
        self.viewport = tk.Canvas(container, bg="#323639", bd=0, highlightthickness=0)
        self.h_rule.grid(row=0, column=1, sticky="ew"); self.v_rule.grid(row=1, column=0, sticky="ns"); self.viewport.grid(row=1, column=1, sticky="nsew")
        v_scr = ttk.Scrollbar(container, orient=tk.VERTICAL, command=self._sync_v); v_scr.grid(row=1, column=2, sticky="ns")
        self.viewport.configure(yscrollcommand=v_scr.set)
        self.viewport.bind("<Configure>", lambda e: self.controller.refresh())
        self.viewport.bind_all("<MouseWheel>", self._on_wheel)

    def set_application_title(self, filename):
        self.root.title(f"{self.base_title} - {filename}")

    def update_progress(self, value):
        self.progress['value'] = value; self.root.update()

    def get_viewport_size(self):
        self.root.update_idletasks(); return self.viewport.winfo_width(), self.viewport.winfo_height()

    def display_page(self, pix, ox, oy, region):
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        self.tk_img = ImageTk.PhotoImage(img); self.viewport.delete("all")
        self.viewport.create_image(ox, oy, anchor=tk.NW, image=self.tk_img)
        self.viewport.config(scrollregion=region); self.h_rule.config(scrollregion=region); self.v_rule.config(scrollregion=region)

    def draw_text_layer(self, words, ox, oy, zoom):
        for w in words:
            r_id = self.viewport.create_rectangle(w[0]*zoom+ox, w[1]*zoom+oy, w[2]*zoom+ox, w[3]*zoom+oy, outline="#0078d7", fill="#0078d7", stipple="gray25")
            self.viewport.tag_bind(r_id, "<Enter>", lambda e, t=w[4]: self._show_tooltip(e, t))
            self.viewport.tag_bind(r_id, "<Leave>", self._hide_tooltip); self.viewport.tag_bind(r_id, "<Motion>", self._move_tooltip)

    def draw_csv_layer(self, words, ox, oy, zoom):
        """Menggambar overlay dari CSV dengan warna Hijau"""
        for w in words:
            r_id = self.viewport.create_rectangle(w[0]*zoom+ox, w[1]*zoom+oy, w[2]*zoom+ox, w[3]*zoom+oy, outline="#28a745", fill="#28a745", stipple="gray25")
            self.viewport.tag_bind(r_id, "<Enter>", lambda e, t=w[4]: self._show_tooltip(e, t))
            self.viewport.tag_bind(r_id, "<Leave>", self._hide_tooltip); self.viewport.tag_bind(r_id, "<Motion>", self._move_tooltip)

    def draw_rulers(self, dw, dh, ox, oy, z):
        self.h_rule.delete("all"); self.v_rule.delete("all")
        step = 100 if z < 1.0 else 50
        for u in range(0, int(dw)+1, 10):
            if u % step == 0:
                self.h_rule.create_line(u*z+ox, 25, u*z+ox, 0)
                self.h_rule.create_text(u*z+ox+2, 2, text=str(u), anchor=tk.NW, font=("Arial", 7))
        for u in range(0, int(dh)+1, 10):
            if u % step == 0:
                self.v_rule.create_line(25, u*z+oy, 0, u*z+oy)
                self.v_rule.create_text(2, u*z+oy+2, text=str(u), anchor=tk.NW, font=("Arial", 7))

    def update_ui_info(self, page_num, total, zoom, is_sandwich, width, height, has_csv):
        """Sinkronisasi parameter dengan interface.py untuk menghilangkan peringatan IDE"""
        self.pg_ent.delete(0, tk.END); self.pg_ent.insert(0, str(page_num))
        self.lbl_total.config(text=f"/ {total}")
        self.text_toggle.config(state="normal" if is_sandwich else "disabled")
        self.csv_toggle.config(state="normal" if has_csv else "disabled")
        if not has_csv: self.csv_overlay_var.set(False)
        self.lbl_sandwich_status.config(text=f"Status: {'Sandwich' if is_sandwich else 'Image Only'}")
        self.lbl_page_dims.config(text=f"Dimensi: {int(width)}x{int(height)} pt")
        self.lbl_zoom_info.config(text=f"Zoom: {int(zoom*100)}%")
        self._hide_tooltip()

    def _on_export_csv(self):
        if not self.controller.doc: return
        win = tk.Toplevel(self.root); win.title("Pengaturan Ekspor"); win.geometry("450x250"); win.grab_set()
        path_var = tk.StringVar(value=os.getcwd())
        f_p = ttk.LabelFrame(win, text=" Folder Penyimpanan ", padding=10); f_p.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(f_p, textvariable=path_var, wraplength=300).pack(side=tk.LEFT)
        ttk.Button(f_p, text="Ubah", command=lambda: path_var.set(filedialog.askdirectory() or path_var.get())).pack(side=tk.RIGHT)
        f_r = ttk.LabelFrame(win, text=" Rentang Halaman ", padding=10); f_r.pack(fill=tk.X, padx=10, pady=5)
        ent_r = ttk.Entry(f_r); ent_r.insert(0, f"1-{len(self.controller.doc)}"); ent_r.pack(fill=tk.X)
        def _exec():
            idxs = self.controller.parse_page_ranges(ent_r.get(), len(self.controller.doc))
            if idxs is None: return messagebox.showerror("Error", "Range tidak valid")
            fname = f"Export_{os.path.basename(self.controller.doc.name).replace('.pdf', '.csv')}"
            win.destroy(); self.lbl_sandwich_status.config(text="Status: Mengekspor...")
            self.controller.export_text_to_csv(os.path.join(path_var.get(), fname), idxs)
            self.lbl_sandwich_status.config(text=f"Status: Berhasil ({len(idxs)} Hal)")
        ttk.Button(win, text="Batal", command=win.destroy).pack(side=tk.RIGHT, padx=10); ttk.Button(win, text="Ekspor", command=_exec).pack(side=tk.RIGHT)

    def _show_tooltip(self, e, txt):
        if self.tip_window or not txt: return
        self.tip_window = tw = tk.Toplevel(self.root); tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{e.x_root+15}+{e.y_root+10}")
        tk.Label(tw, text=txt, background="#ffffca", relief=tk.SOLID, borderwidth=1, font=("Arial", 9), padx=4).pack()

    def _move_tooltip(self, e):
        if self.tip_window: self.tip_window.wm_geometry(f"+{e.x_root+15}+{e.y_root+10}")

    def _hide_tooltip(self, e=None):
        if self.tip_window: self.tip_window.destroy(); self.tip_window = None

    def _on_open(self):
        p = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        if p: self.controller.open_document(p)

    def _sync_v(self, *a): self.viewport.yview(*a); self.v_rule.yview(*a)

    def _on_wheel(self, e):
        if e.state & 0x0004: self.controller.set_zoom("in" if e.delta > 0 else "out")
        else: d = int(-1*(e.delta/120)); self.viewport.yview_scroll(d, "units"); self.v_rule.yview_scroll(d, "units")