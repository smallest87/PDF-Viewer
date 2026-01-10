import fitz
import os
import csv

class PDFController:
    def __init__(self, view):
        self.view = view
        self.doc = None
        self.current_page = 0
        self.zoom_level = 1.0
        self.padding = 30
        self.show_text_layer = False
        self.show_csv_layer = False
        self.csv_data_path = None # Path file CSV dengan nama yang sama

    def open_document(self, path):
        if not path: return
        self.doc = fitz.open(path)
        self.current_page = 0
        
        # Cek keberadaan file CSV di folder yang sama
        self.csv_data_path = path.rsplit('.', 1)[0] + ".csv"
        
        self.view.set_application_title(os.path.basename(path))
        self.refresh()

    def toggle_text_layer(self, value):
        self.show_text_layer = value
        self.refresh()

    def toggle_csv_layer(self, value):
        self.show_csv_layer = value
        self.refresh()

    def _get_csv_data_for_page(self, page_num):
        """Membaca data koordinat dari file CSV pendamping"""
        if not self.csv_data_path or not os.path.exists(self.csv_data_path):
            return []
        
        page_words = []
        try:
            with open(self.csv_data_path, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f, delimiter=';')
                for row in reader:
                    if int(row['halaman']) == page_num:
                        # Konversi desimal koma ke titik untuk float Python
                        x0 = float(row['x0'].replace(',', '.'))
                        y0 = float(row['top'].replace(',', '.'))
                        x1 = float(row['x1'].replace(',', '.'))
                        y1 = float(row['bottom'].replace(',', '.'))
                        page_words.append((x0, y0, x1, y1, row['teks']))
        except: pass
        return page_words

    def refresh(self):
        if not self.doc: return
        page = self.doc[self.current_page]
        vw, _ = self.view.get_viewport_size()
        mat = fitz.Matrix(self.zoom_level, self.zoom_level)
        pix = page.get_pixmap(matrix=mat)
        ox, oy = max(0, (vw - pix.width) / 2), self.padding
        region = (0, 0, max(vw, pix.width), pix.height + (self.padding * 2))
        
        self.view.display_page(pix, ox, oy, region)
        
        if self.show_text_layer:
            self.view.draw_text_layer(page.get_text("words"), ox, oy, self.zoom_level)
            
        if self.show_csv_layer:
            csv_words = self._get_csv_data_for_page(self.current_page + 1)
            self.view.draw_csv_layer(csv_words, ox, oy, self.zoom_level)
        
        self.view.draw_rulers(page.rect.width, page.rect.height, ox, oy, self.zoom_level)
        is_sandwich = bool(page.get_text().strip())
        has_csv = os.path.exists(self.csv_data_path) if self.csv_data_path else False
        
        self.view.update_ui_info(
            self.current_page+1, len(self.doc), self.zoom_level, 
            is_sandwich, page.rect.width, page.rect.height, has_csv
        )

    def change_page(self, delta):
        if self.doc and 0 <= self.current_page + delta < len(self.doc):
            self.current_page += delta
            self.refresh()

    def jump_to_page(self, page_num):
        if self.doc and 0 <= page_num - 1 < len(self.doc):
            self.current_page = page_num - 1
            self.refresh()

    def set_zoom(self, direction):
        if direction == "in": self.zoom_level = min(5.0, self.zoom_level + 0.2)
        else: self.zoom_level = max(0.1, self.zoom_level - 0.2)
        self.refresh()

    def parse_page_ranges(self, range_str, total_pages):
        pages = set()
        try:
            for part in range_str.split(','):
                part = part.strip()
                if '-' in part:
                    start, end = map(int, part.split('-'))
                    pages.update(range(start - 1, end))
                else:
                    pages.add(int(part) - 1)
        except: return None
        return sorted([p for p in pages if 0 <= p < total_pages])

    def export_text_to_csv(self, filepath, page_indices):
        if not self.doc or not page_indices: return
        total = len(page_indices)
        
        def fmt(val):
            if isinstance(val, (float, int)): return str(round(val, 2)).replace('.', ',')
            return str(val).replace(';', ' ').replace('\n', ' ').strip()

        header = ["nomor", "halaman", "teks", "x0", "x1", "top", "bottom", "font_style", "font_size", "sumbu"]
        with open(filepath, mode='w', encoding='utf-8-sig') as f:
            f.write(";".join(header) + "\n")
            idx = 1
            for i, p_idx in enumerate(page_indices):
                blocks = self.doc[p_idx].get_text("dict")["blocks"]
                for b in [b for b in blocks if b["type"] == 0]:
                    for line in b["lines"]:
                        for span in line["spans"]:
                            x0, y0, x1, y1 = span["bbox"]
                            row = [idx, p_idx + 1, span["text"], x0, x1, y0, y1, span["font"], span["size"], (y0 + y1) / 2]
                            f.write(";".join(map(fmt, row)) + "\n")
                            idx += 1
                self.view.update_progress(((i + 1) / total) * 100)
            self.view.update_progress(0)