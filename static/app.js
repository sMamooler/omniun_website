/* ── State ─────────────────────────────────────────────── */
const state = {
  modality: null,
  search: "",
  perCategory: 5,
  allSamples: [],   // full list loaded once from samples.json
  stats: null,
};

/* ── Element refs ──────────────────────────────────────── */
const els = {
  landingScreen:       document.getElementById("landingScreen"),
  browseScreen:        document.getElementById("browseScreen"),
  modalityChooser:     document.getElementById("modalityChooser"),
  activeModalityChips: document.getElementById("activeModalityChips"),
  backBtn:             document.getElementById("backBtn"),
  searchInput:         document.getElementById("searchInput"),
  statusBar:           document.getElementById("statusBar"),
  resultsList:         document.getElementById("resultsList"),
  statsNote:           document.getElementById("statsNote"),
};

/* ── Helpers ───────────────────────────────────────────── */
function debounce(fn, ms) {
  let t;
  return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
}

function titleCase(str) {
  return str.replaceAll("_", " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function escapeHtml(v) {
  return String(v)
    .replaceAll("&", "&amp;").replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;").replaceAll('"', "&quot;");
}

const ICONS = { video: "🎬", audio: "🎙️", chart: "📊", code: "💻", table: "📋", graph: "🕸️" };

/* ── Client-side filtering & grouping ──────────────────── */
function filterSamples(modality, search) {
  const q = search.trim().toLowerCase();
  return state.allSamples.filter((s) => {
    if (modality !== "all" && s.modality !== modality) return false;
    if (!q) return true;
    return [s.key, s.question, s.explanation || "", s.clarification || "", s.answer || ""]
      .join(" ").toLowerCase().includes(q);
  });
}

function groupByCategory(samples, perCategory) {
  const grouped = {};
  for (const s of samples) {
    if (!grouped[s.category]) grouped[s.category] = [];
    if (grouped[s.category].length < perCategory) grouped[s.category].push(s);
  }
  return Object.keys(grouped).sort().map((cat) => ({ category: cat, items: grouped[cat] }));
}

/* ── Render modality buttons ───────────────────────────── */
function renderModalityButtons(container, compact) {
  if (!state.stats) return;
  const modalities = Object.keys(state.stats.counts_by_modality);

  if (compact) {
    container.innerHTML = modalities.map((m) => `
      <button class="modality-tab-btn${state.modality === m ? " selected" : ""}"
              type="button" data-modality="${escapeHtml(m)}">
        ${ICONS[m] || ""} ${titleCase(m)}
      </button>
    `).join("");
  } else {
    container.innerHTML = modalities.map((m) => `
      <button class="modality-btn${state.modality === m ? " selected" : ""}"
              type="button" data-modality="${escapeHtml(m)}">
        <span class="btn-icon">${ICONS[m] || "📁"}</span>
        <span class="btn-label">${titleCase(m)}</span>
      </button>
    `).join("");
  }

  for (const btn of container.querySelectorAll("[data-modality]")) {
    btn.addEventListener("click", () => selectModality(btn.dataset.modality));
  }
}

/* ── Parse markdown table → HTML table ─────────────────── */
function markdownTableToHTML(md) {
  const lines = md.trim().split('\n').map(l => l.trim()).filter(l => l);
  if (lines.length < 2) return `<div class="table-block"><pre>${escapeHtml(md)}</pre></div>`;

  const parseCells = (line) =>
    line.replace(/^\||\|$/g, '').split('|').map(c => c.trim());

  const sepIdx = lines.findIndex(l => /^\|?[\s\-:]+\|/.test(l) && /---/.test(l));
  if (sepIdx < 1) return `<div class="table-block"><pre>${escapeHtml(md)}</pre></div>`;

  const headers = parseCells(lines[0]);
  const dataRows = lines.slice(sepIdx + 1);

  const thead = `<thead><tr>${headers.map(h => `<th>${escapeHtml(h)}</th>`).join('')}</tr></thead>`;
  const tbody = `<tbody>${dataRows.map(row => {
    const cells = parseCells(row);
    return `<tr>${cells.map(c => `<td>${escapeHtml(c)}</td>`).join('')}</tr>`;
  }).join('')}</tbody>`;

  return `<div class="table-block"><table>${thead}${tbody}</table></div>`;
}

/* ── Render media inside a card ────────────────────────── */
function renderMediaHTML(item) {
  if (!item.media_url) {
    return `<div class="media-missing">Media not available for <code>${escapeHtml(item.key)}</code></div>`;
  }
  if (item.modality === "video") {
    return `<video controls preload="none" src="${escapeHtml(item.media_url)}"></video>`;
  }
  if (item.modality === "audio") {
    return `<audio controls preload="none" src="${escapeHtml(item.media_url)}"></audio>`;
  }
  if (item.modality === "chart") {
    return `<img class="chart-img" src="${escapeHtml(item.media_url)}" alt="Chart for ${escapeHtml(item.key)}">`;
  }
  if (item.modality === "code") {
    if (item.media_content) {
      return `<pre class="code-block"><code>${escapeHtml(item.media_content)}</code></pre>`;
    }
    return `<div class="media-missing">Code not available for <code>${escapeHtml(item.key)}</code></div>`;
  }
  if (item.modality === "table") {
    if (item.media_content) {
      return markdownTableToHTML(item.media_content);
    }
    return `<div class="media-missing">Table not available for <code>${escapeHtml(item.key)}</code></div>`;
  }
  if (item.modality === "graph") {
    if (item.media_content) {
      return `<pre class="code-block graph-block"><code>${escapeHtml(item.media_content)}</code></pre>`;
    }
    return `<div class="media-missing">Graph not available for <code>${escapeHtml(item.key)}</code></div>`;
  }
  return `<div class="media-missing">Unsupported modality</div>`;
}

/* ── Judge label → CSS class ───────────────────────────── */
const JUDGE_LABEL_CLASS = {
  "reasoned_abstention":                "pill-good",
  "abstention_with_clarification_request": "pill-good",
  "premise_refutation":                 "pill-good",
  "confident_direct_answer":            "pill-bad",
  "hedged_best_effort_answer":          "pill-warn",
  "provides_multiple_answers":          "pill-warn",
};

function judgeLabel(item) {
  if (!item.qwen_omni_judge_label) return "";
  const cls = JUDGE_LABEL_CLASS[item.qwen_omni_judge_label] || "pill-neutral";
  const text = item.qwen_omni_judge_label.replaceAll("_", " ");
  return `<span class="pill ${cls}">${escapeHtml(text)}</span>`;
}

/* ── Render a single example card ──────────────────────── */
function exampleCardHTML(item) {
  const isAudio = item.modality === "audio";
  const isText  = item.modality === "code" || item.modality === "table" || item.modality === "graph";
  const mediaClass = isAudio ? "card-media card-media-audio"
                   : isText  ? "card-media card-media-text"
                   : "card-media";
  const mediaZone = `<div class="${mediaClass}">${renderMediaHTML(item)}</div>`;

  const modelSection = item.qwen_omni_response ? `
    <details class="model-response">
      <summary>
        <span class="model-name">Qwen3-Omni response</span>
        ${judgeLabel(item)}
      </summary>
      <p class="model-response-text">${escapeHtml(item.qwen_omni_response)}</p>
    </details>
  ` : "";

  return `
    <div class="example-card">
      ${mediaZone}
      <div class="card-body">
        <p class="card-question">${escapeHtml(item.question)}</p>
        <div class="card-meta">
          <span class="pill pill-neutral">${item.media_exists ? "media ready" : "no media"}</span>
        </div>
        <p class="card-key">${escapeHtml(item.key)}</p>
        ${modelSection}
      </div>
    </div>
  `;
}

/* ── Render a category section ─────────────────────────── */
function categorySectionHTML(group) {
  const cards = group.items.map(exampleCardHTML).join("");
  return `
    <section class="category-section">
      <div class="category-header">
        <h2>${escapeHtml(titleCase(group.category))}</h2>
      </div>
      <div class="examples-grid">${cards}</div>
    </section>
  `;
}

/* ── Render all results ────────────────────────────────── */
function renderResults() {
  const filtered = filterSamples(state.modality || "all", state.search);
  const groups   = groupByCategory(filtered, state.perCategory);

  if (groups.length === 0) {
    els.resultsList.innerHTML = `<div class="empty-state">No examples found.</div>`;
    els.statusBar.textContent = "";
    return;
  }

  els.statusBar.textContent =
    `${titleCase(state.modality)} · ${groups.length} categor${groups.length === 1 ? "y" : "ies"}`;

  els.resultsList.innerHTML = groups.map(categorySectionHTML).join("");
}

/* ── Select a modality ─────────────────────────────────── */
function selectModality(modality) {
  state.modality = modality;
  state.search = "";
  els.searchInput.value = "";

  els.landingScreen.classList.add("hidden");
  els.browseScreen.classList.remove("hidden");

  renderModalityButtons(els.activeModalityChips, true);
  renderResults();
}

/* ── Back to landing ───────────────────────────────────── */
els.backBtn.addEventListener("click", () => {
  els.browseScreen.classList.add("hidden");
  els.landingScreen.classList.remove("hidden");
  state.modality = null;
  renderModalityButtons(els.modalityChooser, false);
});

/* ── Search ────────────────────────────────────────────── */
els.searchInput.addEventListener("input", debounce(() => {
  state.search = els.searchInput.value.trim();
  renderResults();
}, 200));

/* ── Boot: load samples.json once ─────────────────────── */
async function boot() {
  const res = await fetch("data/samples.json");
  const payload = await res.json();

  state.stats      = payload.stats;
  state.allSamples = payload.samples;

  const cats  = Object.keys(state.stats.counts_by_category).length;
  els.statsNote.textContent = `${cats} categories`;

  renderModalityButtons(els.modalityChooser, false);
}

boot();
