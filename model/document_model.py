"""Module untuk mendefinisikan struktur data dokumen PDF.

Menggunakan `typing.Any` untuk memberikan fleksibilitas pada atribut yang
bergantung pada library eksternal (seperti PyMuPDF atau Pandas) tanpa
memerlukan dependensi yang kaku pada level model.
"""

from typing import Any


class PDFDocumentModel:
    """Pusat penyimpanan data dan status aplikasi (State Management).

    Kelas ini berfungsi sebagai Single Source of Truth untuk status dokumen PDF,
    navigasi antarmuka, dan data audit yang terkait.

    Attributes:
        doc (Optional[Any]): Objek dokumen PDF (misalnya dari library PyMuPDF/fitz).
        file_name (str): Nama file dokumen yang sedang dibuka.
        file_path (str): Path lengkap menuju file dokumen.
        current_page (int): Indeks halaman yang sedang ditampilkan (0-indexed).
        total_pages (int): Jumlah total halaman dalam dokumen.
        zoom_level (float): Faktor perbesaran tampilan (1.0 = 100%).
        padding (int): Jarak luar antar elemen tampilan dalam piksel.
        csv_path (Optional[str]): Path file CSV hasil audit/overlay.
        is_sandwich (bool): Status apakah dokumen memiliki layer teks (sandwich PDF).
        has_csv (bool): Status apakah data CSV telah dimuat ke dalam model.
        selected_row_id (Optional[Any]): ID baris yang sedang dipilih pada tabel atau overlay.

    """

    def __init__(self) -> None:
        """Inisialisasi state default untuk model dokumen."""
        # Data Dokumen Dasar
        self.doc: Any | None = None
        self.file_name: str = ""
        self.file_path: str = ""

        # Status Navigasi & Tampilan
        self.current_page: int = 0
        self.total_pages: int = 0
        self.zoom_level: float = 1.0
        self.padding: int = 30

        # Status Overlay & Audit
        self.csv_path: str | None = None
        self.is_sandwich: bool = False
        self.has_csv: bool = False

        # State Seleksi (Untuk interaksi dua arah)
        self.selected_row_id: Any | None = None

    def reset(self) -> None:
        """Mengembalikan state model ke kondisi awal.

        Digunakan saat menutup dokumen atau membersihkan memori sebelum
        memuat dokumen baru.
        """
        self.doc = None
        self.current_page = 0
        self.zoom_level = 1.0
        self.selected_row_id = None
