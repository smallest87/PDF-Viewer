from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QSplitter, QDockWidget, QFileDialog, QFileDialog, QInputDialog, QLineEdit
from PyQt6.QtCore import Qt
from interface import PDFViewInterface
from View.toolbar import PyQt6Toolbar
from View.viewport import PyQt6Viewport
from View.status_bar import PyQt6StatusBar
from View.dockers.csv_table_view import PyQt6CSVTableView
from View.dockers.layer_manager import LayerManagerWidget
from View.dockers.coordinate_dock import CoordinateDock

class PyQt6PDFView(QMainWindow, PDFViewInterface):
    def __init__(self, root_app, controller_factory):
        super().__init__()
        self.app = root_app
        self.base_title = "PDF-Nexus Ultimate V4"
        self.setWindowTitle(self.base_title)
        self.resize(1280, 800)
        
        # 1. Inisialisasi State & Controller (DIPANGGIL HANYA SEKALI)
        self.controller = controller_factory(self)
        self.csv_table_widget = None # Inisialisasi awal untuk mencegah AttributeError
        
        # 2. Setup Antarmuka (DIPANGGIL HANYA SEKALI)
        self._setup_ui()
        self._setup_dock_widget()

    def _setup_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # Toolbar
        self.toolbar = PyQt6Toolbar(self)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar)

        # Viewport
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.viewport = PyQt6Viewport(self)
        self.splitter.addWidget(self.viewport)
        self.main_layout.addWidget(self.splitter)

        # Status Bar
        self.status_bar = PyQt6StatusBar(self)
        self.setStatusBar(self.status_bar)

    def _setup_dock_widget(self):
    
        self.csv_dock = QDockWidget("CSV Data Inspector", self)
        self.csv_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable | 
            QDockWidget.DockWidgetFeature.DockWidgetClosable |
            QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        self.csv_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.csv_dock.setVisible(False)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.csv_dock)

        # Dock Koordinat Realtime
        self.dock_coords = QDockWidget("Live Coordinates", self)
        self.coord_widget = CoordinateDock()
        self.dock_coords.setWidget(self.coord_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock_coords)

        # Dock Baru untuk Layer
        self.layer_dock = QDockWidget("Layers", self)
        self.layer_manager = LayerManagerWidget(self.controller)
        self.layer_dock.setWidget(self.layer_manager)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.layer_dock)

    # Tambahkan metode baru di PyQt6PDFView:
    def update_coord_display(self, x0, top):
        """Update label koordinat atau tampilkan '-' jika di luar jangkauan."""
        if x0 is None or top is None:
            # Panggil metode update_coords dengan nilai kosong
            self.coord_widget.update_coords(None, None)
        else:
            self.coord_widget.update_coords(x0, top)

    def show_csv_panel(self, headers, data):
        """Menampilkan widget tabel di dalam panel dock."""
        self.csv_table_widget = PyQt6CSVTableView(
            self, headers, data, self.controller._handle_table_click
        )
        self.csv_dock.setWidget(self.csv_table_widget)
        self.csv_dock.setVisible(True)

    def update_highlight_only(self, sid):
        """Sinkronisasi Visual: PDF <-> Tabel CSV."""
        # 1. Update highlight visual pada Viewport (PDF)
        self.viewport.apply_highlight_to_items(sid)
        
        # 2. Sinkronisasi ke Panel Tabel CSV
        if self.csv_table_widget is not None:
            # Ambil data grup berdasarkan sumbu elemen yang dipilih
            grouped_ids = self.controller.get_grouped_ids()
            
            # Berikan tanda warna pada grup, namun kursor tetap di sid
            self.csv_table_widget.select_row_and_mark_group(sid, grouped_ids)

    # --- IMPLEMENTASI PDFViewInterface ---
    def display_page(self, pix, ox, oy, region):
        from PyQt6.QtGui import QImage, QPixmap
        qimg = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
        self.viewport.set_background_pdf(QPixmap.fromImage(qimg), ox, oy, region)

    def draw_rulers(self, dw, dh, ox, oy, z): self.viewport.update_rulers(dw, dh, ox, oy, z)
    def draw_text_layer(self, w, ox, oy, z): self.viewport.render_overlay_layer(w, ox, oy, z, "text_layer")
    def draw_csv_layer(self, w, ox, oy, z): self.viewport.render_overlay_layer(w, ox, oy, z, "csv_layer")
    def clear_overlay_layer(self, tag): self.viewport.clear_overlay_layer(tag)
    
    def update_ui_info(self, p, t, z, s, w, h, c):
        self.toolbar.update_navigation(p, t)
        self.toolbar.update_layer_states(s, c)
        self.status_bar.update_status(z, s, w, h)

    def get_viewport_size(self): return self.viewport.width(), self.viewport.height()
    def update_progress(self, v): self.status_bar.set_progress(v); self.app.processEvents()
    def set_application_title(self, f): self.setWindowTitle(f"{self.base_title} - {f}")
    def set_grouping_control_state(self, a): self.toolbar.set_grouping_enabled(a)

    # --- SLOT EVENT ---
    def _on_open(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open PDF", "", "PDF Files (*.pdf)")
        if path: self.controller.open_document(path)

    def _on_view_csv_table(self): self.controller.open_csv_table()

    def _on_export_csv(self):
        if not self.controller.model.doc: 
            return
            
        # 1. Minta rentang halaman (opsional, default semua halaman)
        total = self.controller.model.total_pages
        range_str, ok = QInputDialog.getText(
            self, "Export Range", 
            f"Masukkan halaman (1-{total}) atau kosongkan untuk semua:",
            QLineEdit.EchoMode.Normal, f"1-{total}"
        )
        if not ok: return

        # 2. Minta lokasi penyimpanan file
        path, _ = QFileDialog.getSaveFileName(self, "Export CSV", "", "CSV Files (*.csv)")
        if path:
            # 3. Panggil controller untuk memproses ekspor
            self.controller.start_export(path, range_str)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.csv_dock.isVisible():
            print(f"[DEBUG] Window Resize -> [Dock: {self.csv_dock.width()}px] vs [Viewport: {self.viewport.width()}px]")