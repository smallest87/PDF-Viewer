import fitz
import os
import csv
import tkinter as tk
from View.csv_table_view import CSVTableView

class PDFController:
    def __init__(self, view, model):
        self.view = view
        self.model = model
        self.table_view = None 
        
        from Controller.document_mgr import DocumentManager
        from Controller.overlay_mgr import OverlayManager
        from Controller.export_mgr import ExportManager
        
        self.doc_mgr = DocumentManager(self.model)
        self.overlay_mgr = OverlayManager()
        self.export_mgr = ExportManager()

        # Atribut untuk Fitur Line Grouping
        self.line_grouping_enabled_var = tk.BooleanVar(value=False)
        self.group_tolerance = 2.0

    def open_document(self, path):
        """Membuka PDF dan merender awal"""
        fname = self.doc_mgr.open_pdf(path)
        if fname:
            self.model.file_name = fname
            self.model.file_path = path
            self.model.csv_path = path.rsplit('.', 1)[0] + ".csv"
            self.view.set_application_title(fname)
            self.refresh(full_refresh=True)

    def open_csv_table(self):
        """Membuka window tabel data CSV"""
        if not self.model.has_csv: return
        headers, data = [], []
        try:
            with open(self.model.csv_path, mode='r', encoding='utf-8-sig') as f:
                reader = csv.reader(f, delimiter=';')
                headers = next(reader)
                data = [row for row in reader]
            
            if self.table_view and self.table_view.winfo_exists():
                self.table_view.focus_force()
            else:
                self.table_view = CSVTableView(
                    self.view.root, self.model.file_name, headers, data,
                    on_row_select_callback=self._handle_table_click
                )
        except Exception as e: print(f"Error Muat Tabel: {e}")

    # --- LOGIKA LINE GROUPING (BERDASARKAN KOLOM SUMBU) ---
    def toggle_line_grouping(self):
        """Trigger pembaruan visual saat checkbox grouping diklik"""
        self.view.update_highlight_only(self.model.selected_row_id)

    def update_tolerance(self, val):
        """Memperbarui nilai toleransi sumbu vertikal dari input user"""
        try:
            # Formula: |sumbu_target - sumbu_elemen| <= toleransi
            self.group_tolerance = float(str(val).replace(',', '.'))
            self.view.update_highlight_only(self.model.selected_row_id)
        except ValueError:
            print("Nilai toleransi harus berupa angka.")

    def get_grouped_ids(self):
        """Mencari ID elemen yang memiliki 'sumbu' serupa di halaman yang sama"""
        if not self.line_grouping_enabled_var.get() or not self.model.selected_row_id:
            return []

        grouped_ids = []
        try:
            with open(self.model.csv_path, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f, delimiter=';')
                rows = list(reader)
                
                # Cari baris yang saat ini dipilih
                target = next((r for r in rows if str(r.get('nomor')) == str(self.model.selected_row_id)), None)
                if not target: return []

                target_sumbu = float(target['sumbu'].replace(',', '.'))
                target_page = str(target['halaman'])

                for r in rows:
                    if str(r['halaman']) == target_page:
                        curr_sumbu = float(r['sumbu'].replace(',', '.'))
                        # Cek kedekatan posisi vertikal berdasarkan sumbu tengah
                        if abs(curr_sumbu - target_sumbu) <= self.group_tolerance:
                            grouped_ids.append(str(r['nomor']))
        except: pass
        return grouped_ids

    # --- NAVIGASI & REFRESH ---
    def _handle_table_click(self, row_data):
        try:
            row_id = str(row_data[0])
            old_page = self.model.current_page
            target_page = int(row_data[1]) - 1 
            self.model.selected_row_id = row_id
            
            if target_page == old_page:
                self.view.update_highlight_only(row_id)
            else:
                self.model.current_page = target_page
                self.refresh(full_refresh=True)
        except: pass

    def handle_overlay_click(self, row_id):
        self.model.selected_row_id = str(row_id)
        self.view.update_highlight_only(row_id)
        if self.table_view and self.table_view.winfo_exists():
            idx = int(row_id) - 1
            self.view.root.after(0, lambda: self.table_view.select_row_by_index(idx))

    def refresh(self, full_refresh=True):
        if not self.model.doc: return
        page = self.model.doc[self.model.current_page]
        vw, _ = self.view.get_viewport_size()
        z = self.model.zoom_level

        if full_refresh:
            mat = fitz.Matrix(z, z)
            pix = page.get_pixmap(matrix=mat)
            ox, oy = max(0, (vw - pix.width) / 2), self.model.padding
            region = (0, 0, max(vw, pix.width), pix.height + (oy * 2))
            self.view.display_page(pix, ox, oy, region)
            self.view.draw_rulers(page.rect.width, page.rect.height, ox, oy, z)
        else:
            ox = max(0, (vw - (page.rect.width * z)) / 2)
            oy = self.model.padding

        if self.overlay_mgr.show_text_layer:
            self.view.draw_text_layer(page.get_text("words"), ox, oy, z)
        
        if self.overlay_mgr.show_csv_layer:
            self.overlay_mgr.csv_path = self.model.csv_path
            data = self.overlay_mgr.get_csv_data(self.model.current_page + 1)
            self.view.draw_csv_layer(data, ox, oy, z)

        self.model.is_sandwich = bool(page.get_text().strip())
        self.model.has_csv = os.path.exists(self.model.csv_path or "")
        self.view.update_ui_info(self.model.current_page + 1, len(self.model.doc), z, 
                                 self.model.is_sandwich, page.rect.width, page.rect.height, self.model.has_csv)
        # Aktifkan/matikan tombolGrouping berdasarkan ada tidaknya seleksi
        self.view.set_grouping_control_state(self.model.selected_row_id is not None)

    def change_page(self, d):
        if self.doc_mgr.move_page(d): self.refresh(full_refresh=True)
    def set_zoom(self, d):
        self.doc_mgr.set_zoom(d)
        self.refresh(full_refresh=True)
    def jump_to_page(self, n):
        if self.model.doc and 0 < n <= len(self.model.doc):
            self.model.current_page = n - 1
            self.refresh(full_refresh=True)
    def toggle_text_layer(self, v):
        self.overlay_mgr.show_text_layer = v
        self.refresh(full_refresh=False)
    def toggle_csv_layer(self, v):
        self.overlay_mgr.show_csv_layer = v
        self.refresh(full_refresh=False)