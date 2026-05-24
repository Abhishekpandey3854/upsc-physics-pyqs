import csv
import re
from collections import Counter
from pathlib import Path

try:
    import ftfy
except ImportError:  # pragma: no cover
    ftfy = None


ROOT = Path(__file__).resolve().parents[1]
PAPER_DIR = ROOT / "output" / "llm_clean_pyqs" / "papers"
OUT_DIR = ROOT / "output" / "llm_clean_pyqs"

BROAD_ORDER = [
    "Mechanics",
    "Electrodynamics",
    "Quantum Mechanics",
    "Wave Optics",
    "Thermal and Statistical Physics",
    "Atomic and Molecular Physics",
    "Nuclear Physics",
    "Solid State and Electronics",
]

RULES = [
    ("Mechanics", "Rigid body dynamics", ["rigid", "moment of inertia", "angular momentum", "torque-free", "principal axes", "rolling", "gyroscope", "euler", "parallel axes", "perpendicular axes"]),
    ("Mechanics", "Central force and gravitation", ["central force", "orbit", "kepler", "satellite", "gravitational", "escape velocity", "self-energy", "planet", "inverse-square"]),
    ("Mechanics", "Oscillations", ["oscillator", "oscillation", "damped", "amplitude", "resonance", "beats", "simple harmonic", "zero-point energy"]),
    ("Mechanics", "Elasticity and fluid mechanics", ["young's modulus", "elastic", "shaft", "torsion", "viscosity", "poiseuille", "streamline", "bernoulli", "surface tension", "capillary"]),
    ("Mechanics", "Special relativity", ["lorentz", "relativistic", "rest mass", "proper", "contraction", "time dilation", "0.9c", "0.8c", "explosions"]),
    ("Electrodynamics", "Electrostatics and boundary-value problems", ["electric field", "electric potential", "charge density", "conducting sphere", "image charge", "dielectric", "capacitance", "laplace", "poisson"]),
    ("Electrodynamics", "Magnetostatics", ["magnetic field", "magnetic vector potential", "vector potential", "biot", "savart", "ampere", "solenoid", "current loop"]),
    ("Electrodynamics", "Electromagnetic induction and AC circuits", ["kirchhoff", "capacitor", "inductor", "impedance", "reactance", "rlc", "ac circuit", "power factor", "coil", "lcr"]),
    ("Electrodynamics", "Electromagnetic waves", ["electromagnetic wave", "poynting", "displacement current", "maxwell", "radiation pressure", "radio wave", "plasma frequency"]),
    ("Quantum Mechanics", "Foundations and operators", ["uncertainty", "operator", "commutator", "eigenvalue", "eigenfunction", "wave function", "wavefunction", "normaliz", "expectation", "hamiltonian"]),
    ("Quantum Mechanics", "Potential problems and tunnelling", ["potential well", "potential barrier", "tunnelling", "tunneling", "transmission probability", "infinite potential", "schrodinger", "schrodinger's equation"]),
    ("Quantum Mechanics", "Angular momentum and spin", ["spin", "pauli", "sigma", "angular momentum", "spin matrices"]),
    ("Wave Optics", "Interference and diffraction", ["interference", "diffraction", "fraunhofer", "fresnel", "double-slit", "newton's rings", "grating", "fringe", "missing orders"]),
    ("Wave Optics", "Polarization", ["polarization", "polarized", "birefringence", "quarter-wave", "half-wave", "malus"]),
    ("Wave Optics", "Geometrical and matrix optics", ["lens", "mirror", "prism", "matrix method", "refractive index", "thick lens", "optical fiber", "fibre"]),
    ("Wave Optics", "Lasers", ["laser", "population inversion", "resonator", "he-ne", "line-shape", "fwhm", "pumping", "lasing"]),
    ("Thermal and Statistical Physics", "Thermodynamics", ["thermodynamic", "entropy", "heat engine", "reversible", "carnot", "chemical potential", "phase rule", "van der waals", "joule-kelvin", "heat capacity", "heat capacities", "adiabatic", "molar heat"]),
    ("Thermal and Statistical Physics", "Statistical mechanics", ["partition function", "bose", "fermi", "maxwell-boltzmann", "blackbody", "planck", "rayleigh-jeans", "density of states", "specific heat", "classical statistics"]),
    ("Atomic and Molecular Physics", "Atomic spectra and structure", ["zeeman", "stark", "lamb shift", "balmer", "hydrogen spectrum", "fine structure", "lande", "stern-gerlach", "term symbols", "spin-orbit", "bohr orbit", "bohr magneton"]),
    ("Atomic and Molecular Physics", "Molecular spectra", ["raman", "rotational", "vibrational", "diatomic", "molecular", "hcl", "hf molecule", "infrared", "franck-condon"]),
    ("Atomic and Molecular Physics", "Magnetic resonance", ["epr", "electron paramagnetic resonance", "nmr"]),
    ("Nuclear Physics", "Nuclear structure and radioactivity", ["nuclear", "deuteron", "shell model", "single-particle", "radioactive", "decay", "binding energy", "semi-empirical", "liquid drop", "magic numbers", "odd-a"]),
    ("Nuclear Physics", "Nuclear reactions and particle physics", ["q-value", "reaction", "cross-section", "fission", "fusion", "quark", "lepton", "meson", "baryon", "elementary particles"]),
    ("Solid State and Electronics", "Crystal structure and lattice dynamics", ["crystal", "lattice", "reciprocal lattice", "miller", "bragg", "x-ray diffraction", "xrd", "phonon"]),
    ("Solid State and Electronics", "Band theory and semiconductors", ["band", "semiconductor", "fermi level", "p-n junction", "diode", "transistor", "hall effect", "solar cell", "thermistor", "effective mass"]),
    ("Solid State and Electronics", "Superconductivity and magnetism", ["superconductor", "superconductivity", "diamagnetic", "paramagnetic", "ferromagnetic", "susceptibility"]),
    ("Solid State and Electronics", "Analog and digital electronics", ["amplifier", "op-amp", "mosfet", "logic gate", "nand", "nor", "microprocessor", "flip-flop", "rectifier"]),
]

SYMBOL_REPLACEMENTS = [
    (r"\bDelta omega\b", "\u0394\u03c9"),
    (r"\bDelta nu-bar\b", "\u0394\u03bd\u0304"),
    (r"\bomega0\b", "\u03c9\u2080"),
    (r"\bomega_0\b", "\u03c9\u2080"),
    (r"\bomega_p\b", "\u03c9_p"),
    (r"\bomegat\b", "\u03c9t"),
    (r"\bmomega\b", "m\u03c9"),
    (r"\bomega\b", "\u03c9"),
    (r"\bgamma\b", "\u03b3"),
    (r"\bGamma\b", "\u0393"),
    (r"\brho_0\b", "\u03c1\u2080"),
    (r"\brho\b", "\u03c1"),
    (r"\bsigma_x\b", "\u03c3\u2093"),
    (r"\bsigma_y\b", "\u03c3\u1d67"),
    (r"\bsigma_z\b", "\u03c3_z"),
    (r"\bsigma_\+\b", "\u03c3\u208a"),
    (r"\bsigma_-\b", "\u03c3\u208b"),
    (r"\bsigma_alpha\b", "\u03c3_\u03b1"),
    (r"\bsigma_beta\b", "\u03c3_\u03b2"),
    (r"\bsigma_gamma\b", "\u03c3_\u03b3"),
    (r"\btau/theta\b", "\u03c4/\u03b8"),
    (r"\btau\b", "\u03c4"),
    (r"\btheta\b", "\u03b8"),
    (r"\blambda_0\b", "\u03bb\u2080"),
    (r"\blambda\b", "\u03bb"),
    (r"\bmu\b", "\u03bc"),
    (r"\beta\b", "\u03b7"),
    (r"\bpi\b", "\u03c0"),
    (r"\bAngstrom\b", "\u00c5"),
    (r"\bohm\b", "\u03a9"),
    (r"\bdegree\b", "\u00b0"),
    (r"\bj-hat\b", "\u0135"),
    (r"\bi-hat\b", "\u00ee"),
    (r"\bk-hat\b", "k\u0302"),
    (r"\balpha\b", "\u03b1"),
    (r"\bbeta\b", "\u03b2"),
    (r"\bepsilon\b", "\u03b5"),
]


def normalize_symbols(text: str) -> str:
    if ftfy is not None:
        text = ftfy.fix_text(text)
    # Repair common mojibake that came from earlier OCR/model passes.
    replacements = {
        "\u00ce\u00b8": "\u03b8",
        "\u00ce\u00bb": "\u03bb",
        "\u00cf\u20ac": "\u03c0",
        "\u00cf\u2030": "\u03c9",
        "\u00c3\u2014": "\u00d7",
        "\u00c3\u2013": "\u00d7",
        "\u00c3\u2026": "\u00c5",
        "\u00c2\u00b0": "\u00b0",
        "\u00c2": "",
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    text = text.replace(" x 10^", " \u00d7 10^")
    text = text.replace("Schrodinger", "Schr\u00f6dinger")
    text = text.replace("Lande", "Land\u00e9")
    text = text.replace("H_alpha", "H\u03b1")
    text = text.replace("hbar", "\u210f")
    text = text.replace("`NA`", "`N_A`").replace("`NB`", "`N_B`")
    text = text.replace("omega1", "\u03c9\u2081").replace("omega2", "\u03c9\u2082").replace("omega3", "\u03c9\u2083")
    text = text.replace("omega_a/omega_s", "\u03c9_a/\u03c9_s")
    text = text.replace("omega_a", "\u03c9_a").replace("omega_s", "\u03c9_s")
    text = text.replace("omega_p", "\u03c9_p")
    text = text.replace("gamma_He", "\u03b3_He").replace("gamma_air", "\u03b3_air")
    text = text.replace("sigma_+", "\u03c3\u208a").replace("sigma_-", "\u03c3\u208b")
    text = text.replace("sigma_n", "\u03c3_n").replace("sigma_p", "\u03c3_p")
    text = text.replace(" deg", "\u00b0")
    text = text.replace("`v_0`", "`v\u2080`")
    for pattern, repl in SYMBOL_REPLACEMENTS:
        text = re.sub(pattern, repl, text, flags=re.I)
    return text


def parse_paper(path: Path):
    text = path.read_text(encoding="utf-8-sig", errors="ignore")
    m = re.match(r"(\d{4})_Paper_(I{1,2})", path.stem)
    if not m:
        return []
    year, paper = m.groups()
    q_matches = list(re.finditer(r"(?m)^##\s+(Q[1-8])\b.*$", text))
    rows = []
    for i, qm in enumerate(q_matches):
        qid = qm.group(1)
        qblock = text[qm.start(): q_matches[i + 1].start() if i + 1 < len(q_matches) else len(text)]
        images = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", qblock)
        topic = re.search(r"\*\*Topic:\*\*\s*(.+)", qblock)
        subtopic = re.search(r"\*\*Subtopic:\*\*\s*(.+)", qblock)
        meta = f"{topic.group(1) if topic else ''} {subtopic.group(1) if subtopic else ''}"
        body = re.split(r"\*\*Source [^*]+:\*\*", qblock, maxsplit=1)[0]
        body = re.sub(r"^##.*\n", "", body, count=1).strip()
        body = re.sub(r"\*\*Topic:\*\*.*\n", "", body)
        body = re.sub(r"\*\*Subtopic:\*\*.*\n", "", body).strip()
        for part_label, part_text in split_parts(body):
            part_text = normalize_symbols(part_text.strip())
            broad, sub = classify_part(part_text)
            if sub == "General / needs manual classification":
                broad, sub = classify_part(part_text + " " + meta)
            rows.append({
                "broad": broad,
                "subtopic": sub,
                "year": year,
                "paper": paper,
                "qid": qid,
                "part": part_label,
                "question": part_text,
                "paper_file": str(path.resolve()),
                "images": images,
            })
    return rows


def split_parts(body: str):
    matches = list(re.finditer(r"(?m)^\*\*\(([a-f])\)\*\*", body))
    if not matches:
        return [("", body)]
    prefix = body[:matches[0].start()].strip()
    prefix = prefix if len(prefix) > 25 else ""
    parts = []
    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        text = body[match.start():end].strip()
        if prefix:
            text = prefix + "\n\n" + text
        parts.append((match.group(1), text))
    return parts


def classify_part(text: str):
    low = text.lower()
    if any(k in low for k in ["deuteron", "nuclear density", "shell model", "magic numbers", "semi-empirical mass", "radioactive", "q-value"]):
        if any(k in low for k in ["q-value", "reaction", "quark", "elementary particle"]):
            return "Nuclear Physics", "Nuclear reactions and particle physics"
        return "Nuclear Physics", "Nuclear structure and radioactivity"
    if any(k in low for k in ["phase transition", "clausius", "maxwell-boltzmann", "mean free path", "van der waals", "heat capacity", "heat engine", "chemical potential", "partition function"]):
        if any(k in low for k in ["partition function", "maxwell-boltzmann", "mean free path", "blackbody", "planck", "density of states"]):
            return "Thermal and Statistical Physics", "Statistical mechanics"
        return "Thermal and Statistical Physics", "Thermodynamics"
    if any(k in low for k in ["effective mass", "semiconductor", "p-n junction", "hall effect", "solar cell", "thermistor", "x-ray diffraction", "xrd", "reciprocal lattice"]):
        if any(k in low for k in ["x-ray diffraction", "xrd", "reciprocal lattice", "miller"]):
            return "Solid State and Electronics", "Crystal structure and lattice dynamics"
        return "Solid State and Electronics", "Band theory and semiconductors"
    if any(k in low for k in ["laser", "population inversion", "lasing", "pumping scheme"]):
        return "Wave Optics", "Lasers"
    if any(k in low for k in ["zeeman", "lamb shift", "stern-gerlach", "balmer", "bohr orbit", "hydrogen spectrum", "fine structure"]):
        return "Atomic and Molecular Physics", "Atomic spectra and structure"
    if any(k in low for k in ["raman", "diatomic molecule", "rotational spectrum", "vibrational spectrum", "franck-condon"]):
        return "Atomic and Molecular Physics", "Molecular spectra"
    best = ("Mechanics", "General / needs manual classification", 0)
    for broad, sub, keys in RULES:
        score = sum(1 for key in keys if key in low)
        if score > best[2]:
            best = (broad, sub, score)
    return best[0], best[1]


def make_ref(row):
    part = f"({row['part']})" if row["part"] else ""
    return f"{row['year']} Paper {row['paper']} {row['qid']}{part}"


def sort_key(row):
    return (BROAD_ORDER.index(row["broad"]), row["subtopic"], row["year"], row["paper"], row["qid"], row["part"])


def write_outputs(rows):
    rows.sort(key=sort_key)
    compact = OUT_DIR / "UPSC_Physics_Optional_PYQs_Broad_Tree_Clean.md"
    visual = OUT_DIR / "UPSC_Physics_Optional_PYQs_Broad_Tree_Clean_VISUAL.md"
    csv_path = OUT_DIR / "UPSC_Physics_Optional_PYQs_Broad_Tree_Clean.csv"

    for path, with_images in [(compact, False), (visual, True)]:
        lines = [
            "# UPSC Physics Optional PYQs - Broad Topic Tree",
            "",
            "Classification tree: Mechanics; Electrodynamics; Quantum Mechanics; Wave Optics; Thermal and Statistical Physics; Atomic and Molecular Physics; Nuclear Physics; Solid State and Electronics.",
            "Entries are split at subpart level where possible, so mixed compulsory questions appear under the relevant broad topic.",
            "",
        ]
        current_broad = current_sub = None
        for row in rows:
            if row["broad"] != current_broad:
                lines.append(f"\n## {row['broad']}\n")
                current_broad = row["broad"]
                current_sub = None
            if row["subtopic"] != current_sub:
                lines.append(f"\n### {row['subtopic']}\n")
                current_sub = row["subtopic"]
            lines.append(f"#### {make_ref(row)}")
            lines.append("")
            lines.append(row["question"])
            lines.append("")
            lines.append(f"Paper file: [{Path(row['paper_file']).name}]({Path(row['paper_file']).as_posix()})")
            lines.append("")
            if with_images:
                lines.append("Source image(s):")
                lines.append("")
                for img in row["images"]:
                    lines.append(f"![{make_ref(row)} source]({img.strip('<>')})")
                    lines.append("")
            lines.append("---")
            lines.append("")
        path.write_text("\n".join(lines), encoding="utf-8")

    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["broad", "subtopic", "year", "paper", "qid", "part", "question", "paper_file", "images"])
        writer.writeheader()
        for row in rows:
            writer.writerow(row | {"images": ";".join(row["images"])})

    print(compact)
    print(visual)
    print(csv_path)
    print(f"entries={len(rows)}")
    print(Counter(row["broad"] for row in rows))


def main():
    rows = []
    for path in sorted(PAPER_DIR.glob("20*_Paper_*.md")):
        rows.extend(parse_paper(path))
    write_outputs(rows)


if __name__ == "__main__":
    main()
