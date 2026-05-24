from pathlib import Path

import fitz


ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = ROOT / "pdfs"
PAGE_DIR = ROOT / "text" / "pages"
PAGE_DIR.mkdir(parents=True, exist_ok=True)


def main():
    for pdf_path in sorted(PDF_DIR.glob("20*_Paper_*.pdf")):
        doc = fitz.open(pdf_path)
        for page_index in range(len(doc)):
            out = PAGE_DIR / f"{pdf_path.stem}_p{page_index + 1:02d}.png"
            if out.exists() and out.stat().st_size > 10_000:
                continue
            page = doc[page_index]
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            pix.save(out)
            print(out.name, flush=True)


if __name__ == "__main__":
    main()
