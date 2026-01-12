from PyQt6.QtWidgets import QWidget, QTableView, QVBoxLayout, QHeaderView, QAbstractItemView, QSizePolicy
from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex, QTimer, QEvent
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
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            return str(row_data[index.column()])

        # LOGIKA PENANDA GRUP (BACKGROUND)
        if role == Qt.ItemDataRole.BackgroundRole:
            if row_id in self.marked_ids:
                return QBrush(QColor(255, 243, 176)) # Kuning cerah untuk penanda grup
        
        return None

    # --- TAMBAHKAN INI UNTUK MENGAKTIFKAN FLAGS EDITING ---
    def flags(self, index):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        
        # Mengambil flags default (selectable, enabled) dan menambah Editable
        return super().flags(index) | Qt.ItemFlag.ItemIsEditable
    
    # --- TAMBAHKAN INI AGAR NILAI BARU DITERIMA ---
    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if index.isValid() and role == Qt.ItemDataRole.EditRole:
            # Update data internal
            self._data[index.row()][index.column()] = value
            # Emit sinyal bahwa data berubah agar UI me-refresh cell tersebut
            self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole])
            return True
        return False

    def set_marked_ids(self, ids):
        """Update warna tanpa reset seluruh model (Fokus tetap terjaga)"""
        self.marked_ids = set(ids) if ids else set()
        # Beritahu view bahwa seluruh area data perlu digambar ulang warnanya
        top_left = self.index(0, 0)
        bottom_right = self.index(self.rowCount() - 1, self.columnCount() - 1)
        self.dataChanged.emit(top_left, bottom_right, [Qt.ItemDataRole.BackgroundRole])

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self._headers[section]
        return None

# --- 2. WIDGET PANEL ---
class PyQt6CSVTableView(QWidget):
    def __init__(self, parent, headers, data, on_row_select_callback=None):
        super().__init__(parent)
        self.on_row_select = on_row_select_callback
        self.headers = headers # Simpan headers untuk referensi
        
        # Cari index kolom yang mengandung kata 'teks' atau 'text'
        self.text_col_index = -1
        for i, h in enumerate(headers):
            if "teks" in h.lower() or "text" in h.lower():
                self.text_col_index = i
                break

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
        self.table_view.installEventFilter(self)

        # 1. AKTIFKAN WORDWRAP
        self.table_view.setWordWrap(True)

        # 1. Matikan kalkulasi otomatis global (Biang kerok freeze)
        v_header = self.table_view.verticalHeader()
        v_header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive) # Biarkan user resize manual jika mau
        v_header.setDefaultSectionSize(25) # Tinggi default awal yang tipis
        v_header.hide()

        # CSS Tetap
        self.table_view.setStyleSheet("""
            QTableView {
                selection-background-color: #0078d7;
                selection-color: white;
            }
            QTableView:inactive {
                selection-background-color: #0078d7;
            }
        """)
        
        self.table_view.setFont(QFont("Bahnschrift SemiLight Condensed", 9))
        self.model = CSVModel(headers, data)
        self.table_view.setModel(self.model)
        
        # 2. Tangkap sinyal saat user melakukan resize kolom secara manual (Realtime)
        h_header = self.table_view.horizontalHeader()
        h_header.sectionResized.connect(self._on_column_resized)

        # 3. Tetapkan lebar awal kolom teks agar tidak meledak
        for i, header_text in enumerate(headers):
            h_header.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
            if i == self.text_col_index:
                self.table_view.setColumnWidth(i, 200)
            else:
                self.table_view.setColumnWidth(i, 80)
        
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table_view.setAlternatingRowColors(True)
        layout.addWidget(self.table_view)

        self.table_view.selectionModel().selectionChanged.connect(self._row_selected)

    # --- LOGIKA EXCEL-STYLE RESIZING ---
    def _on_column_resized(self, logicalIndex, oldSize, newSize):
        """Hanya hitung ulang tinggi baris jika kolom teks yang di-resize."""
        if logicalIndex == self.text_col_index:
            # Gunakan timer singkat agar tidak terlalu berat saat ditarik-tarik (Debouncing)
            QTimer.singleShot(10, self._resize_visible_rows_only)

    def _resize_visible_rows_only(self):
        """Hanya merubah tinggi baris yang sedang tampil di layar (Performa Kilat)."""
        # Dapatkan range baris yang saat ini terlihat oleh mata user
        viewport_rect = self.table_view.viewport().rect()
        top_row = self.table_view.rowAt(viewport_rect.top())
        bottom_row = self.table_view.rowAt(viewport_rect.bottom())

        if top_row == -1: top_row = 0
        if bottom_row == -1: bottom_row = self.model.rowCount() - 1

        # Block sinyal sementara agar tidak terjadi feedback loop
        self.table_view.setUpdatesEnabled(False)
        
        # Hanya hitung tinggi untuk baris yang terlihat saja (Misal 10-20 baris)
        for row in range(top_row, bottom_row + 1):
            self.table_view.resizeRowToContents(row)
            
        self.table_view.setUpdatesEnabled(True)

    # LOGIKA MENANGKAP TOMBOL ENTER
    def eventFilter(self, source, event):
        if source is self.table_view and event.type() == QEvent.Type.KeyPress:
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                current_index = self.table_view.currentIndex()
                if current_index.isValid():
                    # Targetkan baris yang aktif, tapi kolom pindah ke 'text_col_index'
                    target_row = current_index.row()
                    target_col = self.text_col_index if self.text_col_index != -1 else current_index.column()
                    
                    target_index = self.model.index(target_row, target_col)
                    
                    # Pindahkan kursor ke cell tersebut dan buka mode edit
                    self.table_view.setCurrentIndex(target_index)
                    self.table_view.edit(target_index)
                    return True # Event ditangani, jangan teruskan ke default QTableView
        
        return super().eventFilter(source, event)

    def _row_selected(self, selected, deselected):
        if self.on_row_select:
            indexes = self.table_view.selectionModel().selectedRows()
            if indexes:
                self.on_row_select(self.model._data[indexes[0].row()])

    def select_row_and_mark_group(self, target_sid, group_ids):
        """Menandai grup dan menetapkan kursor tanpa merusak posisi kolom."""
        # 1. Update tanda visual di Model (sudah benar menggunakan dataChanged)
        self.model.set_marked_ids(group_ids)
        
        if target_sid:
            row_idx = int(target_sid) - 1
            if 0 <= row_idx < self.model.rowCount():
                # AMBIL indeks kursor saat ini
                current_index = self.table_view.currentIndex()
                
                # CEK: Jika kursor sudah berada di baris yang benar, JANGAN panggil selectRow lagi
                # Ini akan mencegah kursor melompat kembali ke kolom 0 saat navigasi keyboard
                if current_index.isValid() and current_index.row() == row_idx:
                    return

                # Jika memang perlu pindah (misal karena input manual atau klik dari luar)
                self.table_view.selectionModel().blockSignals(True)
                
                # Gunakan setCurrentIndex agar kita bisa menentukan kolomnya secara spesifik
                # Kita arahkan ke kolom yang sedang aktif saat ini, bukan otomatis ke kolom 0
                target_col = current_index.column() if current_index.isValid() else 0
                new_index = self.model.index(row_idx, target_col)
                
                self.table_view.setCurrentIndex(new_index)
                self.table_view.selectRow(row_idx) # Sekarang aman karena index sudah diatur
                self.table_view.scrollTo(new_index)
                
                self.table_view.selectionModel().blockSignals(False)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.debug_timer.start(250)

    def _log_resize_final(self):
        main_view = self.window()
        if hasattr(main_view, 'viewport'):
            print(f"[DEBUG-OK] Resize Selesai -> Dock: {self.width()}px | Viewport: {main_view.viewport.width()}px")