import fitz
import os
import csv

class PDFController:
    """
    Controller utama yang mengelola logika bisnis dan sinkronisasi data.
    Dioptimalkan untuk sistem Dockable Panel PyQt6.
    """
    def __init__(self, view, model):
        self.view = view
        self.model = model
        
        # Inisialisasi atribut untuk menghindari AttributeError
        self.table_view = None 
        
        # Inisialisasi Manager
        from Controller.document_mgr import DocumentManager
        from Controller.overlay_mgr import OverlayManager
        from Controller.export_mgr import ExportManager
        
        self.doc_mgr = DocumentManager(self.model)
        self.overlay_mgr = OverlayManager()
        self.export_mgr = ExportManager()

        # State & Cache RAM untuk performa tinggi
        self.group_tolerance = 2.0
        self.page_data_cache = [] 

    # --- LOGIKA DOKUMEN & NAVIGASI ---

    def open_document(self, path):
        """Membuka PDF dan mengeset path CSV secara otomatis"""
        fname = self.doc_mgr.open_pdf(path)
        if fname:
            self.model.file_name = fname
            self.model.file_path = path
            self.model.csv_path = path.rsplit('.', 1)[0] + ".csv"
            self.view.set_application_title(fname)
            self.refresh(full_refresh=True)

    def change_page(self, delta):
        """Pindah halaman dan reset seleksi baris"""
        if self.doc_mgr.move_page(delta):
            self.model.selected_row_id = None
            self.refresh(full_refresh=True)

    def jump_to_page(self, page_num):
        if self.model.doc and 0 < page_num <= self.model.total_pages:
            self.model.current_page = page_num - 1
            self.model.selected_row_id = None
            self.refresh(full_refresh=True)

    def set_zoom(self, direction):
        self.doc_mgr.set_zoom(direction)
        self.refresh(full_refresh=True)

    # --- TOGGLE LAYER ---

    def toggle_text_layer(self, visible):
        self.overlay_mgr.show_text_layer = visible
        self.refresh(full_refresh=False)

    def toggle_csv_layer(self, visible):
        self.overlay_mgr.show_csv_layer = visible
        self.refresh(full_refresh=False)

    # --- LOGIKA PANEL TABEL (DOCKING SYSTEM) ---

    def open_csv_table(self):
        """Memerintahkan View untuk menampilkan panel CSV di dalam Dock"""
        if not self.model.has_csv:
            return
            
        try:
            with open(self.model.csv_path, mode='r', encoding='utf-8-sig') as f:
                reader = csv.reader(f, delimiter=';')
                headers = next(reader)
                data = [list(row) for row in reader]
            
            # Panggil metode interface untuk memunculkan panel dock
            self.view.show_csv_panel(headers, data)
        except Exception as e:
            print(f"Gagal memuat tabel: {e}")

    def _handle_table_click(self, row_data):
        """Sinkronisasi: Klik baris di Panel -> Highlight PDF"""
        try:
            row_id = str(row_data[0])
            target_page = int(row_data[1]) - 1
            self.model.selected_row_id = row_id
            
            if target_page == self.model.current_page:
                self.view.update_highlight_only(row_id)
            else:
                self.model.current_page = target_page
                self.refresh(full_refresh=True)
        except Exception as e:
            print(f"Error sinkronisasi tabel: {e}")

    def handle_overlay_click(self, row_id):
        """Sinkronisasi: Klik PDF -> Highlight di Panel Tabel"""
        self.model.selected_row_id = str(row_id)
        # Delegasikan ke view untuk memperbarui highlight di PDF dan seleksi di tabel dock
        self.view.update_highlight_only(row_id)

    # --- LOGIKA GROUPING (RAM CACHE) ---

    def get_grouped_ids(self):
        """Mencari ID elemen yang sejajar secara vertikal menggunakan cache RAM"""
        if not self.view.toolbar.chk_group.isChecked() or not self.model.selected_row_id:
            return set()

        target = next((d for d in self.page_data_cache if str(d[5]) == str(self.model.selected_row_id)), None)
        if not target:
            return set()

        # Sumbu tengah target: (y0 + y1) / 2
        t_sumbu = (target[1] + target[3]) / 2
        grouped_ids = set()
        
        for d in self.page_data_cache:
            curr_sumbu = (d[1] + d[3]) / 2
            # Menggunakan formula toleransi: $$|S_{target} - S_{current}| \leq \delta$$
            if abs(curr_sumbu - t_sumbu) <= self.group_tolerance:
                grouped_ids.add(str(d[5]))
                
        return grouped_ids

    def toggle_line_grouping(self):
        """Hanya update tampilan jika ada baris yang dipilih"""
        if self.model.selected_row_id:
            self.view.update_highlight_only(self.model.selected_row_id)
        # Jika tidak ada yang dipilih, fungsi diam saja (hanya mengganti state centang)

    def update_tolerance(self, val):
        try:
            self.group_tolerance = float(str(val).replace(',', '.'))
            self.view.update_highlight_only(self.model.selected_row_id)
        except ValueError:
            pass

    # --- REFRESH ENGINE ---

    def refresh(self, full_refresh=True):
        """Orkestrasi rendering halaman dan layer overlay"""
        if not self.model.doc:
            return
            
        page = self.model.doc[self.model.current_page]
        vw, _ = self.view.get_viewport_size()
        z = self.model.zoom_level

        if full_refresh:
            # Render PDF Pixmap
            pix = page.get_pixmap(matrix=fitz.Matrix(z, z))
            ox, oy = max(0, (vw - pix.width) / 2), self.model.padding
            region = (0, 0, max(vw, pix.width), pix.height + (oy * 2))
            
            self.view.display_page(pix, ox, oy, region)
            self.view.draw_rulers(page.rect.width, page.rect.height, ox, oy, z)
            
            # Update Cache RAM dari data CSV untuk halaman ini
            if os.path.exists(self.model.csv_path or ""):
                self.overlay_mgr.csv_path = self.model.csv_path
                self.page_data_cache = self.overlay_mgr.get_csv_data(self.model.current_page + 1)
            else:
                self.page_data_cache = []
        else:
            ox = max(0, (vw - (page.rect.width * z)) / 2)
            oy = self.model.padding

        # Render Layer Teks
        if self.overlay_mgr.show_text_layer:
            self.view.draw_text_layer(page.get_text("words"), ox, oy, z)
        else:
            self.view.clear_overlay_layer("text_layer")
        
        # Render Layer CSV (Ambil dari cache RAM)
        if self.overlay_mgr.show_csv_layer:
            self.view.draw_csv_layer(self.page_data_cache, ox, oy, z)
        else:
            self.view.clear_overlay_layer("csv_layer")

        # Sinkronisasi Informasi UI
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
        # self.view.set_grouping_control_state(self.model.selected_row_id is not None)
        self.view.set_grouping_control_state(self.model.doc is not None)