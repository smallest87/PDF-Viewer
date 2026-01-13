# File: View/toolbar.py
from PyQt6.QtCore import QSize
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QCheckBox,
    QLineEdit,
    QSizePolicy,
    QToolBar,
    QToolButton,
    QWidget,
)

from Controller.app_state import app_state


class PyQt6Toolbar(QToolBar):
    def __init__(self, view):
        super().__init__("Main Toolbar", view)
        self.view = view

        # Hubungkan ke state global
        app_state.visibility_changed.connect(self._sync_checkboxes)

        self.setMovable(False)
        self.setIconSize(QSize(24, 24))
        self._build_ui()

    def _get_active_controller(self):
        if hasattr(self.view, "_get_active_child"):
            child = self.view._get_active_child()
            return child.controller if child else None
        return None

    def _build_ui(self):
        style = self.style()

        # 1. FILE & DATA CONTROLS
        self.open_act = QAction(
            style.standardIcon(style.StandardPixmap.SP_DialogOpenButton),
            "Open PDF",
            self,
        )
        self.open_act.triggered.connect(self.view._on_open)
        self.addAction(self.open_act)

        self.export_act = QAction(
            style.standardIcon(style.StandardPixmap.SP_DialogSaveButton),
            "Export CSV",
            self,
        )
        self.export_act.triggered.connect(self.view._on_export_csv)
        self.addAction(self.export_act)

        self.btn_table = QToolButton(self)
        self.btn_table.setIcon(
            style.standardIcon(style.StandardPixmap.SP_FileDialogContentsView)
        )
        self.btn_table.clicked.connect(self.view._on_view_csv_table)
        self.btn_table.setEnabled(False)
        self.addWidget(self.btn_table)

        self.addSeparator()

        # 2. LAYER CONTROLS (Wajib dibuat dulu sebelum di-connect)
        self.chk_text = QCheckBox("T", self)
        self.chk_csv = QCheckBox("C", self)

        # Ambil status awal dari global state
        self.chk_text.setChecked(app_state.get_visibility("text_layer"))
        self.chk_csv.setChecked(app_state.get_visibility("csv_layer"))

        # Hubungkan aksi ke Global State
        self.chk_text.stateChanged.connect(
            lambda s: app_state.set_visibility("text_layer", s == 2)
        )
        self.chk_csv.stateChanged.connect(
            lambda s: app_state.set_visibility("csv_layer", s == 2)
        )

        self.addWidget(self.chk_text)
        self.addWidget(self.chk_csv)

        # 3. GROUPING CONTROLS (Pindahkan ke sini, jangan di _sync_checkboxes)
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.addWidget(spacer)

        self.chk_group = QCheckBox("G", self)
        self.chk_group.stateChanged.connect(
            lambda s: self._exec_controller_action("_on_toggle_line_grouping")
        )
        self.chk_group.setEnabled(False)
        self.addWidget(self.chk_group)

        self.ent_tolerance = QLineEdit("2.0", self)
        self.ent_tolerance.setFixedWidth(35)
        self.ent_tolerance.setEnabled(False)
        self.ent_tolerance.returnPressed.connect(self._update_tol)
        self.addWidget(self.ent_tolerance)

    def _sync_checkboxes(self, tag, is_visible):
        """Hanya bertugas menyamakan tampilan ceklis dengan data global."""
        self.chk_text.blockSignals(True)
        self.chk_csv.blockSignals(True)
        if tag == "text_layer":
            self.chk_text.setChecked(is_visible)
        elif tag == "csv_layer":
            self.chk_csv.setChecked(is_visible)
        self.chk_text.blockSignals(False)
        self.chk_csv.blockSignals(False)

    def _exec_controller_action(self, method_name, *args):
        ctrl = self._get_active_controller()
        if ctrl:
            getattr(ctrl, method_name)(*args)

    def _update_tol(self):
        ctrl = self._get_active_controller()
        if ctrl:
            ctrl._on_update_tolerance(self.ent_tolerance.text())

    def update_layer_states(self, has_text, has_csv):
        self.btn_table.setEnabled(has_csv)

    def set_grouping_enabled(self, enabled):
        self.chk_group.setEnabled(enabled)
        self.ent_tolerance.setEnabled(enabled)
