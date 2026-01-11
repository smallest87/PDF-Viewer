from PyQt6.QtWidgets import (
    QToolBar, QToolButton, QLineEdit, QLabel, 
    QCheckBox, QWidget, QHBoxLayout
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt

class PyQt6Toolbar(QToolBar):
    def __init__(self, view):
        super().__init__("Main Toolbar", view)
        self.view = view
        self.setMovable(False)
        self._build_ui()

    def _build_ui(self):
        # 1. FILE & DATA CONTROLS
        self.open_act = QAction("Open PDF", self)
        self.open_act.triggered.connect(self.view._on_open)
        self.addAction(self.open_act)

        self.export_act = QAction("Export CSV", self)
        self.export_act.triggered.connect(self.view._on_export_csv)
        self.addAction(self.export_act)

        self.btn_table = QToolButton(self)
        self.btn_table.setText("📊 Table")
        self.btn_table.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        self.btn_table.clicked.connect(self.view._on_view_csv_table)
        self.btn_table.setEnabled(False)
        self.addWidget(self.btn_table)

        # Penggunaan addSeparator yang benar (Metode, bukan Widget)
        self.addSeparator()

        # 2. NAVIGATION
        self.prev_act = QAction("<<", self)
        self.prev_act.triggered.connect(lambda: self.view.controller.change_page(-1))
        self.addAction(self.prev_act)

        self.pg_ent = QLineEdit(self)
        self.pg_ent.setFixedWidth(40)
        self.pg_ent.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pg_ent.returnPressed.connect(self._jump_page)
        self.addWidget(self.pg_ent)

        self.lbl_total = QLabel("/ 0", self)
        self.addWidget(self.lbl_total)

        self.next_act = QAction(">>", self)
        self.next_act.triggered.connect(lambda: self.view.controller.change_page(1))
        self.addAction(self.next_act)

        self.addSeparator()

        # 3. ZOOM & LAYERS
        self.zoom_in_act = QAction("Zoom +", self)
        self.zoom_in_act.triggered.connect(lambda: self.view.controller.set_zoom("in"))
        self.addAction(self.zoom_in_act)

        self.zoom_out_act = QAction("Zoom -", self)
        self.zoom_out_act.triggered.connect(lambda: self.view.controller.set_zoom("out"))
        self.addAction(self.zoom_out_act)

        self.chk_text = QCheckBox("Text Layer", self)
        self.chk_text.stateChanged.connect(lambda s: self.view.controller.toggle_text_layer(s == 2))
        self.addWidget(self.chk_text)

        self.chk_csv = QCheckBox("CSV Overlay", self)
        self.chk_csv.stateChanged.connect(lambda s: self.view.controller.toggle_csv_layer(s == 2))
        self.addWidget(self.chk_csv)

        # 4. LINE GROUPING CONTROLS
        self.addSeparator()
        self.addWidget(QLabel(" | Grouping:", self))
        
        self.chk_group = QCheckBox("Line", self)
        self.chk_group.stateChanged.connect(lambda s: self.view.controller.toggle_line_grouping())
        self.chk_group.setEnabled(False)
        self.addWidget(self.chk_group)

        self.addWidget(QLabel("Tol:", self))
        self.ent_tolerance = QLineEdit("2.0", self)
        self.ent_tolerance.setFixedWidth(40)
        self.ent_tolerance.setEnabled(False)
        self.ent_tolerance.returnPressed.connect(self._update_tol)
        self.addWidget(self.ent_tolerance)

    def _jump_page(self):
        try:
            val = int(self.pg_ent.text())
            self.view.controller.jump_to_page(val)
        except: pass

    def _update_tol(self):
        self.view.controller.update_tolerance(self.ent_tolerance.text())

    def update_navigation(self, current, total):
        self.pg_ent.setText(str(current))
        self.lbl_total.setText(f"/ {total}")

    def update_layer_states(self, is_sandwich, has_csv):
        self.chk_text.setEnabled(is_sandwich)
        self.chk_csv.setEnabled(has_csv)
        self.btn_table.setEnabled(has_csv)

    def set_grouping_enabled(self, active):
        self.chk_group.setEnabled(active)
        self.ent_tolerance.setEnabled(active)