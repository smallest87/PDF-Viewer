import tkinter as tk
from tkinter import filedialog, messagebox
import os
from interface import PDFViewInterface
from View.toolbar import ToolbarComponent
from View.viewport import ViewportComponent
from View.status_bar import StatusBarComponent
from View.tooltip import TooltipManager

class TkinterPDFView(PDFViewInterface):
    def __init__(self, root, controller_class):
        self.root = root
        self.base_title = "Modular PDF Viewer Pro"
        self.root.title(self.base_title)
        
        # Dependency Injection Controller
        self.controller = controller_class(self)
        
        # Inisialisasi Tooltip Manager
        self.tooltip = TooltipManager(self.root)
        
        # Variabel Kontrol untuk Toggle Layer (Dishare ke Toolbar)
        self.text_layer_var = tk.BooleanVar(value=False)
        self.csv_overlay_var = tk.BooleanVar(value=False)
        
        self._setup_ui()

    def _setup_ui(self):
        """Menyusun layout utama menggunakan sub-komponen"""
        # 1. Toolbar Atas
        self.toolbar = ToolbarComponent(self.root, self)
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        # 2. Status Bar Bawah
        self.status_bar = StatusBarComponent(self.root)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # 3. Viewport Tengah (Canvas & Rulers)
        self.viewport = ViewportComponent(self.root)
        self.viewport.pack(fill=tk.BOTH, expand=True)
        
        # Bindings event utama
        self.viewport.canvas.bind("<Configure>", lambda e: self.controller.refresh())
        self.viewport.canvas.bind_all("<MouseWheel>", self._on_wheel)

    # --- IMPLEMENTASI PDFViewInterface (WAJIB) ---

    def set_application_title(self, filename):
        self.root.title(f"{self.base_title} - {filename}")

    def update_progress(self, value):
        self.status_bar.progress['value'] = value
        self.root.update()

    def get_viewport_size(self):
        self.root.update_idletasks()
        return self.viewport.canvas.winfo_width(), self.viewport.canvas.winfo_height()

    def display_page(self, pix, ox, oy, region):
        from PIL import Image, ImageTk
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        self.viewport.tk_img = ImageTk.PhotoImage(img)
        self.viewport.canvas.delete("all")
        self.viewport.canvas.create_image(ox, oy, anchor=tk.NW, image=self.viewport.tk_img)
        self.viewport.canvas.config(scrollregion=region)
        self.viewport.h_rule.config(scrollregion=region)
        self.viewport.v_rule.config(scrollregion=region)

    def draw_text_layer(self, words, ox, oy, zoom):
        self._draw_overlay(words, ox, oy, zoom, color="#0078d7", tag="text_layer")

    def draw_csv_layer(self, words, ox, oy, zoom):
        self._draw_overlay(words, ox, oy, zoom, color="#28a745", tag="csv_layer")

    def draw_rulers(self, doc_w, doc_h, ox, oy, zoom):
        self.viewport.h_rule.delete("all")
        self.viewport.v_rule.delete("all")
        step = 100 if zoom < 1.0 else 50
        # Horizontal Ruler
        for u in range(0, int(doc_w)+1, 10):
            if u % step == 0:
                x = u * zoom + ox
                self.viewport.h_rule.create_line(x, 25, x, 0)
                self.viewport.h_rule.create_text(x+2, 2, text=str(u), anchor=tk.NW, font=("Arial", 7))
        # Vertical Ruler
        for u in range(0, int(doc_h)+1, 10):
            if u % step == 0:
                y = u * zoom + oy
                self.viewport.v_rule.create_line(25, y, 0, y)
                self.viewport.v_rule.create_text(2, y+2, text=str(u), anchor=tk.NW, font=("Arial", 7))

    def update_ui_info(self, page_num, total, zoom, is_sandwich, width, height, has_csv):
        # Update Navigasi di Toolbar
        self.toolbar.pg_ent.delete(0, tk.END)
        self.toolbar.pg_ent.insert(0, str(page_num))
        self.toolbar.lbl_total.config(text=f"/ {total}")
        
        # Update Status Toggle di Toolbar
        self.toolbar.text_toggle.config(state="normal" if is_sandwich else "disabled")
        self.toolbar.csv_toggle.config(state="normal" if has_csv else "disabled")
        if not has_csv: self.csv_overlay_var.set(False)
        
        # Update Label di Status Bar
        status_txt = "Sandwich" if is_sandwich else "Image Only"
        self.status_bar.lbl_status.config(text=f"Status: {status_txt}")
        self.status_bar.lbl_dims.config(text=f"Dimensi: {int(width)}x{int(height)} pt")
        self.status_bar.lbl_zoom.config(text=f"Zoom: {int(zoom*100)}%")
        self.tooltip.hide()

    # --- PRIVATE HELPERS ---

    def _draw_overlay(self, words, ox, oy, zoom, color, tag):
        """Helper internal untuk menggambar kotak overlay dengan pengiriman koordinat"""
        for w in words:
            # Koordinat asli: w[0]=x0, w[1]=top, w[2]=x1, w[3]=bottom
            x0, top, x1, bottom = w[0], w[1], w[2], w[3]
            text_content = w[4]

            r_id = self.viewport.canvas.create_rectangle(
                x0*zoom+ox, top*zoom+oy, x1*zoom+ox, bottom*zoom+oy, 
                outline=color, fill=color, stipple="gray25", tags=tag
            )
            
            # WAJIB: Kirim tuple koordinat (x0, top, x1, bottom) ke tooltip
            self.viewport.canvas.tag_bind(
                r_id, "<Enter>", 
                lambda e, t=text_content, c=(x0, top, x1, bottom): self.tooltip.show(e, t, c)
            )
            self.viewport.canvas.tag_bind(r_id, "<Leave>", lambda e: self.tooltip.hide())
            self.viewport.canvas.tag_bind(r_id, "<Motion>", self.tooltip.move)

    def _on_open(self):
        p = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        if p: self.controller.open_document(p)

    def _on_export_csv(self):
        """Menangani dialog ekspor dinamis"""
        if not self.controller.doc: return
        win = tk.Toplevel(self.root)
        win.title("Pengaturan Ekspor"); win.geometry("450x250"); win.grab_set()
        
        path_var = tk.StringVar(value=os.getcwd())
        f_p = tk.LabelFrame(win, text=" Folder Penyimpanan ", padx=10, pady=10)
        f_p.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(f_p, textvariable=path_var, wraplength=300, justify="left").pack(side=tk.LEFT)
        tk.Button(f_p, text="Ubah", command=lambda: path_var.set(filedialog.askdirectory() or path_var.get())).pack(side=tk.RIGHT)
        
        f_r = tk.LabelFrame(win, text=" Rentang Halaman ", padx=10, pady=10)
        f_r.pack(fill=tk.X, padx=10, pady=5)
        ent_r = tk.Entry(f_r)
        ent_r.insert(0, f"1-{len(self.controller.doc)}")
        ent_r.pack(fill=tk.X)
        
        def _exec():
            idxs = self.controller.parse_page_ranges(ent_r.get(), len(self.controller.doc))
            if idxs is None: return messagebox.showerror("Error", "Range tidak valid")
            fname = f"{os.path.basename(self.controller.doc.name).replace('.pdf', '.csv')}"
            win.destroy()
            self.status_bar.lbl_status.config(text="Status: Mengekspor...")
            self.controller.export_text_to_csv(os.path.join(path_var.get(), fname), idxs)
            self.status_bar.lbl_status.config(text=f"Status: Berhasil ({len(idxs)} Hal)")

        btn_f = tk.Frame(win, pady=10)
        btn_f.pack(side=tk.BOTTOM, fill=tk.X)
        tk.Button(btn_f, text="Batal", command=win.destroy).pack(side=tk.RIGHT, padx=10)
        tk.Button(btn_f, text="Ekspor", command=_exec).pack(side=tk.RIGHT)

    def _on_wheel(self, e):
        if e.state & 0x0004: self.controller.set_zoom("in" if e.delta > 0 else "out")
        else:
            d = int(-1*(e.delta/120))
            self.viewport.canvas.yview_scroll(d, "units")
            self.viewport.v_rule.yview_scroll(d, "units")