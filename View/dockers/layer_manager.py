# File: View/dockers/layer_manager.py
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import QListView, QVBoxLayout, QWidget

from controller.app_state import app_state


class LayerManagerWidget(QWidget):
    def __init__(self, main_view):
        super().__init__()
        self.main_view = main_view
        self._setup_ui()

        # 3. Hubungkan ke state global untuk sinkronisasi otomatis
        # Jika status berubah dari Toolbar, Layer Manager akan ikut terupdate
        app_state.visibility_changed.connect(self._sync_layers)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        self.view = QListView()
        self.model = QStandardItemModel()

        # Inisialisasi layer dengan mengambil status langsung dari app_state
        self.add_layer(
            "Teks Layer (T)", app_state.get_visibility("text_layer"), "text_layer"
        )
        self.add_layer(
            "CSV Overlay (C)", app_state.get_visibility("csv_layer"), "csv_layer"
        )

        self.view.setModel(self.model)

        # 1. User klik kontrol ceklist di List View
        self.model.itemChanged.connect(self._on_visibility_changed)
        layout.addWidget(self.view)

    def add_layer(self, name, is_visible, tag):
        item = QStandardItem(name)
        item.setCheckable(True)
        # Set status berdasarkan variabel global saat pertama kali dibuat
        item.setCheckState(
            Qt.CheckState.Checked if is_visible else Qt.CheckState.Unchecked
        )
        item.setData(tag, Qt.ItemDataRole.UserRole)
        self.model.appendRow(item)

    def _on_visibility_changed(self, item):
        """Mengirim perubahan status ke variabel global."""
        tag = item.data(Qt.ItemDataRole.UserRole)
        is_visible = item.checkState() == Qt.CheckState.Checked

        # 2. Status ceklist disimpan di variabel global
        # Biarkan app_state yang mengurus broadcast ke seluruh Controller
        app_state.set_visibility(tag, is_visible)

    def _sync_layers(self, tag, is_visible):
        """Kontrol ceklist mengambil nilai status dari variabel global (Sinkronisasi)."""
        # Matikan sinyal sementara agar tidak terjadi loop (umpan balik)
        self.model.blockSignals(True)

        for i in range(self.model.rowCount()):
            item = self.model.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == tag:
                target_state = (
                    Qt.CheckState.Checked if is_visible else Qt.CheckState.Unchecked
                )
                if item.checkState() != target_state:
                    item.setCheckState(target_state)

        self.model.blockSignals(False)
