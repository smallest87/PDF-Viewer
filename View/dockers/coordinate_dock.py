from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class CoordinateDock(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Container styling
        self.frame = QFrame()
        self.frame.setStyleSheet("background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 5px;")
        frame_layout = QVBoxLayout(self.frame)

        self.lbl_title = QLabel("PDF REALTIME COORDS")
        self.lbl_title.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.lbl_title.setStyleSheet("color: #495057; border: none;")

        # Label untuk x0 dan top
        self.val_x0 = QLabel("x0: 0.00")
        self.val_top = QLabel("top: 0.00")
        
        for lbl in [self.val_x0, self.val_top]:
            lbl.setFont(QFont("Consolas", 9))
            lbl.setStyleSheet("border: none;")

        frame_layout.addWidget(self.lbl_title)
        frame_layout.addWidget(self.val_x0)
        frame_layout.addWidget(self.val_top)
        
        layout.addWidget(self.frame)
        layout.addStretch()

    def update_coords(self, x0, top):
        """Menampilkan koordinat atau tanda strip jika tidak aktif."""
        if x0 is None or top is None:
            self.val_x0.setText("x0 :    -   ")
            self.val_top.setText("top:    -   ")
            # Opsional: Ubah warna jadi abu-abu saat tidak aktif
            self.val_x0.setStyleSheet("color: #adb5bd; border: none; font-weight: bold;")
            self.val_top.setStyleSheet("color: #adb5bd; border: none; font-weight: bold;")
        else:
            self.val_x0.setText(f"x0 : {x0:>8.2f}")
            self.val_top.setText(f"top: {top:>8.2f}")
            # Kembalikan warna biru saat aktif
            self.val_x0.setStyleSheet("border: none;")
            self.val_top.setStyleSheet("border: none;")