from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
PAGE_DIR = ROOT / "text" / "pages"
IMG_DIR = ROOT / "output" / "pilot_2025_paper_i_images"
OUT = ROOT / "output" / "pilot_2025_paper_i_visual_markdown.md"
IMG_DIR.mkdir(parents=True, exist_ok=True)


def crop(page_no, name, box):
    img = Image.open(PAGE_DIR / f"2025_Paper_I_p{page_no:02d}.png")
    w, h = img.size
    left, top, right, bottom = box
    if right <= 1:
        right = int(w * right)
    if bottom <= 1:
        bottom = int(h * bottom)
    out = IMG_DIR / f"{name}.png"
    img.crop((left, top, right, bottom)).save(out)
    return out


QUESTIONS = [
    {
        "qid": "Q1",
        "topic": "Mixed: Mechanics, Relativity, Optics, EM Waves",
        "subtopic": "Compulsory short questions",
        "images": [(3, "q1_page3", (0, 120, 1107, 1515))],
        "text": """**(a)** Consider a large stationary cylinder of inner radius `R`. A smaller solid cylinder of radius `r` rolls without slipping inside the larger cylinder. Determine the equation of motion of the smaller cylinder. **10**

**(b)** Derive the expression for the gravitational self-energy of a uniform solid sphere of mass `M` and radius `R`. **10**

**(c)** A particle of rest mass `1 kg` and velocity of magnitude `0.9c` collides with a particle of mass `2 kg` at rest. After collision the two particles coalesce and form a single particle of mass `M` and velocity `V`. Determine `M` and `V`. **10**

**(d)** In a double-slit Fraunhofer diffraction experiment, the slit width is `0.12 mm` and the spacing between the two slits is `0.48 mm`. The distance of the screen from the slits is `1.5 m`. If the wavelength of the light used is `600 nm`, determine:

1. the missing orders of the interference maxima, and
2. the distance between the central maximum and the first minimum. **10**

**(e)** A light beam of wavelength `600 nm` produced by a `20 mW` laser source is incident on a plane mirror. Determine:

1. number of photons per second striking the surface of the mirror, and
2. force exerted by the light beam on the mirror. **10**""",
    },
    {
        "qid": "Q2",
        "topic": "Classical Mechanics and Relativity",
        "subtopic": "Rigid body dynamics, damped oscillator, Lorentz invariance",
        "images": [(4, "q2_page4_top", (0, 0, 1107, 980))],
        "text": """**(a)** A body moves about a point `O` under no force, the principal moments of inertia at `O` being `3A`, `5A` and `6A`. The components of the initial angular velocity about the principal axes are `ω1 = n`, `ω2 = 0` and `ω3 = n`. Find the components `ω1`, `ω2` and `ω3` for large values of time `t`. **20**

**(b)** A harmonic oscillator is represented by the equation

```text
m d²x/dt² + γ dx/dt + kx = 0
```

where `m = 0.25 kg`, `γ = 0.07 kg s⁻¹` and `k = 85 N m⁻¹`. Determine:

1. the period of oscillation, and
2. the number of oscillations in which its amplitude will become half of its original value. **15**

**(c)** Show that the electromagnetic wave equation is invariant under Lorentz transformations. **15**""",
    },
    {
        "qid": "Q3",
        "topic": "Optics and Rigid Body Dynamics",
        "subtopic": "Laser physics and inertia tensor",
        "images": [
            (4, "q3_page4_bottom", (0, 900, 1107, 1510)),
            (5, "q3_page5_top", (0, 0, 1107, 690)),
        ],
        "text": """**(a)** Consider a laser system consisting of an active medium placed between a pair of mirrors forming a resonator. Obtain an expression for the threshold population inversion required for the oscillations of laser. **20**

**(b)** For a He-Ne laser system, what will be the magnitude of `Δω` which represents FWHM of the line shape function `g(ω)`, if resonant frequency `ω₀ = 3 × 10¹⁵ s⁻¹` and temperature `T = 300 K`? **10**

**(c)** A cube of mass `M` and side `a` is rotating with angular velocity `ω` around one of its edges, which is, say, along the x-axis. Obtain the expressions for its angular momentum and kinetic energy.

Given inertia tensor components are printed in the source image; verify symbols from the crop before solving. **20**""",
    },
    {
        "qid": "Q4",
        "topic": "Optics and Elasticity",
        "subtopic": "Matrix optics, thin films, torsion of shafts",
        "images": [(5, "q4_page5_bottom", (0, 610, 1107, 1515))],
        "text": """**(a)** Consider a thick lens of thickness `t` made of a material of relative refractive index `n`. Let `R1` and `R2` be the radii of curvature of its two surfaces. Obtain the system matrix of the lens. **15**

**(b)** Consider multiple reflections from a plane parallel film of thickness `h` and refractive index `n1` and derive an expression for the total reflectivity from the surface of the film. **20**

**(c)** A solid shaft of mass `M`, length `l` and radius `r` is to be replaced by a lighter hollow shaft of the same length `l` and having the same rating of `τ/θ`, where `τ` is the couple and `θ` is the angle of twist. Estimate the percentage reduction in mass of the hollow shaft if the outer radius of the shaft is twice the inner radius. Assume the material of the new shaft is the same as that of the replaced shaft. **15**""",
    },
    {
        "qid": "Q5",
        "topic": "Electrodynamics and Thermal Physics",
        "subtopic": "Image method, torque, Kirchhoff laws, displacement current, heat engine",
        "images": [
            (6, "q5_page6", (0, 90, 1107, 1515)),
            (7, "q5_page7_top", (0, 0, 1107, 350)),
        ],
        "text": """**(a)** Consider a point charge of `5 nC` placed at a distance of `1 m` from a perfect conducting plane `(z = 0)` of infinite extent. Find the electric field at a point `(2, 2, 0) m` and show that it is normal to the plane. **10**

**(b)** A rectangular coil consists of `50` closely wrapped turns and has dimensions `0.5 m × 0.4 m`. It carries a current of `1.5 A`. If a uniform magnetic field `B = 0.1 T` is applied such that the direction of the magnetic field makes an angle of `60°` with respect to the plane of the coil, what is the torque exerted on the coil by the magnetic field? **10**

**(c)** State and explain Kirchhoff's current law and Kirchhoff's voltage law. Derive these laws from the principles of charge conservation and energy conservation. **10**

**(d)** A parallel plate capacitor having circular plates of radius `10 cm` is being charged. If the electric field at any instant within the capacitor changes at the rate `50 V m⁻¹ s⁻¹`, calculate the magnetic intensity `|H|` inside the capacitor. **10**

**(e)** A reversible heat engine operates with three reservoirs at `300 K`, `400 K` and `1200 K`. It absorbs `1200 kJ` energy as heat from the reservoir at `1200 K` and delivers `400 kJ` work. Determine the heat interactions with the other two reservoirs. **10**""",
    },
    {
        "qid": "Q6",
        "topic": "Electrodynamics and Statistical Mechanics",
        "subtopic": "Vector potential, AC circuits, Helmholtz free energy",
        "images": [
            (7, "q6_page7_bottom", (0, 300, 1107, 1515)),
            (8, "q6_page8_top", (0, 0, 1107, 910)),
        ],
        "text": """**(a)** Consider a long straight wire of length `L` carrying a current `I`. Determine the magnetic vector potential `A` at a point `P` located at distance `x` from the wire. **20**

**(b)** As shown in the figure, a series circuit connected across a `200 V`, `60 Hz` line consists of a capacitor of capacitive reactance `30 Ω`, a non-inductive resistor of `44 Ω` and a coil of inductive reactance `90 Ω` and resistance `36 Ω`. Determine:

1. power factor of the circuit,
2. power absorbed by the circuit, and
3. power dissipated in the coil. **15**

**(c)** Consider a mixture of `N_A` molecules of a monatomic gas A and `N_B` molecules of a monatomic gas B. For this mixture, obtain the Helmholtz free energy and pressure. The particle partition function for a monatomic gas is printed in the source image; verify the exact formula from the crop. **15**""",
    },
    {
        "qid": "Q7",
        "topic": "Thermal Physics and Electrodynamics",
        "subtopic": "Phase rule, Van der Waals gas, conducting sphere in electric field",
        "images": [
            (8, "q7_page8_bottom", (0, 820, 1107, 1515)),
            (9, "q7_page9_top", (0, 0, 1107, 930)),
        ],
        "text": """**(a)** A ternary system consists of three components `(A, B and C)` in equilibrium with two phases. Determine the number of degrees of freedom using Gibbs' phase rule and discuss the effect of pressure and temperature variations on the phase equilibrium. **15**

**(b)** Discuss briefly the considerations which led Van der Waals to modify the gas equation. What are the critical constants of a gas? Calculate the values of these constants in terms of the constants of the Van der Waals equation. **15**

**(c)** Consider a conducting sphere of radius `a` in a uniform electric field `E`. Find the induced surface charge density on the sphere and determine the electric field `E` at a point `P` characterized by radius vector `r`. **20**""",
    },
    {
        "qid": "Q8",
        "topic": "Electromagnetic Waves and Statistical Physics",
        "subtopic": "Displacement current, Poynting vector, chemical potential, Planck law",
        "images": [
            (9, "q8_page9_bottom", (0, 820, 1107, 1515)),
            (10, "q8_page10", (0, 0, 1107, 620)),
        ],
        "text": """**(a)** 

1. In free space, an electric field `E` is given by:

```text
E = 10 cos(ωt - 100x) ĵ V/m
```

Find the angular frequency `ω` and the displacement current. **10**

2. An electromagnetic wave has its magnetic field `|B| = 55 × 10⁻⁸ T`. Determine the magnitude of the Poynting vector. **5**

**(b)** Explain why, at equilibrium, the chemical potential of a component must be the same in all coexisting phases. Derive the equilibrium condition for a binary liquid-vapour system in terms of chemical potential. **15**

**(c)** Derive Planck's radiation law for blackbody radiation using the Bose-Einstein distribution function. Explain how results from quantum statistics differ from classical results derived from the Rayleigh-Jeans law. **20**""",
    },
]


def main():
    lines = [
        "# Pilot Extraction: UPSC Physics Optional 2025 Paper I",
        "",
        "This is a quality pilot: each question has cleaned Markdown plus source image crop(s). Any symbol-heavy part that was unclear from OCR is explicitly marked for visual verification against the crop.",
        "",
    ]
    for q in QUESTIONS:
        lines.append(f"## {q['qid']} - {q['topic']}")
        lines.append("")
        lines.append(f"**Subtopic:** {q['subtopic']}")
        lines.append("")
        lines.append(q["text"])
        lines.append("")
        lines.append("**Source crop(s):**")
        lines.append("")
        for page_no, name, box in q["images"]:
            path = crop(page_no, name, box).resolve()
            lines.append(f"![{q['qid']} source crop]({path.as_posix()})")
            lines.append("")
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
