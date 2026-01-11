from PyQt6.QtWidgets import QWidget, QTableView, QVBoxLayout, QHeaderView, QAbstractItemView, QSizePolicy
from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex, QTimer
from PyQt6.QtGui import QFont, QColor, QBrush

# --- 1. MODEL DATA ---
class CSVModel(QAbstractTableModel):
    def __init__(self, headers, data):
        super().__init__()
        self._headers = headers
        self._data = data
        self.marked_ids = set() # Menyimpan ID baris yang merupakan anggota grup

    def rowCount(self, parent=QModelIndex()): return len(self._data)
    def columnCount(self, parent=QModelIndex()): return len(self._headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
            
        row_data = self._data[index.row()]
        row_id = str(row_data[0]) # Menggunakan kolom 'nomor' sebagai ID

        # Logika Teks Utama
        if role == Qt.ItemDataRole.DisplayRole:
            return str(row_data[index.column()])

        # LOGIKA PENANDA GRUP (BACKGROUND)
        if role == Qt.ItemDataRole.BackgroundRole:
            if row_id in self.marked_ids:
                return QBrush(QColor(255, 243, 176)) # Kuning cerah untuk penanda grup
        
        return None

    def set_marked_ids(self, ids):
        """Memperbarui daftar ID grup dan me-refresh tampilan tabel secara efisien."""
        self.beginResetModel()
        self.marked_ids = set(ids) if ids else set()
        self.endResetModel()

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self._headers[section]
        return None

# --- 2. WIDGET PANEL ---
class PyQt6CSVTableView(QWidget):
    def __init__(self, parent, headers, data, on_row_select_callback=None):
        super().__init__(parent)
        self.on_row_select = on_row_select_callback
        
        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        self.debug_timer = QTimer()
        self.debug_timer.setSingleShot(True)
        self.debug_timer.timeout.connect(self._log_resize_final)
        
        self._setup_ui(headers, data)

    def _setup_ui(self, headers, data):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.table_view = QTableView(self)
        self.table_view.setMinimumWidth(0)

        # CSS untuk memastikan highlight aktif tetap terlihat jelas
        self.table_view.setStyleSheet("""
            QTableView {
                selection-background-color: #0078d7;
                selection-color: white;
            }
            QTableView:inactive {
                selection-background-color: #0078d7;
            }
        """)
        
        v_header = self.table_view.verticalHeader()
        v_header.setDefaultSectionSize(20)
        v_header.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        v_header.hide()
        
        self.table_view.setFont(QFont("Bahnschrift SemiLight Condensed", 9))
        self.model = CSVModel(headers, data)
        self.table_view.setModel(self.model)
        
        h_header = self.table_view.horizontalHeader()
        for i, header_text in enumerate(headers):
            if "teks" in header_text.lower() or "text" in header_text.lower():
                h_header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
            else:
                h_header.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
                self.table_view.resizeColumnToContents(i)
        
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection) # Mempertahankan satu kursor
        self.table_view.setAlternatingRowColors(True)
        layout.addWidget(self.table_view)

        self.table_view.selectionModel().selectionChanged.connect(self._row_selected)

    def _row_selected(self, selected, deselected):
        if self.on_row_select:
            indexes = self.table_view.selectionModel().selectedRows()
            if indexes:
                self.on_row_select(self.model._data[indexes[0].row()])

    def select_row_and_mark_group(self, target_sid, group_ids):
        """Menandai grup dan menetapkan kursor tanpa memicu feedback loop."""
        # 1. Update tanda visual di Model
        self.model.set_marked_ids(group_ids)
        
        # 2. Update seleksi kursor (DIPROTEKSI DENGAN BLOCK SIGNALS)
        if target_sid:
            row_idx = int(target_sid) - 1
            if 0 <= row_idx < self.model.rowCount():
                # BLOKIR SINYAL agar tidak memicu _row_selected kembali ke controller
                self.table_view.selectionModel().blockSignals(True)
                
                self.table_view.selectRow(row_idx)
                self.table_view.scrollTo(self.model.index(row_idx, 0))
                
                # AKTIFKAN KEMBALI setelah selesai
                self.table_view.selectionModel().blockSignals(False)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.debug_timer.start(250)

    def _log_resize_final(self):
        main_view = self.window()
        if hasattr(main_view, 'viewport'):
            print(f"[DEBUG-OK] Resize Selesai -> Dock: {self.width()}px | Viewport: {main_view.viewport.width()}px")