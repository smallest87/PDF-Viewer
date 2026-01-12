from PyQt6.QtWidgets import (QWidget, QTableView, QVBoxLayout, QHeaderView, 
                             QAbstractItemView, QSizePolicy, QStyledItemDelegate, QStyle)
from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex, QTimer, QEvent
from PyQt6.QtGui import (QFont, QColor, QBrush, QTextDocument, QTextCursor, QTextCharFormat)

# =============================================================================
# 1. DELEGATE: LOGIKA PEWARNAAN KARAKTER & WORDWRAP DINAMIS
# =============================================================================
class OCRTextDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._doc_cache = {} 

    def _get_document(self, text, width, font):
        cache_key = (text, width)
        if cache_key in self._doc_cache:
            return self._doc_cache[cache_key]

        doc = QTextDocument()
        doc.setDefaultFont(font)
        doc.setTextWidth(width)
        
        cursor = QTextCursor(doc)
        format_num = QTextCharFormat()
        format_num.setForeground(QColor("#0000FF")) 
        format_text = QTextCharFormat()
        format_text.setForeground(QColor("#8B4513")) 

        for char in text:
            cursor.insertText(char, format_num if char.isdigit() else format_text)
        
        if len(self._doc_cache) > 500: self._doc_cache.clear() 
        self._doc_cache[cache_key] = doc
        return doc

    def paint(self, painter, option, index):
        text = str(index.data(Qt.ItemDataRole.DisplayRole))
        if not text: return super().paint(painter, option, index)

        painter.save()
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())

        doc = self._get_document(text, option.rect.width(), option.font)
        painter.translate(option.rect.x(), option.rect.y())
        painter.setClipRect(0, 0, option.rect.width(), option.rect.height())
        doc.drawContents(painter)
        painter.restore()

    def sizeHint(self, option, index):
        text = str(index.data(Qt.ItemDataRole.DisplayRole))
        view = option.widget
        width = view.columnWidth(index.column()) if view else 200
        doc = self._get_document(text, width, option.font)
        return doc.size().toSize()

# =============================================================================
# 2. MODEL: PENGELOLA DATA (AUTO-SAVE TRIGGER)
# =============================================================================
class CSVModel(QAbstractTableModel):
    def __init__(self, headers, data, parent=None):
        super().__init__(parent) # Parent dikirim agar bisa akses Controller
        self._headers = headers
        self._data = data
        self.marked_ids = set()

    def rowCount(self, parent=QModelIndex()): return len(self._data)
    def columnCount(self, parent=QModelIndex()): return len(self._headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid(): return None
        row_idx, col_idx = index.row(), index.column()
        
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            return str(self._data[row_idx][col_idx])
            
        if role == Qt.ItemDataRole.BackgroundRole:
            if str(self._data[row_idx][0]) in self.marked_ids:
                return QBrush(QColor(255, 243, 176))
        return None

    def flags(self, index):
        return super().flags(index) | Qt.ItemFlag.ItemIsEditable

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        """Menyimpan editan ke memori dan memicu auto-save ke file fisik."""
        if index.isValid() and role == Qt.ItemDataRole.EditRole:
            # 1. Update list internal
            self._data[index.row()][index.column()] = value
            self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole])
            
            # 2. Trigger Simpan via Hirarki: TableView -> MainView -> Controller
            table_widget = self.parent() 
            if hasattr(table_widget, 'view') and hasattr(table_widget.view, 'controller'):
                table_widget.view.controller.save_csv_data(self._headers, self._data)
                
            return True
        return False

    def set_marked_ids(self, ids):
        self.marked_ids = set(ids) if ids else set()
        self.dataChanged.emit(self.index(0, 0), 
                              self.index(self.rowCount()-1, self.columnCount()-1), 
                              [Qt.ItemDataRole.BackgroundRole])

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self._headers[section]
        return None

# =============================================================================
# 3. VIEW: KOMPONEN TABEL
# =============================================================================
class PyQt6CSVTableView(QWidget):
    def __init__(self, parent, headers, data, on_row_select_callback=None):
        super().__init__(parent)
        self.view = parent # Simpan referensi ke Main View
        self.on_row_select = on_row_select_callback
        self.text_col_index = next((i for i, h in enumerate(headers) if "teks" in h.lower() or "text" in h.lower()), -1)
        self._setup_ui(headers, data)

    def _setup_ui(self, headers, data):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.table_view = QTableView(self)
        self.table_view.setWordWrap(True)
        
        v_header = self.table_view.verticalHeader()
        v_header.setDefaultSectionSize(25)
        v_header.hide()

        # Inisialisasi model dengan 'self' sebagai parent
        self.model = CSVModel(headers, data, self) 
        self.table_view.setModel(self.model)

        if self.text_col_index != -1:
            self.delegate = OCRTextDelegate(self)
            self.table_view.setItemDelegateForColumn(self.text_col_index, self.delegate)
        
        h_header = self.table_view.horizontalHeader()
        h_header.sectionResized.connect(self._on_column_resized)

        for i in range(len(headers)):
            h_header.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
            if i == self.text_col_index:
                self.table_view.setColumnWidth(i, 450)
            else:
                self.table_view.resizeColumnToContents(i)
                self.table_view.setColumnWidth(i, self.table_view.columnWidth(i) + 15)
        
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.selectionModel().selectionChanged.connect(self._row_selected)
        layout.addWidget(self.table_view)

    def _on_column_resized(self, logicalIndex, oldSize, newSize):
        if logicalIndex == self.text_col_index:
            if hasattr(self, 'delegate'): self.delegate._doc_cache.clear()
            QTimer.singleShot(10, self._resize_visible_rows_only)

    def _resize_visible_rows_only(self):
        rect = self.table_view.viewport().rect()
        top, bottom = self.table_view.rowAt(rect.top()), self.table_view.rowAt(rect.bottom())
        if top == -1: top = 0
        if bottom == -1: bottom = self.model.rowCount() - 1

        self.table_view.setUpdatesEnabled(False)
        for row in range(top, bottom + 1):
            self.table_view.resizeRowToContents(row)
        self.table_view.setUpdatesEnabled(True)

    def _row_selected(self):
        if self.on_row_select:
            indexes = self.table_view.selectionModel().selectedRows()
            if indexes: self.on_row_select(self.model._data[indexes[0].row()])

    def select_row_and_mark_group(self, target_sid, group_ids):
        self.model.set_marked_ids(group_ids)
        if target_sid:
            row_idx = int(target_sid) - 1
            if 0 <= row_idx < self.model.rowCount():
                curr = self.table_view.currentIndex()
                if curr.isValid() and curr.row() == row_idx: return
                
                idx = self.model.index(row_idx, curr.column() if curr.isValid() else 0)
                self.table_view.selectionModel().blockSignals(True)
                self.table_view.setCurrentIndex(idx)
                self.table_view.selectRow(row_idx)
                self.table_view.scrollTo(idx)
                self.table_view.selectionModel().blockSignals(False)