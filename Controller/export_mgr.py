import os

class ExportManager:
    def parse_ranges(self, range_str, total_pages):
        """Logika parsing rentang halaman (misal: 1, 3, 5-10)"""
        pages = set()
        try:
            for part in range_str.split(','):
                part = part.strip()
                if '-' in part:
                    start, end = map(int, part.split('-'))
                    pages.update(range(start - 1, end))
                else: pages.add(int(part) - 1)
        except: return None
        return sorted([p for p in pages if 0 <= p < total_pages])

    def to_csv(self, doc, filepath, indices, view):
        """Proses ekstraksi teks ke file CSV"""
        def fmt(val):
            if isinstance(val, (float, int)): return str(round(val, 2)).replace('.', ',')
            return str(val).replace(';', ' ').replace('\n', ' ').strip()

        header = ["nomor", "halaman", "teks", "x0", "x1", "top", "bottom", "font_style", "font_size", "sumbu"]
        with open(filepath, mode='w', encoding='utf-8-sig') as f:
            f.write(";".join(header) + "\n")
            idx = 1
            for i, p_idx in enumerate(indices):
                blocks = doc[p_idx].get_text("dict")["blocks"]
                for b in [b for b in blocks if b["type"] == 0]:
                    for line in b["lines"]:
                        for span in line["spans"]:
                            x0, y0, x1, y1 = span["bbox"]
                            # Perhitungan sumbu tengah: $ (y0 + y1) / 2 $
                            row = [idx, p_idx + 1, span["text"], x0, x1, y0, y1, span["font"], span["size"], (y0 + y1) / 2]
                            f.write(";".join(map(fmt, row)) + "\n")
                            idx += 1
                view.update_progress(((i + 1) / len(indices)) * 100)
            view.update_progress(0)