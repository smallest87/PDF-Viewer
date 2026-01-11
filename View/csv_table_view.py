from PyQt6.QtWidgets import QWidget, QTableView, QVBoxLayout, QHeaderView, QAbstractItemView, QSizePolicy
from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex, QTimer
from PyQt6.QtGui import QFont

# --- 1. MODEL DATA ---
class CSVModel(QAbstractTableModel):
    def __init__(self, headers, data):
        super().__init__()
        self._headers = headers
        self._data = data

    def rowCount(self, parent=QModelIndex()): return len(self._data)
    def columnCount(self, parent=QModelIndex()): return len(self._headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if index.isValid() and role == Qt.ItemDataRole.DisplayRole:
            return str(self._data[index.row()][index.column()])
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self._headers[section]
        return None

# --- 2. WIDGET PANEL ---
class PyQt6CSVTableView(QWidget):
    def __init__(self, parent, headers, data, on_row_select_callback=None):
        super().__init__(parent)
        self.on_row_select = on_row_select_callback
        
        # Izinkan panel menyusut total
        self.setMinimumWidth(0) 
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Timer untuk throttling log agar tidak bottleneck I/O
        self.debug_timer = QTimer()
        self.debug_timer.setSingleShot(True)
        self.debug_timer.timeout.connect(self._log_resize_final)
        
        self._setup_ui(headers, data)

    def _setup_ui(self, headers, data):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.table_view = QTableView(self)
        self.table_view.setMinimumWidth(0)

        # --- TAMBAHKAN KODE INI UNTUK FIX WARNA HIGHLIGHT ---
        self.table_view.setStyleSheet("""
            QTableView {
                selection-background-color: #0078d7; /* Warna biru saat aktif */
                selection-color: white;
            }
            QTableView:inactive {
                selection-background-color: #0078d7; /* Tetap biru meski kehilangan fokus */
                selection-color: white;
            }
        """)
        
        # PENGGANTI setUniformRowHeights: Optimasi baris statis
        v_header = self.table_view.verticalHeader()
        v_header.setDefaultSectionSize(20)
        v_header.setSectionResizeMode(QHeaderView.ResizeMode.Fixed) # Sangat Cepat
        v_header.hide()
        
        # Font Compact
        self.table_view.setFont(QFont("Bahnschrift SemiLight Condensed", 9))
        self.model = CSVModel(headers, data)
        self.table_view.setModel(self.model)
        
        # Optimasi Kolom (Interactive Mode)
        h_header = self.table_view.horizontalHeader()
        for i, header_text in enumerate(headers):
            if "teks" in header_text.lower() or "text" in header_text.lower():
                h_header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
            else:
                h_header.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
                self.table_view.resizeColumnToContents(i) 
        
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_view.setAlternatingRowColors(True)
        layout.addWidget(self.table_view)

        # Event Binding
        self.table_view.selectionModel().selectionChanged.connect(self._row_selected)

    def _row_selected(self, selected, deselected):
        if self.on_row_select:
            indexes = self.table_view.selectionModel().selectedRows()
            if indexes:
                self.on_row_select(self.model._data[indexes[0].row()])

    def select_row_by_index(self, index):
        if 0 <= index < self.model.rowCount():
            self.table_view.selectRow(index)
            self.table_view.scrollTo(self.model.index(index, 0))

    def resizeEvent(self, event):
        """Memicu timer log untuk menghindari bottleneck print"""
        super().resizeEvent(event)
        self.debug_timer.start(250) 

    def _log_resize_final(self):
        """Mencetak log hanya saat resize berhenti"""
        main_view = self.window()
        if hasattr(main_view, 'viewport'):
            print(f"[DEBUG-OK] Resize Selesai -> Dock: {self.width()}px | Viewport: {main_view.viewport.width()}px")