import csv
import os

import fitz

from Controller.app_state import app_state
from Controller.document_mgr import DocumentManager
from Controller.export_mgr import ExportManager
from Controller.overlay_mgr import OverlayManager


class PDFController:
    def __init__(self, view, model):
        self.view = view
        self.model = model

        self._doc_mgr = DocumentManager(self.model)
        self._overlay_mgr = OverlayManager()
        self._export_mgr = ExportManager()

        # Konfigurasi Internal
        self._group_tolerance = 2.0
        self._page_data_cache = []  # Cache data CSV per halaman
        self._words_cache = {}  # Cache teks PDF: {page_index: words_list}

        # SINKRONISASI GLOBAL: Setiap jendela bereaksi jika ada perubahan status global
        app_state.visibility_changed.connect(self._on_global_state_changed)

    def _refresh(self, full_refresh=True):
        """Fungsi utama penyegaran tampilan dengan sistem Caching."""
        if not self.model.doc:
            return

        p_idx = self.model.current_page
        page = self.model.doc[p_idx]
        vw, _ = self.view.get_viewport_size()
        z = self.model.zoom_level

        # Sinkronisasi status layer dengan Global App State sebelum rendering
        self._overlay_mgr.show_text_layer = app_state.get_visibility("text_layer")
        self._overlay_mgr.show_csv_layer = app_state.get_visibility("csv_layer")

        # --- TAHAP 1: RENDERING GAMBAR (PIXMAP) ---
        if full_refresh:
            pix = page.get_pixmap(matrix=fitz.Matrix(z, z))
            ox, oy = max(0, (vw - pix.width) / 2), self.model.padding
            region = (0, 0, max(vw, pix.width), pix.height + (oy * 2))
            self.view.display_page(pix, ox, oy, region)
            self.view.draw_rulers(page.rect.width, page.rect.height, ox, oy, z)

            # Ambil data CSV dari cache memori (Bukan Disk)
            self._page_data_cache = self._overlay_mgr.get_csv_data(p_idx + 1)
        else:
            # Kalkulasi ulang offset jika hanya zoom/toggle layer tanpa reload pixmap
            ox = max(0, (vw - (page.rect.width * z)) / 2)
            oy = self.model.padding

        # --- TAHAP 2: RENDERING TEKS LAYER (CACHE) ---
        if p_idx not in self._words_cache:
            self._words_cache[p_idx] = page.get_text("words")

        if self._overlay_mgr.show_text_layer:
            self.view.draw_text_layer(self._words_cache[p_idx], ox, oy, z)
        else:
            self.view.clear_overlay_layer("text_layer")

        # --- TAHAP 3: RENDERING CSV OVERLAY ---
        if self._overlay_mgr.show_csv_layer:
            self.view.draw_csv_layer(self._page_data_cache, ox, oy, z)
        else:
            self.view.clear_overlay_layer("csv_layer")

        # --- TAHAP 4: SINKRONISASI UI ---
        self.model.has_csv = os.path.exists(self.model.csv_path or "")
        # Kirim data p, t, z, s, w, h, c untuk child_nav_bar
        self.view.update_ui_info(
            p_idx + 1,
            self.model.total_pages,
            z,
            bool(page.get_text().strip()),
            page.rect.width,
            page.rect.height,
            self.model.has_csv,
        )
        self.view.set_grouping_control_state(self.model.doc is not None)

        if self.model.selected_row_id:
            self.view.update_highlight_only(self.model.selected_row_id)

    def _on_global_state_changed(self, tag, is_visible):
        """Update visibilitas layer berdasarkan sinyal dari App State."""
        if tag == "text_layer":
            self._overlay_mgr.show_text_layer = is_visible
        elif tag == "csv_layer":
            self._overlay_mgr.show_csv_layer = is_visible
        self._refresh(full_refresh=False)  # Refresh tanpa render ulang pixmap
        print(f"[DEBUG] Global state changed: {tag} set to {is_visible}")

    def open_document(self, path):
        """Memuat dokumen dan melakukan pre-indexing CSV untuk performa."""
        fname = self._doc_mgr.open_pdf(path)
        if fname:
            self.model.file_name = fname
            self.model.file_path = path
            self.model.csv_path = path.rsplit(".", 1)[0] + ".csv"
            self._words_cache = {}  # Reset cache teks untuk dokumen baru

            # OPTIMASI: Indexing CSV satu kali di awal
            if os.path.exists(self.model.csv_path):
                self._overlay_mgr.load_csv_to_cache(self.model.csv_path)

            self.view.set_application_title(fname)
            self._refresh(full_refresh=True)

    def save_csv_data(self, headers, data):
        """Menyimpan data dan langsung memperbarui cache overlay."""
        if not self.model.csv_path:
            return
        try:
            with open(
                self.model.csv_path, mode="w", encoding="utf-8-sig", newline=""
            ) as f:
                writer = csv.writer(
                    f, delimiter=";", quotechar='"', quoting=csv.QUOTE_MINIMAL
                )
                writer.writerow(headers)
                writer.writerows(data)

            # Update cache internal agar perubahan langsung terlihat di viewport
            self._overlay_mgr.load_csv_to_cache(self.model.csv_path)
            self._page_data_cache = self._overlay_mgr.get_csv_data(
                self.model.current_page + 1
            )
            self._refresh(full_refresh=False)
        except Exception as e:
            print(f"[ERROR] Auto-save gagal: {e}")

    def change_page(self, delta):
        if self._doc_mgr.move_page(delta):
            self.model.selected_row_id = None
            self._refresh(full_refresh=True)

    def jump_to_page(self, page_num):
        if self.model.doc and 0 < page_num <= self.model.total_pages:
            self.model.current_page = page_num - 1
            self.model.selected_row_id = None
            self._refresh(full_refresh=True)

    def set_zoom(self, direction):
        self._doc_mgr.set_zoom(direction)
        self._refresh(full_refresh=True)
        print(f"Zoom level sekarang: {self.model.zoom_level}")

    def open_csv_table(self):
        """Membuka data CSV ke panel Dock utama."""
        if not self.model.has_csv:
            return
        try:
            with open(
                self.model.csv_path, mode="r", encoding="utf-8-sig", newline=""
            ) as f:
                reader = csv.reader(f, delimiter=";", quotechar='"')
                headers = next(reader)
                data = [list(row) for row in reader]
            self.view.show_csv_panel(headers, data)
        except Exception as e:
            print(f"Gagal memuat tabel: {e}")

    def _handle_table_click(self, row_data):
        """Sinkronisasi saat baris di tabel Dock diklik."""
        try:
            row_id = str(row_data[0])
            if self.model.selected_row_id == row_id:
                return
            target_page = int(row_data[1]) - 1
            self.model.selected_row_id = row_id

            if target_page == self.model.current_page:
                self.view.update_highlight_only(row_id)
            else:
                self.model.current_page = target_page
                self._refresh(full_refresh=True)
        except Exception as e:
            print(f"Error sinkronisasi tabel: {e}")

    def _on_overlay_click(self, row_id):
        """Aksi saat kotak overlay di PDF diklik."""
        self.model.selected_row_id = str(row_id)
        self.view.update_highlight_only(row_id)

    def _get_grouped_ids(self):
        """Logika pengelompokan baris berdasarkan sumbu Y (Horizontal Grouping)."""
        # Cek status grouping dari Toolbar Global via Parent View
        if (
            not hasattr(self.view, "parent_view")
            or not self.view.parent_view.toolbar.chk_group.isChecked()
        ):
            return set()
        if not self.model.selected_row_id:
            return set()

        target = next(
            (
                d
                for d in self._page_data_cache
                if str(d[5]) == str(self.model.selected_row_id)
            ),
            None,
        )
        if not target:
            return set()

        t_sumbu = (target[1] + target[3]) / 2
        grouped_ids = set()
        for d in self._page_data_cache:
            curr_sumbu = (d[1] + d[3]) / 2
            if abs(curr_sumbu - t_sumbu) <= self._group_tolerance:
                grouped_ids.add(str(d[5]))
        return grouped_ids

    def _on_toggle_line_grouping(self):
        if self.model.selected_row_id:
            self.view.update_highlight_only(self.model.selected_row_id)

    def _on_update_tolerance(self, val):
        """Update toleransi pengelompokan sumbu."""
        try:
            self._group_tolerance = float(str(val).replace(",", "."))
            if self.model.selected_row_id:
                self.view.update_highlight_only(self.model.selected_row_id)
        except ValueError:
            pass

    def start_export(self, path, range_str):
        """Memulai proses ekspor teks ke CSV."""
        if not self.model.doc:
            return
        indices = self._export_mgr.parse_ranges(range_str, self.model.total_pages)
        if indices is not None:
            self._export_mgr.to_csv(self.model.doc, path, indices, self.view)
            self._refresh(full_refresh=False)
