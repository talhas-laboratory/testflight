const SVG_NS = "http://www.w3.org/2000/svg";
const canvas = document.querySelector("#world-canvas");
const viewport = document.querySelector("#viewport");
const atmosphereLayer = document.querySelector("#atmosphere");
const edgeLayer = document.querySelector("#edges");
const nodeLayer = document.querySelector("#nodes");

const state = {
  data: null,
  mode: "world",
  systemId: null,
  selectedId: null,
  scale: 1,
  tx: 0,
  ty: 0,
  dragging: false,
  dragMoved: false,
  dragStart: null,
  dossiers: new Map(),
};

const SYSTEM_COLORS = {
  identity: "#f25d86",
  expression: "#8070d8",
  offering: "#e9dc52",
  experience: "#8dbbd1",
  perception: "#e796ae",
  governance: "#66736a",
  environment: "#5b9c70",
  event: "#a293d6",
};

function svg(tag, attrs = {}, text = null) {
  const element = document.createElementNS(SVG_NS, tag);
  Object.entries(attrs).forEach(([key, value]) => element.setAttribute(key, String(value)));
  if (text !== null) element.textContent = text;
  return element;
}

function truncate(value, limit = 31) {
  if (!value) return "Untitled record";
  return value.length > limit ? `${value.slice(0, limit - 1)}…` : value;
}

function systemById(systemId) {
  return state.data.systems.find((item) => item.id === systemId);
}

function nodeById(nodeId) {
  return state.data.nodes.find((item) => item.id === nodeId);
}

function directRelations(nodeId) {
  return state.data.edges.filter((edge) => edge.source === nodeId || edge.target === nodeId);
}

function setTransform() {
  viewport.setAttribute("transform", `translate(${state.tx} ${state.ty}) scale(${state.scale})`);
}

function resetTransform() {
  state.scale = 1;
  state.tx = 0;
  state.ty = 0;
  setTransform();
}

function addAtmosphere(x, y, radius, color, fine = false) {
  atmosphereLayer.append(
    svg("circle", {
      class: `field-halo${fine ? " fine" : ""}`,
      cx: x,
      cy: y,
      r: radius,
      fill: color,
    }),
  );
}

function curvePath(a, b, bend = 0.12) {
  const mx = (a.x + b.x) / 2;
  const my = (a.y + b.y) / 2;
  const dx = b.x - a.x;
  const dy = b.y - a.y;
  return `M ${a.x} ${a.y} Q ${mx - dy * bend} ${my + dx * bend} ${b.x} ${b.y}`;
}

function registerNode(group, nodeId, onActivate) {
  group.dataset.node = nodeId;
  group.setAttribute("role", "button");
  group.setAttribute("tabindex", "0");
  group.addEventListener("click", (event) => {
    event.stopPropagation();
    onActivate();
  });
  group.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      onActivate();
    }
  });
}

function renderBrandNode(position) {
  const group = svg("g", {
    class: "graph-node brand-node",
    transform: `translate(${position.x} ${position.y})`,
    "aria-label": "Biotic, Brand world root",
  });
  group.append(svg("circle", { class: "node-shape", r: 152 }));
  group.append(svg("text", { class: "brand-subtitle", y: -48 }, "BRAND WORLD"));
  group.append(svg("text", { class: "brand-title", y: 17 }, "Biotic"));
  group.append(
    svg(
      "text",
      { class: "brand-subtitle", y: 58 },
      `${state.data.nodes.length} RECORDS · ${state.data.edges.length} RELATIONS`,
    ),
  );
  registerNode(group, state.data.meta.brandId, () => openCard(state.data.meta.brandId));
  nodeLayer.append(group);
}

function renderSystemNode(system, position) {
  const group = svg("g", {
    class: "graph-node system-node",
    transform: `translate(${position.x} ${position.y})`,
    "data-system": system.id,
    "aria-label": `${system.label}, ${system.recordCount} records. Enter subsystem.`,
  });
  group.append(svg("rect", { class: "node-shape", x: -112, y: -53, width: 224, height: 106 }));
  group.append(svg("text", { class: "node-kicker", x: -92, y: -28 }, String(system.index).padStart(2, "0")));
  group.append(svg("text", { class: "node-label", x: -92, y: 6 }, system.label));
  group.append(svg("text", { class: "node-count", x: -92, y: 32 }, `${system.recordCount} RECORDS`));
  registerNode(group, `system:${system.id}`, () => focusSystem(system.id));
  nodeLayer.append(group);
}

function renderWorld() {
  const center = { x: 800, y: 500 };
  const positions = new Map();
  state.data.systems.forEach((system, index) => {
    const angle = -Math.PI / 2 + (index * Math.PI * 2) / state.data.systems.length;
    positions.set(system.id, {
      x: center.x + Math.cos(angle) * 550,
      y: center.y + Math.sin(angle) * 340,
    });
  });

  addAtmosphere(center.x, center.y, 205, "#f5f4ef");
  state.data.systems.forEach((system) => {
    const position = positions.get(system.id);
    addAtmosphere(position.x, position.y, 95, SYSTEM_COLORS[system.id], true);
    edgeLayer.append(
      svg("path", { class: "world-edge secondary", d: curvePath(center, position, 0.04) }),
    );
  });

  const nodeSystem = new Map(state.data.nodes.map((node) => [node.id, node.system]));
  const pairCounts = new Map();
  state.data.edges.forEach((edge) => {
    const sourceSystem = nodeSystem.get(edge.source);
    const targetSystem = nodeSystem.get(edge.target);
    if (!positions.has(sourceSystem) || !positions.has(targetSystem) || sourceSystem === targetSystem) return;
    const pair = [sourceSystem, targetSystem].sort().join("::");
    pairCounts.set(pair, (pairCounts.get(pair) || 0) + 1);
  });
  pairCounts.forEach((count, pair) => {
    const [sourceSystem, targetSystem] = pair.split("::");
    edgeLayer.append(
      svg("path", {
        class: "world-edge",
        d: curvePath(positions.get(sourceSystem), positions.get(targetSystem), 0.08),
        opacity: Math.min(0.28 + count * 0.07, 0.72),
      }),
    );
  });

  renderBrandNode(center);
  state.data.systems.forEach((system) => renderSystemNode(system, positions.get(system.id)));
  document.querySelector("#canvas-caption").textContent =
    "Eight canonical ontology systems · select one to reveal its subsystem";
  document.querySelector("#system-crumb").hidden = true;
  document.querySelector("#world-crumb").setAttribute("aria-current", "page");
}

function radialPositions(items, center, inner = false) {
  const positions = new Map();
  const firstRingCount = Math.min(items.length, inner ? 8 : 10);
  items.forEach((item, index) => {
    const firstRing = index < firstRingCount;
    const ringItems = firstRing ? firstRingCount : items.length - firstRingCount;
    const ringIndex = firstRing ? index : index - firstRingCount;
    const angle = -Math.PI / 2 + (ringIndex * Math.PI * 2) / Math.max(ringItems, 1);
    const rx = firstRing ? 350 : 585;
    const ry = firstRing ? 245 : 365;
    positions.set(item.id, {
      x: center.x + Math.cos(angle) * rx,
      y: center.y + Math.sin(angle) * ry,
    });
  });
  return positions;
}

function renderRecordNode(node, position, external = false) {
  const selected = node.id === state.selectedId;
  const group = svg("g", {
    class: `graph-node record-node${external ? " external" : ""}${selected ? " selected" : ""}`,
    transform: `translate(${position.x} ${position.y})`,
    "data-system": node.system,
    "aria-label": `${node.label}. ${node.semanticType}. ${node.status}.`,
  });
  const radius = external ? 42 : 58;
  group.append(svg("circle", { class: "node-shape", r: radius }));
  group.append(svg("text", { class: "node-kicker", y: external ? -7 : -18 }, truncate(node.semanticType, 18)));
  group.append(svg("text", { class: "node-label", y: external ? 12 : 4 }, truncate(node.label, external ? 18 : 24)));
  if (!external) group.append(svg("text", { class: "node-count", y: 27 }, node.status.toUpperCase()));
  registerNode(group, node.id, () => openCard(node.id));
  nodeLayer.append(group);
}

function renderSystemCore(system, center) {
  const group = svg("g", {
    class: "graph-node system-core",
    transform: `translate(${center.x} ${center.y})`,
    "data-system": system.id,
    "aria-label": `${system.label} subsystem. Return to whole world.`,
  });
  group.append(svg("circle", { class: "node-shape", r: 130 }));
  group.append(svg("text", { class: "node-kicker", y: -49 }, `${String(system.index).padStart(2, "0")} / SYSTEM`));
  group.append(svg("text", { class: "node-label", y: 9 }, system.label));
  group.append(svg("text", { class: "node-count", y: 43 }, `${system.recordCount} PROJECTED RECORDS`));
  registerNode(group, `system:${system.id}`, returnToWorld);
  nodeLayer.append(group);
}

function renderSystem() {
  const system = systemById(state.systemId);
  const center = { x: 800, y: 500 };
  const localNodes = state.data.nodes.filter((node) => node.system === state.systemId);
  const localIds = new Set(localNodes.map((node) => node.id));
  const externalIds = new Set();
  state.data.edges.forEach((edge) => {
    if (localIds.has(edge.source) && !localIds.has(edge.target) && edge.target !== state.data.meta.brandId) externalIds.add(edge.target);
    if (localIds.has(edge.target) && !localIds.has(edge.source) && edge.source !== state.data.meta.brandId) externalIds.add(edge.source);
  });
  const externalNodes = [...externalIds].map(nodeById).filter(Boolean).slice(0, 8);
  const localPositions = radialPositions(localNodes, center, true);
  const externalPositions = new Map();
  externalNodes.forEach((node, index) => {
    const angle =
      -Math.PI / 2 + ((index + 0.5) * Math.PI * 2) / Math.max(externalNodes.length, 1);
    externalPositions.set(node.id, {
      x: center.x + Math.cos(angle) * 700,
      y: center.y + Math.sin(angle) * 420,
    });
  });
  const positions = new Map([...localPositions, ...externalPositions]);

  addAtmosphere(center.x, center.y, 210, SYSTEM_COLORS[system.id]);
  localNodes.forEach((node) => {
    const position = localPositions.get(node.id);
    edgeLayer.append(
      svg("path", {
        class: "registration-line",
        d: curvePath(center, position, 0.03),
      }),
    );
  });

  state.data.edges.forEach((edge) => {
    let source = positions.get(edge.source);
    let target = positions.get(edge.target);
    if (edge.source === state.data.meta.brandId && localIds.has(edge.target)) source = center;
    if (edge.target === state.data.meta.brandId && localIds.has(edge.source)) target = center;
    if (!source || !target) return;
    const active = state.selectedId && (edge.source === state.selectedId || edge.target === state.selectedId);
    const path = svg("path", {
      class: `local-edge${active ? " active" : ""}${edge.status === "held" ? " held" : ""}`,
      d: curvePath(source, target, 0.07),
    });
    edgeLayer.append(path);
    if (active) {
      edgeLayer.append(
        svg(
          "text",
          { class: "edge-label", x: (source.x + target.x) / 2, y: (source.y + target.y) / 2 - 8 },
          edge.relation,
        ),
      );
    }
  });

  renderSystemCore(system, center);
  localNodes.forEach((node) => renderRecordNode(node, localPositions.get(node.id)));
  externalNodes.forEach((node) => renderRecordNode(node, externalPositions.get(node.id), true));
  document.querySelector("#canvas-caption").textContent = state.selectedId
    ? `${directRelations(state.selectedId).length} direct relations highlighted · detail remains off-canvas`
    : `${system.label} subsystem · ${localNodes.length} local records · ${externalNodes.length} boundary portals`;
  const systemCrumb = document.querySelector("#system-crumb");
  systemCrumb.hidden = false;
  systemCrumb.textContent = system.label;
  systemCrumb.setAttribute("aria-current", "page");
  document.querySelector("#world-crumb").removeAttribute("aria-current");
}

function renderGraph() {
  atmosphereLayer.replaceChildren();
  edgeLayer.replaceChildren();
  nodeLayer.replaceChildren();
  if (state.mode === "world") renderWorld();
  else renderSystem();
}

function focusSystem(systemId) {
  state.mode = "system";
  state.systemId = systemId;
  state.selectedId = null;
  closeCard();
  resetTransform();
  renderGraph();
}

function returnToWorld() {
  state.mode = "world";
  state.systemId = null;
  state.selectedId = null;
  closeCard();
  resetTransform();
  renderGraph();
}

function createMetaRow(term, value) {
  const fragment = document.createDocumentFragment();
  const dt = document.createElement("dt");
  const dd = document.createElement("dd");
  dt.textContent = term;
  dd.textContent = value || "Not recorded";
  fragment.append(dt, dd);
  return fragment;
}

function humanize(value) {
  return String(value || "").replaceAll("_", " ");
}

function formatScopeValue(value) {
  if (Array.isArray(value)) return value.length ? value.join(" · ") : "Not recorded";
  if (value && typeof value === "object") {
    const parts = Object.entries(value).map(([key, item]) => `${humanize(key)}: ${item}`);
    return parts.length ? parts.join(" · ") : "Not recorded";
  }
  return value || "Not recorded";
}

function appendTextSection(panel, title, text, emptyText = "Not recorded") {
  const section = document.createElement("section");
  section.className = "grounding-section";
  const heading = document.createElement("h3");
  heading.textContent = title;
  const copy = document.createElement("p");
  copy.textContent = text || emptyText;
  if (!text) copy.className = "empty-copy";
  section.append(heading, copy);
  panel.append(section);
}

function appendListSection(panel, title, values, emptyText = "Not recorded") {
  const section = document.createElement("section");
  section.className = "grounding-section";
  const heading = document.createElement("h3");
  heading.textContent = title;
  section.append(heading);
  if (!values?.length) {
    const empty = document.createElement("p");
    empty.className = "empty-copy";
    empty.textContent = emptyText;
    section.append(empty);
  } else {
    const list = document.createElement("ul");
    list.className = "grounding-list";
    values.forEach((value) => {
      const item = document.createElement("li");
      item.textContent = humanize(value);
      list.append(item);
    });
    section.append(list);
  }
  panel.append(section);
}

function renderGroundingPanel(node, dossier = null) {
  const panel = document.querySelector("#panel-grounding");
  panel.replaceChildren();
  const grounding = dossier?.grounding || node.grounding || {};

  appendTextSection(panel, "Assertion", grounding.assertion);
  appendTextSection(
    panel,
    "Interpretation",
    grounding.interpretation,
    "No separate interpretation is recorded.",
  );
  appendListSection(panel, "Permitted use", grounding.permittedUses, "No explicit use rule is recorded.");

  const scopeSection = document.createElement("section");
  scopeSection.className = "grounding-section";
  const heading = document.createElement("h3");
  heading.textContent = "Scope";
  const list = document.createElement("dl");
  const scope = grounding.scope || {};
  list.append(
    createMetaRow("Record ID", node.id),
    createMetaRow("System", systemById(scope.system || node.system)?.label || scope.system || node.system),
    createMetaRow("Type", scope.semanticType || node.semanticType),
    createMetaRow("Contexts", formatScopeValue(scope.contextIds)),
    createMetaRow("Valid time", formatScopeValue(scope.validTime)),
    createMetaRow("Source locus", scope.sourceLocus || node.sourcePath),
  );
  scopeSection.append(heading, list);
  panel.append(scopeSection);
  appendListSection(panel, "Constraints", grounding.constraints, "No explicit constraint is recorded.");
  appendListSection(panel, "Unknowns", grounding.unknowns, "No explicit unknown is recorded.");
}

function renderContextPanel(node, dossier = null) {
  const panel = document.querySelector("#panel-context");
  panel.replaceChildren();
  const relations = dossier?.context?.relations || directRelations(node.id).map((relation) => {
    const incoming = relation.target === node.id;
    const peerId = incoming ? relation.source : relation.target;
    const peer = nodeById(peerId);
    return {
      ...relation,
      direction: incoming ? "incoming" : "outgoing",
      peer: {
        id: peerId,
        label: peer?.label || peerId,
        semanticType: peer?.semanticType || "unknown",
        system: peer?.system || "unknown",
      },
    };
  });
  if (!relations.length) {
    const empty = document.createElement("p");
    empty.className = "empty-copy";
    empty.textContent = "No direct semantic relationship is recorded for this item.";
    panel.append(empty);
  } else {
    const heading = document.createElement("h3");
    heading.textContent = "Semantic neighbourhood";
    const list = document.createElement("ul");
    list.className = "relation-list";
    relations.forEach((relation) => {
      const li = document.createElement("li");
      const strong = document.createElement("strong");
      strong.textContent = `${relation.direction === "incoming" ? "←" : "→"} ${relation.relation}`;
      const label = document.createElement("span");
      label.textContent = relation.peer.label;
      const meta = document.createElement("small");
      meta.textContent = `${relation.peer.semanticType} / ${relation.peer.system} · ${relation.status} · ${relation.epistemicStatus}`;
      li.append(strong, label, meta);
      list.append(li);
    });
    panel.append(heading, list);
  }

  const contextIds = dossier?.context?.contextIds || node.grounding?.scope?.contextIds || [];
  appendListSection(
    panel,
    "Context identifiers",
    contextIds,
    "No explicit context identifier is attached.",
  );
}

function sourceLink(source, fullText) {
  if (!fullText?.url) return null;
  const link = document.createElement("a");
  link.className = "source-action";
  link.href = fullText.url;
  link.target = "_blank";
  link.rel = "noreferrer";
  link.textContent = "Open live full text ↗";
  link.setAttribute("aria-label", `Open live full text for ${source.title || source.id}`);
  return link;
}

function renderSourcesPanel(node, dossier = null, error = "") {
  const panel = document.querySelector("#panel-sources");
  panel.replaceChildren();
  if (error) {
    const empty = document.createElement("p");
    empty.className = "dossier-error";
    empty.textContent = error;
    panel.append(empty);
    return;
  }

  if (!dossier) {
    const loading = document.createElement("p");
    loading.className = "empty-copy";
    loading.textContent = "Compiling bounded source context…";
    panel.append(loading);
    return;
  }

  const policy = document.createElement("div");
  policy.className = "content-policy";
  const policyTitle = document.createElement("strong");
  policyTitle.textContent = "Content availability";
  const policyCopy = document.createElement("p");
  const fullTextStored = [true, "permitted", "retained", "required"].includes(
    dossier.contentPolicy?.full_text_storage,
  );
  policyCopy.textContent = fullTextStored
    ? "The retained source body is available in this workspace."
    : "Full source bodies are not stored in this workspace. The ontology retains bounded excerpts and paraphrased findings; use the live original for full text.";
  policy.append(policyTitle, policyCopy);
  panel.append(policy);

  if (!dossier.sources.length) {
    const empty = document.createElement("p");
    empty.className = "empty-copy";
    empty.textContent = "No direct source dossier is recorded. Absence is not proof of completeness.";
    panel.append(empty);
    return;
  }

  dossier.sources.forEach((item, index) => {
    const source = item.source;
    const article = document.createElement("article");
    article.className = "source-dossier";
    const head = document.createElement("header");
    const marker = document.createElement("span");
    marker.textContent = `SOURCE ${String(index + 1).padStart(2, "0")}`;
    const title = document.createElement("h3");
    title.textContent = source.title || source.id;
    const link = sourceLink(source, item.fullText);
    head.append(marker, title);
    if (link) head.append(link);
    article.append(head);

    const meta = document.createElement("dl");
    meta.append(
      createMetaRow("Source ID", source.id),
      createMetaRow("Type", humanize(source.source_type)),
      createMetaRow("Authority", source.authority_tier),
      createMetaRow("Evidence tier", source.evidence_tier),
      createMetaRow("Valid time", formatScopeValue(source.valid_time)),
      createMetaRow("Permitted use", humanize(source.permitted_use)),
    );
    article.append(meta);

    item.evidence.forEach((evidence) => {
      const evidenceBlock = document.createElement("section");
      evidenceBlock.className = "evidence-block";
      const label = document.createElement("strong");
      label.textContent = "Bounded source excerpt";
      const quote = document.createElement("blockquote");
      quote.textContent = evidence.evidence_excerpt || "No excerpt retained.";
      const evidenceMeta = document.createElement("small");
      evidenceMeta.textContent = `${evidence.id} · ${humanize(evidence.binding)} · ${evidence.actor_authority || "authority not recorded"} · ${evidence.epistemic_status || "status unknown"}`;
      evidenceBlock.append(label, quote, evidenceMeta);
      if (evidence.paraphrased_findings?.length) {
        appendListSection(evidenceBlock, "Paraphrased findings", evidence.paraphrased_findings);
      }
      if (evidence.limitations?.length) {
        appendListSection(evidenceBlock, "Evidence limitations", evidence.limitations);
      }
      article.append(evidenceBlock);
    });
    panel.append(article);
  });
}

async function loadRecordDossier(node) {
  if (state.dossiers.has(node.id)) return state.dossiers.get(node.id);
  const response = await fetch(`/api/records/${encodeURIComponent(node.id)}`, {
    headers: { Accept: "application/json" },
  });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || `Dossier request failed (${response.status})`);
  state.dossiers.set(node.id, payload);
  return payload;
}

function openCard(nodeId) {
  const node = nodeById(nodeId);
  if (!node) return;
  state.selectedId = nodeId;
  document.querySelector("#specimen-index").textContent = `${node.semanticType} / ${node.system}`;
  document.querySelector("#specimen-title").textContent = node.label;
  const status = document.querySelector("#specimen-status");
  status.replaceChildren();
  [
    ["record", node.status],
    ["epistemic", node.epistemicStatus],
  ].forEach(([label, value]) => {
    const span = document.createElement("span");
    span.textContent = `${label}: ${value}`;
    status.append(span);
  });
  renderGroundingPanel(node);
  renderContextPanel(node);
  renderSourcesPanel(node);
  document.querySelectorAll(".specimen-tabs button").forEach((button) => {
    button.setAttribute("aria-pressed", String(button.dataset.panel === "grounding"));
  });
  document.querySelectorAll(".specimen-panel").forEach((panel) => {
    panel.hidden = panel.id !== "panel-grounding";
  });
  const card = document.querySelector("#specimen-card");
  card.classList.remove("is-dossier");
  card.hidden = false;
  if (state.mode === "system") renderGraph();
  loadRecordDossier(node)
    .then((dossier) => {
      if (state.selectedId !== node.id) return;
      renderGroundingPanel(node, dossier);
      renderContextPanel(node, dossier);
      renderSourcesPanel(node, dossier);
    })
    .catch((error) => {
      if (state.selectedId !== node.id) return;
      renderSourcesPanel(node, null, `Source context unavailable: ${error.message}`);
    });
}

function closeCard() {
  const card = document.querySelector("#specimen-card");
  card.hidden = true;
  card.classList.remove("is-dossier");
  if (state.selectedId) {
    state.selectedId = null;
    if (state.data && state.mode === "system") renderGraph();
  }
}

function bindControls() {
  document.querySelector("#world-crumb").addEventListener("click", returnToWorld);
  document.querySelector("#system-crumb").addEventListener("click", () => {
    state.selectedId = null;
    closeCard();
    renderGraph();
  });
  document.querySelector("#close-card").addEventListener("click", closeCard);
  document.querySelector("#zoom-in").addEventListener("click", () => {
    state.scale = Math.min(2.25, state.scale * 1.16);
    setTransform();
  });
  document.querySelector("#zoom-out").addEventListener("click", () => {
    state.scale = Math.max(0.55, state.scale / 1.16);
    setTransform();
  });
  document.querySelector("#reset-view").addEventListener("click", resetTransform);
  document.querySelectorAll(".specimen-tabs button").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll(".specimen-tabs button").forEach((peer) => {
        peer.setAttribute("aria-pressed", String(peer === button));
      });
      document.querySelectorAll(".specimen-panel").forEach((panel) => {
        panel.hidden = panel.id !== `panel-${button.dataset.panel}`;
      });
      document
        .querySelector("#specimen-card")
        .classList.toggle("is-dossier", button.dataset.panel !== "grounding");
    });
  });

  canvas.addEventListener("wheel", (event) => {
    event.preventDefault();
    const rect = canvas.getBoundingClientRect();
    const x = ((event.clientX - rect.left) / rect.width) * 1600;
    const y = ((event.clientY - rect.top) / rect.height) * 1000;
    const nextScale = Math.max(0.55, Math.min(2.25, state.scale * (event.deltaY < 0 ? 1.1 : 0.9)));
    const ratio = nextScale / state.scale;
    state.tx = x - (x - state.tx) * ratio;
    state.ty = y - (y - state.ty) * ratio;
    state.scale = nextScale;
    setTransform();
  }, { passive: false });

  canvas.addEventListener("pointerdown", (event) => {
    if (event.target.closest?.("[data-node]")) return;
    state.dragging = true;
    state.dragMoved = false;
    state.dragStart = { x: event.clientX, y: event.clientY, tx: state.tx, ty: state.ty };
    canvas.classList.add("is-dragging");
    canvas.setPointerCapture(event.pointerId);
  });
  canvas.addEventListener("pointermove", (event) => {
    if (!state.dragging) return;
    if (Math.abs(event.clientX - state.dragStart.x) + Math.abs(event.clientY - state.dragStart.y) > 3) {
      state.dragMoved = true;
    }
    const rect = canvas.getBoundingClientRect();
    state.tx = state.dragStart.tx + ((event.clientX - state.dragStart.x) / rect.width) * 1600;
    state.ty = state.dragStart.ty + ((event.clientY - state.dragStart.y) / rect.height) * 1000;
    setTransform();
  });
  canvas.addEventListener("pointerup", (event) => {
    if (!state.dragging) return;
    state.dragging = false;
    canvas.classList.remove("is-dragging");
    canvas.releasePointerCapture(event.pointerId);
    if (!state.dragMoved) closeCard();
  });
}

async function initialise() {
  bindControls();
  try {
    const response = await fetch("/api/world");
    const payload = await response.json();
    if (!response.ok || payload.error) throw new Error(payload.error || `Request failed: ${response.status}`);
    if (!Array.isArray(payload.systems) || payload.systems.length !== 8) {
      throw new Error("The projection did not provide the eight canonical Brand systems.");
    }
    state.data = payload;
    document.querySelector("#world-scope").textContent = payload.meta.workspaceId;
    document.querySelector("#world-version").textContent = `Ontology ${payload.meta.ontologyVersion}`;
    document.querySelector("#projection-count").textContent = `${payload.nodes.length} records / ${payload.edges.length} relations`;
    document.querySelector("#projection-fingerprint").textContent = payload.meta.fingerprint;
    document.querySelector("#loading-state").hidden = true;
    renderGraph();
  } catch (error) {
    document.querySelector("#loading-state").hidden = true;
    const errorState = document.querySelector("#error-state");
    errorState.hidden = false;
    errorState.textContent = `Unable to compile this Brand world: ${error.message}`;
  }
}

initialise();
