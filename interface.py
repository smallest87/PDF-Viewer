class PDFViewInterface:
    """Kontrak Abstraksi untuk GUI PDF Viewer (Tanpa Metaclass Conflict)"""
    
    def display_page(self, pix, ox, oy, region): raise NotImplementedError()
    def draw_rulers(self, doc_w, doc_h, ox, oy, zoom): raise NotImplementedError()
    def draw_text_layer(self, words, ox, oy, zoom): raise NotImplementedError()
    def draw_csv_layer(self, words, ox, oy, zoom): raise NotImplementedError()
    
    # WAJIB: Metode untuk pembersihan layer secara selektif
    def clear_overlay_layer(self, tag): raise NotImplementedError()
    
    def update_ui_info(self, page_num, total, zoom, is_sandwich, width, height, has_csv): raise NotImplementedError()
    def get_viewport_size(self): raise NotImplementedError()
    def update_progress(self, value): raise NotImplementedError()
    def set_application_title(self, filename): raise NotImplementedError()
    def update_highlight_only(self, selected_id): raise NotImplementedError()
    def set_grouping_control_state(self, active): raise NotImplementedError()