import fitz
import os # Tambahkan import os

class PDFController:
    def __init__(self, view):
        self.view = view
        self.doc = None
        self.current_page = 0
        self.zoom_level = 1.0
        self.padding = 30
        self.show_text_layer = False # State toggle

    def open_document(self, path):
        if not path: return
        self.doc = fitz.open(path)
        self.current_page = 0

        # Ambil nama file saja dari path lengkap
        filename = os.path.basename(path)
        self.view.set_application_title(filename)

        self.refresh()

    def toggle_text_layer(self, value):
        self.show_text_layer = value
        self.refresh()

    def refresh(self):
        if not self.doc: return
        page = self.doc[self.current_page]
        
        vw, _ = self.view.get_viewport_size()
        mat = fitz.Matrix(self.zoom_level, self.zoom_level)
        pix = page.get_pixmap(matrix=mat)
        
        ox = max(0, (vw - pix.width) / 2)
        oy = self.padding
        region = (0, 0, max(vw, pix.width), pix.height + (self.padding * 2))
        
        # 1. Tampilkan Halaman Utama
        self.view.display_page(pix, ox, oy, region)
        
        # 2. Gambar Layer Teks jika aktif
        if self.show_text_layer:
            words = page.get_text("words")
            self.view.draw_text_layer(words, ox, oy, self.zoom_level)
        
        # 3. Update Rulers & UI
        # Update Rulers & UI dengan menyertakan dimensi halaman
        self.view.draw_rulers(page.rect.width, page.rect.height, ox, oy, self.zoom_level)
        is_sandwich = bool(page.get_text().strip())
        
        self.view.update_ui_info(
            self.current_page + 1, 
            len(self.doc), 
            self.zoom_level, 
            is_sandwich,
            page.rect.width,
            page.rect.height
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
        """Mengubah string '1, 2, 5-10' menjadi list indeks [0, 1, 4, 5...6, 9]"""
        pages = set()
        try:
            for part in range_str.split(','):
                part = part.strip()
                if '-' in part:
                    start, end = map(int, part.split('-'))
                    pages.update(range(start - 1, end))
                else:
                    pages.add(int(part) - 1)
        except:
            return None # Input tidak valid
        
        # Filter agar tidak melebihi jumlah halaman yang ada
        return sorted([p for p in pages if 0 <= p < total_pages])

    def export_text_to_csv(self, filepath, page_indices):
        """Ekspor teks berdasarkan daftar indeks halaman tertentu"""
        if not self.doc or not page_indices: return
        
        total_to_export = len(page_indices)
        
        def fmt(val):
            if isinstance(val, (float, int)):
                return str(round(val, 2)).replace('.', ',')
            return str(val).replace(';', ' ').replace('\n', ' ').strip()

        header = ["nomor", "halaman", "teks", "x0", "x1", "top", "bottom", "font_style", "font_size", "sumbu"]
        
        with open(filepath, mode='w', encoding='utf-8-sig') as f:
            f.write(";".join(header) + "\n")
            global_index = 1
            
            for i, page_idx in enumerate(page_indices):
                page = self.doc[page_idx]
                blocks = page.get_text("dict")["blocks"]
                for b in blocks:
                    if b["type"] == 0:
                        for line in b["lines"]:
                            for span in line["spans"]:
                                x0, y0, x1, y1 = span["bbox"]
                                sumbu = (y0 + y1) / 2
                                row = [global_index, page_idx + 1, span["text"], x0, x1, y0, y1, span["font"], span["size"], sumbu]
                                f.write(";".join(map(fmt, row)) + "\n")
                                global_index += 1
                
                # Update progress berdasarkan progres daftar halaman terpilih
                self.view.update_progress(((i + 1) / total_to_export) * 100)
            
            self.view.update_progress(0)

    def export_all_text_to_csv(self, filepath):
        if not self.doc: return
        total_pages = len(self.doc) #
        
        def fmt(val):
            if isinstance(val, (float, int)):
                return str(round(val, 2)).replace('.', ',')
            return str(val).replace(';', ' ').replace('\n', ' ').strip()

        header = ["nomor", "halaman", "teks", "x0", "x1", "top", "bottom", "font_style", "font_size", "sumbu"]
        
        with open(filepath, mode='w', encoding='utf-8-sig') as f:
            f.write(";".join(header) + "\n")
            global_index = 1
            
            for page_idx in range(total_pages):
                page = self.doc[page_idx] #
                blocks = page.get_text("dict")["blocks"] #
                
                for b in blocks:
                    if b["type"] == 0:
                        for line in b["lines"]:
                            for span in line["spans"]:
                                x0, y0, x1, y1 = span["bbox"]
                                sumbu = (y0 + y1) / 2
                                row = [global_index, page_idx + 1, span["text"], x0, x1, y0, y1, span["font"], span["size"], sumbu]
                                f.write(";".join(map(fmt, row)) + "\n")
                                global_index += 1
                
                # Hitung dan kirim progress ke View
                progress_percent = ((page_idx + 1) / total_pages) * 100
                self.view.update_progress(progress_percent)
            
            # Reset progress setelah selesai
            self.view.update_progress(0)