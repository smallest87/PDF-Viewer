import sys

from PyQt6.QtWidgets import QApplication

from controller.main_controller import PDFController
from model.document_model import PDFDocumentModel
from view.main_view import PyQt6PDFView


def main():
    # 1. Inisialisasi Aplikasi Qt
    # sys.argv digunakan agar aplikasi mendukung argumen baris perintah OS
    app = QApplication(sys.argv)

    # 2. Inisialisasi Model (State Management)
    # Model tetap menggunakan struktur lama karena bersifat UI-Agnostic
    model = PDFDocumentModel()

    # 3. Inisialisasi View dengan Controller Factory
    # Lambda digunakan untuk injeksi ketergantungan (Dependency Injection)
    # View akan membuat Controller, dan Controller akan mereferensi View tersebut
    view = PyQt6PDFView(app, lambda v: PDFController(v, model))

    # 4. Tampilkan Antarmuka
    view.show()

    # 5. Jalankan Event Loop Utama
    # sys.exit memastikan aplikasi tertutup bersih saat window di-close
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
