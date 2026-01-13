# Modifikasi File: View/components/child_nav_bar.py
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLineEdit, QLabel
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtCore import Qt, QSize

class ChildNavBar(QWidget):
    def __init__(self, parent_child):
        super().__init__()
        self.child = parent_child
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 2, 10, 2)
        layout.setSpacing(8)
        self.setFixedHeight(32) # Sedikit lebih tinggi untuk kenyamanan ikon
        self.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa; 
                border-top: 1px solid #dee2e6;
            }
            QPushButton {
                border: none;
                border-radius: 4px;
                padding: 2px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
            QPushButton:pressed {
                background-color: #dee2e6;
            }
        """)

        # Ukuran standar ikon
        icon_size = QSize(16, 16)

        # --- BAGIAN ZOOM ---
        # Ganti 'path/to/icon_minus.png' dengan jalur file Anda
        self.btn_zoom_out = QPushButton()
        self.btn_zoom_out.setIcon(QIcon("icons/zoom_out.png")) 
        self.btn_zoom_out.setIconSize(icon_size)
        self.btn_zoom_out.setFixedWidth(28)
        self.btn_zoom_out.clicked.connect(lambda: self.child.controller.set_zoom("out"))

        self.lbl_zoom = QLabel("100%")
        self.lbl_zoom.setFixedWidth(45)
        self.lbl_zoom.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_zoom.setStyleSheet("font-size: 10px; color: #6c757d; border: none;")

        # Ganti 'path/to/icon_plus.png'
        self.btn_zoom_in = QPushButton()
        self.btn_zoom_in.setIcon(QIcon("icons/zoom_in.png"))
        self.btn_zoom_in.setIconSize(icon_size)
        self.btn_zoom_in.setFixedWidth(28)
        self.btn_zoom_in.clicked.connect(lambda: self.child.controller.set_zoom("in"))

        # --- BAGIAN NAVIGASI HALAMAN ---
        # Ganti 'path/to/icon_prev.png'
        self.btn_prev = QPushButton()
        self.btn_prev.setIcon(QIcon("icons/arrow_left.png"))
        self.btn_prev.setIconSize(icon_size)
        self.btn_prev.setFixedWidth(28)
        self.btn_prev.clicked.connect(lambda: self.child.controller.change_page(-1))

        self.pg_ent = QLineEdit()
        self.pg_ent.setFixedWidth(35)
        self.pg_ent.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pg_ent.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ced4da;
                border-radius: 3px;
                background: white;
                font-size: 11px;
            }
        """)
        self.pg_ent.returnPressed.connect(self._on_jump)

        self.lbl_total = QLabel("/ 0")
        self.lbl_total.setStyleSheet("border: none; color: #495057;")

        # Ganti 'path/to/icon_next.png'
        self.btn_next = QPushButton()
        self.btn_next.setIcon(QIcon("icons/arrow_right.png"))
        self.btn_next.setIconSize(icon_size)
        self.btn_next.setFixedWidth(28)
        self.btn_next.clicked.connect(lambda: self.child.controller.change_page(1))

        # Tata Letak
        layout.addWidget(self.btn_zoom_out)
        layout.addWidget(self.lbl_zoom)
        layout.addWidget(self.btn_zoom_in)
        layout.addStretch()
        layout.addWidget(self.btn_prev)
        layout.addWidget(self.pg_ent)
        layout.addWidget(self.lbl_total)
        layout.addWidget(self.btn_next)

    def _on_jump(self):
        try:
            val = int(self.pg_ent.text())
            self.child.controller.jump_to_page(val)
        except: pass

    def update_info(self, current, total, zoom):
        self.pg_ent.setText(str(current))
        self.lbl_total.setText(f"/ {total}")
        self.lbl_zoom.setText(f"{int(zoom * 100)}%")