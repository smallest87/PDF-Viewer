import fitz
import os
from Controller.document_mgr import DocumentManager
from Controller.overlay_mgr import OverlayManager
from Controller.export_mgr import ExportManager

class PDFController:
    def __init__(self, view):
        self.view = view
        self.doc_mgr = DocumentManager(self)
        self.overlay_mgr = OverlayManager()
        self.export_mgr = ExportManager()

    @property
    def doc(self): return self.doc_mgr.doc

    def open_document(self, path):
        fname = self.doc_mgr.open_pdf(path)
        if fname:
            self.overlay_mgr.csv_path = path.rsplit('.', 1)[0] + ".csv"
            self.view.set_application_title(fname)
            self.refresh()

    def toggle_text_layer(self, val):
        self.overlay_mgr.show_text_layer = val
        self.refresh()

    def toggle_csv_layer(self, val):
        self.overlay_mgr.show_csv_layer = val
        self.refresh()

    def refresh(self):
        # 1. Validasi Keberadaan Dokumen
        # Mencegah error jika fungsi dipanggil saat belum ada file yang dibuka.
        if not self.doc: return 

        # 2. Pengambilan Objek Halaman Aktif
        # Mengakses objek halaman dari PyMuPDF berdasarkan indeks yang disimpan di DocumentManager.
        page = self.doc[self.doc_mgr.current_page] 

        # 3. Identifikasi Kapasitas Layar
        # vw (viewport width) diambil untuk menghitung posisi horizontal (centering).
        vw, _ = self.view.get_viewport_size() 

        # 4. Inisialisasi Skala Zoom
        # Mengambil level zoom (misal 1.0 = 100%) untuk transformasi koordinat.
        z = self.doc_mgr.zoom_level 

        # 5. Transformasi Matriks & Rasterisasi
        # Membuat matriks transformasi skalar untuk me-render PDF ke gambar (pixmap) sesuai zoom.
        mat = fitz.Matrix(z, z) 
        pix = page.get_pixmap(matrix=mat) 

        # 6. Kalkulasi Offset untuk Centering
        # ox (offset x) memastikan jika lebar gambar < lebar layar, gambar akan berada di tengah:
        # $$ox = \max(0, \frac{vw - pix.width}{2})$$
        # oy (offset y) mengambil nilai padding statis (misal 30pt) agar dokumen tidak menempel ke atas.
        ox, oy = max(0, (vw - pix.width) / 2), self.doc_mgr.padding 

        # 7. Penentuan Wilayah Scroll (Region)
        # Menentukan batas area yang bisa di-scroll oleh kanvas, termasuk ruang padding bawah.
        region = (0, 0, max(vw, pix.width), pix.height + (oy * 2)) 

        # 8. Render Layer Dasar (Gambar PDF)
        # Mengirim data gambar dan koordinat offset ke View untuk ditampilkan di kanvas.
        self.view.display_page(pix, ox, oy, region) 

        # 9. Logika Overlay Layer Teks Meta PDF (Warna Biru)
        # Jika toggle aktif, ambil kata-kata asli dari PDF dan gambar kotak overlay-nya.
        if self.overlay_mgr.show_text_layer:
            self.view.draw_text_layer(page.get_text("words"), ox, oy, z) 

        # 10. Logika Overlay Layer CSV (Warna Hijau)
        # Jika toggle aktif, ambil data koordinat dari file CSV pendamping (halaman + 1 karena indeks PDF mulai 0).
        if self.overlay_mgr.show_csv_layer:
            data = self.overlay_mgr.get_csv_data(self.doc_mgr.current_page + 1)
            self.view.draw_csv_layer(data, ox, oy, z) 

        # 11. Sinkronisasi Instrumen Bantu (Rulers)
        # Menggambar penggaris berdasarkan dimensi asli PDF yang telah dikalikan zoom.
        self.view.draw_rulers(page.rect.width, page.rect.height, ox, oy, z) 

        # 12. Identifikasi Status Dokumen (Audit Metadata)
        # is_s: Cek apakah dokumen memiliki layer teks (Sandwich) dengan cara men-strip whitespace.
        # has_csv: Cek fisik keberadaan file CSV di folder penyimpanan lokal.
        is_s = bool(page.get_text().strip())
        has_csv = os.path.exists(self.overlay_mgr.csv_path or "") 

        # 13. Pembaruan Informasi UI Total
        # Mengirim seluruh data status ke Status Bar (nomor halaman, total, zoom, status audit).
        self.view.update_ui_info(
            self.doc_mgr.current_page + 1, len(self.doc), z, is_s, 
            page.rect.width, page.rect.height, has_csv
        )

    def change_page(self, delta):
        if self.doc_mgr.move_page(delta): self.refresh()

    def jump_to_page(self, num):
        if self.doc and 0 <= num - 1 < len(self.doc):
            self.doc_mgr.current_page = num - 1
            self.refresh()

    def set_zoom(self, d):
        self.doc_mgr.set_zoom(d)
        self.refresh()

    def parse_page_ranges(self, s, t): return self.export_mgr.parse_ranges(s, t)

    def export_text_to_csv(self, f, i):
        self.export_mgr.to_csv(self.doc, f, i, self.view)