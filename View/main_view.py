from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QSplitter, QDockWidget, QApplication, QFileDialog
from PyQt6.QtCore import Qt
from interface import PDFViewInterface
from View.toolbar import PyQt6Toolbar
from View.viewport import PyQt6Viewport
from View.status_bar import PyQt6StatusBar
from View.csv_table_view import PyQt6CSVTableView

class PyQt6PDFView(QMainWindow, PDFViewInterface):
    def __init__(self, root_app, controller_factory):
        super().__init__()
        self.app = root_app
        self.base_title = "PDF-Nexus Ultimate V4"
        self.setWindowTitle(self.base_title)
        self.resize(1280, 800)
        self.controller = controller_factory(self)
        
        self._setup_ui()
        self._setup_dock_widget() # Inisialisasi sistem panel

    def _setup_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.toolbar = PyQt6Toolbar(self)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.viewport = PyQt6Viewport(self)
        self.splitter.addWidget(self.viewport)
        self.main_layout.addWidget(self.splitter)

        self.status_bar = PyQt6StatusBar(self)
        self.setStatusBar(self.status_bar)

    def _setup_dock_widget(self):
        """Optimasi sistem docking agar fleksibel"""
        self.csv_dock = QDockWidget("CSV Data Inspector", self)
        
        # Pastikan fitur DockWidgetFeatures diset lengkap
        self.csv_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable | 
            QDockWidget.DockWidgetFeature.DockWidgetClosable |
            QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        
        self.csv_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.csv_dock.setVisible(False)
        
        # PENTING: Set posisi awal
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.csv_dock)
        
        # Tambahkan status awal untuk debug
        print("[DEBUG] STATUS: Docking System Initialized (Flexible Mode)")

    def show_csv_panel(self, headers, data):
        """Menampilkan panel dan mengirimkan status aktivasi ke debug"""
        # 1. Tampilkan status activating docking
        print("\n" + "="*50)
        print(f"[DEBUG] STATUS: Activating CSV Docking Panel...")
        print(f"[DEBUG] TARGET: Sisi Kiri (Default)")
        
        from View.csv_table_view import PyQt6CSVTableView
        self.csv_table_widget = PyQt6CSVTableView(
            self, headers, data, self.controller._handle_table_click
        )
        self.csv_dock.setWidget(self.csv_table_widget)
        self.csv_dock.setVisible(True)
        
        # 2. Tampilkan perbandingan lebar awal
        dock_w = self.csv_dock.width()
        view_w = self.viewport.width()
        print(f"[DEBUG] INITIAL WIDTH -> Dock: {dock_w}px | Viewport: {view_w}px")
        print("="*50 + "\n")

    def resizeEvent(self, event):
        """Pembaruan debug saat ukuran window utama berubah"""
        super().resizeEvent(event)
        if self.csv_dock.isVisible():
            dock_w = self.csv_dock.width()
            view_w = self.viewport.width()
            # Gunakan penanda tegas untuk membedakan resize window vs resize dock
            print(f"[DEBUG] Window Resize -> [Dock: {dock_w}px] vs [Viewport: {view_w}px]")

    # --- IMPLEMENTASI INTERFACE LAINNYA ---
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
    def update_highlight_only(self, sid):
        self.viewport.apply_highlight_to_items(sid)
        if self.csv_table_widget and sid: # Sinkronisasi ke panel
            self.csv_table_widget.select_row_by_index(int(sid) - 1)
    def set_grouping_control_state(self, a): self.toolbar.set_grouping_enabled(a)
    def _on_open(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open PDF", "", "PDF Files (*.pdf)")
        if path: self.controller.open_document(path)
    def _on_view_csv_table(self): self.controller.open_csv_table()
    def _on_export_csv(self): pass