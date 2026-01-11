from PyQt6.QtWidgets import QStatusBar, QLabel, QProgressBar
from PyQt6.QtCore import Qt

class PyQt6StatusBar(QStatusBar):
    def __init__(self, parent):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        # Label Status Utama
        self.lbl_status = QLabel("Ready", self)
        self.addWidget(self.lbl_status, 1)

        # Informasi Dimensi
        self.lbl_dims = QLabel("Dimensi: -", self)
        self.addPermanentWidget(self.lbl_dims)

        # Informasi Zoom
        self.lbl_zoom = QLabel("Zoom: 100%", self)
        self.addPermanentWidget(self.lbl_zoom)

        # Progress Bar untuk Ekspor
        self.progress = QProgressBar(self)
        self.progress.setMaximumHeight(15)
        self.progress.setMaximumWidth(150)
        self.progress.setVisible(False)
        self.addPermanentWidget(self.progress)

    def update_status(self, zoom, is_sandwich, width, height):
        status_txt = "Sandwich" if is_sandwich else "Image Only"
        self.lbl_status.setText(f"Status: {status_txt}")
        self.lbl_dims.setText(f"Dimensi: {int(width)}x{int(height)} pt")
        self.lbl_zoom.setText(f"Zoom: {int(zoom*100)}%")

    def set_progress(self, value):
        """Menangani visibilitas progress bar secara otomatis"""
        if 0 < value < 100:
            self.progress.setVisible(True)
            self.progress.setValue(int(value))
        else:
            self.progress.setVisible(False)