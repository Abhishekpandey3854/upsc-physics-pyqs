import csv
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAPER_DIR = ROOT / "output" / "llm_clean_pyqs" / "papers"
OUT_DIR = ROOT / "output" / "llm_clean_pyqs"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def parse_paper(path: Path):
    text = path.read_text(encoding="utf-8", errors="ignore")
    stem = path.stem
    m = re.match(r"(\d{4})_Paper_(I{1,2})", stem)
    if not m:
        return []
    year, paper = m.groups()
    matches = list(re.finditer(r"(?m)^##\s+(Q[1-8])\b.*$", text))
    rows = []
    for i, mt in enumerate(matches):
        qid = mt.group(1)
        start = mt.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block = text[start:end].strip()
        topic = "Needs manual check"
        subtopic = "Needs manual check"
        topic_m = re.search(r"\*\*Topic:\*\*\s*(.+)", block)
        sub_m = re.search(r"\*\*Subtopic:\*\*\s*(.+)", block)
        if topic_m:
            topic = topic_m.group(1).strip()
        elif " - " in mt.group(0):
            topic = mt.group(0).split(" - ", 1)[1].strip()
        if sub_m:
            subtopic = sub_m.group(1).strip()
        rows.append({
            "topic": topic,
            "subtopic": subtopic,
            "year": year,
            "paper": paper,
            "qid": qid,
            "paper_file": str(path.resolve()),
            "block": block,
        })
    return rows


def quality_flags(block):
    flags = []
    if re.search(r"[Â�]|[a-zA-Z]{1,2}\s+[a-zA-Z]{1,2}\s+[a-zA-Z]{1,2}\s+[A-Z]{2,}", block):
        flags.append("possible_ocr_noise")
    if "verify from image" in block.lower():
        flags.append("has_verify_note")
    if len(re.findall(r"!\[", block)) == 0:
        flags.append("missing_image")
    if len(block) < 350:
        flags.append("short_block")
    return ";".join(flags)


def main():
    rows = []
    for path in sorted(PAPER_DIR.glob("20*_Paper_*.md")):
        rows.extend(parse_paper(path))
    rows.sort(key=lambda r: (r["topic"], r["subtopic"], r["year"], r["paper"], r["qid"]))

    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["topic"], row["subtopic"])].append(row)

    master = OUT_DIR / "UPSC_Physics_Optional_PYQs_LLM_Clean_Topicwise.md"
    lines = [
        "# UPSC Physics Optional PYQs - LLM-Cleaned Topic/Subtopic-wise Compilation",
        "",
        "Coverage: available PDFs in this workspace. 2014 is excluded because the archive links resolved to duplicate 2015 PDFs.",
        "Each entry points to a polished per-paper visual Markdown file with source image crops under the question.",
        "",
    ]
    for (topic, subtopic), items in grouped.items():
        lines.append(f"\n## {topic} - {subtopic}\n")
        for item in items:
            lines.append(f"- **{item['year']} Paper {item['paper']} {item['qid']}**: [open visual question block]({Path(item['paper_file']).as_posix()})")
    master.write_text("\n".join(lines), encoding="utf-8")

    full_master = OUT_DIR / "UPSC_Physics_Optional_PYQs_LLM_Clean_Topicwise_FULL_VISUAL.md"
    lines = [
        "# UPSC Physics Optional PYQs - LLM-Cleaned Topic/Subtopic-wise Full Visual Compilation",
        "",
        "Coverage: available PDFs in this workspace. 2014 is excluded because the archive links resolved to duplicate 2015 PDFs.",
        "Questions are grouped by topic/subtopic. Each entry keeps the cleaned Markdown question and the source-paper image crop(s) directly below it.",
        "",
    ]
    for (topic, subtopic), items in grouped.items():
        lines.append(f"\n## {topic} - {subtopic}\n")
        for item in items:
            block = item["block"]
            block = re.sub(r"^##\s+Q[1-8].*$", "", block, count=1, flags=re.M).strip()
            lines.append(f"### {item['year']} Paper {item['paper']} {item['qid']}")
            lines.append("")
            lines.append(block)
            lines.append("")
            lines.append("---")
            lines.append("")
    full_master.write_text("\n".join(lines), encoding="utf-8")

    csv_path = OUT_DIR / "UPSC_Physics_Optional_PYQs_LLM_Clean_Index.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["topic", "subtopic", "year", "paper", "qid", "paper_file", "quality_flags"])
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row[k] for k in ["topic", "subtopic", "year", "paper", "qid", "paper_file"]} | {"quality_flags": quality_flags(row["block"])})
    print(master)
    print(full_master)
    print(csv_path)
    print(f"papers={len(list(PAPER_DIR.glob('20*_Paper_*.md')))} entries={len(rows)}")


if __name__ == "__main__":
    main()
