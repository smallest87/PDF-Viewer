from abc import ABC, abstractmethod

class PDFViewInterface(ABC):
    """Kontrak Abstraksi untuk GUI PDF Viewer"""
    
    @abstractmethod
    def display_page(self, pix, ox, oy, region): pass
    
    @abstractmethod
    def draw_rulers(self, doc_w, doc_h, ox, oy, zoom): pass

    @abstractmethod
    def draw_text_layer(self, words, ox, oy, zoom): pass
    
    @abstractmethod
    def draw_csv_layer(self, words, ox, oy, zoom): pass
    
    @abstractmethod
    def update_ui_info(self, page_num, total, zoom, is_sandwich, width, height, has_csv): 
        """Memperbarui teks informasi di UI termasuk status file CSV"""
        pass

    @abstractmethod
    def get_viewport_size(self): pass

    @abstractmethod
    def update_progress(self, value): pass

    @abstractmethod
    def set_application_title(self, filename): pass