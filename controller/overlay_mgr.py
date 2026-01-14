import csv
import os


class OverlayManager:
    def __init__(self):
        self.show_text_layer = False
        self.show_csv_layer = False
        self.csv_path = None
        self._csv_cache = {}  # Cache: {halaman: [data_list]}

    def load_csv_to_cache(self, path):
        """Membaca CSV satu kali dan menyimpannya dalam memori berdasarkan halaman."""
        if not path or not os.path.exists(path):
            return
        self.csv_path = path
        self._csv_cache = {}

        try:
            with open(path, encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f, delimiter=";", quotechar='"')
                for row in reader:
                    p_num = int(row["halaman"])
                    if p_num not in self._csv_cache:
                        self._csv_cache[p_num] = []

                    # Simpan data yang sudah dikonversi
                    self._csv_cache[p_num].append(
                        (
                            float(row["x0"].replace(",", ".")),
                            float(row["top"].replace(",", ".")),
                            float(row["x1"].replace(",", ".")),
                            float(row["bottom"].replace(",", ".")),
                            row["teks"],
                            row["nomor"],
                        )
                    )
        except Exception as e:
            print(f"Error caching CSV: {e}")

    def get_csv_data(self, page_num):
        """Mendapatkan data dari cache (Sangat Cepat)."""
        return self._csv_cache.get(page_num, [])
