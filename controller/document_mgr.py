import os

import fitz


class DocumentManager:
    def __init__(self, model):
        self.model = model

    def open_pdf(self, path):
        """Memvalidasi file dan mengupdate state di Model"""
        if not path:
            return None
        try:
            self.model.doc = fitz.open(path)
            self.model.current_page = 0
            self.model.total_pages = len(self.model.doc)
            return os.path.basename(path)
        except Exception as e:
            print(f"Error opening PDF: {e}")
            return None

    def set_zoom(self, direction):
        """Logika kalkulasi zoom yang disimpan ke Model"""
        if direction == "in":
            self.model.zoom_level = min(5.0, self.model.zoom_level + 0.2)
        else:
            self.model.zoom_level = max(0.1, self.model.zoom_level - 0.2)

    def move_page(self, delta):
        """Navigasi halaman dengan validasi range"""
        new_page = self.model.current_page + delta
        if 0 <= new_page < self.model.total_pages:
            self.model.current_page = new_page
            return True
        return False
