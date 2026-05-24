import csv
import json
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_CSV = ROOT / "output" / "llm_clean_pyqs" / "UPSC_Physics_Optional_PYQs_Broad_Tree_Clean.csv"
DOCS = ROOT / "docs"
ASSETS = DOCS / "assets"
DATA_DIR = DOCS / "data"
IMAGE_DIR = ASSETS / "images"


def slug(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "item"


def rel_posix(path: Path) -> str:
    return path.as_posix()


def copy_image(src_text: str) -> str | None:
    src_text = src_text.strip().strip("<>")
    if not src_text:
        return None
    src = Path(src_text)
    if not src.exists():
        return None
    paper_folder = src.parent.name
    dest_dir = IMAGE_DIR / paper_folder
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    if not dest.exists() or dest.stat().st_size != src.stat().st_size:
        shutil.copy2(src, dest)
    return rel_posix(dest.relative_to(DOCS))


def load_questions():
    questions = []
    with SOURCE_CSV.open(encoding="utf-8-sig", newline="") as f:
        for idx, row in enumerate(csv.DictReader(f), start=1):
            images = []
            for img in (row.get("images") or "").split(";"):
                copied = copy_image(img)
                if copied:
                    images.append(copied)
            part = row["part"].strip()
            ref = f"{row['year']} Paper {row['paper']} {row['qid']}{f'({part})' if part else ''}"
            qid = f"{row['year']}-{row['paper']}-{row['qid']}-{part or 'all'}-{idx}"
            questions.append({
                "id": slug(qid),
                "broad": row["broad"].strip(),
                "subtopic": row["subtopic"].strip(),
                "year": int(row["year"]),
                "paper": row["paper"].strip(),
                "qid": row["qid"].strip(),
                "part": part,
                "ref": ref,
                "question": row["question"].strip(),
                "images": images,
            })
    return questions


def write_json(questions):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    broad_order = [
        "Mechanics",
        "Electrodynamics",
        "Quantum Mechanics",
        "Wave Optics",
        "Thermal and Statistical Physics",
        "Atomic and Molecular Physics",
        "Nuclear Physics",
        "Solid State and Electronics",
    ]
    counts = {}
    subtopics = {}
    years = set()
    for q in questions:
        counts[q["broad"]] = counts.get(q["broad"], 0) + 1
        subtopics.setdefault(q["broad"], {})
        subtopics[q["broad"]][q["subtopic"]] = subtopics[q["broad"]].get(q["subtopic"], 0) + 1
        years.add(q["year"])
    payload = {
        "generatedFrom": "output/llm_clean_pyqs/UPSC_Physics_Optional_PYQs_Broad_Tree_Clean.csv",
        "broadOrder": broad_order,
        "counts": counts,
        "subtopics": subtopics,
        "years": sorted(years),
        "questions": questions,
    }
    (DATA_DIR / "questions.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_site_files():
    DOCS.mkdir(exist_ok=True)
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")
    (DOCS / "index.html").write_text(INDEX_HTML, encoding="utf-8")
    (DOCS / "robots.txt").write_text(ROBOTS_TXT, encoding="utf-8")
    (DOCS / "sitemap.xml").write_text(SITEMAP_XML, encoding="utf-8")
    (ASSETS / "styles.css").write_text(STYLES_CSS, encoding="utf-8")
    (ASSETS / "app.js").write_text(APP_JS, encoding="utf-8")


INDEX_HTML = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>UPSC Physics Optional PYQs Topic Wise | Previous Year Questions</title>
    <meta name="description" content="UPSC Physics Optional previous year questions arranged topic-wise and subtopic-wise for Mechanics, Electrodynamics, Quantum Mechanics, Wave Optics, Thermal Physics, Atomic Physics, Nuclear Physics, Solid State and Electronics." />
    <meta name="keywords" content="UPSC Physics Optional PYQs, UPSC Physics previous year questions, UPSC topic wise physics PYQs, UPSC optional physics questions, UPSC Physics Optional topic wise, IAS Physics Optional PYQ" />
    <meta name="robots" content="index, follow" />
    <link rel="canonical" href="https://abhishekpandey3854.github.io/upsc-physics-pyqs/" />
    <meta property="og:title" content="UPSC Physics Optional PYQs Topic Wise" />
    <meta property="og:description" content="Searchable topic-wise UPSC Physics Optional previous year questions with source paper images." />
    <meta property="og:type" content="website" />
    <meta property="og:url" content="https://abhishekpandey3854.github.io/upsc-physics-pyqs/" />
    <meta name="twitter:card" content="summary" />
    <link rel="stylesheet" href="assets/styles.css" />
    <script type="application/ld+json">
      {
        "@context": "https://schema.org",
        "@type": "EducationalOccupationalProgram",
        "name": "UPSC Physics Optional PYQs Topic Wise",
        "description": "Topic-wise and subtopic-wise UPSC Physics Optional previous year questions with searchable static pages.",
        "educationalProgramMode": "online",
        "provider": {
          "@type": "Person",
          "name": "Abhishek Pandey"
        },
        "url": "https://abhishekpandey3854.github.io/upsc-physics-pyqs/"
      }
    </script>
  </head>
  <body>
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-title">UPSC Physics Optional PYQs</div>
        <div class="brand-subtitle">Topic-wise previous year questions</div>
      </div>
      <label class="search">
        <span>Search</span>
        <input id="search" type="search" placeholder="keyword, year, topic..." />
      </label>
      <div class="filters">
        <label>
          Broad topic
          <select id="broadFilter"></select>
        </label>
        <label>
          Year
          <select id="yearFilter"></select>
        </label>
      </div>
      <nav id="topicNav" class="topic-nav" aria-label="Topic tree"></nav>
    </aside>

    <main class="content">
      <header class="topbar">
        <div>
          <h1>Physics Optional PYQs</h1>
          <p id="summary">Loading questions...</p>
        </div>
        <button id="expandAll" type="button">Expand images</button>
      </header>
      <section id="results" class="results" aria-live="polite"></section>
    </main>

    <script src="assets/app.js"></script>
  </body>
</html>
"""


ROBOTS_TXT = """User-agent: *
Allow: /

Sitemap: https://abhishekpandey3854.github.io/upsc-physics-pyqs/sitemap.xml
"""


SITEMAP_XML = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://abhishekpandey3854.github.io/upsc-physics-pyqs/</loc>
    <changefreq>monthly</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>
"""


STYLES_CSS = """:root {
  color-scheme: light;
  --bg: #f5f6f8;
  --panel: #ffffff;
  --text: #18202a;
  --muted: #647084;
  --line: #d9dee7;
  --accent: #2457c5;
  --accent-soft: #e9efff;
  --code: #f0f3f7;
}

* { box-sizing: border-box; }

body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font: 15px/1.55 system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

.sidebar {
  position: fixed;
  inset: 0 auto 0 0;
  width: 320px;
  overflow: auto;
  border-right: 1px solid var(--line);
  background: var(--panel);
  padding: 18px;
}

.brand { margin-bottom: 18px; }
.brand-title { font-size: 18px; font-weight: 750; }
.brand-subtitle { color: var(--muted); font-size: 13px; margin-top: 2px; }

.search span,
.filters label {
  display: block;
  color: var(--muted);
  font-size: 12px;
  font-weight: 650;
  margin-bottom: 6px;
}

input,
select,
button {
  width: 100%;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: #fff;
  color: var(--text);
  font: inherit;
}

input,
select { padding: 9px 10px; }

button {
  width: auto;
  padding: 9px 12px;
  cursor: pointer;
}

.filters {
  display: grid;
  gap: 10px;
  margin: 14px 0 18px;
}

.topic-nav {
  display: grid;
  gap: 10px;
  padding-bottom: 20px;
}

.nav-group {
  border-top: 1px solid var(--line);
  padding-top: 10px;
}

.nav-group button {
  width: 100%;
  border: 0;
  background: transparent;
  text-align: left;
  padding: 4px 0;
  font-weight: 750;
}

.nav-subtopic {
  display: block;
  color: var(--muted);
  text-decoration: none;
  font-size: 13px;
  padding: 4px 0 4px 10px;
}

.nav-subtopic:hover { color: var(--accent); }

.content {
  margin-left: 320px;
  padding: 24px 28px 60px;
}

.topbar {
  display: flex;
  align-items: start;
  justify-content: space-between;
  gap: 18px;
  margin-bottom: 18px;
}

h1 { font-size: 28px; margin: 0; }
h2 { font-size: 22px; margin: 34px 0 10px; }
h3 { font-size: 16px; margin: 0; }
p { margin: 0 0 10px; }

#summary { color: var(--muted); margin-top: 4px; }

.results { display: grid; gap: 14px; }

.topic-heading {
  padding-top: 10px;
  border-top: 1px solid var(--line);
}

.question-card {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 16px;
}

.question-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 8px 0 12px;
}

.pill {
  background: var(--accent-soft);
  color: #163f99;
  border-radius: 999px;
  padding: 3px 8px;
  font-size: 12px;
  font-weight: 650;
}

.question-body { max-width: 940px; }
.question-body p { margin: 8px 0; }
.question-body ol { margin-top: 8px; }
.question-body code {
  background: var(--code);
  border-radius: 4px;
  padding: 1px 4px;
}
.question-body pre {
  overflow: auto;
  background: var(--code);
  border-radius: 6px;
  padding: 12px;
}

.images {
  margin-top: 12px;
  display: grid;
  gap: 10px;
}

.image-toggle {
  border: 1px solid var(--line);
  background: #fff;
  color: var(--accent);
  font-weight: 650;
}

.image-list[hidden] { display: none; }
.image-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 12px;
}
.image-list img {
  width: 100%;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: #fff;
}

@media (max-width: 900px) {
  .sidebar {
    position: static;
    width: auto;
    border-right: 0;
    border-bottom: 1px solid var(--line);
  }
  .content {
    margin-left: 0;
    padding: 18px;
  }
  .topbar { display: block; }
  #expandAll { margin-top: 12px; }
}
"""


APP_JS = """const state = {
  data: null,
  search: "",
  broad: "All",
  year: "All",
  expanded: false,
};

const $ = (id) => document.getElementById(id);

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function renderMarkdown(markdown) {
  let text = escapeHtml(markdown);
  const codeBlocks = [];
  text = text.replace(/```text\\n([\\s\\S]*?)```/g, (_, code) => {
    const token = `@@CODE${codeBlocks.length}@@`;
    codeBlocks.push(`<pre><code>${code.trim()}</code></pre>`);
    return token;
  });
  text = text.replace(/`([^`]+)`/g, "<code>$1</code>");
  text = text.replace(/\\*\\*([^*]+)\\*\\*/g, "<strong>$1</strong>");
  text = text.replace(/\\n\\n+/g, "</p><p>");
  text = `<p>${text}</p>`;
  text = text.replace(/<p>\\s*(\\d+)\\.\\s/g, "<p>$1. ");
  codeBlocks.forEach((block, idx) => {
    text = text.replace(`@@CODE${idx}@@`, block);
  });
  return text;
}

function questionMatches(q) {
  const haystack = `${q.broad} ${q.subtopic} ${q.ref} ${q.question}`.toLowerCase();
  const searchOk = !state.search || haystack.includes(state.search.toLowerCase());
  const broadOk = state.broad === "All" || q.broad === state.broad;
  const yearOk = state.year === "All" || String(q.year) === state.year;
  return searchOk && broadOk && yearOk;
}

function filteredQuestions() {
  return state.data.questions.filter(questionMatches);
}

function renderFilters() {
  const broad = $("broadFilter");
  broad.innerHTML = `<option>All</option>` + state.data.broadOrder
    .map((item) => `<option>${item}</option>`)
    .join("");
  const year = $("yearFilter");
  year.innerHTML = `<option>All</option>` + state.data.years
    .map((item) => `<option>${item}</option>`)
    .join("");
}

function renderNav() {
  const nav = $("topicNav");
  nav.innerHTML = state.data.broadOrder.map((broad) => {
    const subtopics = state.data.subtopics[broad] || {};
    const links = Object.entries(subtopics)
      .sort((a, b) => a[0].localeCompare(b[0]))
      .map(([sub, count]) => `<a class="nav-subtopic" href="#${slug(broad + "-" + sub)}">${sub} (${count})</a>`)
      .join("");
    return `<div class="nav-group"><button type="button" data-broad="${broad}">${broad} (${state.data.counts[broad] || 0})</button>${links}</div>`;
  }).join("");
  nav.querySelectorAll("button[data-broad]").forEach((button) => {
    button.addEventListener("click", () => {
      state.broad = button.dataset.broad;
      $("broadFilter").value = state.broad;
      render();
    });
  });
}

function slug(value) {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
}

function groupQuestions(questions) {
  const groups = new Map();
  questions.forEach((q) => {
    const key = `${q.broad}||${q.subtopic}`;
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(q);
  });
  return groups;
}

function renderQuestion(q) {
  const imageButton = q.images.length
    ? `<button class="image-toggle" type="button">Source images (${q.images.length})</button>`
    : "";
  const images = q.images.length
    ? `<div class="image-list" ${state.expanded ? "" : "hidden"}>${q.images.map((src) => `<img loading="lazy" src="${src}" alt="${q.ref} source image" />`).join("")}</div>`
    : "";
  return `<article class="question-card" id="${q.id}">
    <h3>${q.ref}</h3>
    <div class="question-meta">
      <span class="pill">${q.broad}</span>
      <span class="pill">${q.subtopic}</span>
    </div>
    <div class="question-body">${renderMarkdown(q.question)}</div>
    <div class="images">${imageButton}${images}</div>
  </article>`;
}

function render() {
  const questions = filteredQuestions();
  $("summary").textContent = `${questions.length} questions shown out of ${state.data.questions.length}`;
  const groups = groupQuestions(questions);
  const html = [...groups.entries()].map(([key, items]) => {
    const [broad, subtopic] = key.split("||");
    return `<section class="topic-heading" id="${slug(broad + "-" + subtopic)}">
      <h2>${broad}</h2>
      <p class="subheading">${subtopic} · ${items.length} entries</p>
      <div class="results">${items.map(renderQuestion).join("")}</div>
    </section>`;
  }).join("");
  $("results").innerHTML = html || `<p>No questions match the current filters.</p>`;
  document.querySelectorAll(".image-toggle").forEach((button) => {
    button.addEventListener("click", () => {
      const list = button.parentElement.querySelector(".image-list");
      list.hidden = !list.hidden;
    });
  });
}

async function init() {
  const response = await fetch("data/questions.json");
  state.data = await response.json();
  renderFilters();
  renderNav();
  $("search").addEventListener("input", (event) => {
    state.search = event.target.value;
    render();
  });
  $("broadFilter").addEventListener("change", (event) => {
    state.broad = event.target.value;
    render();
  });
  $("yearFilter").addEventListener("change", (event) => {
    state.year = event.target.value;
    render();
  });
  $("expandAll").addEventListener("click", () => {
    state.expanded = !state.expanded;
    $("expandAll").textContent = state.expanded ? "Collapse images" : "Expand images";
    render();
  });
  render();
}

init().catch((error) => {
  $("summary").textContent = "Failed to load question data.";
  console.error(error);
});
"""


def main():
    if DOCS.exists():
        shutil.rmtree(DOCS)
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    questions = load_questions()
    write_json(questions)
    write_site_files()
    print(DOCS)
    print(f"questions={len(questions)}")
    print(f"images={len(list(IMAGE_DIR.rglob('*.*')))}")


if __name__ == "__main__":
    main()
