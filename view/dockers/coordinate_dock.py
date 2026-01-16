"""Module untuk menyediakan widget dock pemantau koordinat.

Menggunakan `PyQt6.QtCore.Qt` untuk mengatur enumerasi flag seperti alignment
dan properti inti widget lainnya.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QCheckBox, QFrame, QLabel, QVBoxLayout, QWidget


class CoordinateDock(QWidget):
    """Widget sidebar (dock) untuk menampilkan koordinat PDF secara real-time.

    Widget ini menyediakan antarmuka visual untuk memantau posisi kursor (x0 dan top)
    pada dokumen PDF serta menyediakan kontrol untuk mengaktifkan atau
    menonaktifkan pelacakan koordinat.

    Attributes:
        chk_active (QCheckBox): Checkbox untuk mengaktifkan/matikan fitur koordinat.
        frame (QFrame): Container visual untuk label koordinat.
        lbl_title (QLabel): Label judul panel.
        val_x0 (QLabel): Label untuk menampilkan nilai koordinat horizontal (x0).
        val_top (QLabel): Label untuk menampilkan nilai koordinat vertikal (top).

    """

    def __init__(self) -> None:
        """Inisialisasi komponen UI dan tata letak CoordinateDock."""
        super().__init__()
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Mengatur hierarki layout, styling CSS, dan inisialisasi widget internal.

        Metode ini bersifat internal untuk membangun tampilan awal saat objek dibuat.
        """
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 1. Kontrol Centang "Aktifkan"
        self.chk_active = QCheckBox("Aktifkan")
        self.chk_active.setChecked(True)
        self.chk_active.setFont(QFont("Segoe UI", 9))
        self.chk_active.setStyleSheet(
            """
            QCheckBox {
                color: #495057;
                padding: 2px;
            }
            QCheckBox::indicator {
                width: 14px;
                height: 14px;
            }
        """
        )
        layout.addWidget(self.chk_active)

        # Container styling
        self.frame = QFrame()
        self.frame.setStyleSheet(
            "background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 5px;"
        )
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

    def update_coords(self, x0: float | None, top: float | None) -> None:
        """Memperbarui tampilan nilai koordinat pada antarmuka.

        Jika salah satu koordinat bernilai None, tampilan akan diubah menjadi
        tanda strip (-) dengan warna teks yang diredam (muted).

        Args:
            x0 (Optional[float]): Koordinat horizontal dari PDF.
            top (Optional[float]): Koordinat vertikal dari PDF.

        """
        if x0 is None or top is None:
            self.val_x0.setText("x0 :    -   ")
            self.val_top.setText("top:    -   ")
            # Ubah warna jadi abu-abu saat tidak aktif
            gray_style = "color: #adb5bd; border: none; font-weight: bold;"
            self.val_x0.setStyleSheet(gray_style)
            self.val_top.setStyleSheet(gray_style)
        else:
            self.val_x0.setText(f"x0 : {x0:>8.2f}")
            self.val_top.setText(f"top: {top:>8.2f}")
            # Kembalikan warna default saat aktif
            self.val_x0.setStyleSheet("border: none;")
            self.val_top.setStyleSheet("border: none;")
