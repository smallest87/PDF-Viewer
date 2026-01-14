import csv


class ExportManager:
    def parse_ranges(self, range_str, total_pages):
        """Logika parsing rentang halaman (misal: 1, 3, 5-10)"""
        pages = set()
        try:
            for part in range_str.split(","):
                part = part.strip()
                if "-" in part:
                    start, end = map(int, part.split("-"))
                    pages.update(range(start - 1, end))
                else:
                    pages.add(int(part) - 1)
        except Exception:
            return None
        return sorted([p for p in pages if 0 <= p < total_pages])

    def to_csv(self, doc, filepath, indices, view):
        """Proses ekstraksi teks ke file CSV yang aman bagi karakter khusus."""
        header = [
            "nomor",
            "halaman",
            "teks",
            "x0",
            "x1",
            "top",
            "bottom",
            "font_style",
            "font_size",
            "sumbu",
        ]

        try:
            # Gunakan newline='' dan quoting=csv.QUOTE_MINIMAL agar ';' di dalam teks aman dibungkus tanda kutip
            with open(filepath, mode="w", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(
                    f, delimiter=";", quotechar='"', quoting=csv.QUOTE_MINIMAL
                )
                writer.writerow(header)

                idx = 1
                for i, p_idx in enumerate(indices):
                    blocks = doc[p_idx].get_text("dict")["blocks"]
                    for b in [b for b in blocks if b["type"] == 0]:
                        for line in b["lines"]:
                            for span in line["spans"]:
                                x0, y0, x1, y1 = span["bbox"]

                                # Logika format angka desimal dengan koma tetap bisa dipertahankan
                                row = [
                                    idx,
                                    p_idx + 1,
                                    span["text"]
                                    .replace("\n", " ")
                                    .strip(),  # Jangan hapus ';' disini!
                                    str(round(x0, 2)).replace(".", ","),
                                    str(round(x1, 2)).replace(".", ","),
                                    str(round(y0, 2)).replace(".", ","),
                                    str(round(y1, 2)).replace(".", ","),
                                    span["font"],
                                    span["size"],
                                    str(round((y0 + y1) / 2, 2)).replace(
                                        ".", ","
                                    ),  # Formula: $$ \frac{y_{0} + y_{1}}{2} $$
                                ]
                                writer.writerow(row)
                                idx += 1
                    view.update_progress(((i + 1) / len(indices)) * 100)
                view.update_progress(0)
        except Exception as e:
            print(f"Export gagal: {e}")
