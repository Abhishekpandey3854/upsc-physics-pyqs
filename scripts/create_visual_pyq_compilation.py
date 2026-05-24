import csv
import re
from collections import defaultdict
from pathlib import Path

from PIL import Image

from build_topicwise_from_tesseract import classify, extract_whole_questions


ROOT = Path(__file__).resolve().parents[1]
PAGE_DIR = ROOT / "text" / "pages"
TSV_DIR = ROOT / "text" / "tesseract_tsv"
OCR_DIR = ROOT / "text" / "tesseract_ocr"
OUT_DIR = ROOT / "output" / "visual_pyq_compilation"
PAPER_DIR = OUT_DIR / "papers"
IMG_DIR = OUT_DIR / "question_images"
PAPER_DIR.mkdir(parents=True, exist_ok=True)
IMG_DIR.mkdir(parents=True, exist_ok=True)


def page_key(path: Path):
    m = re.match(r"(\d{4})_Paper_(I{1,2})_p(\d{2})", path.stem)
    return (m.group(1), m.group(2), int(m.group(3))) if m else None


def parse_tsv_lines(tsv_path: Path):
    rows = []
    for line in tsv_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        cols = line.split("\t")
        if len(cols) < 12 or cols[0] == "level":
            continue
        level, page_num, block_num, par_num, line_num, word_num = cols[:6]
        if level != "5":
            continue
        text = cols[11].strip()
        if not text:
            continue
        try:
            left, top, width, height = map(int, cols[6:10])
        except ValueError:
            continue
        key = (block_num, par_num, line_num)
        rows.append((key, text, left, top, width, height))

    grouped = defaultdict(list)
    for row in rows:
        grouped[row[0]].append(row[1:])

    lines = []
    for parts in grouped.values():
        parts.sort(key=lambda x: x[1])
        text = " ".join(p[0] for p in parts)
        left = min(p[1] for p in parts)
        top = min(p[2] for p in parts)
        right = max(p[1] + p[3] for p in parts)
        bottom = max(p[2] + p[4] for p in parts)
        lines.append({"text": text, "left": left, "top": top, "right": right, "bottom": bottom})
    return sorted(lines, key=lambda x: (x["top"], x["left"]))


def normalize_q(raw):
    raw = raw.upper().replace("@", "Q").replace("©", "Q").replace("O", "Q")
    if raw in {"QL", "QI"}:
        return "Q1"
    m = re.search(r"[1-8]", raw)
    return f"Q{m.group(0)}" if m else None


MARKER_RE = re.compile(
    r"^\s*[\.\-©@]?\s*((?:[Q@©O](?:[1-8]|L|I))|[1-8])\s*[\.\)]?\s*(?=(?:[fF]?\(?[a-e@©0O]\)?)|Answer all|Answer any|\()", re.I
)


def find_markers(stem):
    markers = []
    for tsv in sorted(TSV_DIR.glob(f"{stem}_p*.tsv")):
        key = page_key(tsv)
        if not key:
            continue
        _, _, page_no = key
        for line in parse_tsv_lines(tsv):
            m = MARKER_RE.match(line["text"])
            if not m:
                continue
            qid = normalize_q(m.group(1))
            if not qid:
                continue
            markers.append({"qid": qid, "page": page_no, "top": line["top"], "text": line["text"]})
    markers.sort(key=lambda x: (x["page"], x["top"]))
    return markers


def sequential_markers(markers):
    # Pick question starts independently. Old papers often have Hindi/English
    # sections split across pages, so page order is not always Q1, Q2, Q3...
    # A Q-like marker with "(a)" is usually a true start; numeric markers with
    # "Answer all..." are valid for compulsory Q1/Q5 in older papers.
    best = {}
    def score(m):
        text = m["text"]
        s = 0
        if re.match(r"^\s*[Q@©O]", text, re.I):
            s += 8
        if re.search(r"\([a-e@©0O]\)|f\([a-e]\)|fa\)", text, re.I):
            s += 5
        if "Answer all" in text or "Answer any" in text:
            s += 4
        if re.search(r"[A-Za-z]{4,}", text):
            s += 1
        if "Answers must" in text or "Question-cum-Answer" in text:
            s -= 20
        if m["page"] <= 1:
            s -= 8
        return s

    for qn in range(1, 9):
        target = f"Q{qn}"
        candidates = [m for m in markers if m["qid"] == target]
        if candidates:
            best[target] = sorted(candidates, key=lambda m: (-score(m), m["page"], m["top"]))[0]
    return sorted(best.values(), key=lambda m: (m["page"], m["top"]))


def crop_question(stem, qid, start, end):
    paths = []
    for page_no in range(start["page"], end["page"] + 1):
        img_path = PAGE_DIR / f"{stem}_p{page_no:02d}.png"
        if not img_path.exists():
            continue
        img = Image.open(img_path)
        w, h = img.size
        top = 70 if page_no != start["page"] else max(0, start["top"] - 35)
        bottom = h - 35 if page_no != end["page"] else min(h, end["top"] - 12)
        if bottom - top < 120:
            bottom = min(h, top + 450)
        out = IMG_DIR / stem
        out.mkdir(parents=True, exist_ok=True)
        suffix = "" if start["page"] == end["page"] else f"_p{page_no:02d}"
        crop_path = out / f"{stem}_{qid}{suffix}.png"
        img.crop((0, top, w, bottom)).save(crop_path)
        paths.append(crop_path)
    return paths


def question_texts(stem):
    txt_path = OCR_DIR / f"{stem}.txt"
    if not txt_path.exists():
        return {}
    blocks = extract_whole_questions(txt_path.read_text(encoding="utf-8", errors="ignore"))
    return {qid: text for qid, text in blocks}


def fallback_page_images(stem):
    out = IMG_DIR / stem
    out.mkdir(parents=True, exist_ok=True)
    paths = []
    for img_path in sorted(PAGE_DIR.glob(f"{stem}_p*.png")):
        page_no = page_key(img_path)[2]
        if page_no <= 2:
            continue
        dest = out / f"{stem}_page_{page_no:02d}.png"
        if not dest.exists():
            Image.open(img_path).save(dest)
        paths.append(dest)
    return paths


def clean_markdown_text(text):
    text = re.sub(r"\s+", " ", text).strip()
    text = text.replace("SECTION—B", "").replace("SECTION-B", "")
    # Keep OCR as a draft, but remove the most repetitive footer debris.
    text = re.sub(r"\b[A-Z]{3,}-[A-Z]-PHY\b.*?(?=Q\d|$)", "", text)
    return text


def main():
    stems = []
    for pdf in sorted((ROOT / "pdfs").glob("20*_Paper_*.pdf")):
        stems.append(pdf.stem)

    master_rows = []
    manifest_rows = []
    for stem in stems:
        year, paper = re.match(r"(\d{4})_Paper_(I{1,2})", stem).groups()
        texts = question_texts(stem)
        markers = sequential_markers(find_markers(stem))
        qids = [f"Q{i}" for i in range(1, 9)]
        paper_lines = [
            f"# UPSC Physics Optional {year} Paper {paper}",
            "",
            "Each question has OCR-assisted Markdown plus visual source crop(s). Treat formula-heavy OCR text as a draft and verify from the image immediately below it.",
            "",
        ]

        detected = {m["qid"]: m for m in markers}
        for qid in qids:
            text = clean_markdown_text(texts.get(qid, "OCR text was not cleanly isolated for this question. Use the source image crop/full-page fallback below."))
            topic, subtopic, score = classify(text)

            start = detected.get(qid)
            next_marker = None
            if start:
                later = [m for m in markers if (m["page"], m["top"]) > (start["page"], start["top"])]
                next_marker = later[0] if later else None
            if start and next_marker:
                images = crop_question(stem, qid, start, next_marker)
            elif start:
                # Last detected question: crop from start to end of the paper.
                last_page = max(page_key(p)[2] for p in PAGE_DIR.glob(f"{stem}_p*.png"))
                images = crop_question(stem, qid, start, {"page": last_page, "top": 10_000})
            else:
                images = fallback_page_images(stem)

            anchor = f"{year}-paper-{paper.lower()}-{qid.lower()}"
            paper_lines.extend([
                f"## {qid} - {topic}",
                "",
                f"**Subtopic:** {subtopic}",
                "",
                text,
                "",
                "**Source image(s):**",
                "",
            ])
            for img in images:
                paper_lines.append(f"![{stem} {qid}]({img.resolve().as_posix()})")
                paper_lines.append("")

            master_rows.append({
                "topic": topic,
                "subtopic": subtopic,
                "year": year,
                "paper": paper,
                "qid": qid,
                "text": text,
                "paper_file": str((PAPER_DIR / f"{stem}.md").resolve()),
                "image_count": len(images),
                "classification_score": score,
            })
            manifest_rows.append([year, paper, qid, len(images), "detected" if start else "fallback_full_pages"])

        (PAPER_DIR / f"{stem}.md").write_text("\n".join(paper_lines), encoding="utf-8")

    master_rows.sort(key=lambda r: (r["topic"], r["subtopic"], r["year"], r["paper"], r["qid"]))
    master_md = OUT_DIR / "UPSC_Physics_Optional_PYQs_Topicwise_Visual_2010_2025_available.md"
    lines = [
        "# UPSC Physics Optional PYQs - Topic/Subtopic-wise Visual Compilation",
        "",
        "Coverage: available PDFs in this workspace. 2014 is excluded because the archive links resolved to duplicate 2015 PDFs.",
        "Each entry links to a per-paper Markdown file and includes OCR-assisted text. The per-paper files contain the visual source crops.",
        "",
    ]
    current = None
    for r in master_rows:
        key = (r["topic"], r["subtopic"])
        if key != current:
            lines.append(f"\n## {r['topic']} - {r['subtopic']}\n")
            current = key
        rel = Path(r["paper_file"]).resolve().as_posix()
        lines.append(f"- **{r['year']} Paper {r['paper']} {r['qid']}** ([visual source]({rel})): {r['text'][:700]}{'...' if len(r['text']) > 700 else ''}")
    master_md.write_text("\n".join(lines), encoding="utf-8")

    master_csv = OUT_DIR / "UPSC_Physics_Optional_PYQs_Topicwise_Visual_2010_2025_available.csv"
    with master_csv.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(master_rows[0].keys()))
        writer.writeheader()
        writer.writerows(master_rows)

    manifest = OUT_DIR / "crop_manifest.csv"
    with manifest.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["year", "paper", "qid", "image_count", "crop_mode"])
        writer.writerows(manifest_rows)

    print(master_md)
    print(master_csv)
    print(manifest)
    print(f"papers={len(stems)} entries={len(master_rows)}")


if __name__ == "__main__":
    main()
