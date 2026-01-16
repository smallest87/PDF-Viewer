"""Module untuk manajemen tampilan tabel CSV menggunakan pola Model-View-Delegate.

Module ini menyediakan:
1. OCRTextDelegate: Menangani pewarnaan teks (angka vs huruf) dan word wrap.
2. CSVModel: Mengelola data mentah dan logika sinkronisasi ke Controller.
3. PyQt6CSVTableView: Komponen UI utama untuk menampilkan dan mengedit data.
"""

from collections.abc import Callable, Iterable
from typing import Any

from PyQt6.QtCore import QAbstractTableModel, QModelIndex, QSize, Qt, QTimer
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QPainter,
    QTextCharFormat,
    QTextCursor,
    QTextDocument,
)
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTableView,
    QVBoxLayout,
    QWidget,
)


class OCRTextDelegate(QStyledItemDelegate):
    """Delegate khusus untuk kolom teks hasil OCR.

    Menangani pewarnaan karakter secara dinamis (biru untuk angka, cokelat untuk teks)
    dan melakukan caching dokumen untuk optimasi performa rendering.

    Attributes:
        _doc_cache (Dict[Tuple[str, int], QTextDocument]): Cache untuk objek QTextDocument.

    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Inisialisasi delegate dengan cache kosong."""
        super().__init__(parent)
        self._doc_cache: dict[tuple[str, int], QTextDocument] = {}

    def _get_document(self, text: str, width: int, font: QFont) -> QTextDocument:
        """Membuat atau mengambil QTextDocument dari cache untuk teks tertentu.

        Args:
            text (str): Teks yang akan dirender.
            width (int): Lebar kolom yang tersedia.
            font (QFont): Font yang digunakan pada view.

        Returns:
            QTextDocument: Objek dokumen yang sudah diformat.

        """
        cache_key = (text, width)
        if cache_key in self._doc_cache:
            return self._doc_cache[cache_key]

        doc = QTextDocument()
        doc.setDefaultFont(font)
        doc.setTextWidth(float(width))

        cursor = QTextCursor(doc)
        format_num = QTextCharFormat()
        format_num.setForeground(QColor("#0000FF"))  # Blue
        format_text = QTextCharFormat()
        format_text.setForeground(QColor("#8B4513"))  # Brown

        for char in text:
            cursor.insertText(char, format_num if char.isdigit() else format_text)

        if len(self._doc_cache) > 500:
            self._doc_cache.clear()
        self._doc_cache[cache_key] = doc
        return doc

    def paint(
        self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex
    ) -> None:
        """Render isi sel dengan format teks kustom."""
        text = str(index.data(Qt.ItemDataRole.DisplayRole))
        if not text:
            return super().paint(painter, option, index)

        painter.save()
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())

        doc = self._get_document(text, option.rect.width(), option.font)
        painter.translate(float(option.rect.x()), float(option.rect.y()))
        painter.setClipRect(0, 0, option.rect.width(), option.rect.height())
        doc.drawContents(painter)
        painter.restore()

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        """Menghitung ukuran sel berdasarkan konten yang di-wrap."""
        text = str(index.data(Qt.ItemDataRole.DisplayRole))
        view = option.widget
        # Type check safely for width calculation
        width = (
            view.columnWidth(index.column()) if isinstance(view, QTableView) else 200
        )
        doc = self._get_document(text, width, option.font)
        return doc.size().toSize()


class CSVModel(QAbstractTableModel):
    """Model data untuk menampung konten CSV.

    Menangani penyimpanan data di memori, penandaan (marking) baris,
    dan memicu penyimpanan otomatis melalui controller saat data diubah.
    """

    def __init__(
        self, headers: list[str], data: list[list[Any]], parent: QWidget | None = None
    ) -> None:
        """Inisialisasi model.

        Args:
            headers (List[str]): Daftar nama kolom.
            data (List[List[Any]]): Data baris dan kolom.
            parent (Optional[QWidget]): Parent widget (biasanya PyQt6CSVTableView).

        """
        super().__init__(parent)
        self._headers: list[str] = headers
        self._data: list[list[Any]] = data
        self.marked_ids: set[str] = set()

    def rowCount(self, parent: QModelIndex | None = None) -> int:
        """Mendapatkan jumlah baris dalam model data.

        Args:
            parent (Optional[QModelIndex]): Index parent dari model.
                Default adalah None (null index).

        Returns:
            int: Jumlah total baris berdasarkan data internal.

        """
        # Jika parent tidak None dan valid (untuk model tree), logika bisa berbeda.
        # Namun untuk model tabel flat, kita cukup mengembalikan panjang data.
        return len(self._data)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Mendapatkan jumlah kolom."""
        return len(self._headers)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """Mendapatkan data untuk index dan role tertentu."""
        if not index.isValid():
            return None
        row_idx, col_idx = index.row(), index.column()

        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            return str(self._data[row_idx][col_idx])

        if role == Qt.ItemDataRole.BackgroundRole:
            if str(self._data[row_idx][0]) in self.marked_ids:
                return QBrush(QColor(255, 243, 176))
        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        """Mengatur flag item agar bisa diedit."""
        return super().flags(index) | Qt.ItemFlag.ItemIsEditable

    def setData(
        self, index: QModelIndex, value: Any, role: int = Qt.ItemDataRole.EditRole
    ) -> bool:
        """Menyimpan perubahan data dari UI ke memori dan memicu auto-save.

        Args:
            index (QModelIndex): Lokasi data yang diubah.
            value (Any): Nilai baru.
            role (int): Role pengeditan.

        Returns:
            bool: True jika berhasil disimpan.

        """
        if index.isValid() and role == Qt.ItemDataRole.EditRole:
            self._data[index.row()][index.column()] = value
            self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole])

            # Trigger Simpan via Hirarki
            table_widget = self.parent()
            if hasattr(table_widget, "view") and hasattr(
                table_widget.view, "controller"
            ):
                table_widget.view.controller.save_csv_data(self._headers, self._data)
            return True
        return False

    def set_marked_ids(self, ids: Iterable[str]) -> None:
        """Menandai baris-baris tertentu dengan warna latar belakang.

        Args:
            ids (Iterable[str]): Kumpulan ID baris (kolom pertama) yang akan ditandai.

        """
        self.marked_ids = set(ids) if ids else set()
        self.dataChanged.emit(
            self.index(0, 0),
            self.index(self.rowCount() - 1, self.columnCount() - 1),
            [Qt.ItemDataRole.BackgroundRole],
        )

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        """Mendapatkan label untuk header tabel."""
        if (
            orientation == Qt.Orientation.Horizontal
            and role == Qt.ItemDataRole.DisplayRole
        ):
            return self._headers[section]
        return None


class PyQt6CSVTableView(QWidget):
    """Widget utama pembungkus QTableView untuk data CSV.

    Mengintegrasikan model dan delegate serta menangani logika resize dinamis.
    """

    def __init__(
        self,
        parent: QWidget,
        headers: list[str],
        data: list[list[Any]],
        on_row_select_callback: Callable[[list[Any]], None] | None = None,
    ) -> None:
        """Inisialisasi View.

        Args:
            parent (QWidget): Main View utama.
            headers (List[str]): Header CSV.
            data (List[List[Any]]): Data CSV.
            on_row_select_callback (Optional[Callable]): Fungsi yang dipanggil saat baris dipilih.

        """
        super().__init__(parent)
        self.view: QWidget = parent
        self.on_row_select: Callable | None = on_row_select_callback
        self.text_col_index: int = next(
            (
                i
                for i, h in enumerate(headers)
                if "teks" in h.lower() or "text" in h.lower()
            ),
            -1,
        )
        self._setup_ui(headers, data)

    def _setup_ui(self, headers: list[str], data: list[list[Any]]) -> None:
        """Membangun antarmuka tabel dan menghubungkan sinyal."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.table_view = QTableView(self)
        self.table_view.setWordWrap(True)

        v_header = self.table_view.verticalHeader()
        v_header.setDefaultSectionSize(25)
        v_header.hide()

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
                self.table_view.setColumnWidth(i, 150)
            else:
                self.table_view.resizeColumnToContents(i)
                self.table_view.setColumnWidth(i, self.table_view.columnWidth(i) + 15)

        self.table_view.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table_view.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.table_view.setAlternatingRowColors(True)
        self.table_view.selectionModel().selectionChanged.connect(self._row_selected)
        layout.addWidget(self.table_view)

    def _on_column_resized(
        self, logical_index: int, old_size: int, new_size: int
    ) -> None:
        """Menangani penyesuaian tinggi baris saat lebar kolom diubah."""
        if logical_index == self.text_col_index:
            if hasattr(self, "delegate"):
                self.delegate._doc_cache.clear()
            QTimer.singleShot(10, self._resize_visible_rows_only)

    def _resize_visible_rows_only(self) -> None:
        """Optimasi resize hanya untuk baris yang tampak di layar."""
        rect = self.table_view.viewport().rect()
        top = self.table_view.rowAt(rect.top())
        bottom = self.table_view.rowAt(rect.bottom())

        if top == -1:
            top = 0
        if bottom == -1:
            bottom = self.model.rowCount() - 1

        self.table_view.setUpdatesEnabled(False)
        for row in range(top, bottom + 1):
            self.table_view.resizeRowToContents(row)
        self.table_view.setUpdatesEnabled(True)

    def _row_selected(self) -> None:
        """Mengirim data baris terpilih ke callback."""
        if self.on_row_select:
            indexes = self.table_view.selectionModel().selectedRows()
            if indexes:
                self.on_row_select(self.model._data[indexes[0].row()])

    def select_row_and_mark_group(
        self, target_sid: str | None, group_ids: Iterable[str]
    ) -> None:
        """Memilih baris tertentu secara programatik dan menandai grup ID terkait.

        Args:
            target_sid (Optional[str]): ID baris yang akan dipilih/fokus.
            group_ids (Iterable[str]): Daftar ID baris yang akan diberi warna latar belakang.

        """
        self.model.set_marked_ids(group_ids)
        if target_sid:
            try:
                row_idx = int(target_sid) - 1
                if 0 <= row_idx < self.model.rowCount():
                    curr = self.table_view.currentIndex()
                    if curr.isValid() and curr.row() == row_idx:
                        return

                    idx = self.model.index(
                        row_idx, curr.column() if curr.isValid() else 0
                    )
                    self.table_view.selectionModel().blockSignals(True)
                    self.table_view.setCurrentIndex(idx)
                    self.table_view.selectRow(row_idx)
                    self.table_view.scrollTo(idx)
                    self.table_view.selectionModel().blockSignals(False)
            except ValueError:
                pass
