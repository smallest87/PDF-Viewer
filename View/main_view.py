# File: View/main_view.py
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QDockWidget,
    QFileDialog,
    QInputDialog,
    QLineEdit,
    QMainWindow,
    QMdiArea,
    QVBoxLayout,
    QWidget,
)

from interface import PDFViewInterface
from Model.document_model import PDFDocumentModel
from View.dockers.coordinate_dock import CoordinateDock
from View.dockers.csv_table_view import PyQt6CSVTableView
from View.dockers.layer_manager import LayerManagerWidget
from View.mdi_child import PDFMdiChild
from View.status_bar import PyQt6StatusBar
from View.toolbar import PyQt6Toolbar


class PyQt6PDFView(QMainWindow, PDFViewInterface):
    def __init__(self, root_app, controller_factory):
        super().__init__()
        self.app = root_app
        self.base_title = "PDF-Nexus Ultimate V4"
        self.setWindowTitle(self.base_title)
        self.resize(1280, 800)

        self.controller_factory = controller_factory
        self.csv_table_widget = None

        self._setup_ui()
        self._setup_dock_widget()

    def _setup_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.toolbar = PyQt6Toolbar(self)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar)

        self.mdi_area = QMdiArea()
        self.mdi_area.setViewMode(QMdiArea.ViewMode.SubWindowView)
        self.mdi_area.subWindowActivated.connect(self._on_subwindow_activated)
        self.main_layout.addWidget(self.mdi_area)

        self._setup_menus()

        self.status_bar = PyQt6StatusBar(self)
        self.setStatusBar(self.status_bar)

    def _setup_menus(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("&File")
        file_menu.addAction(self.toolbar.open_act)
        file_menu.addAction(self.toolbar.export_act)

        self.window_menu = menubar.addMenu("&Window")
        self.window_menu.aboutToShow.connect(self._update_window_menu)

    def _update_window_menu(self):
        self.window_menu.clear()
        tile_act = QAction("Tile Windows", self)
        tile_act.triggered.connect(self.mdi_area.tileSubWindows)
        self.window_menu.addAction(tile_act)

        cascade_act = QAction("Cascade Windows", self)
        cascade_act.triggered.connect(self.mdi_area.cascadeSubWindows)
        self.window_menu.addAction(cascade_act)

        self.window_menu.addSeparator()

        windows = self.mdi_area.subWindowList()
        if not windows:
            empty_act = QAction("No Documents Open", self)
            empty_act.setEnabled(False)
            self.window_menu.addAction(empty_act)
            return

        for i, window in enumerate(windows):
            action = QAction(f"{i+1}. {window.windowTitle()}", self)
            action.setCheckable(True)
            action.setChecked(window == self.mdi_area.activeSubWindow())
            action.triggered.connect(
                lambda checked, w=window: self.mdi_area.setActiveSubWindow(w)
            )
            self.window_menu.addAction(action)

    def _get_active_child(self):
        active_sub = self.mdi_area.activeSubWindow()
        if active_sub and isinstance(active_sub, PDFMdiChild):
            return active_sub
        return None

    def _on_subwindow_activated(self, window):
        if window and isinstance(window, PDFMdiChild):
            window.controller._refresh(full_refresh=False)

    def _setup_dock_widget(self):
        self.csv_dock = QDockWidget("CSV Data Inspector", self)
        self.csv_dock.setVisible(False)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.csv_dock)

        self.dock_coords = QDockWidget("Live Coordinates", self)
        self.coord_widget = CoordinateDock()
        self.dock_coords.setWidget(self.coord_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock_coords)

        self.layer_dock = QDockWidget("Layers", self)
        self.layer_manager = LayerManagerWidget(self)
        self.layer_dock.setWidget(self.layer_manager)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.layer_dock)

    def _update_coord_display(self, x0, top):
        self.coord_widget.update_coords(x0, top)
        print(f"[DEBUG] Updated coord display to ({x0}, {top}) from MainView")

    def show_csv_panel(self, headers, data):
        child = self._get_active_child()
        if not child:
            return
        self.csv_table_widget = PyQt6CSVTableView(
            self, headers, data, child.controller._handle_table_click
        )
        self.csv_dock.setWidget(self.csv_table_widget)
        self.csv_dock.setVisible(True)

    # --- IMPLEMENTASI PDFViewInterface (Delegasi ke Child) ---
    def update_progress(self, v):
        self.status_bar.set_progress(v)
        self.app.processEvents()

    def set_application_title(self, f):
        self.setWindowTitle(f"{self.base_title} - {f}")

    def set_grouping_control_state(self, a):
        self.toolbar.set_grouping_enabled(a)

    # --- SLOT EVENT ---
    def _on_open(self):
        print("[DEBUG] Triggered Open File Dialog")
        path, _ = QFileDialog.getOpenFileName(self, "Open PDF", "", "PDF Files (*.pdf)")
        if path:
            new_sub = PDFMdiChild(self, PDFDocumentModel)
            self.mdi_area.addSubWindow(new_sub)
            new_sub.show()
            new_sub.controller.open_document(path)

    def _on_view_csv_table(self):
        print("[DEBUG] Triggered View CSV Table")
        child = self._get_active_child()
        if child:
            child.controller.open_csv_table()

    def _on_export_csv(self):
        print("[DEBUG] Triggered Export CSV Dialog")
        child = self._get_active_child()
        if not child or not child.model.doc:
            return
        total = child.model.total_pages
        range_str, ok = QInputDialog.getText(
            self,
            "Export Range",
            f"Halaman (1-{total}):",
            QLineEdit.EchoMode.Normal,
            f"1-{total}",
        )
        if ok and (
            path := QFileDialog.getSaveFileName(
                self, "Export CSV", "", "CSV Files (*.csv)"
            )[0]
        ):
            child.controller.start_export(path, range_str)

    def resize_event(self, event):
        print("[DEBUG] Window Resize Event Triggered")
        super().resize_event(event)
        # PERBAIKAN: Gunakan active child untuk mendapatkan lebar viewport
        if self.csv_dock.isVisible():
            child = self._get_active_child()
            vp_w = child.viewport.width() if child else 0
            print(
                f"[DEBUG] Window Resize -> [Dock: {self.csv_dock.width()}px] vs [Active Viewport: {vp_w}px]"
            )
