from PyQt6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsRectItem, 
    QFrame, QVBoxLayout
)
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPen, QColor, QBrush, QPainter

# Import komponen modular (sesuaikan path jika berbeda folder)
from View.components.ruler_system import RulerWrapper 

class ClickableGraphicsView(QGraphicsView):
    def __init__(self, scene, viewport_parent):
        super().__init__(scene)
        self.viewport_parent = viewport_parent
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setStyleSheet("background-color: #323639; border: none;")
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            item = self.itemAt(event.pos())
            if item and isinstance(item, QGraphicsRectItem):
                row_id = item.data(0)
                tag = item.data(1)
                if tag == "csv_layer" and row_id:
                    self.viewport_parent.view.controller.handle_overlay_click(row_id)
        super().mousePressEvent(event)

class PyQt6Viewport(QFrame):
    def __init__(self, parent_view):
        super().__init__()
        self.view = parent_view
        self.scene = QGraphicsScene()
        self.graphics_view = ClickableGraphicsView(self.scene, self)
        
        # Integrasi Modular Ruler
        self.container = RulerWrapper(self.graphics_view)
        
        self.overlay_items = {}
        self._setup_layout()

    def _setup_layout(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.container)

    def update_rulers(self, doc_w, doc_h, ox, oy, zoom):
        """Update penggaris melalui wrapper modular."""
        self.container.set_params(doc_w, doc_h, ox, oy, zoom)

    def set_background_pdf(self, pixmap, ox, oy, region):
        self.scene.clear()
        self.overlay_items.clear()
        bg = self.scene.addPixmap(pixmap)
        bg.setPos(ox, oy)
        bg.setZValue(-1)
        self.scene.setSceneRect(QRectF(region[0], region[1], region[2], region[3]))

    def clear_overlay_layer(self, tag):
        for item in [i for i in self.scene.items() if i.data(1) == tag]:
            self.scene.removeItem(item)
        if tag == "csv_layer": 
            self.overlay_items.clear()

    def render_overlay_layer(self, words, ox, oy, zoom, tag):
        self.clear_overlay_layer(tag)
        color = QColor("#0078d7") if tag == "text_layer" else QColor("#28a745")
        grouped_ids = self.view.controller.get_grouped_ids() if tag == "csv_layer" else set()
        sel_id = str(self.view.controller.model.selected_row_id)
        
        for w in words:
            rect = QRectF(w[0]*zoom + ox, w[1]*zoom + oy, (w[2]-w[0])*zoom, (w[3]-w[1])*zoom)
            item = QGraphicsRectItem(rect)
            row_id = str(w[5]) if len(w) > 5 else None
            item.setData(0, row_id)
            item.setData(1, tag)
            
            item.setBrush(QBrush(QColor(color.red(), color.green(), color.blue(), 60)))
            is_active = (row_id == sel_id)
            is_grouped = (row_id in grouped_ids)
            
            pen_color = QColor("red") if is_active else (QColor("orange") if is_grouped else color)
            item.setPen(QPen(pen_color, 2 if is_active or is_grouped else 1))
            item.setZValue(1)
            self.scene.addItem(item)
            
            if tag == "csv_layer" and row_id: 
                self.overlay_items[row_id] = item

    def apply_highlight_to_items(self, selected_id):
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
                item.setZValue(1)