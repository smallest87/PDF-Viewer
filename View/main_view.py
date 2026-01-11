import sys
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QSplitter, QFileDialog, QApplication
from PyQt6.QtCore import Qt
from interface import PDFViewInterface
from View.toolbar import PyQt6Toolbar
from View.viewport import PyQt6Viewport
from View.status_bar import PyQt6StatusBar

class PyQt6PDFView(QMainWindow, PDFViewInterface):
    def __init__(self, root_app, controller_factory):
        super().__init__()
        self.app = root_app
        self.base_title = "PDF-Nexus Ultimate V4 (PyQt6 Edition)"
        self.setWindowTitle(self.base_title)
        self.resize(1200, 800)
        self.controller = controller_factory(self)
        self._setup_ui()

    def _setup_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.toolbar = PyQt6Toolbar(self)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.viewport = PyQt6Viewport(self)
        self.splitter.addWidget(self.viewport)
        self.main_layout.addWidget(self.splitter)
        self.status_bar = PyQt6StatusBar(self)
        self.setStatusBar(self.status_bar)

    # --- IMPLEMENTASI INTERFACE ---
    def display_page(self, pix, ox, oy, region):
        from PyQt6.QtGui import QImage, QPixmap
        qimg = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
        self.viewport.set_background_pdf(QPixmap.fromImage(qimg), ox, oy, region)

    def draw_rulers(self, doc_w, doc_h, ox, oy, zoom): self.viewport.update_rulers(doc_w, doc_h, ox, oy, zoom)
    def draw_text_layer(self, words, ox, oy, zoom): self.viewport.render_overlay_layer(words, ox, oy, zoom, "text_layer")
    def draw_csv_layer(self, words, ox, oy, zoom): self.viewport.render_overlay_layer(words, ox, oy, zoom, "csv_layer")
    
    # JEMBATAN KE VIEWPORT
    def clear_overlay_layer(self, tag): self.viewport.clear_overlay_layer(tag)

    def update_ui_info(self, page_num, total, zoom, is_sandwich, width, height, has_csv):
        self.toolbar.update_navigation(page_num, total)
        self.toolbar.update_layer_states(is_sandwich, has_csv)
        self.status_bar.update_status(zoom, is_sandwich, width, height)

    def get_viewport_size(self): return self.viewport.width(), self.viewport.height()
    def update_progress(self, value):
        self.status_bar.set_progress(value)
        self.app.processEvents()

    def set_application_title(self, filename): self.setWindowTitle(f"{self.base_title} - {filename}")
    def update_highlight_only(self, selected_id): self.viewport.apply_highlight_to_items(selected_id)
    def set_grouping_control_state(self, active): self.toolbar.set_grouping_enabled(active)

    # --- HANDLERS ---
    def _on_open(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open PDF", "", "PDF Files (*.pdf)")
        if path: self.controller.open_document(path)
    def _on_view_csv_table(self): self.controller.open_csv_table()
    def _on_export_csv(self): pass