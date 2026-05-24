import csv
import re
from pathlib import Path

import easyocr
import fitz


ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = ROOT / "pdfs"
OCR_DIR = ROOT / "text" / "ocr"
OUT_DIR = ROOT / "output"
OUT_DIR.mkdir(exist_ok=True)
OCR_DIR.mkdir(parents=True, exist_ok=True)


TOPICS = [
    ("Classical Mechanics", "Central force, gravitation and orbits", [
        "central force", "kepler", "orbit", "areal", "gravitational", "self-energy", "sphere of mass",
        "effective potential"
    ]),
    ("Classical Mechanics", "Rigid body dynamics", [
        "rigid body", "moment of inertia", "principal moment", "euler", "angular velocity", "rolling",
        "without slipping", "cylinder rolls"
    ]),
    ("Classical Mechanics", "Oscillations", [
        "harmonic oscillator", "oscillation", "damped", "amplitude", "resonance", "simple harmonic"
    ]),
    ("Classical Mechanics", "Fluid mechanics and elasticity", [
        "bernoulli", "viscosity", "streamline", "elastic", "hooke", "young", "poiseuille"
    ]),
    ("Special Relativity", "Relativistic kinematics and dynamics", [
        "rest mass", "velocity of magnitude", "lorentz transformation", "relativistic", "proper time",
        "invariant under lorentz"
    ]),
    ("Waves and Optics", "Interference and diffraction", [
        "double slit", "fraunhofer", "diffraction", "interference", "missing orders", "maxima",
        "minima", "slit", "fringe"
    ]),
    ("Waves and Optics", "Geometrical optics", [
        "lens", "mirror", "paraxial", "matrix method", "focal", "refraction", "reflection"
    ]),
    ("Waves and Optics", "Polarization", [
        "polarization", "polarisation", "birefringence", "quarter wave", "half wave", "malus"
    ]),
    ("Waves and Optics", "Laser physics", [
        "laser", "population inversion", "resonator", "einstein coefficient", "threshold"
    ]),
    ("Electrodynamics", "Electrostatics and boundary-value problems", [
        "laplace", "poisson", "electrostatic", "potential", "electric field", "conducting", "dielectric",
        "method of images", "boundary condition", "capacitance"
    ]),
    ("Electrodynamics", "Magnetostatics", [
        "biot", "savart", "ampere", "magnetic field", "magnetostatic", "current loop", "solenoid"
    ]),
    ("Electrodynamics", "Electromagnetic induction and circuits", [
        "induction", "faraday", "lcr", "kirchhoff", "network", "impedance", "current electricity"
    ]),
    ("Electrodynamics", "Electromagnetic waves", [
        "electromagnetic wave", "maxwell", "poynting", "wave equation", "radiation pressure",
        "light beam", "photons per second", "plane mirror"
    ]),
    ("Thermal and Statistical Physics", "Thermodynamics", [
        "thermodynamic", "entropy", "enthalpy", "carnot", "heat engine", "free energy", "clausius"
    ]),
    ("Thermal and Statistical Physics", "Kinetic theory and statistical mechanics", [
        "maxwell boltzmann", "partition function", "fermi", "bose", "black body", "specific heat",
        "equipartition", "statistical"
    ]),
    ("Quantum Mechanics", "Foundations and operators", [
        "schrodinger", "wave function", "operator", "commutator", "uncertainty", "eigenvalue",
        "normalization", "expectation value"
    ]),
    ("Quantum Mechanics", "Potential problems and angular momentum", [
        "potential well", "barrier", "tunnelling", "tunneling", "harmonic oscillator", "angular momentum",
        "spherical harmonics", "hydrogen atom"
    ]),
    ("Atomic and Molecular Physics", "Atomic spectra and structure", [
        "atomic", "spectrum", "spectra", "zeeman", "stark", "fine structure", "hyperfine",
        "selection rule", "hydrogen"
    ]),
    ("Atomic and Molecular Physics", "Molecular spectra", [
        "molecular", "rotational", "vibrational", "raman", "infrared", "born-oppenheimer"
    ]),
    ("Nuclear and Particle Physics", "Nuclear structure and radioactivity", [
        "nuclear", "radioactivity", "decay", "alpha", "beta", "gamma", "binding energy", "shell model",
        "liquid drop"
    ]),
    ("Nuclear and Particle Physics", "Reactions and particle physics", [
        "reaction", "scattering", "cross-section", "cross section", "fission", "fusion", "quark",
        "lepton", "meson", "baryon", "particle"
    ]),
    ("Solid State Physics", "Crystal structure and lattice dynamics", [
        "crystal", "lattice", "bragg", "x-ray", "phonon", "debye", "miller indices"
    ]),
    ("Solid State Physics", "Band theory and semiconductors", [
        "band", "semiconductor", "fermi level", "p-n junction", "diode", "transistor", "hall effect",
        "superconduct"
    ]),
    ("Electronics", "Analog and digital electronics", [
        "amplifier", "op-amp", "feedback", "logic gate", "flip-flop", "rectifier", "oscillator circuit",
        "boolean"
    ]),
]


def ocr_pdf(pdf_path: Path, reader: easyocr.Reader) -> str:
    out_path = OCR_DIR / f"{pdf_path.stem}.txt"
    if out_path.exists() and out_path.stat().st_size > 1000:
        return out_path.read_text(encoding="utf-8", errors="ignore")

    doc = fitz.open(pdf_path)
    pages = []
    for page_index in range(len(doc)):
        page = doc[page_index]
        # First two pages normally contain instructions/constants in Hindi and English.
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
        img_path = OCR_DIR / f"{pdf_path.stem}_p{page_index + 1}.png"
        pix.save(img_path)
        lines = reader.readtext(str(img_path), detail=0, paragraph=True)
        pages.append(f"\n--- PAGE {page_index + 1} ---\n" + "\n".join(lines))
        img_path.unlink(missing_ok=True)
        print(f"OCR {pdf_path.name} page {page_index + 1}/{len(doc)}", flush=True)

    text = "\n".join(pages)
    out_path.write_text(text, encoding="utf-8")
    return text


def clean_question(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    text = text.replace("  ", " ")
    # Keep the English side of bilingual lines where OCR captured a Hindi/English slash.
    phrases = [
        "Consider ", "Derive ", "A particle ", "In double", "A light", "A body ", "The ",
        "Show ", "Explain ", "Calculate ", "Determine ", "Find ", "Obtain ", "Discuss ",
        "What ", "Write ", "Using ", "Starting ", "Prove ", "Evaluate "
    ]
    starts = [text.find(p) for p in phrases if text.find(p) >= 0]
    if starts:
        text = text[min(starts):]
    text = re.sub(r"\bSLPM[-A-Z]*\b.*$", "", text).strip()
    return text


def split_questions(text: str, year: str, paper: str):
    body = text
    # Drop pages before SECTION A when possible.
    pos = body.find("SECTION A")
    if pos >= 0:
        body = body[pos:]
    pattern = re.compile(r"(Q\s*[1-8]\s*\.\s*\([a-z]\)|Q\s*[1-8]\s*\.|(?:^|\s)\([a-z]\))", re.I)
    matches = list(pattern.finditer(body))
    rows = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        chunk = body[start:end]
        qid = re.sub(r"\s+", "", m.group(1).upper())
        qtext = clean_question(chunk.replace(m.group(1), ""))
        if len(qtext) < 45:
            continue
        marks = ""
        mark_match = re.search(r"\b(10|15|20|25|30)\b\s*$", qtext)
        if mark_match:
            marks = mark_match.group(1)
            qtext = qtext[:mark_match.start()].strip()
        topic, subtopic, score = classify(qtext)
        rows.append({
            "year": year,
            "paper": paper,
            "question_no": qid,
            "marks": marks,
            "topic": topic,
            "subtopic": subtopic,
            "question": qtext,
            "classification_score": score,
        })
    return rows


def classify(question: str):
    q = question.lower()
    best = ("Needs manual check", "OCR/classification uncertain", 0)
    for topic, subtopic, keys in TOPICS:
        score = sum(1 for key in keys if key in q)
        if score > best[2]:
            best = (topic, subtopic, score)
    if best[2] == 0:
        if "paper_ii" in q:
            return "Paper II mixed", "Needs manual check", 0
        return best
    return best


def write_outputs(rows):
    rows = sorted(rows, key=lambda r: (r["topic"], r["subtopic"], r["year"], r["paper"], r["question_no"]))
    csv_path = OUT_DIR / "upsc_physics_optional_pyqs_topicwise_2016_2025.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "topic", "subtopic", "year", "paper", "question_no", "marks", "question", "classification_score"
        ])
        writer.writeheader()
        writer.writerows(rows)

    md_path = OUT_DIR / "upsc_physics_optional_pyqs_topicwise_2016_2025.md"
    lines = [
        "# UPSC Physics Optional PYQs: Topic/Subtopic-wise Index (2016-2025)",
        "",
        "Source PDFs: official UPSC links gathered from PWOnlyIAS current link table; PDFs saved under `pdfs/`.",
        "Note: the source PDFs are scanned bilingual papers. Questions were OCR-extracted and auto-classified; entries marked `Needs manual check` should be verified against the PDF.",
        "",
    ]
    current = None
    for r in rows:
        key = (r["topic"], r["subtopic"])
        if key != current:
            lines.append(f"\n## {r['topic']} - {r['subtopic']}\n")
            current = key
        ref = f"{r['year']} Paper {r['paper']} {r['question_no']}"
        mark = f" [{r['marks']} marks]" if r["marks"] else ""
        lines.append(f"- **{ref}{mark}:** {r['question']}")
    md_path.write_text("\n".join(lines), encoding="utf-8")

    summary_path = OUT_DIR / "topic_counts_2016_2025.csv"
    counts = {}
    for r in rows:
        counts[(r["topic"], r["subtopic"])] = counts.get((r["topic"], r["subtopic"]), 0) + 1
    with summary_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["topic", "subtopic", "count"])
        for (topic, subtopic), count in sorted(counts.items(), key=lambda x: (-x[1], x[0])):
            writer.writerow([topic, subtopic, count])
    print(f"Wrote {len(rows)} question entries")
    print(csv_path)
    print(md_path)
    print(summary_path)


def main():
    reader = easyocr.Reader(["en"], gpu=False, verbose=False)
    rows = []
    for pdf in sorted(PDF_DIR.glob("20*_Paper_*.pdf")):
        m = re.match(r"(\d{4})_Paper_(I{1,2})\.pdf", pdf.name)
        if not m:
            continue
        year, paper = m.groups()
        text = ocr_pdf(pdf, reader)
        rows.extend(split_questions(text, year, paper))
    write_outputs(rows)


if __name__ == "__main__":
    main()
