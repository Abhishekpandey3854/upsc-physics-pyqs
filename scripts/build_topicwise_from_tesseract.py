import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OCR_DIR = ROOT / "text" / "tesseract_ocr"
OUT_DIR = ROOT / "output"
OUT_DIR.mkdir(exist_ok=True)


TOPICS = [
    ("Classical Mechanics", "Central force, gravitation and orbits", ["central force", "kepler", "orbit", "gravitational", "self-energy", "uniform solid sphere", "potential energy"]),
    ("Classical Mechanics", "Rigid body dynamics", ["rigid", "moment of inertia", "principal moment", "euler", "angular velocity", "rolling", "without slipping", "cylinder"]),
    ("Classical Mechanics", "Oscillations", ["harmonic oscillator", "oscillation", "damped", "amplitude", "resonance", "simple harmonic"]),
    ("Classical Mechanics", "Fluid mechanics and elasticity", ["bernoulli", "viscosity", "streamline", "elastic", "hooke", "young's modulus", "poiseuille"]),
    ("Special Relativity", "Relativistic kinematics and dynamics", ["rest mass", "lorentz", "relativistic", "proper time", "velocity of magnitude", "coalesce"]),
    ("Waves and Optics", "Interference and diffraction", ["double slit", "fraunhofer", "diffraction", "interference", "missing orders", "fringe", "maxima", "minima", "slit width"]),
    ("Waves and Optics", "Geometrical optics", ["lens", "mirror", "paraxial", "focal", "refraction", "reflection", "prism"]),
    ("Waves and Optics", "Polarization", ["polarization", "polarisation", "birefringence", "quarter wave", "half wave", "malus"]),
    ("Waves and Optics", "Laser physics", ["laser", "population inversion", "resonator", "einstein coefficient", "threshold"]),
    ("Electrodynamics", "Electrostatics and boundary-value problems", ["laplace", "poisson", "electrostatic", "electric potential", "electric field", "dielectric", "method of images", "capacitance"]),
    ("Electrodynamics", "Magnetostatics", ["biot", "savart", "ampere", "magnetic field", "magnetostatic", "solenoid"]),
    ("Electrodynamics", "Electromagnetic induction and circuits", ["induction", "faraday", "lcr", "kirchhoff", "impedance", "current electricity"]),
    ("Electrodynamics", "Electromagnetic waves", ["electromagnetic wave", "maxwell", "poynting", "wave equation", "radiation pressure", "plane mirror", "photons per second"]),
    ("Thermal and Statistical Physics", "Thermodynamics", ["thermodynamic", "entropy", "enthalpy", "carnot", "heat engine", "free energy", "clausius"]),
    ("Thermal and Statistical Physics", "Kinetic theory and statistical mechanics", ["maxwell-boltzmann", "maxwell boltzmann", "partition function", "fermi", "bose", "black body", "specific heat", "equipartition", "statistical"]),
    ("Quantum Mechanics", "Foundations and operators", ["schrodinger", "schrodinger", "wave function", "operator", "commutator", "uncertainty", "eigenvalue", "expectation value"]),
    ("Quantum Mechanics", "Potential problems and angular momentum", ["potential well", "potential barrier", "tunnelling", "tunneling", "angular momentum", "spherical harmonics", "hydrogen atom"]),
    ("Atomic and Molecular Physics", "Atomic spectra and structure", ["atomic", "spectrum", "spectra", "zeeman", "stark", "fine structure", "hyperfine", "selection rule"]),
    ("Atomic and Molecular Physics", "Molecular spectra", ["molecular", "rotational", "vibrational", "raman", "infrared", "born-oppenheimer"]),
    ("Nuclear and Particle Physics", "Nuclear structure and radioactivity", ["nuclear", "radioactivity", "decay", "alpha", "beta", "gamma", "binding energy", "shell model", "liquid drop"]),
    ("Nuclear and Particle Physics", "Reactions and particle physics", ["reaction", "scattering", "cross-section", "cross section", "fission", "fusion", "quark", "lepton", "meson", "baryon", "particle physics"]),
    ("Solid State Physics", "Crystal structure and lattice dynamics", ["crystal", "lattice", "bragg", "x-ray", "phonon", "debye", "miller indices"]),
    ("Solid State Physics", "Band theory and semiconductors", ["band", "semiconductor", "fermi level", "p-n junction", "diode", "transistor", "hall effect", "superconduct"]),
    ("Electronics", "Analog and digital electronics", ["amplifier", "op-amp", "feedback", "logic gate", "flip-flop", "rectifier", "boolean"]),
]


def classify(question):
    q = question.lower()
    best = ("Needs manual check", "OCR/classification uncertain", 0)
    for topic, subtopic, keys in TOPICS:
        score = sum(1 for key in keys if key in q)
        if score > best[2]:
            best = (topic, subtopic, score)
    return best


def normalize(text):
    text = text.replace("\r", "\n")
    text = re.sub(r"[|]", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text


def clean_question(text):
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\bSLPM[-A-Z]*\b.*$", "", text).strip()
    text = re.sub(r"\b\d+\s*$", "", text).strip()
    return text


def extract_question_blocks(text):
    text = normalize(text)
    pos = text.find("SECTION A")
    if pos != -1:
        text = text[pos:]
    # Captures Q1. (a), Q2. (a), and later subparts (b), (c), etc.
    marker = re.compile(r"(?:(Q\s*[1-8]\s*\.\s*)?(\([a-e]\)))", re.I)
    matches = list(marker.finditer(text))
    blocks = []
    current_q = None
    for i, m in enumerate(matches):
        if m.group(1):
            current_q = re.search(r"[1-8]", m.group(1)).group(0)
        if not current_q:
            continue
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        qid = f"Q{current_q}{m.group(2).lower()}"
        chunk = clean_question(text[start:end])
        if len(chunk) > 50:
            blocks.append((qid, chunk))
    return blocks


def normalize_q_marker(raw):
    raw = raw.upper()
    raw = raw.replace("@", "Q").replace("©", "Q").replace("O", "Q")
    if raw in {"QL", "QI"}:
        return "Q1"
    m = re.search(r"[1-8]", raw)
    return f"Q{m.group(0)}" if m else raw


def extract_whole_questions(text):
    text = normalize(text)
    pos = text.find("SECTION A")
    if pos != -1:
        text = text[pos:]
    # Tesseract often reads Q1 as QL/QI and occasionally prefixes later question
    # numbers with @ or ©. Treat those as question markers at line starts.
    marker = re.compile(r"(?m)^\s*[\.\-©@]?\s*((?:[Q@©O](?:[1-8]|L|I))|[1-8])\s*[\.\)]?\s*(?=[fF]?\(?[a-e@©0O]\)?|\()", re.I)
    matches = list(marker.finditer(text))
    blocks = []
    seen = set()
    for i, m in enumerate(matches):
        qid = normalize_q_marker(m.group(1))
        if qid in seen:
            continue
        seen.add(qid)
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        chunk = clean_question(text[start:end])
        if len(chunk) > 100:
            blocks.append((qid, chunk))
    return blocks


def main():
    rows = []
    whole_rows = []
    for txt_path in sorted(OCR_DIR.glob("20*_Paper_*.txt")):
        m = re.match(r"(\d{4})_Paper_(I{1,2})\.txt", txt_path.name)
        if not m:
            continue
        year, paper = m.groups()
        text = txt_path.read_text(encoding="utf-8", errors="ignore")
        for qid, question in extract_question_blocks(text):
            topic, subtopic, score = classify(question)
            rows.append({
                "topic": topic,
                "subtopic": subtopic,
                "year": year,
                "paper": paper,
                "question_no": qid,
                "question": question,
                "classification_score": score,
            })
        for qid, question in extract_whole_questions(text):
            topic, subtopic, score = classify(question)
            whole_rows.append({
                "topic": topic,
                "subtopic": subtopic,
                "year": year,
                "paper": paper,
                "question_no": qid,
                "question": question,
                "classification_score": score,
            })

    rows.sort(key=lambda r: (r["topic"], r["subtopic"], r["year"], r["paper"], r["question_no"]))
    whole_rows.sort(key=lambda r: (r["topic"], r["subtopic"], r["year"], r["paper"], r["question_no"]))
    csv_path = OUT_DIR / "upsc_physics_optional_pyqs_topicwise_2010_2025_available.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["topic", "subtopic", "year", "paper", "question_no", "question", "classification_score"])
        writer.writeheader()
        writer.writerows(rows)

    md_path = OUT_DIR / "upsc_physics_optional_pyqs_topicwise_2010_2025_available.md"
    lines = [
        "# UPSC Physics Optional PYQs: Topic/Subtopic-wise Index (2010-2025 Available Papers)",
        "",
        "Source: official UPSC PDFs for 2016-2025 and archive PDFs for 2010-2013 and 2015, downloaded in `pdfs/`. OCR performed locally with Tesseract.js.",
        "Because the papers are scanned bilingual PDFs, verify any garbled wording against the source PDFs.",
        "",
    ]
    current = None
    for r in rows:
        key = (r["topic"], r["subtopic"])
        if key != current:
            lines.append(f"\n## {r['topic']} - {r['subtopic']}\n")
            current = key
        lines.append(f"- **{r['year']} Paper {r['paper']} {r['question_no']}:** {r['question']}")
    md_path.write_text("\n".join(lines), encoding="utf-8")

    counts = {}
    for r in rows:
        counts[(r["topic"], r["subtopic"])] = counts.get((r["topic"], r["subtopic"]), 0) + 1
    count_path = OUT_DIR / "topic_counts_2010_2025_available.csv"
    with count_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["topic", "subtopic", "count"])
        for (topic, subtopic), count in sorted(counts.items(), key=lambda x: (-x[1], x[0])):
            writer.writerow([topic, subtopic, count])
    print(f"Wrote {len(rows)} entries")
    print(csv_path)
    print(md_path)
    print(count_path)

    whole_csv = OUT_DIR / "upsc_physics_optional_pyqs_topicwise_question_blocks_2010_2025_available.csv"
    with whole_csv.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["topic", "subtopic", "year", "paper", "question_no", "question", "classification_score"])
        writer.writeheader()
        writer.writerows(whole_rows)

    whole_md = OUT_DIR / "upsc_physics_optional_pyqs_topicwise_question_blocks_2010_2025_available.md"
    lines = [
        "# UPSC Physics Optional PYQs: Topic/Subtopic-wise Question Blocks (2010-2025 Available Papers)",
        "",
        "This version keeps each UPSC question number as a block, including all visible subparts. It is more robust than subpart splitting for scanned bilingual PDFs.",
        "Source: official UPSC PDFs for 2016-2025 and archive PDFs for 2010-2013 and 2015, downloaded in `pdfs/`. OCR performed locally with Tesseract.js.",
        "",
    ]
    current = None
    for r in whole_rows:
        key = (r["topic"], r["subtopic"])
        if key != current:
            lines.append(f"\n## {r['topic']} - {r['subtopic']}\n")
            current = key
        lines.append(f"- **{r['year']} Paper {r['paper']} {r['question_no']}:** {r['question']}")
    whole_md.write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote {len(whole_rows)} question-block entries")
    print(whole_csv)
    print(whole_md)


if __name__ == "__main__":
    main()
