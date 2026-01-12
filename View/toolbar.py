from PyQt6.QtWidgets import (
    QToolBar, QToolButton, QLineEdit, QLabel, 
    QCheckBox, QWidget, QHBoxLayout, QSizePolicy
)
from PyQt6.QtGui import QAction, QIcon, QFont
from PyQt6.QtCore import Qt, QSize

class PyQt6Toolbar(QToolBar):
    def __init__(self, view):
        super().__init__("Main Toolbar", view)
        self.view = view
        
        # Konfigurasi Utama: Hanya Ikon
        self.setMovable(False)
        self.setIconSize(QSize(24, 24))
        # MODE INI PENTING: Memastikan teks simbol dirender sebagai ikon
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        
        # Styling Profesional
        self.setStyleSheet("""
            QToolBar {
                background: #bcbcbc;
                border-bottom: 1px solid #d1d1d1;
                padding: 4px;
            }
            QToolButton {
                background-color: transparent;
                font-weight: bold; /* Agar simbol +/- terlihat tegas */
                font-size: 16px;
                padding: 4px;
            }
            QToolButton:hover {
                background-color: #f3f6f4;
                border: 2px solid #eeeeee;
            }
            QLineEdit {
                border: 1px solid #cccccc;
                border-radius: 3px;
                background: #fdfdfd;
            }
            /* Styling khusus untuk checkbox huruf tunggal agar terlihat seperti toggle */
            QCheckBox {
                spacing: 0px; padding: 4px; font-weight: bold; color: #555;
            }
        """)
        
        self._build_ui()

    def _build_ui(self):
        style = self.style()
        
        # 1. FILE & DATA CONTROLS
        self.open_act = QAction(style.standardIcon(style.StandardPixmap.SP_DialogOpenButton), "Open PDF", self)
        self.open_act.setToolTip("Open PDF File")
        self.open_act.triggered.connect(self.view._on_open)
        self.addAction(self.open_act)

        self.export_act = QAction(style.standardIcon(style.StandardPixmap.SP_DialogSaveButton), "Export CSV", self)
        self.export_act.setToolTip("Export Data to CSV")
        self.export_act.triggered.connect(self.view._on_export_csv)
        self.addAction(self.export_act)

        self.btn_table = QToolButton(self)
        self.btn_table.setIcon(style.standardIcon(style.StandardPixmap.SP_FileDialogContentsView))
        self.btn_table.setToolTip("View Data Table")
        self.btn_table.clicked.connect(self.view._on_view_csv_table)
        self.btn_table.setEnabled(False)
        self.addWidget(self.btn_table)

        self.addSeparator()

        # 2. NAVIGATION
        self.prev_act = QAction(style.standardIcon(style.StandardPixmap.SP_ArrowBack), "Previous Page", self)
        self.prev_act.setToolTip("Previous Page")
        self.prev_act.triggered.connect(lambda: self.view.controller.change_page(-1))
        self.addAction(self.prev_act)

        self.pg_ent = QLineEdit(self)
        self.pg_ent.setFixedWidth(40)
        self.pg_ent.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pg_ent.setToolTip("Current Page Number")
        self.pg_ent.returnPressed.connect(self._jump_page)
        self.addWidget(self.pg_ent)

        self.lbl_total = QLabel("/ 0", self)
        self.lbl_total.setStyleSheet("margin-right: 5px; color: #555555; font-size: 12px;")
        self.addWidget(self.lbl_total)

        self.next_act = QAction(style.standardIcon(style.StandardPixmap.SP_ArrowForward), "Next Page", self)
        self.next_act.setToolTip("Next Page")
        self.next_act.triggered.connect(lambda: self.view.controller.change_page(1))
        self.addAction(self.next_act)

        self.addSeparator()

        # =====================================================================
        # 3. ZOOM CONTROLS (DIUBAH)
        # Menggunakan simbol tipografi Minus (U+2212) dan Plus yang jelas
        # =====================================================================
        self.zoom_out_act = QAction("−", self) 
        self.zoom_out_act.setToolTip("Zoom Out")
        self.zoom_out_act.triggered.connect(lambda: self.view.controller.set_zoom("out"))
        self.addAction(self.zoom_out_act)

        self.zoom_in_act = QAction("+", self)
        self.zoom_in_act.setToolTip("Zoom In")
        self.zoom_in_act.triggered.connect(lambda: self.view.controller.set_zoom("in"))
        self.addAction(self.zoom_in_act)
        # =====================================================================

        self.addSeparator()

        # 4. LAYER & GROUPING
        self.chk_text = QCheckBox("T", self)
        self.chk_text.setToolTip("Toggle Text Layer")
        self.chk_text.stateChanged.connect(lambda s: self.view.controller.toggle_text_layer(s == 2))
        self.addWidget(self.chk_text)

        self.chk_csv = QCheckBox("C", self)
        self.chk_csv.setToolTip("Toggle CSV Overlay")
        self.chk_csv.stateChanged.connect(lambda s: self.view.controller.toggle_csv_layer(s == 2))
        self.addWidget(self.chk_csv)

        # Spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.addWidget(spacer)

        self.chk_group = QCheckBox("G", self)
        self.chk_group.setToolTip("Toggle Line Grouping")
        self.chk_group.stateChanged.connect(lambda s: self.view.controller.toggle_line_grouping())
        self.chk_group.setEnabled(False)
        self.addWidget(self.chk_group)

        self.ent_tolerance = QLineEdit("2.0", self)
        self.ent_tolerance.setFixedWidth(35)
        self.ent_tolerance.setToolTip("Grouping Tolerance")
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