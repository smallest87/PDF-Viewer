from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem, QFrame, QGridLayout, QWidget
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPen, QColor, QBrush, QPainter

class PyQt6Ruler(QWidget):
    def __init__(self, orientation, parent=None):
        super().__init__(parent)
        self.orientation = orientation
        self.zoom_scale, self.offset, self.doc_size = 1.0, 0, 0
        self.setFixedSize(25, 25)

    def update_params(self, doc_size, offset, zoom):
        self.doc_size, self.offset, self.zoom_scale = doc_size, offset, zoom
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#f0f0f0"))
        p.setPen(QPen(Qt.GlobalColor.black, 1))
        is_horz = self.orientation == Qt.Orientation.Horizontal
        step = 100 if self.zoom_scale < 1.0 else 50
        for u in range(0, int(self.doc_size) + 1, 10):
            pos = u * self.zoom_scale + self.offset
            if is_horz:
                if u % step == 0:
                    p.drawLine(int(pos), 25, int(pos), 5)
                    p.drawText(int(pos) + 2, 12, str(u))
                elif u % 10 == 0: p.drawLine(int(pos), 25, int(pos), 18)
            else:
                if u % step == 0:
                    p.drawLine(25, int(pos), 5, int(pos))
                    p.drawText(2, int(pos) - 2, str(u))
                elif u % 10 == 0: p.drawLine(25, int(pos), 18, int(pos))

class PyQt6Viewport(QFrame):
    def __init__(self, parent_view):
        super().__init__()
        self.view = parent_view
        self.scene = QGraphicsScene()
        self.graphics_view = QGraphicsView(self.scene)
        self.graphics_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.graphics_view.setStyleSheet("background-color: #323639; border: none;")
        self.h_ruler = PyQt6Ruler(Qt.Orientation.Horizontal)
        self.v_ruler = PyQt6Ruler(Qt.Orientation.Vertical)
        self.overlay_items = {}
        self._setup_layout()

    def _setup_layout(self):
        l = QGridLayout(self)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(0)
        l.addWidget(QWidget(), 0, 0)
        l.addWidget(self.h_ruler, 0, 1)
        l.addWidget(self.v_ruler, 1, 0)
        l.addWidget(self.graphics_view, 1, 1)

    def set_background_pdf(self, pixmap, ox, oy, region):
        self.scene.clear()
        self.overlay_items.clear()
        bg = self.scene.addPixmap(pixmap)
        bg.setPos(ox, oy)
        bg.setZValue(-1)
        self.scene.setSceneRect(QRectF(region[0], region[1], region[2], region[3]))

    def update_rulers(self, doc_w, doc_h, ox, oy, zoom):
        self.h_ruler.update_params(doc_w, ox, zoom)
        self.v_ruler.update_params(doc_h, oy, zoom)

    def clear_overlay_layer(self, tag):
        """Hapus item berdasarkan tag metadata"""
        for item in [i for i in self.scene.items() if i.data(1) == tag]:
            self.scene.removeItem(item)
        if tag == "csv_layer": self.overlay_items.clear()

    def render_overlay_layer(self, words, ox, oy, zoom, tag):
        """Gambar layer tanpa stacking"""
        self.clear_overlay_layer(tag)
        color = QColor("#0078d7") if tag == "text_layer" else QColor("#28a745")
        
        # Ambil grup ID sekali saja di luar loop
        grouped_ids = self.view.controller.get_grouped_ids() if tag == "csv_layer" else set()
        sel_id = str(self.view.controller.model.selected_row_id)

        for w in words:
            # w = (x0, y0, x1, y1, teks, nomor)
            rect = QRectF(w[0]*zoom + ox, w[1]*zoom + oy, (w[2]-w[0])*zoom, (w[3]-w[1])*zoom)
            item = QGraphicsRectItem(rect)
            row_id = str(w[5]) if len(w) > 5 else None
            
            item.setData(0, row_id) # Metadata ID
            item.setData(1, tag)    # Metadata Layer Tag
            item.setBrush(QBrush(QColor(color.red(), color.green(), color.blue(), 60)))
            
            is_active = (row_id == sel_id)
            is_grouped = (row_id in grouped_ids)
            item.setPen(QPen(QColor("red") if is_active else (QColor("orange") if is_grouped else color), 2 if is_active or is_grouped else 1))
            
            self.scene.addItem(item)
            if tag == "csv_layer" and row_id: self.overlay_items[row_id] = item

    def apply_highlight_to_items(self, selected_id):
        """Update visual tercepat: Ambil grup 1x, terapkan ke semua"""
        grouped_ids = self.view.controller.get_grouped_ids()
        sel_id_str = str(selected_id)
        
        for row_id, item in self.overlay_items.items():
            rid = str(row_id)
            is_active = (rid == sel_id_str)
            is_grouped = (rid in grouped_ids)
            
            if is_active:
                item.setPen(QPen(QColor("red"), 3))
                item.setZValue(10)
            elif is_grouped:
                item.setPen(QPen(QColor("orange"), 2))
                item.setZValue(5)
            else:
                item.setPen(QPen(QColor("#28a745"), 1))
                item.setZValue(0)