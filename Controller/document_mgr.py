import fitz
import os

class DocumentManager:
    def __init__(self, controller):
        self.c = controller
        self.doc = None
        self.current_page = 0
        self.zoom_level = 1.0
        self.padding = 30

    def open_pdf(self, path):
        """Membuka file PDF dan mereset status"""
        if not path: return None
        self.doc = fitz.open(path)
        self.current_page = 0
        return os.path.basename(path)

    def set_zoom(self, direction):
        """Menghitung level zoom"""
        if direction == "in": self.zoom_level = min(5.0, self.zoom_level + 0.2)
        else: self.zoom_level = max(0.1, self.zoom_level - 0.2)

    def move_page(self, delta):
        """Navigasi relatif halaman"""
        if self.doc and 0 <= self.current_page + delta < len(self.doc):
            self.current_page += delta
            return True
        return False