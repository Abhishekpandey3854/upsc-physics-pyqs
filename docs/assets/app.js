const state = {
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
  text = text.replace(/```text\n([\s\S]*?)```/g, (_, code) => {
    const token = `@@CODE${codeBlocks.length}@@`;
    codeBlocks.push(`<pre><code>${code.trim()}</code></pre>`);
    return token;
  });
  text = text.replace(/`([^`]+)`/g, "<code>$1</code>");
  text = text.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  text = text.replace(/\n\n+/g, "</p><p>");
  text = `<p>${text}</p>`;
  text = text.replace(/<p>\s*(\d+)\.\s/g, "<p>$1. ");
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
