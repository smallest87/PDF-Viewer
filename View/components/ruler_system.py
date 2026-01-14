from typing import override

from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QAbstractScrollArea, QGridLayout, QSizePolicy, QWidget


class ModularRuler(QWidget):
    """Widget penggaris yang murni menangani penggambaran (rendering)."""

    def __init__(self, orientation, parent=None):
        super().__init__(parent)
        self.orientation = orientation
        self.zoom_scale = 1.0
        self.offset = 0
        self.doc_size = 0
        self.scroll_val = 0

        if self.orientation == Qt.Orientation.Horizontal:
            self.setFixedHeight(25)
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        else:
            self.setFixedWidth(25)
            self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

    def update_params(self, doc_size, offset, zoom, scroll_val):
        self.doc_size = doc_size
        self.offset = offset
        self.zoom_scale = zoom
        self.scroll_val = scroll_val
        self.update()

    @override
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QColor("#bcbcbc"))
        p.setPen(QPen(QColor("#333333"), 1))

        is_horz = self.orientation == Qt.Orientation.Horizontal
        step = 100 if self.zoom_scale < 1.0 else 50

        for u in range(0, int(self.doc_size) + 1, 10):
            pos = (u * self.zoom_scale + self.offset) - self.scroll_val
            if (
                pos < -100
                or (is_horz and pos > self.width())
                or (not is_horz and pos > self.height())
            ):
                continue

            if is_horz:
                if u % step == 0:
                    p.drawLine(int(pos), 25, int(pos), 5)
                    p.drawText(int(pos) + 2, 12, str(u))
                elif u % 10 == 0:
                    p.drawLine(int(pos), 25, int(pos), 18)
            else:
                if u % step == 0:
                    p.drawLine(25, int(pos), 5, int(pos))
                    p.drawText(2, int(pos) - 2, str(u))
                elif u % 10 == 0:
                    p.drawLine(25, int(pos), 18, int(pos))


class RulerWrapper(QWidget):
    """Wrapper yang membungkus QGraphicsView dengan penggaris H/V secara otomatis."""

    def __init__(self, target_widget: QAbstractScrollArea):
        super().__init__()
        self.target = target_widget
        self.h_ruler = ModularRuler(Qt.Orientation.Horizontal)
        self.v_ruler = ModularRuler(Qt.Orientation.Vertical)

        self._doc_params = {"dw": 0, "dh": 0, "ox": 0, "oy": 0, "z": 1.0}

        self._setup_layout()
        # Koneksi otomatis: Saat scrollbar target bergerak, penggaris update otomatis
        self.target.horizontalScrollBar().valueChanged.connect(self.sync_scroll)
        self.target.verticalScrollBar().valueChanged.connect(self.sync_scroll)

    def _setup_layout(self):
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        corner = QWidget()
        corner.setFixedSize(25, 25)
        corner.setStyleSheet("background-color: #bcbcbc;")

        layout.addWidget(corner, 0, 0)
        layout.addWidget(self.h_ruler, 0, 1)
        layout.addWidget(self.v_ruler, 1, 0)
        layout.addWidget(self.target, 1, 1)

    def set_params(self, dw, dh, ox, oy, z):
        """Method untuk dipanggil dari Viewport saat zoom atau load file."""
        self._doc_params = {"dw": dw, "dh": dh, "ox": ox, "oy": oy, "z": z}
        self.sync_scroll()

    @pyqtSlot()
    def sync_scroll(self):
        p = self._doc_params
        h_val = self.target.horizontalScrollBar().value()
        v_val = self.target.verticalScrollBar().value()
        self.h_ruler.update_params(p["dw"], p["ox"], p["z"], h_val)
        self.v_ruler.update_params(p["dh"], p["oy"], p["z"], v_val)
