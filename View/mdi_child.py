# File: View/mdi_child.py
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QMdiSubWindow, QVBoxLayout, QWidget

from Controller.main_controller import PDFController
from View.components.child_nav_bar import ChildNavBar  # Tambahkan import ini
from View.viewport import PyQt6Viewport


class PDFMdiChild(QMdiSubWindow):
    def __init__(self, parent_view, model_class):
        super().__init__()
        self.parent_view = parent_view  # Ini adalah PyQt6PDFView (Main Window)

        # Inisialisasi Model dan Controller khusus untuk dokumen ini
        self.model = model_class()
        self.controller = PDFController(self, self.model)

        self._setup_ui()
        print(
            f"[DEBUG] Created PDFMdiChild with Model ID: {id(self.model)} and Controller ID: {id(self.controller)}"
        )

    def _setup_ui(self):
        self.main_container = QWidget()
        self.layout = QVBoxLayout(self.main_container)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)  # Memastikan navigasi melekat ke viewport

        # 1. Viewport di atas
        self.viewport = PyQt6Viewport(self)
        self.layout.addWidget(self.viewport)

        # 2. Navigasi Bar di bawah (Membatalkan posisi di toolbar global)
        self.nav_bar = ChildNavBar(self)
        self.layout.addWidget(self.nav_bar)

        self.setWidget(self.main_container)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        print(
            f"[DEBUG] UI setup complete for PDFMdiChild with Model ID: {id(self.model)}"
        )

    @property
    def toolbar(self):
        """Akses ke toolbar utama aplikasi."""
        return self.parent_view.toolbar

    def _update_coord_display(self, x, y):
        """Meneruskan koordinat ke dock di jendela utama."""
        # Kita hanya update jika jendela ini yang sedang aktif/difokuskan mouse
        self.parent_view._update_coord_display(x, y)

    def show_csv_panel(self, headers, data):
        """Membuka panel CSV di dock jendela utama."""
        self.parent_view.show_csv_panel(headers, data)
        print(
            f"[DEBUG] Requested CSV panel display from MdiChild with Model ID: {id(self.model)}"
        )

    def update_progress(self, v):
        """Update progress bar di status bar utama."""
        self.parent_view.update_progress(v)
        print(
            f"[DEBUG] Updated progress to {v}% from MdiChild with Model ID: {id(self.model)}"
        )

    # --- IMPLEMENTASI INTERFACE UNTUK CONTROLLER ---

    def get_viewport_size(self):
        return self.viewport.width(), self.viewport.height()

    def display_page(self, pix, ox, oy, region):
        qimg = QImage(
            pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888
        )
        self.viewport.set_background_pdf(QPixmap.fromImage(qimg), ox, oy, region)

    def draw_rulers(self, dw, dh, ox, oy, z):
        self.viewport.update_rulers(dw, dh, ox, oy, z)

    def draw_text_layer(self, w, ox, oy, z):
        self.viewport.render_overlay_layer(w, ox, oy, z, "text_layer")

    def draw_csv_layer(self, w, ox, oy, z):
        self.viewport.render_overlay_layer(w, ox, oy, z, "csv_layer")

    def clear_overlay_layer(self, tag):
        self.viewport.clear_overlay_layer(tag)

    def update_ui_info(self, p, t, z, s, w, h, c):
        """Pembaruan UI dokumen yang dipicu oleh Controller."""
        if self.model.file_name:
            self.setWindowTitle(self.model.file_name)

        # 1. Update Navigasi & Zoom Lokal (Tambahkan parameter z/zoom)
        self.nav_bar.update_info(p, t, z)

        # 2. Update Status Bar & Toolbar Global (Hanya status layer/dock)
        if self.parent_view.mdi_area.activeSubWindow() == self:
            self.parent_view.toolbar.update_layer_states(s, c)
            self.parent_view.status_bar.update_status(z, s, w, h)
        print(
            f"[DEBUG] UI info updated: Page {p}/{t}, Zoom {z}, Sandwich {s}, CSV {c} from MdiChild with Model ID: {id(self.model)}"
        )

    def update_highlight_only(self, sid):
        """Sinkronisasi highlight antara PDF dan Tabel CSV Global."""
        self.viewport.apply_highlight_to_items(sid)
        if self.parent_view.mdi_area.activeSubWindow() == self:
            if self.parent_view.csv_table_widget:
                grouped_ids = self.controller._get_grouped_ids()
                self.parent_view.csv_table_widget.select_row_and_mark_group(
                    sid, grouped_ids
                )

    def set_application_title(self, f):
        self.setWindowTitle(f)

    def set_grouping_control_state(self, a):
        if self.parent_view.mdi_area.activeSubWindow() == self:
            self.parent_view.toolbar.set_grouping_enabled(a)
