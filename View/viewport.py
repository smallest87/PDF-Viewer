from typing import override

from components.ruler_system import RulerWrapper
from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QPainter, QPen
from PyQt6.QtWidgets import (
    QFrame,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsView,
    QVBoxLayout,
)


class ClickableGraphicsView(QGraphicsView):
    def __init__(self, scene, viewport_parent):
        super().__init__(scene)
        self.viewport_parent = viewport_parent

        # AKTIFKAN TRACKING MOUSE
        self.setMouseTracking(True)

        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setStyleSheet("background-color: #323639; border: none;")
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)

    @override
    def mouseMoveEvent(self, event):
        """Menangkap koordinat scene saat mouse bergerak."""
        # 1. Konversi posisi mouse ke koordinat Scene
        scene_pos = self.mapToScene(event.pos())

        # 2. Kirim data ke Main View (via Viewport Parent)
        self.viewport_parent.on_mouse_moved(scene_pos)

        # 3. Cek apakah ada item (teks/csv) di bawah kursor
        item = self.itemAt(event.pos())
        if item and isinstance(item, QGraphicsRectItem):
            # Jika item adalah overlay, ambil data koordinat aslinya
            # (Pastikan item memiliki data koordinat PDF asli jika diperlukan)
            pass

        super().mouseMoveEvent(event)

    @override
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            item = self.itemAt(event.pos())
            if item and isinstance(item, QGraphicsRectItem):
                row_id = item.data(0)
                tag = item.data(1)
                if tag == "csv_layer" and row_id:
                    self.viewport_parent.view.controller._on_overlay_click(row_id)
        super().mouse_press_event(event)


class PyQt6Viewport(QFrame):
    def __init__(self, parent_view):
        super().__init__()
        self.view = parent_view
        self.scene = QGraphicsScene()
        self.graphics_view = ClickableGraphicsView(self.scene, self)

        # Penampung variabel transformasi
        self.last_ox = 0
        self.last_oy = 0
        self.last_zoom = 1.0
        self.last_doc_w = 0  # Tambahkan ini
        self.last_doc_h = 0  # Tambahkan ini

        self.container = RulerWrapper(self.graphics_view)
        self.overlay_items = {}
        self._setup_layout()

    def on_mouse_moved(self, scene_pos):
        """Logika konversi dengan pengecekan batas halaman."""
        # 1. Cek apakah ada dokumen aktif
        if not self.view.controller.model.doc or self.last_zoom <= 0:
            self.view._update_coord_display(None, None)
            return

        # 2. Hitung koordinat relatif terhadap PDF asli
        pdf_x = (scene_pos.x() - self.last_ox) / self.last_zoom
        pdf_top = (scene_pos.y() - self.last_oy) / self.last_zoom

        # 3. Validasi: Hanya aktif jika di dalam area halaman (0 sampai lebar/tinggi)
        if 0 <= pdf_x <= self.last_doc_w and 0 <= pdf_top <= self.last_doc_h:
            self.view._update_coord_display(pdf_x, pdf_top)
        else:
            # Jika di luar halaman, kirim None untuk mengosongkan display
            self.view._update_coord_display(None, None)

    def _setup_layout(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.container)

    def update_rulers(self, doc_w, doc_h, ox, oy, zoom):
        """Update penggaris dan simpan nilai transformasi."""
        self.last_ox = ox
        self.last_oy = oy
        self.last_zoom = zoom
        self.last_doc_w = doc_w  # Simpan lebar dokumen asli
        self.last_doc_h = doc_h  # Simpan tinggi dokumen asli
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
        grouped_ids = (
            self.view.controller._get_grouped_ids() if tag == "csv_layer" else set()
        )
        sel_id = str(self.view.controller.model.selected_row_id)

        for w in words:
            rect = QRectF(
                w[0] * zoom + ox,
                w[1] * zoom + oy,
                (w[2] - w[0]) * zoom,
                (w[3] - w[1]) * zoom,
            )
            item = QGraphicsRectItem(rect)
            row_id = str(w[5]) if len(w) > 5 else None
            item.setData(0, row_id)
            item.setData(1, tag)

            item.setBrush(QBrush(QColor(color.red(), color.green(), color.blue(), 60)))
            is_active = row_id == sel_id
            is_grouped = row_id in grouped_ids

            pen_color = (
                QColor("red")
                if is_active
                else (QColor("orange") if is_grouped else color)
            )
            item.setPen(QPen(pen_color, 2 if is_active or is_grouped else 1))
            item.setZValue(1)
            self.scene.addItem(item)

            if tag == "csv_layer" and row_id:
                self.overlay_items[row_id] = item

    def apply_highlight_to_items(self, selected_id):
        """Pemusatan Vertikal Eksklusif: Menjaga kursor horizontal tetap di tempatnya."""
        grouped_ids = self.view.controller._get_grouped_ids()
        sel_id_str = str(selected_id)

        target_item = None
        for row_id, item in self.overlay_items.items():
            rid = str(row_id)
            is_active = rid == sel_id_str
            is_grouped = rid in grouped_ids

            if is_active:
                item.setPen(QPen(QColor("red"), 3))
                item.setZValue(10)
                target_item = item  # Referensi untuk centering
            elif is_grouped:
                item.setPen(QPen(QColor("orange"), 2))
                item.setZValue(5)
            else:
                item.setPen(QPen(QColor("#28a745"), 1))
                item.setZValue(1)

        # LOGIKA PEMUSATAN VERTIKAL SAJA
        if target_item:
            # 1. Dapatkan pusat viewport saat ini dipetakan ke koordinat scene (Sumbu X)
            current_view_center = self.graphics_view.viewport().rect().center()
            current_scene_center = self.graphics_view.mapToScene(current_view_center)

            # 2. Dapatkan pusat vertikal dari item target (Sumbu Y)
            target_center_y = target_item.sceneBoundingRect().center().y()

            # 3. Lakukan pemusatan dengan mempertahankan X lama dan memperbarui Y baru
            self.graphics_view.centerOn(current_scene_center.x(), target_center_y)
