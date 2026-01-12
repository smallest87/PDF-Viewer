from PyQt6.QtWidgets import QWidget, QVBoxLayout, QListView
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtCore import Qt

class LayerManagerWidget(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        self.view = QListView()
        self.model = QStandardItemModel()
        
        # Contoh Menambahkan Layer
        self.add_layer("Teks Layer (T)", True, "text_layer")
        self.add_layer("CSV Overlay (C)", False, "csv_layer")

        self.view.setModel(self.model)
        self.model.itemChanged.connect(self._on_visibility_changed)
        layout.addWidget(self.view)

    def add_layer(self, name, is_visible, tag):
        item = QStandardItem(name)
        item.setCheckable(True)
        item.setCheckState(Qt.CheckState.Checked if is_visible else Qt.CheckState.Unchecked)
        item.setData(tag, Qt.ItemDataRole.UserRole) # Simpan tag untuk identifikasi di Controller
        self.model.appendRow(item)

    def _on_visibility_changed(self, item):
        tag = item.data(Qt.ItemDataRole.UserRole)
        is_visible = item.checkState() == Qt.CheckState.Checked
        
        # Kirim perintah ke controller untuk update layer di PDF
        if tag == "text_layer":
            self.controller.toggle_text_layer(is_visible)
        elif tag == "csv_layer":
            self.controller.toggle_csv_layer(is_visible)