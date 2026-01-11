from PyQt6.QtWidgets import QDialog, QTableView, QVBoxLayout, QHeaderView, QAbstractItemView
from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex

# --- 5.1 MODEL DATA (Sangat Efisien) ---
class CSVModel(QAbstractTableModel):
    def __init__(self, headers, data):
        super().__init__()
        self._headers = headers
        self._data = data

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            return str(self._data[index.row()][index.column()])
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self._headers[section]
        return None

# --- 5.2 VIEW WINDOW ---
class PyQt6CSVTableView(QDialog):
    """Window child untuk inspeksi data CSV menggunakan QTableView"""
    def __init__(self, parent, title, headers, data, on_row_select_callback=None):
        super().__init__(parent)
        self.setWindowTitle(f"Data Inspector - {title}")
        self.resize(900, 500)
        
        # Simpan callback
        self.on_row_select = on_row_select_callback
        
        self._setup_ui(headers, data)

    def _setup_ui(self, headers, data):
        layout = QVBoxLayout(self)
        
        # Inisialisasi Table View
        self.table_view = QTableView(self)
        
        # Inisialisasi Model
        self.model = CSVModel(headers, data)
        self.table_view.setModel(self.model)
        
        # Konfigurasi Tampilan
        header = self.table_view.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table_view.setAlternatingRowColors(True)
        
        # Binding Event: Pengganti 'row_select' pada tksheet
        self.table_view.selectionModel().selectionChanged.connect(self._row_selected)
        
        layout.addWidget(self.table_view)

    def _row_selected(self, selected, deselected):
        """Trigger callback saat baris dipilih"""
        if self.on_row_select:
            indexes = self.table_view.selectionModel().selectedRows()
            if indexes:
                row_idx = indexes[0].row()
                # Ambil data asli dari list data model
                row_data = self.model._data[row_idx]
                self.on_row_select(row_data)

    def select_row_by_index(self, index):
        """Menyorot baris secara otomatis dari PDF"""
        if 0 <= index < self.model.rowCount():
            self.table_view.selectRow(index)
            # Otomatis scroll ke baris tujuan (see() di tksheet)
            self.table_view.scrollTo(self.model.index(index, 0))

    def refresh_data(self, headers, data):
        """Update isi tanpa tutup jendela"""
        self.model = CSVModel(headers, data)
        self.table_view.setModel(self.model)