from abc import ABC, abstractmethod

class PDFViewInterface(ABC):
    """Kontrak Abstraksi untuk GUI PDF Viewer"""
    
    @abstractmethod
    def display_page(self, pix, ox, oy, region): 
        """Menampilkan gambar PDF di layar"""
        pass
    
    @abstractmethod
    def draw_rulers(self, doc_w, doc_h, ox, oy, zoom): 
        """Menggambar penggaris berdasarkan koordinat dokumen"""
        pass

    @abstractmethod
    def draw_text_layer(self, words, ox, oy, zoom): pass # Tambahan baru
    
    @abstractmethod
    def update_ui_info(self, page_num, total, zoom, is_sandwich, width, height): 
        """Memperbarui teks informasi di UI termasuk dimensi halaman"""
        pass

    @abstractmethod
    def get_viewport_size(self): 
        """Mendapatkan lebar/tinggi viewport saat ini"""
        pass

    @abstractmethod
    def update_progress(self, value):
        """Memperbarui nilai progress bar (0-100)"""
        pass

    @abstractmethod
    def set_application_title(self, filename):
        """Mengubah judul jendela aplikasi berdasarkan file yang dibuka"""
        pass