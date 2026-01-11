import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from interface import PDFViewInterface
from View.toolbar import ToolbarComponent
from View.viewport import ViewportComponent
from View.status_bar import StatusBarComponent
from View.tooltip import TooltipManager

class TkinterPDFView(PDFViewInterface):
    def __init__(self, root, controller_factory):
        self.root = root
        self.base_title = "Modular PDF Viewer Pro (MVC)"
        self.root.title(self.base_title)
        
        self.controller = controller_factory(self)
        self.tooltip = TooltipManager(self.root)
        self.text_layer_var = tk.BooleanVar(value=False)
        self.csv_overlay_var = tk.BooleanVar(value=False)
        
        self._setup_ui()

    def _setup_ui(self):
        self.toolbar = ToolbarComponent(self.root, self)
        self.toolbar.pack(side=tk.TOP, fill=tk.X)
        self.status_bar = StatusBarComponent(self.root)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.viewport = ViewportComponent(self.root)
        self.viewport.pack(fill=tk.BOTH, expand=True)
        
        # Local bind untuk scrolling mandiri
        self.viewport.canvas.bind("<Configure>", lambda e: self.controller.refresh(full_refresh=True))
        self.viewport.canvas.bind("<MouseWheel>", self._on_wheel)

    # --- IMPLEMENTASI INTERFACE ---
    def draw_rulers(self, dw, dh, ox, oy, zoom):
        self.viewport.h_rule.delete("all")
        self.viewport.v_rule.delete("all")
        step = 100 if zoom < 1.0 else 50
        for u in range(0, int(dw) + 1, 10):
            x = u * zoom + ox
            if u % step == 0:
                self.viewport.h_rule.create_line(x, 25, x, 0, fill="#333333")
                self.viewport.h_rule.create_text(x+2, 2, text=str(u), anchor=tk.NW, font=("Arial", 7))
        for u in range(0, int(dh) + 1, 10):
            y = u * zoom + oy
            if u % step == 0:
                self.viewport.v_rule.create_line(25, y, 0, y, fill="#333333")
                self.viewport.v_rule.create_text(2, y+2, text=str(u), anchor=tk.NW, font=("Arial", 7))

    def display_page(self, pix, ox, oy, region):
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        self.viewport.tk_img = ImageTk.PhotoImage(img)
        self.viewport.canvas.delete("pdf_bg")
        self.viewport.canvas.create_image(ox, oy, anchor=tk.NW, image=self.viewport.tk_img, tags="pdf_bg")
        self.viewport.canvas.tag_lower("pdf_bg")
        self.viewport.canvas.config(scrollregion=region)

    def draw_text_layer(self, words, ox, oy, zoom):
        self.viewport.canvas.delete("text_layer")
        self._draw_overlay(words, ox, oy, zoom, "#0078d7", "text_layer")

    def draw_csv_layer(self, words, ox, oy, zoom):
        self.viewport.canvas.delete("csv_layer")
        self._draw_overlay(words, ox, oy, zoom, "#28a745", "csv_layer")

    # --- FITUR HIGHLIGHT & GROUPING VISUAL ---
    def set_grouping_control_state(self, active):
        st = tk.NORMAL if active else tk.DISABLED
        if hasattr(self.toolbar, 'chk_group'): self.toolbar.chk_group.config(state=st)
        if hasattr(self.toolbar, 'ent_tolerance'): self.toolbar.ent_tolerance.config(state=st)

    def update_highlight_only(self, selected_id):
        """Update visual instan tanpa render ulang PDF"""
        self.viewport.canvas.itemconfig("csv_layer", width=1, outline="#28a745")
        
        # Highlight grup baris (Oranye)
        grouped_ids = self.controller.get_grouped_ids()
        for g_id in grouped_ids:
            self.viewport.canvas.itemconfig(f"item_{g_id}", width=3, outline="orange")
        
        # Highlight utama (Merah)
        target_tag = f"item_{selected_id}"
        self.viewport.canvas.itemconfig(target_tag, width=4, outline="red")
        self.viewport.canvas.tag_raise(target_tag)

    def _draw_overlay(self, words, ox, oy, zoom, color, tag):
        """Metode inti penampil overlay dengan tagging unik per ID"""
        selected_id = self.controller.model.selected_row_id
        grouped_ids = self.controller.get_grouped_ids() if tag == "csv_layer" else []

        for w in words:
            # w = (x0, y0, x1, y1, teks, nomor)
            x0, y0, x1, y1 = w[0], w[1], w[2], w[3]
            txt, row_id = w[4], w[5] if len(w) > 5 else None
            
            rid_str = str(row_id)
            is_active = (rid_str == str(selected_id))
            is_grouped = (rid_str in grouped_ids)

            o_col, l_wid = color, 1
            if is_active: o_col, l_wid = "red", 4
            elif is_grouped: o_col, l_wid = "orange", 3

            r_id = self.viewport.canvas.create_rectangle(
                x0*zoom+ox, y0*zoom+oy, x1*zoom+ox, y1*zoom+oy, 
                outline=o_col, width=l_wid, fill=color, stipple="gray25", 
                tags=(tag, f"item_{row_id}")
            )
            
            # Tooltip & Click Event Bindings
            self.viewport.canvas.tag_bind(r_id, "<Enter>", lambda e, t=txt, c=(x0,y0,x1,y1): self.tooltip.show(e,t,c))
            self.viewport.canvas.tag_bind(r_id, "<Leave>", lambda e: self.tooltip.hide())
            if tag == "csv_layer" and row_id:
                self.viewport.canvas.tag_bind(r_id, "<Button-1>", lambda e, rid=row_id: self.controller.handle_overlay_click(rid))

    def update_ui_info(self, pn, total, z, is_s, w, h, has_csv):
        self.toolbar.pg_ent.delete(0, tk.END); self.toolbar.pg_ent.insert(0, str(pn))
        self.toolbar.lbl_total.config(text=f"/ {total}")
        self.toolbar.text_toggle.config(state=tk.NORMAL if is_s else tk.DISABLED)
        self.toolbar.csv_toggle.config(state=tk.NORMAL if has_csv else tk.DISABLED)
        self.toolbar.btn_table.config(state=tk.NORMAL if has_csv else tk.DISABLED)

    # --- HANDLERS NAVIGASI ---
    def _on_open(self):
        p = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        if p: self.controller.open_document(p)

    def _on_view_csv_table(self):
        self.controller.open_csv_table()

    def _on_export_csv(self):
        pass # Silakan isi logika ekspor Anda kembali di sini

    def _on_wheel(self, e):
        d = int(-1*(e.delta/120))
        self.viewport.canvas.yview_scroll(d, "units")

    def set_application_title(self, f): self.root.title(f"{self.base_title} - {f}")
    def update_progress(self, v): self.status_bar.progress['value'] = v; self.root.update()
    def get_viewport_size(self): self.root.update_idletasks(); return self.viewport.canvas.winfo_width(), self.viewport.canvas.winfo_height()