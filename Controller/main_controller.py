import fitz
import os
import csv

class PDFController:
    """
    Controller utama yang mengatur alur data antara Model dan View.
    Telah dioptimalkan dengan Caching RAM untuk performa grouping yang instan.
    """
    def __init__(self, view, model):
        self.view = view
        self.model = model
        self.table_view = None 
        
        # Inisialisasi Manager Independen
        from Controller.document_mgr import DocumentManager
        from Controller.overlay_mgr import OverlayManager
        from Controller.export_mgr import ExportManager
        
        self.doc_mgr = DocumentManager(self.model)
        self.overlay_mgr = OverlayManager()
        self.export_mgr = ExportManager()

        # State Kontrol & Cache RAM
        self.group_tolerance = 2.0
        self.page_data_cache = [] # Menyimpan data CSV halaman aktif di memori

    # --- LOGIKA DOKUMEN & NAVIGASI ---

    def open_document(self, path):
        """Membuka PDF dan menginisialisasi path CSV terkait"""
        fname = self.doc_mgr.open_pdf(path)
        if fname:
            self.model.file_name = fname
            self.model.file_path = path
            # Asumsi standar: nama_file.pdf -> nama_file.csv
            self.model.csv_path = path.rsplit('.', 1)[0] + ".csv"
            self.view.set_application_title(fname)
            self.refresh(full_refresh=True)

    def change_page(self, delta):
        """Berpindah halaman dan mereset state seleksi"""
        if self.doc_mgr.move_page(delta):
            self.model.selected_row_id = None
            self.refresh(full_refresh=True)

    def jump_to_page(self, page_num):
        """Navigasi langsung ke nomor halaman tertentu"""
        if self.model.doc and 0 < page_num <= self.model.total_pages:
            self.model.current_page = page_num - 1
            self.model.selected_row_id = None
            self.refresh(full_refresh=True)

    def set_zoom(self, direction):
        """Mengatur skala zoom dan merender ulang tampilan"""
        self.doc_mgr.set_zoom(direction)
        self.refresh(full_refresh=True)

    # --- TOGGLE LAYER CONTROLS (FIXED) ---

    def toggle_text_layer(self, visible):
        """Mengaktifkan atau menyembunyikan layer teks PDF"""
        self.overlay_mgr.show_text_layer = visible
        self.refresh(full_refresh=False)

    def toggle_csv_layer(self, visible):
        """Mengaktifkan atau menyembunyikan layer overlay CSV"""
        self.overlay_mgr.show_csv_layer = visible
        self.refresh(full_refresh=False)

    # --- JANTUNG APLIKASI: REFRESH LOGIC ---

    def refresh(self, full_refresh=True):
        """Koordinasi utama rendering PDF dan Overlay"""
        if not self.model.doc: return
        
        page = self.model.doc[self.model.current_page]
        vw, _ = self.view.get_viewport_size()
        z = self.model.zoom_level

        if full_refresh:
            # 1. Render PDF Pixmap
            pix = page.get_pixmap(matrix=fitz.Matrix(z, z))
            ox, oy = max(0, (vw - pix.width) / 2), self.model.padding
            region = (0, 0, max(vw, pix.width), pix.height + (oy * 2))
            
            self.view.display_page(pix, ox, oy, region)
            self.view.draw_rulers(page.rect.width, page.rect.height, ox, oy, z)
            
            # 2. FIX: Sinkronisasi path dan Update Cache RAM
            if os.path.exists(self.model.csv_path or ""):
                self.overlay_mgr.csv_path = self.model.csv_path
                self.page_data_cache = self.overlay_mgr.get_csv_data(self.model.current_page + 1)
            else:
                self.page_data_cache = []
        else:
            # Kalkulasi offset ulang tanpa re-render PDF (Fast Toggle)
            ox = max(0, (vw - (page.rect.width * z)) / 2)
            oy = self.model.padding

        # 3. Pengelolaan Layer Teks
        if self.overlay_mgr.show_text_layer:
            self.view.draw_text_layer(page.get_text("words"), ox, oy, z)
        else:
            self.view.clear_overlay_layer("text_layer")
        
        # 4. Pengelolaan Layer CSV (Menggunakan Cache RAM)
        if self.overlay_mgr.show_csv_layer:
            self.view.draw_csv_layer(self.page_data_cache, ox, oy, z)
        else:
            self.view.clear_overlay_layer("csv_layer")

        # 5. Sinkronisasi UI Info
        self.model.has_csv = os.path.exists(self.model.csv_path or "")
        self.view.update_ui_info(
            self.model.current_page + 1, 
            self.model.total_pages, 
            z, 
            bool(page.get_text().strip()), 
            page.rect.width, 
            page.rect.height, 
            self.model.has_csv
        )
        self.view.set_grouping_control_state(self.model.selected_row_id is not None)

    # --- LOGIKA GROUPING & INTERAKSI ---

    def get_grouped_ids(self):
        """Mencari elemen dalam satu grup baris (sumbu vertikal sama)"""
        if not self.view.toolbar.chk_group.isChecked() or not self.model.selected_row_id:
            return set()

        target = next((d for d in self.page_data_cache if str(d[5]) == str(self.model.selected_row_id)), None)
        if not target: return set()

        t_sumbu = (target[1] + target[3]) / 2
        grouped_ids = set()
        
        for d in self.page_data_cache:
            curr_sumbu = (d[1] + d[3]) / 2
            if abs(curr_sumbu - t_sumbu) <= self.group_tolerance:
                grouped_ids.add(str(d[5]))
        return grouped_ids

    def toggle_line_grouping(self):
        """Update highlight saat opsi grouping diubah"""
        self.view.update_highlight_only(self.model.selected_row_id)

    def update_tolerance(self, val):
        """Update nilai toleransi sumbu dari input toolbar"""
        try:
            self.group_tolerance = float(str(val).replace(',', '.'))
            self.view.update_highlight_only(self.model.selected_row_id)
        except: pass

    def open_csv_table(self):
        """Membuka window inspeksi tabel CSV"""
        if not self.model.has_csv: return
        from View.csv_table_view import PyQt6CSVTableView
        try:
            with open(self.model.csv_path, mode='r', encoding='utf-8-sig') as f:
                reader = csv.reader(f, delimiter=';')
                headers = next(reader)
                data = [list(row) for row in reader]
            
            if self.table_view and self.table_view.isVisible():
                self.table_view.raise_()
                self.table_view.activateWindow()
            else:
                self.table_view = PyQt6CSVTableView(
                    self.view, self.model.file_name, headers, data,
                    on_row_select_callback=self._handle_table_click
                )
                self.table_view.show()
        except Exception as e:
            print(f"Error: {e}")

    def _handle_table_click(self, row_data):
        """Sinkronisasi: Tabel -> Viewport PDF"""
        try:
            row_id, target_page = str(row_data[0]), int(row_data[1]) - 1
            self.model.selected_row_id = row_id
            if target_page == self.model.current_page:
                self.view.update_highlight_only(row_id)
            else:
                self.model.current_page = target_page
                self.refresh(full_refresh=True)
        except: pass

    def handle_overlay_click(self, row_id):
        """Sinkronisasi: Viewport PDF -> Tabel"""
        self.model.selected_row_id = str(row_id)
        self.view.update_highlight_only(row_id)
        if self.table_view and self.table_view.isVisible():
            idx = int(row_id) - 1
            self.table_view.select_row_by_index(idx)