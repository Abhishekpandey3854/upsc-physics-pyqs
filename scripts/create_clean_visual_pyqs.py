import csv
import re
from collections import defaultdict
from pathlib import Path

from build_topicwise_from_tesseract import classify, extract_whole_questions


ROOT = Path(__file__).resolve().parents[1]
SOURCE_VISUAL = ROOT / "output" / "visual_pyq_compilation"
PAPER_SRC = SOURCE_VISUAL / "papers"
IMG_SRC = SOURCE_VISUAL / "question_images"
OCR_DIR = ROOT / "text" / "tesseract_ocr"
OUT_DIR = ROOT / "output" / "clean_visual_pyqs"
PAPER_OUT = OUT_DIR / "papers"
PAPER_OUT.mkdir(parents=True, exist_ok=True)


COMMON = {
    "the", "and", "for", "with", "from", "that", "this", "what", "when", "where", "which", "show",
    "derive", "determine", "calculate", "find", "obtain", "explain", "discuss", "consider", "state",
    "write", "using", "prove", "between", "given", "energy", "field", "potential", "magnetic", "electric",
    "wave", "mass", "velocity", "radius", "current", "voltage", "temperature", "pressure", "frequency",
    "wavelength", "spectrum", "molecule", "nucleus", "electron", "particle", "function", "equation",
    "constant", "system", "body", "point", "surface", "sphere", "cylinder", "oscillator", "laser",
    "capacitor", "resistor", "coil", "circuit", "mirror", "lens", "slit", "diffraction", "interference",
    "entropy", "partition", "semiconductor", "crystal", "atomic", "molecular", "nuclear",
}

STARTERS = re.compile(
    r"\b(Consider|Derive|Show|Determine|Calculate|Find|Obtain|Explain|Discuss|State|Write|What|Why|How|"
    r"Using|Prove|Evaluate|A|An|The|In|For|Let|Given|Distinguish|Differentiate)\b"
)


def line_score(line):
    words = re.findall(r"[A-Za-z]{3,}", line.lower())
    if not words:
        return 0
    common = sum(1 for w in words if w in COMMON)
    has_starter = 2 if STARTERS.search(line) else 0
    vowel_ratio = sum(1 for w in words if re.search(r"[aeiou]", w)) / max(1, len(words))
    penalty = 1 if vowel_ratio < 0.55 and len(words) > 4 else 0
    return common + has_starter - penalty


def strip_noise(text):
    text = text.replace("Â", "").replace("â€”", "-").replace("â€™", "'").replace("â€˜", "'")
    text = text.replace("â€œ", '"').replace("â€", '"').replace("â„¢", "⁻")
    text = re.sub(r"\b[A-Z]{3,}-[A-Z]-PHY\b.*", "", text)
    text = re.sub(r"--- PAGE \d+ ---", "", text)
    return text


def clean_block(raw):
    raw = strip_noise(raw)
    lines = [re.sub(r"\s+", " ", ln).strip() for ln in raw.splitlines()]
    kept = []
    active = False
    for line in lines:
        if not line:
            continue
        if re.match(r"^(SECTION|wus|@Us|Civil Services|Question Paper|Please read|Time Allowed|Maximum Marks)", line, re.I):
            continue
        score = line_score(line)
        formula_like = bool(re.search(r"[=∫∑√πΩωλγμθαβ]|d\^?2|dx|dt|10\^|x10|[A-Z]\s?=", line))
        if score >= 3:
            kept.append(line)
            active = True
        elif active and (score >= 1 or formula_like or re.match(r"^\(?[ivx]+\)", line, re.I)):
            kept.append(line)

    joined = "\n".join(kept)
    joined = re.sub(r"\s+([,.;:?])", r"\1", joined)
    joined = re.sub(r"\bMand\b", "M and", joined)
    joined = re.sub(r"\b0-([0-9])", r"0.\1", joined)
    joined = re.sub(r"\b(\d+)-(\d+)\s*(mm|m|nm|kg|K|A|T|V|Hz|MeV|eV|cm)\b", r"\1.\2 \3", joined)
    joined = re.sub(r"\b10([+-]?\d{1,2})\b", r"10^\1", joined)
    return joined.strip()


def split_subparts(cleaned):
    # Preserve readable paragraphs, but make visible subparts easier to scan.
    cleaned = re.sub(r"\b\(([a-e])\)\s+", r"\n\n**(\1)** ", cleaned)
    cleaned = re.sub(r"\b(i{1,3}|iv|v)\)\s+", r"\n\1) ", cleaned, flags=re.I)
    return cleaned.strip()


def image_links(stem, qid):
    folder = IMG_SRC / stem
    if not folder.exists():
        return []
    return sorted(folder.glob(f"{stem}_{qid}*.png"))


def fallback_visual_links_from_old_paper(stem, qid):
    # The previous generator already wrote image links into per-paper files; use
    # those as the authoritative visual assets.
    return image_links(stem, qid)


def build():
    entries = []
    for ocr_path in sorted(OCR_DIR.glob("20*_Paper_*.txt")):
        stem = ocr_path.stem
        m = re.match(r"(\d{4})_Paper_(I{1,2})", stem)
        if not m:
            continue
        year, paper = m.groups()
        raw = ocr_path.read_text(encoding="utf-8", errors="ignore")
        blocks = dict(extract_whole_questions(raw))

        lines = [
            f"# UPSC Physics Optional {year} Paper {paper}",
            "",
            "Cleaned English Markdown with source-paper images. Formula-heavy text should be verified against the image immediately below the question.",
            "",
        ]
        for n in range(1, 9):
            qid = f"Q{n}"
            cleaned = split_subparts(clean_block(blocks.get(qid, "")))
            if not cleaned:
                cleaned = "_Clean text could not be confidently isolated. Use the source image(s) below._"
            topic, subtopic, score = classify(cleaned)
            imgs = fallback_visual_links_from_old_paper(stem, qid)
            lines.extend([
                f"## {qid} - {topic}",
                "",
                f"**Subtopic:** {subtopic}",
                "",
                cleaned,
                "",
                "**Source image(s):**",
                "",
            ])
            for img in imgs:
                lines.append(f"![{stem} {qid}]({img.resolve().as_posix()})")
                lines.append("")
            entries.append({
                "topic": topic,
                "subtopic": subtopic,
                "year": year,
                "paper": paper,
                "qid": qid,
                "question": cleaned,
                "paper_file": str((PAPER_OUT / f"{stem}.md").resolve()),
                "image_count": len(imgs),
                "classification_score": score,
            })
        (PAPER_OUT / f"{stem}.md").write_text("\n".join(lines), encoding="utf-8")

    entries.sort(key=lambda r: (r["topic"], r["subtopic"], r["year"], r["paper"], r["qid"]))
    grouped = defaultdict(list)
    for e in entries:
        grouped[(e["topic"], e["subtopic"])].append(e)

    master = OUT_DIR / "UPSC_Physics_Optional_PYQs_Clean_Topicwise_Visual.md"
    lines = [
        "# UPSC Physics Optional PYQs - Clean Topic/Subtopic-wise Visual File",
        "",
        "Coverage: available papers in this workspace. 2014 is excluded because the archive links resolved to duplicate 2015 PDFs.",
        "Each item contains cleaned English text and links to a per-paper visual Markdown file with source images.",
        "",
    ]
    for (topic, subtopic), rows in grouped.items():
        lines.append(f"\n## {topic} - {subtopic}\n")
        for r in rows:
            text = r["question"]
            if len(text) > 950:
                text = text[:950].rsplit(" ", 1)[0] + "..."
            lines.append(f"### {r['year']} Paper {r['paper']} {r['qid']}")
            lines.append("")
            lines.append(f"[Open visual question block]({Path(r['paper_file']).as_posix()})")
            lines.append("")
            lines.append(text)
            lines.append("")

    master.write_text("\n".join(lines), encoding="utf-8")
    csv_path = OUT_DIR / "UPSC_Physics_Optional_PYQs_Clean_Topicwise_Visual.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(entries[0].keys()))
        writer.writeheader()
        writer.writerows(entries)
    print(master)
    print(csv_path)
    print(f"entries={len(entries)} papers={len(list(PAPER_OUT.glob('*.md')))}")


if __name__ == "__main__":
    build()
