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

const ICONS = { video: "🎬", audio: "🎙️", chart: "📊", code: "💻", table: "📋", graph: "🕸️", document: "📄" };

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

/* ── Graph parsing ──────────────────────────────────────── */
function parseGraphText(text) {
  const lines = text.trim().split('\n').map(l => l.trim()).filter(Boolean);
  let nodes = [], edges = [], directed = false, graphType = 'general';

  if (/job applicants/i.test(text)) {
    // Bipartite: applicants ↔ jobs
    graphType = 'bipartite';
    const m = text.match(/(\d+) job applicants[\s\S]*?and (\d+) jobs/i);
    const nA = m ? +m[1] : 0, nJ = m ? +m[2] : 0;
    for (let i = 0; i < nA; i++) nodes.push({ id: `a${i}`, label: `A${i}`, group: 'applicant' });
    for (let j = 0; j < nJ; j++) nodes.push({ id: `j${j}`, label: `J${j}`, group: 'job' });
    for (const line of lines) {
      const m = line.match(/Applicant (\d+) is interested in job (\d+)/i);
      if (m) edges.push({ source: `a${m[1]}`, target: `j${m[2]}` });
    }

  } else if (/should be visited before/i.test(text)) {
    // Topological ordering: directed edges from ordering constraints
    directed = true; graphType = 'directed';
    const nodeSet = new Set();
    const hm = text.match(/\d+ nodes numbered from \d+ to (\d+)/i);
    if (hm) for (let i = 0; i <= +hm[1]; i++) nodeSet.add(String(i));
    for (const line of lines) {
      const m = line.match(/node (\d+) should be visited before node (\d+)/i);
      if (m) { nodeSet.add(m[1]); nodeSet.add(m[2]); edges.push({ source: m[1], target: m[2] }); }
    }
    nodes = [...nodeSet].sort((a, b) => +a - +b).map(id => ({ id, label: id }));

  } else if (/edge from node/i.test(text)) {
    // Directed graph with capacities
    directed = true; graphType = 'directed';
    const nodeSet = new Set();
    const hm = text.match(/nodes numbered from \d+ to (\d+)/i);
    if (hm) for (let i = 0; i <= +hm[1]; i++) nodeSet.add(String(i));
    for (const line of lines) {
      const m = line.match(/edge from node (\d+) to node (\d+) with capacity (\d+)/i);
      if (m) { nodeSet.add(m[1]); nodeSet.add(m[2]); edges.push({ source: m[1], target: m[2], label: m[3] }); }
    }
    nodes = [...nodeSet].sort((a, b) => +a - +b).map(id => ({ id, label: id }));

  } else if (/edge between node/i.test(text)) {
    // Undirected graph with weights
    const nodeSet = new Set();
    const hm = text.match(/nodes numbered from \d+ to (\d+)/i);
    if (hm) for (let i = 0; i <= +hm[1]; i++) nodeSet.add(String(i));
    for (const line of lines) {
      const m = line.match(/edge between node (\d+) and node (\d+) with weight (\d+)/i);
      if (m) { nodeSet.add(m[1]); nodeSet.add(m[2]); edges.push({ source: m[1], target: m[2], label: m[3] }); }
    }
    nodes = [...nodeSet].sort((a, b) => +a - +b).map(id => ({ id, label: id }));

  } else {
    // Standard undirected: parse (i,j) pairs
    const nodeSet = new Set();
    const hm = text.match(/nodes are numbered from \d+ to (\d+)/i) ||
               text.match(/numbered from \d+ to (\d+)/i);
    if (hm) for (let i = 0; i <= +hm[1]; i++) nodeSet.add(String(i));
    for (const [, u, v] of text.matchAll(/\((\d+),(\d+)\)/g)) {
      nodeSet.add(u); nodeSet.add(v);
      edges.push({ source: u, target: v });
    }
    nodes = [...nodeSet].sort((a, b) => +a - +b).map(id => ({ id, label: id }));
  }

  return { nodes, edges, directed, graphType };
}

/* ── Graph force-directed layout ────────────────────────── */
function forceLayout(nodes, edges, W, H) {
  if (nodes.length === 0) return {};
  const pad = 40, n = nodes.length;
  const pos = {};
  // Circular initialisation
  const R = Math.min(W, H) / 2 - pad;
  nodes.forEach((nd, i) => {
    const a = (2 * Math.PI * i / n) - Math.PI / 2;
    pos[nd.id] = { x: W / 2 + R * Math.cos(a), y: H / 2 + R * Math.sin(a) };
  });
  if (n < 2) return pos;

  const k = Math.sqrt(W * H / n) * 0.75;
  // Fewer iterations for large/dense graphs to keep it snappy
  const iters = Math.max(40, Math.min(120, Math.floor(5000 / (n * n + edges.length + 1))));
  let temp = k;

  for (let it = 0; it < iters; it++) {
    const disp = {};
    nodes.forEach(nd => { disp[nd.id] = { x: 0, y: 0 }; });

    // Repulsion (all pairs)
    for (let i = 0; i < n; i++) {
      for (let j = i + 1; j < n; j++) {
        const ai = nodes[i].id, bi = nodes[j].id;
        const dx = pos[ai].x - pos[bi].x, dy = pos[ai].y - pos[bi].y;
        const d2 = dx * dx + dy * dy + 0.001, d = Math.sqrt(d2);
        const f = k * k / d2;
        disp[ai].x += dx * f / d; disp[ai].y += dy * f / d;
        disp[bi].x -= dx * f / d; disp[bi].y -= dy * f / d;
      }
    }

    // Attraction (edges)
    for (const e of edges) {
      const s = pos[e.source], t = pos[e.target];
      if (!s || !t || e.source === e.target) continue;
      const dx = t.x - s.x, dy = t.y - s.y;
      const d = Math.sqrt(dx * dx + dy * dy) + 0.001;
      const f = d / k;
      disp[e.source].x += dx * f; disp[e.source].y += dy * f;
      disp[e.target].x -= dx * f; disp[e.target].y -= dy * f;
    }

    // Apply displacements with temperature clamping
    for (const nd of nodes) {
      const p = pos[nd.id], dp = disp[nd.id];
      const mag = Math.sqrt(dp.x * dp.x + dp.y * dp.y) + 0.001;
      const move = Math.min(mag, temp);
      p.x = Math.max(pad, Math.min(W - pad, p.x + (dp.x / mag) * move));
      p.y = Math.max(pad, Math.min(H - pad, p.y + (dp.y / mag) * move));
    }
    temp *= 0.92;
  }
  return pos;
}

/* ── Graph → SVG string ─────────────────────────────────── */
function graphToSVG(text) {
  const { nodes, edges, directed, graphType } = parseGraphText(text);
  if (nodes.length === 0 && edges.length === 0) return null;

  const W = 560;
  // Taller canvas for bipartite so nodes aren't cramped
  const H = graphType === 'bipartite'
    ? Math.max(220, Math.min(480,
        Math.max(
          nodes.filter(n => n.group === 'applicant').length,
          nodes.filter(n => n.group === 'job').length,
          1
        ) * 34 + 60))
    : 340;

  let pos = {};

  if (graphType === 'bipartite') {
    const apps = nodes.filter(n => n.group === 'applicant');
    const jobs = nodes.filter(n => n.group === 'job');
    const lx = 90, rx = W - 90, vPad = 30;
    const aStep = apps.length > 1 ? (H - 2 * vPad) / (apps.length - 1) : 0;
    const jStep = jobs.length > 1 ? (H - 2 * vPad) / (jobs.length - 1) : 0;
    apps.forEach((n, i) => { pos[n.id] = { x: lx, y: vPad + i * aStep }; });
    jobs.forEach((n, i) => { pos[n.id] = { x: rx, y: vPad + i * jStep }; });
  } else {
    pos = forceLayout(nodes, edges, W, H);
  }

  const nr = Math.max(9, Math.min(15, Math.floor(180 / Math.max(nodes.length, 1))));
  const fs = nr < 12 ? 8 : 10;

  let svg = `<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg" class="graph-svg">`;

  if (directed) {
    svg += `<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5"
      markerWidth="5" markerHeight="5" orient="auto">
      <path d="M0,0 L10,5 L0,10 z" fill="#64748b"/>
    </marker></defs>`;
  }

  // Edges
  for (const e of edges) {
    const s = pos[e.source], t = pos[e.target];
    if (!s || !t || e.source === e.target) continue;
    const dx = t.x - s.x, dy = t.y - s.y;
    const d = Math.sqrt(dx * dx + dy * dy) || 1;
    const ux = dx / d, uy = dy / d;
    const arrowOffset = directed ? nr + 4 : nr;
    const x1 = (s.x + ux * nr).toFixed(1),      y1 = (s.y + uy * nr).toFixed(1);
    const x2 = (t.x - ux * arrowOffset).toFixed(1), y2 = (t.y - uy * arrowOffset).toFixed(1);
    const markerAttr = directed ? ' marker-end="url(#arr)"' : '';
    svg += `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}"
      stroke="#475569" stroke-width="1.2" stroke-opacity="0.75"${markerAttr}/>`;
    if (e.label) {
      const mx = ((s.x + t.x) / 2).toFixed(1), my = ((s.y + t.y) / 2 - 4).toFixed(1);
      svg += `<text x="${mx}" y="${my}" font-size="8" fill="#94a3b8" text-anchor="middle">${escapeHtml(e.label)}</text>`;
    }
  }

  // Nodes
  for (const nd of nodes) {
    const p = pos[nd.id];
    if (!p) continue;
    const fill = nd.group === 'applicant' ? '#0ea5e9'
               : nd.group === 'job'       ? '#22c55e'
               : '#3b82f6';
    svg += `<circle cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="${nr}"
      fill="${fill}" stroke="#1e293b" stroke-width="1.5"/>`;
    svg += `<text x="${p.x.toFixed(1)}" y="${p.y.toFixed(1)}" font-size="${fs}"
      fill="#f8fafc" text-anchor="middle" dominant-baseline="central" font-weight="600">${escapeHtml(nd.label)}</text>`;
  }

  // Bipartite legend
  if (graphType === 'bipartite') {
    svg += `<circle cx="14" cy="12" r="5" fill="#0ea5e9" stroke="#1e293b" stroke-width="1"/>
    <text x="23" y="12" font-size="9" fill="#94a3b8" dominant-baseline="central">Applicants</text>
    <circle cx="14" cy="26" r="5" fill="#22c55e" stroke="#1e293b" stroke-width="1"/>
    <text x="23" y="26" font-size="9" fill="#94a3b8" dominant-baseline="central">Jobs</text>`;
  }

  // Stats footer
  svg += `<text x="${W - 6}" y="${H - 5}" font-size="9" fill="#475569" text-anchor="end"
    >${nodes.length} nodes · ${edges.length} edges</text>`;

  svg += `</svg>`;
  return `<div class="graph-viz">${svg}</div>`;
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
  if (item.modality === "document") {
    if (item.media_content) {
      return `<div class="document-block">${escapeHtml(item.media_content)}</div>`;
    }
    return `<div class="media-missing">Document not available for <code>${escapeHtml(item.key)}</code></div>`;
  }
  if (item.modality === "graph") {
    if (item.media_content) {
      return graphToSVG(item.media_content)
        || `<div class="media-missing">Could not render graph for <code>${escapeHtml(item.key)}</code></div>`;
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
  const isAudio    = item.modality === "audio";
  const isText     = item.modality === "code" || item.modality === "table";
  const isGraph    = item.modality === "graph";
  const isDocument = item.modality === "document";
  const mediaClass = isAudio    ? "card-media card-media-audio"
                   : isText     ? "card-media card-media-text"
                   : isGraph    ? "card-media card-media-graph"
                   : isDocument ? "card-media card-media-document"
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
