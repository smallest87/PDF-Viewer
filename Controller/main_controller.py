import fitz
import os
import csv

class PDFController:
    def __init__(self, view, model):
        self.view = view
        self.model = model
        
        from Controller.document_mgr import DocumentManager
        from Controller.overlay_mgr import OverlayManager
        from Controller.export_mgr import ExportManager
        
        self.doc_mgr = DocumentManager(self.model)
        self.overlay_mgr = OverlayManager()
        self.export_mgr = ExportManager()

        self.group_tolerance = 2.0
        self.page_data_cache = [] 

    def open_document(self, path):
        fname = self.doc_mgr.open_pdf(path)
        if fname:
            self.model.file_name = fname
            self.model.file_path = path
            self.model.csv_path = path.rsplit('.', 1)[0] + ".csv"
            self.view.set_application_title(fname)
            self.refresh(full_refresh=True)

    def save_csv_data(self, headers, data):
        """Menulis ulang file CSV secara fisik dan memperbarui cache overlay."""
        if not self.model.csv_path: return
        try:
            with open(self.model.csv_path, mode='w', encoding='utf-8-sig', newline='') as f:
                # Gunakan quoting minimal agar semicolon aman terbungkus tanda kutip
                writer = csv.writer(f, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                writer.writerow(headers)
                writer.writerows(data)
            
            # SINKRONISASI: Update data overlay agar perubahan teks langsung muncul di PDF
            self.page_data_cache = self.overlay_mgr.get_csv_data(self.model.current_page + 1)
            print(f"[DEBUG] Auto-save berhasil ke: {self.model.csv_path}")
        except Exception as e:
            print(f"[ERROR] Gagal menyimpan data CSV: {e}")

    def change_page(self, delta):
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

    def toggle_text_layer(self, visible):
        self.overlay_mgr.show_text_layer = visible
        self.refresh(full_refresh=False)

    def toggle_csv_layer(self, visible):
        self.overlay_mgr.show_csv_layer = visible
        self.refresh(full_refresh=False)

    def open_csv_table(self):
        """Membuka tabel dari file CSV yang ada."""
        if not self.model.has_csv: return
        try:
            with open(self.model.csv_path, mode='r', encoding='utf-8-sig', newline='') as f:
                reader = csv.reader(f, delimiter=';', quotechar='"')
                headers = next(reader)
                data = [list(row) for row in reader]
            self.view.show_csv_panel(headers, data)
        except Exception as e:
            print(f"Gagal memuat tabel: {e}")

    def _handle_table_click(self, row_data):
        try:
            row_id = str(row_data[0])
            if self.model.selected_row_id == row_id: return
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
        self.model.selected_row_id = str(row_id)
        self.view.update_highlight_only(row_id)

    def get_grouped_ids(self):
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
        if self.model.selected_row_id: self.view.update_highlight_only(self.model.selected_row_id)

    def update_tolerance(self, val):
        try:
            self.group_tolerance = float(str(val).replace(',', '.'))
            if self.model.selected_row_id: self.view.update_highlight_only(self.model.selected_row_id)
        except ValueError: pass

    def refresh(self, full_refresh=True):
        if not self.model.doc: return
        page = self.model.doc[self.model.current_page]
        vw, _ = self.view.get_viewport_size()
        z = self.model.zoom_level

        if full_refresh:
            pix = page.get_pixmap(matrix=fitz.Matrix(z, z))
            ox, oy = max(0, (vw - pix.width) / 2), self.model.padding
            region = (0, 0, max(vw, pix.width), pix.height + (oy * 2))
            self.view.display_page(pix, ox, oy, region)
            self.view.draw_rulers(page.rect.width, page.rect.height, ox, oy, z)
            if os.path.exists(self.model.csv_path or ""):
                self.overlay_mgr.csv_path = self.model.csv_path
                self.page_data_cache = self.overlay_mgr.get_csv_data(self.model.current_page + 1)
            else:
                self.page_data_cache = []
        else:
            ox = max(0, (vw - (page.rect.width * z)) / 2)
            oy = self.model.padding

        if self.overlay_mgr.show_text_layer:
            self.view.draw_text_layer(page.get_text("words"), ox, oy, z)
        else:
            self.view.clear_overlay_layer("text_layer")
        
        if self.overlay_mgr.show_csv_layer:
            self.view.draw_csv_layer(self.page_data_cache, ox, oy, z)
        else:
            self.view.clear_overlay_layer("csv_layer")

        self.model.has_csv = os.path.exists(self.model.csv_path or "")
        self.view.update_ui_info(
            self.model.current_page + 1, self.model.total_pages, z, 
            bool(page.get_text().strip()), page.rect.width, page.rect.height, self.model.has_csv
        )
        self.view.set_grouping_control_state(self.model.doc is not None)

        if self.model.selected_row_id:
            self.view.update_highlight_only(self.model.selected_row_id)

    def start_export(self, path, range_str):
        if not self.model.doc: return
        indices = self.export_mgr.parse_ranges(range_str, self.model.total_pages)
        if indices is not None:
            self.export_mgr.to_csv(self.model.doc, path, indices, self.view)
            self.refresh(full_refresh=False)