let snapshot;
let graphZoom = 1;
let activeGraphMode = 'brand';
let graphScene = { mode: 'brand', nodes: [], edges: [] };
let graphCanvasBound = false;
let atlasDepth = 0;
let atlasDomain = 'public-core';
let atlasSelectedId = '';
const $ = (selector) => document.querySelector(selector);
const plural = (count, word) => `${count} ${count === 1 ? word : (word === 'entity' ? 'entities' : `${word}s`)}`;
const escapeHtml = (value = '') => String(value).replace(/[&<>'"]/g, (char) => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', "'":'&#39;', '"':'&quot;' }[char]));

async function initialise() {
  snapshot = await fetch('/api/snapshot').then((response) => response.json());
  atlasSelectedId = snapshot.workspace.brandId;
  const coverage = snapshot.atlas?.coverage;
  $('#provenance').innerHTML = `Read-only workspace projection<br>${plural(coverage?.nodeCount || snapshot.entities.length, 'record')} · ${plural(coverage?.edgeCount || snapshot.relationships.length, 'relationship')}<br><span>${escapeHtml(snapshot.provenance.sourceHash.slice(0, 12))}</span>`;
  for (const context of snapshot.contexts) $('#context-filter').insertAdjacentHTML('beforeend', `<option value="${context.id}">${escapeHtml(context.purpose || context.id)}</option>`);
  populateWorldControls();
  renderAtlas(); renderMap(); renderGraph(); renderVisualLanguage(); renderLearningLoop(); bindEvents();
}

function populateWorldControls() {
  const model = snapshot.worldModel;
  const worldContexts = new Set([
    ...(model?.states || []).map((record) => record.context_id),
    ...(model?.perspectives || []).map((record) => record.context_id),
    ...(model?.relationship_frames || []).map((record) => record.context_id),
  ]);
  const contexts = snapshot.contexts.filter((context) => worldContexts.has(context.id));
  $('#agent-context').innerHTML = contexts.length
    ? contexts.map((context) => `<option value="${escapeHtml(context.id)}">${escapeHtml(context.purpose || context.id)}</option>`).join('')
    : '<option value="">No world-model context available</option>';
  $('#agent-branch').innerHTML = (model?.branches || []).map((branch) => `<option value="${escapeHtml(branch.branch_id)}">${escapeHtml(branch.label)} · ${escapeHtml(branch.branch_kind)}</option>`).join('') || '<option value="">No branch available</option>';
  $('#agent-perspective').insertAdjacentHTML('beforeend', (model?.perspectives || []).map((perspective) => `<option value="${escapeHtml(perspective.perspective_id)}">${escapeHtml(perspective.perspective_type_id.replace('world://ontology/brand/perspective/', ''))}</option>`).join(''));
  const membership = contexts.find((context) => context.id === 'CTX-NIKE-DIGITAL-MEMBERSHIP-CURRENT');
  if (membership) $('#agent-context').value = membership.id;
  const discovery = (model?.branches || []).find((branch) => branch.branch_id === 'BR-NIKE-MEMBER-DISCOVERY-LENS-001');
  if (discovery) $('#agent-branch').value = discovery.branch_id;
  const memberPerspective = (model?.perspectives || []).find((perspective) => perspective.perspective_id === 'PERS-NIKE-MEMBER-PROSPECTIVE-001');
  if (memberPerspective) $('#agent-perspective').value = memberPerspective.perspective_id;
}

function filters() { return { search: $('#search').value.toLowerCase().trim(), context: $('#context-filter').value, perspective: $('#perspective-filter').value }; }
function shown(entity) {
  const {search,context,perspective} = filters();
  const content = `${entity.label} ${entity.description} ${entity.id}`.toLowerCase();
  return (!search || content.includes(search)) && (!context || (entity.context_ids || []).includes(context)) && (!perspective || entity.perspective === perspective);
}

function atlasNode(id) { return snapshot.atlas.nodes.find((item) => item.id === id); }
function atlasEdgesFor(id) { return snapshot.atlas.edges.filter((edge) => edge.sourceId === id || edge.targetId === id); }
function atlasDomainRecord(id) { return snapshot.atlas.domains.find((item) => item.id === id); }
function atlasStatusClass(status = '') {
  const normalized = String(status).toLowerCase();
  if (normalized.includes('held') || normalized.includes('partial') || normalized.includes('hypoth')) return 'held';
  if (normalized.includes('accepted') || normalized.includes('observed') || normalized.includes('reported') || normalized.includes('active')) return 'observed';
  return 'proposed';
}
function atlasFilteredNodes() {
  const query = $('#search').value.toLowerCase().trim();
  const nodes = snapshot.atlas.nodes.filter((node) => atlasDomain === 'all' || node.domain === atlasDomain);
  if (!query) return nodes;
  return nodes.filter((node) => `${node.label} ${node.id} ${node.recordType} ${node.description} ${JSON.stringify(node.payload)}`.toLowerCase().includes(query));
}
function setAtlasDepth(depth) {
  atlasDepth = Number(depth);
  document.querySelectorAll('[data-atlas-depth]').forEach((button) => button.setAttribute('aria-pressed', String(Number(button.dataset.atlasDepth) === atlasDepth)));
  renderAtlas();
}
function setAtlasDomain(domain, descend = false) {
  atlasDomain = domain;
  if (descend && atlasDepth < 2) atlasDepth = 2;
  const first = atlasFilteredNodes()[0];
  if (first && !atlasFilteredNodes().some((node) => node.id === atlasSelectedId)) atlasSelectedId = first.id;
  renderAtlas();
}
function selectAtlasNode(id, descend = true) {
  atlasSelectedId = id;
  const node = atlasNode(id);
  if (node) atlasDomain = node.domain;
  if (descend && atlasDepth < 3) atlasDepth = 3;
  renderAtlas();
}
function atlasDomainNav() {
  const query = $('#search').value.toLowerCase().trim();
  const countFor = (id) => snapshot.atlas.nodes.filter((node) => {
    if (node.domain !== id) return false;
    return !query || `${node.label} ${node.id} ${node.recordType} ${node.description} ${JSON.stringify(node.payload)}`.toLowerCase().includes(query);
  }).length;
  const allCount = snapshot.atlas.domains.reduce((total, domain) => total + countFor(domain.id), 0);
  $('#atlas-domain-nav').innerHTML = `<button type="button" data-atlas-domain="all" aria-pressed="${atlasDomain === 'all'}"><span>All records</span><b>${allCount}</b></button>${snapshot.atlas.domains.map((domain) => `<button type="button" data-atlas-domain="${escapeHtml(domain.id)}" aria-pressed="${atlasDomain === domain.id}"><span>${escapeHtml(domain.label)}</span><b>${countFor(domain.id)}</b></button>`).join('')}`;
  document.querySelectorAll('[data-atlas-domain]').forEach((button) => button.addEventListener('click', () => setAtlasDomain(button.dataset.atlasDomain, true)));
}
function worldOverview() {
  const domains = snapshot.atlas.domains;
  return `<div class="atlas-world" role="img" aria-label="Biotic world surrounded by ${domains.length} bounded semantic domains">
    <div class="atlas-orbit atlas-orbit-a"></div><div class="atlas-orbit atlas-orbit-b"></div><div class="atlas-crosshair x"></div><div class="atlas-crosshair y"></div>
    <button type="button" class="atlas-nucleus" data-atlas-node="${escapeHtml(snapshot.workspace.brandId)}"><small>WORLD</small><strong>Biotic</strong><span>${snapshot.atlas.coverage.nodeCount} records<br>${snapshot.atlas.coverage.edgeCount} relations</span></button>
    ${domains.map((domain, index) => { const angle = (index / domains.length) * Math.PI * 2 - Math.PI / 2; const left = 50 + Math.cos(angle) * 39; const top = 50 + Math.sin(angle) * 41; return `<button type="button" class="atlas-orbit-node" style="left:${left}%;top:${top}%" data-atlas-domain-jump="${escapeHtml(domain.id)}"><span>${String(index + 1).padStart(2, '0')}</span><strong>${escapeHtml(domain.label)}</strong><small>${domain.nodeCount} / ${domain.edgeCount}</small></button>`; }).join('')}
  </div>`;
}
function domainOverview() {
  return `<div class="atlas-planes">${snapshot.atlas.domains.map((domain, index) => `<button type="button" class="atlas-plane" data-atlas-domain-jump="${escapeHtml(domain.id)}" style="--plane:${index}"><span class="atlas-plane-index">0${index + 1}</span><span><strong>${escapeHtml(domain.label)}</strong><small>${escapeHtml(domain.description)}</small></span><span class="atlas-plane-count">${domain.nodeCount}<small>records</small>${domain.edgeCount}<small>relations</small></span></button>`).join('')}</div>`;
}
function recordOverview() {
  const nodes = atlasFilteredNodes();
  const domain = atlasDomain === 'all' ? {label:'All world records', description:'Cross-container search view. Boundaries remain visible on every record.'} : atlasDomainRecord(atlasDomain);
  return `<div class="atlas-record-head"><div><span class="eyebrow">${escapeHtml(domain?.label || atlasDomain)}</span><p>${escapeHtml(domain?.description || '')}</p></div><strong>${nodes.length}</strong></div><div class="atlas-record-grid">${nodes.length ? nodes.map((node) => `<button type="button" class="atlas-record ${atlasStatusClass(node.status)}" data-atlas-node="${escapeHtml(node.id)}"><span class="atlas-record-type">${escapeHtml(node.recordType)}</span><strong>${escapeHtml(node.label)}</strong><small>${escapeHtml(node.status)} · ${escapeHtml(node.domain)}</small></button>`).join('') : '<div class="atlas-empty"><strong>No matching records</strong><span>Change the search or choose another domain.</span></div>'}</div>`;
}
function relationOverview() {
  const selected = atlasNode(atlasSelectedId) || atlasFilteredNodes()[0] || atlasNode(snapshot.workspace.brandId);
  if (!selected) return '<div class="atlas-empty"><strong>No record selected</strong></div>';
  const relations = atlasEdgesFor(selected.id);
  const neighbors = new Map();
  relations.forEach((edge) => { const other = atlasNode(edge.sourceId === selected.id ? edge.targetId : edge.sourceId); if (other) neighbors.set(other.id, other); });
  return `<div class="relation-field"><div class="relation-focus ${atlasStatusClass(selected.status)}"><span>${escapeHtml(selected.recordType)}</span><strong>${escapeHtml(selected.label)}</strong><small>${escapeHtml(selected.id)}</small></div><div class="relation-list">${relations.length ? relations.map((edge) => { const outgoing = edge.sourceId === selected.id; const otherId = outgoing ? edge.targetId : edge.sourceId; const other = atlasNode(otherId); return `<button type="button" class="relation-row ${atlasStatusClass(edge.status)}" data-atlas-node="${escapeHtml(otherId)}"><span class="relation-direction">${outgoing ? 'OUT' : 'IN'}</span><span class="relation-name">${escapeHtml(edge.relationshipType.replaceAll('_', ' '))}<small>${escapeHtml(edge.status)} · ${escapeHtml(edge.domain)}</small></span><strong>${escapeHtml(other?.label || otherId)}</strong></button>`; }).join('') : '<div class="atlas-empty"><strong>No explicit relationships</strong><span>The record remains available as an isolated source-backed item.</span></div>'}</div><p class="relation-caption">${relations.length} direct connections · ${neighbors.size} neighboring records · no inferred path expansion</p></div>`;
}
function evidenceOverview() {
  const selected = atlasNode(atlasSelectedId) || atlasNode(snapshot.workspace.brandId);
  const direct = atlasEdgesFor(selected.id);
  const evidenceEdges = direct.filter((edge) => edge.relationshipType === 'supported_by' || edge.relationshipType === 'derived_from');
  const evidenceNodes = evidenceEdges.map((edge) => atlasNode(edge.sourceId === selected.id ? edge.targetId : edge.sourceId)).filter(Boolean);
  const limitations = selected.payload?.limitations || selected.payload?.gaps || selected.payload?.uncertainty;
  const limitationList = Array.isArray(limitations) ? limitations : (limitations ? [limitations] : []);
  return `<div class="evidence-trace"><article><span class="trace-index">01 / RECORD</span><strong>${escapeHtml(selected.label)}</strong><small>${escapeHtml(selected.id)}</small><p>${escapeHtml(selected.description || 'No prose description is recorded for this item.')}</p></article><i aria-hidden="true">↓</i><article><span class="trace-index">02 / SOURCE LOCUS</span><strong>${escapeHtml(selected.sourcePath)}</strong><small>${escapeHtml(selected.domain)} · ${escapeHtml(selected.status)}</small><p>The atlas points back to this canonical workspace record; it does not replace it.</p></article><i aria-hidden="true">↓</i><article class="trace-evidence"><span class="trace-index">03 / DIRECT EVIDENCE</span>${evidenceNodes.length ? evidenceNodes.map((node) => `<button type="button" data-atlas-node="${escapeHtml(node.id)}"><strong>${escapeHtml(node.label)}</strong><small>${escapeHtml(node.id)}</small></button>`).join('') : '<p>No direct evidence edge is recorded at this layer.</p>'}</article><article class="trace-limits"><span class="trace-index">04 / LIMITS</span>${limitationList.length ? `<ul>${limitationList.map((item) => `<li>${escapeHtml(item)}</li>`).join('')}</ul>` : '<p>No explicit limitation is recorded on this item. Absence is not proof of completeness.</p>'}</article></div>`;
}
function atlasSelection() {
  const selected = atlasNode(atlasSelectedId);
  if (!selected) { $('#atlas-selection').innerHTML = '<p>Select a record to inspect it.</p>'; return; }
  const payloadEntries = Object.entries(selected.payload || {}).filter(([key]) => !['description','summary','limitations'].includes(key)).slice(0, 12);
  $('#atlas-selection').innerHTML = `<p class="eyebrow">Selected record</p><h3>${escapeHtml(selected.label)}</h3><div class="metadata"><span class="pill">${escapeHtml(selected.recordType)}</span><span class="pill">${escapeHtml(selected.domain)}</span><span class="pill ${atlasStatusClass(selected.status) === 'held' ? 'warn' : ''}">${escapeHtml(selected.status)}</span></div><p>${escapeHtml(selected.description || 'This structural record has no separate prose description.')}</p><p class="mono">${escapeHtml(selected.id)}<br>${escapeHtml(selected.sourcePath)}</p><details><summary>Inspect source fields</summary><dl>${payloadEntries.map(([key,value]) => `<div><dt>${escapeHtml(key)}</dt><dd>${escapeHtml(typeof value === 'string' ? value : JSON.stringify(value))}</dd></div>`).join('')}</dl></details>`;
}
function renderAtlas() {
  if (!snapshot?.atlas) return;
  document.querySelectorAll('[data-atlas-depth]').forEach((button) => button.setAttribute('aria-pressed', String(Number(button.dataset.atlasDepth) === atlasDepth)));
  const coverage = snapshot.atlas.coverage;
  $('#atlas-summary').innerHTML = `${coverage.complete ? 'Every indexed structured record is connected.' : `${coverage.danglingEdgeIds.length} unresolved connections.`}<br><span>${coverage.nodeCount} records across ${snapshot.atlas.domains.length} bounded domains; ${coverage.edgeCount} directed relationships.</span>`;
  const renderers = [worldOverview, domainOverview, recordOverview, relationOverview, evidenceOverview];
  $('#atlas-canvas').innerHTML = renderers[atlasDepth]();
  $('#atlas-status').textContent = `${String(atlasDepth).padStart(2, '0')} / ${['whole world','semantic domains','source records','direct relations','evidence trace'][atlasDepth]} · ${atlasDomain === 'all' ? 'all boundaries' : atlasDomain}`;
  atlasDomainNav(); atlasSelection();
  document.querySelectorAll('[data-atlas-domain-jump]').forEach((button) => button.addEventListener('click', () => setAtlasDomain(button.dataset.atlasDomainJump, true)));
  document.querySelectorAll('[data-atlas-node]').forEach((button) => button.addEventListener('click', () => selectAtlasNode(button.dataset.atlasNode)));
}
function renderMap() {
  const types = Object.keys(snapshot.ontology.typeCounts);
  const visible = snapshot.entities.filter(shown);
  $('#map-summary').textContent = `${plural(visible.length, 'record')} currently match your filters. Select one to see its exact evidence, scope and immediate relationships.`;
  $('#ontology-map').innerHTML = types.map((type) => {
    const entities = visible.filter((entity) => entity.entity_type === type);
    return `<article class="type-card" data-count="${entities.length}"><header><h3>${escapeHtml(type)}</h3><span>${String(entities.length).padStart(2, '0')}</span></header><div class="entity-list">${entities.length ? entities.map((entity) => `<button class="entity" data-entity="${entity.id}">${escapeHtml(entity.label)}</button>`).join('') : '<p class="empty-list">No matching records.</p>'}</div></article>`;
  }).join('');
  document.querySelectorAll('[data-entity]').forEach((button) => button.addEventListener('click', () => inspectEntity(button.dataset.entity)));
}

const graphPalette = { brand: '#c5f04a', identity: '#ff7356', expression: '#f4ce78', offering: '#bce3d1', experience: '#9fc9ff', perception: '#e8a9cd', governance: '#d8bcff', environment: '#dfe3d7', event: '#e7ddcd', 'visual-system': '#c5f04a', palette: '#f4ce78', typography: '#d8bcff', 'graphic-device': '#ffb15e', 'product-form': '#9fc9ff', 'image-direction': '#bce3d1', 'social-image-direction': '#e8a9cd', 'creative-principle': '#ff7356', 'copy-system': '#c5f04a', 'voice-pattern': '#d8bcff', 'brand-claim': '#f4ce78', 'ingredient-claim': '#ffb15e', 'product-attribute': '#bce3d1', 'product-boundary': '#9fc9ff', 'claim-boundary': '#dfe3d7', 'message-module': '#e8a9cd', 'observed-phrase': '#f4ce78', 'audience-system': '#c5f04a', 'intended-audience-signal': '#d8bcff', 'problem-context': '#ffb15e', 'use-context': '#bce3d1', 'expression-signal': '#e8a9cd', 'self-reported-signal': '#f4ce78', 'information-need': '#9fc9ff', 'audience-hypothesis': '#ff7356', 'evidence-gap': '#dfe3d7', unknown: '#f7f5ed' };
const supplementalGraphs = {
  visual: { key: 'visualGraph', label: 'visual-language', inspector: 'Visual-language' },
  copy: { key: 'copyClaimsGraph', label: 'copy-and-claims', inspector: 'Copy-and-claims' },
  audience: { key: 'audienceGraph', label: 'audience-evidence', inspector: 'Audience-evidence' },
};
function graphNodePosition(index, count, width, height) {
  if (!index) return { x: width / 2, y: height / 2 };
  const angle = ((index - 1) / Math.max(count - 1, 1)) * Math.PI * 2 - Math.PI / 2;
  const radiusX = Math.min(width * .39, 380); const radiusY = Math.min(height * .34, 195);
  return { x: width / 2 + Math.cos(angle) * radiusX, y: height / 2 + Math.sin(angle) * radiusY };
}
function graphVisible() {
  if (activeGraphMode !== 'brand') {
    const graph = snapshot[supplementalGraphs[activeGraphMode].key];
    return graph?.available ? { nodes: graph.nodes, edges: graph.edges } : { nodes: [], edges: [] };
  }
  const visibleEntityIds = new Set(snapshot.entities.filter(shown).map((entity) => entity.id));
  const root = snapshot.graph.nodes.find((node) => node.kind === 'brand-root');
  const nodeIds = new Set([root.id, ...visibleEntityIds]);
  const { context } = filters();
  const nodes = snapshot.graph.nodes.filter((node) => nodeIds.has(node.id));
  const edges = snapshot.graph.edges.filter((edge) => nodeIds.has(edge.sourceId) && nodeIds.has(edge.targetId) && (!context || edge.contextIds.includes(context)));
  return { nodes, edges };
}
function renderGraph() {
  const { nodes, edges } = graphVisible();
  const canvas = $('#graph-canvas'); const bounds = canvas.getBoundingClientRect();
  const width = Math.max(680, Math.round(bounds.width || 960)); const height = Math.max(450, Math.round(bounds.height || 570)); const radius = 29 * graphZoom;
  const pixelRatio = window.devicePixelRatio || 1;
  canvas.width = Math.round(width * pixelRatio); canvas.height = Math.round(height * pixelRatio);
  const context = canvas.getContext('2d'); context.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0); context.clearRect(0, 0, width, height);
  const positions = new Map(nodes.map((node, index) => [node.id, graphNodePosition(index, nodes.length, width, height)]));
  const isRoot = (node) => String(node.kind || '').endsWith('-root');
  graphScene = { mode: activeGraphMode, nodes: nodes.map((node) => ({ ...node, ...positions.get(node.id), radius: isRoot(node) ? 42 * graphZoom : radius })), edges };
  const drawLabel = (text, x, y, font, color, maxWidth = 160) => {
    context.font = font; context.textAlign = 'center'; context.textBaseline = 'middle';
    const words = text.split(' '); const lines = []; let line = '';
    words.forEach((word) => { const next = line ? `${line} ${word}` : word; if (context.measureText(next).width > maxWidth && line) { lines.push(line); line = word; } else line = next; });
    if (line) lines.push(line); context.lineWidth = 4; context.strokeStyle = '#f0eee5'; context.fillStyle = color;
    lines.slice(0, 2).forEach((item, index) => { const lineY = y + (index - (Math.min(lines.length, 2) - 1) / 2) * 13; context.strokeText(item, x, lineY); context.fillText(item, x, lineY); });
  };
  edges.forEach((edge) => {
    const source = positions.get(edge.sourceId); const target = positions.get(edge.targetId); if (!source || !target) return '';
    const dx = target.x - source.x; const dy = target.y - source.y; const distance = Math.hypot(dx, dy) || 1;
    const sourceRadius = edge.sourceId === nodes[0]?.id ? 45 * graphZoom : radius + 3; const targetRadius = edge.targetId === nodes[0]?.id ? 47 * graphZoom : radius + 5;
    const startX = source.x + (dx / distance) * sourceRadius; const startY = source.y + (dy / distance) * sourceRadius;
    const endX = target.x - (dx / distance) * targetRadius; const endY = target.y - (dy / distance) * targetRadius;
    const held = edge.status === 'held' || edge.epistemicStatus === 'inferred';
    const labelX = (startX + endX) / 2; const labelY = (startY + endY) / 2 - 6;
    context.save(); context.beginPath(); context.setLineDash(held ? [7, 6] : []); context.strokeStyle = held ? '#ff7356' : '#12221d'; context.globalAlpha = .72; context.lineWidth = 1.7; context.moveTo(startX, startY); context.lineTo(endX, endY); context.stroke(); context.setLineDash([]); context.globalAlpha = 1;
    const angle = Math.atan2(endY - startY, endX - startX); context.fillStyle = held ? '#ff7356' : '#12221d'; context.translate(endX, endY); context.rotate(angle); context.beginPath(); context.moveTo(0, 0); context.lineTo(-8, -4); context.lineTo(-8, 4); context.closePath(); context.fill(); context.restore();
    drawLabel(edge.relationshipType.replaceAll('_', ' '), labelX, labelY, "500 10px 'DM Mono'", held ? '#b33d2d' : '#5d675f', 110);
  });
  graphScene.nodes.forEach((node) => {
    context.beginPath(); context.arc(node.x, node.y, node.radius, 0, Math.PI * 2); context.fillStyle = graphPalette[node.entityType] || graphPalette.unknown; context.fill(); context.lineWidth = 1.5; context.strokeStyle = '#12221d'; context.stroke();
    drawLabel(node.label, node.x, node.y + node.radius + 18, isRoot(node) ? '700 13px Fraunces' : '600 11px Manrope', '#12221d', 145);
  });
  const supplemental = activeGraphMode !== 'brand'; const graphLabel = supplemental ? supplementalGraphs[activeGraphMode].label : 'relationship';
  $('#graph-summary').textContent = supplemental
    ? `${Math.max(nodes.length - 1, 0)} ${graphLabel} ${Math.max(nodes.length - 1, 0) === 1 ? 'entity' : 'entities'} and ${plural(edges.length, 'relationship')} from bounded public research. Dashed edges are held inferences or evidence gaps.`
    : `${plural(nodes.length - 1, 'entity')} and ${plural(edges.length, 'relationship')} match the active filters. Dashed edges remain hypotheses, not conclusions.`;
  $('#graph-description').textContent = `${supplemental ? `${graphLabel} graph` : 'Relationship graph'} with ${Math.max(nodes.length - 1, 0)} entity nodes and ${edges.length} relationship edges. Select any node or edge to inspect its evidence and status.`;
  updateGraphZoomReadout();
  if (!graphCanvasBound) { bindGraphCanvas(canvas); graphCanvasBound = true; }
}

function graphPoint(event) { const bounds = $('#graph-canvas').getBoundingClientRect(); return { x: event.clientX - bounds.left, y: event.clientY - bounds.top }; }
function distanceToSegment(point, start, end) { const dx = end.x - start.x; const dy = end.y - start.y; const length = dx * dx + dy * dy || 1; const t = Math.max(0, Math.min(1, ((point.x - start.x) * dx + (point.y - start.y) * dy) / length)); return Math.hypot(point.x - (start.x + t * dx), point.y - (start.y + t * dy)); }
function graphSelection(point) {
  const node = graphScene.nodes.slice().reverse().find((item) => Math.hypot(point.x - item.x, point.y - item.y) <= item.radius + 8); if (node) return { kind: 'node', id: node.id };
  const edge = graphScene.edges.find((item) => { const start = graphScene.nodes.find((node) => node.id === item.sourceId); const end = graphScene.nodes.find((node) => node.id === item.targetId); return start && end && distanceToSegment(point, start, end) < 9; });
  return edge ? { kind: 'edge', id: edge.id } : null;
}
function bindGraphCanvas(canvas) {
  canvas.addEventListener('click', (event) => { const selected = graphSelection(graphPoint(event)); if (!selected) return; if (graphScene.mode !== 'brand') { if (selected.kind === 'node') inspectSupplementalGraphNode(selected.id); else inspectSupplementalGraphRelationship(selected.id); } else if (selected.kind === 'node') selected.id === snapshot.workspace.brandId ? inspectBrandRoot() : inspectEntity(selected.id); else inspectRelationship(selected.id); });
  canvas.addEventListener('mousemove', (event) => { canvas.style.cursor = graphSelection(graphPoint(event)) ? 'pointer' : 'grab'; });
  canvas.addEventListener('keydown', (event) => { if (event.key === '+' || event.key === '=') setGraphZoom(graphZoom + .2); if (event.key === '-') setGraphZoom(graphZoom - .2); });
}

function updateGraphZoomReadout() {
  const readout = $('[data-graph-action="reset"]');
  if (readout) readout.textContent = `${Math.round(graphZoom * 100)}%`;
}
function setGraphZoom(next) {
  graphZoom = Math.min(2.5, Math.max(.6, Math.round(next * 100) / 100));
  renderGraph();
  updateGraphZoomReadout();
}
function bindGraphControls() {
  $('#relationship-graph').addEventListener('wheel', (event) => {
    event.preventDefault(); setGraphZoom(graphZoom + (event.deltaY < 0 ? .12 : -.12));
  }, { passive: false });
  document.querySelectorAll('[data-graph-action]').forEach((button) => button.addEventListener('click', async () => {
    const action = button.dataset.graphAction;
    if (action === 'zoom-in') setGraphZoom(graphZoom + .2);
    if (action === 'zoom-out') setGraphZoom(graphZoom - .2);
    if (action === 'reset') setGraphZoom(1);
    if (action === 'fullscreen') {
      if (document.fullscreenElement) await document.exitFullscreen();
      else await $('#relationship-graph').requestFullscreen();
    }
  }));
  document.addEventListener('fullscreenchange', () => {
    const button = $('[data-graph-action="fullscreen"]');
    if (button) button.innerHTML = document.fullscreenElement ? 'Exit full screen <span>×</span>' : 'Full screen <span>↗</span>';
    renderGraph();
  });
}

function inspectBrandRoot() {
  $('#inspector-content').innerHTML = `<p class="eyebrow">Structural graph anchor</p><h2>${escapeHtml(snapshot.workspace.label)}</h2><div class="metadata"><span class="pill">brand root</span><span class="pill">structural</span></div><p>This node exists only to make brand-to-entity relationships legible. It is not a proposed entity record or independent evidence claim.</p><div class="record"><h4>Stable ID</h4><p class="mono">${escapeHtml(snapshot.workspace.brandId)}</p></div>`;
  $('#inspector').classList.add('open');
}

function formatVisualSources(sourceUrls = []) {
  return sourceUrls.length ? `<ul>${sourceUrls.map((url) => `<li><a href="${escapeHtml(url)}" target="_blank" rel="noreferrer">${escapeHtml(url)} ↗</a></li>`).join('')}</ul>` : '<p>No source URL recorded.</p>';
}
function supplementalGraph() { return snapshot[supplementalGraphs[graphScene.mode]?.key]; }
function inspectSupplementalGraphNode(id) {
  const node = supplementalGraph()?.nodes.find((item) => item.id === id); if (!node) return;
  const held = node.status === 'held';
  const root = String(node.kind || '').endsWith('-root'); const label = supplementalGraphs[graphScene.mode].inspector;
  $('#inspector-content').innerHTML = `<p class="eyebrow">${root ? `${label} graph anchor` : `${label} entity`}</p><h2>${escapeHtml(node.label)}</h2><div class="metadata"><span class="pill">${escapeHtml(node.entityType)}</span><span class="pill">${escapeHtml(node.epistemicStatus)}</span><span class="pill ${held ? 'warn' : ''}">${escapeHtml(node.status)}</span></div><p>${escapeHtml(node.summary)}</p><div class="record"><h4>Stable ID</h4><p class="mono">${escapeHtml(node.id)}</p></div>${held ? '<div class="record"><h4>Interpretation boundary</h4><p>This is deliberately held: it is a proposal, evidence boundary, or hypothesis—not a cleared brand instruction or validated customer fact.</p></div>' : ''}<div class="record"><h4>Observed sources</h4>${formatVisualSources(node.sourceUrls)}</div>`;
  $('#inspector').classList.add('open');
}
function inspectSupplementalGraphRelationship(id) {
  const relationship = supplementalGraph()?.edges.find((item) => item.id === id); if (!relationship) return;
  const held = relationship.status === 'held';
  $('#inspector-content').innerHTML = `<p class="eyebrow">${escapeHtml(supplementalGraphs[graphScene.mode].inspector)} relationship</p><h2>${escapeHtml(relationship.relationshipType.replaceAll('_', ' '))}</h2><div class="metadata"><span class="pill ${held ? 'warn' : ''}">${escapeHtml(relationship.status)}</span><span class="pill">${escapeHtml(relationship.epistemicStatus)}</span></div><div class="record"><h4>Direction</h4><p class="mono">${escapeHtml(relationship.sourceId)} → ${escapeHtml(relationship.targetId)}</p></div>${held ? '<div class="record"><h4>Interpretation boundary</h4><p>This line is a held inference, proposal, or documented evidence gap; it is not an established creative instruction or validated audience fact.</p></div>' : '<p>This relationship is a direct, bounded public observation or brand-authored statement.</p>'}`;
  $('#inspector').classList.add('open');
}

function inspectRelationship(id) {
  const relationship = snapshot.relationships.find((item) => item.id === id); if (!relationship) return;
  const evidence = (relationship.evidence_ids || []).map((eid) => snapshot.evidence.find((item) => item.id === eid)).filter(Boolean);
  const held = relationship.status === 'held';
  $('#inspector-content').innerHTML = `<p class="eyebrow">Directed relationship</p><h2>${escapeHtml(relationship.relationship_type.replaceAll('_', ' '))}</h2><div class="metadata"><span class="pill ${held ? 'warn' : ''}">${escapeHtml(relationship.status)}</span><span class="pill">${escapeHtml(relationship.epistemic_status)}</span><span class="pill">${escapeHtml(relationship.perspective)}</span></div><p>${escapeHtml(relationship.assertion)}</p><div class="record"><h4>Direction</h4><p class="mono">${escapeHtml(relationship.source_id)} → ${escapeHtml(relationship.target_id)}</p></div>${held ? '<div class="record"><h4>Interpretation boundary</h4><p>This edge is deliberately held. It is a testable model relation, not an established causal claim.</p></div>' : ''}<div class="record"><h4>Evidence bundle</h4>${evidence.length ? evidence.map((item) => formatEvidence(item, '')).join('') : '<p>No evidence linked.</p>'}</div>${relationship.limitations?.length ? `<div class="record"><h4>Limitations</h4><ul>${relationship.limitations.map((item) => `<li>${escapeHtml(item)}</li>`).join('')}</ul></div>` : ''}`;
  $('#inspector').classList.add('open');
  document.querySelectorAll('#inspector [data-entity]').forEach((button) => button.addEventListener('click', () => inspectEntity(button.dataset.entity)));
}

function sourceForEvidence(evidence) { return snapshot.sources.find((source) => source.id === evidence.source_id); }
function evidenceCoverage(evidenceId, activeEntityId) {
  return snapshot.entities.filter((entity) => entity.id !== activeEntityId && (entity.evidence_ids || []).includes(evidenceId));
}
function formatEvidence(item, activeEntityId) {
  const source = sourceForEvidence(item);
  const coverage = evidenceCoverage(item.id, activeEntityId);
  const findings = item.paraphrased_findings || [];
  return `<article class="evidence-card">
    <div class="evidence-card__top"><p><strong>${escapeHtml(item.id)}</strong></p><span class="pill">${escapeHtml(item.perspective)}</span></div>
    <p class="excerpt">“${escapeHtml(item.evidence_excerpt)}”</p>
    ${findings.length ? `<div class="findings"><h5>What this source establishes</h5><ul>${findings.map((finding) => `<li>${escapeHtml(finding)}</li>`).join('')}</ul></div>` : ''}
    <div class="source-facts">
      <p class="mono">${escapeHtml(item.actor_authority)} · ${escapeHtml(item.epistemic_status)}</p>
      ${source ? `<p><strong>${escapeHtml(source.publisher)}</strong> · ${escapeHtml(source.source_type)} · authority ${escapeHtml(source.authority_tier)}</p><p class="mono">Valid time: ${escapeHtml(source.valid_time)} · ${escapeHtml(source.status)}</p><p><a href="${escapeHtml(source.canonical_url)}" target="_blank" rel="noreferrer">Read the original source: ${escapeHtml(source.title)} ↗</a></p>` : ''}
    </div>
    ${coverage.length ? `<div class="coverage"><h5>This evidence also supports</h5>${coverage.map((entity) => `<button class="text-link" data-entity="${entity.id}">${escapeHtml(entity.label)} <span>↗</span></button>`).join('')}</div>` : ''}
    ${item.limitations?.length ? `<div class="limitations"><h5>What it does not establish</h5><ul>${item.limitations.map((limit) => `<li>${escapeHtml(limit)}</li>`).join('')}</ul></div>` : ''}
  </article>`;
}
function inspectEntity(id) {
  const entity = snapshot.entities.find((item) => item.id === id); if (!entity) return;
  const evidence = (entity.evidence_ids || []).map((eid) => snapshot.evidence.find((item) => item.id === eid)).filter(Boolean);
  const contexts = (entity.context_ids || []).map((cid) => snapshot.contexts.find((item) => item.id === cid)).filter(Boolean);
  const relationships = snapshot.relationships.filter((item) => item.source_id === id || item.target_id === id);
  $('#inspector-content').innerHTML = `<p class="eyebrow">Exact canonical entity</p><h2>${escapeHtml(entity.label)}</h2><div class="metadata"><span class="pill">${escapeHtml(entity.entity_type)}</span><span class="pill">${escapeHtml(entity.perspective)}</span><span class="pill">${escapeHtml(entity.epistemic_status)}</span><span class="pill ${entity.status === 'held' ? 'warn' : ''}">${escapeHtml(entity.status)}</span></div><p>${escapeHtml(entity.description)}</p><div class="record"><h4>Stable ID</h4><p class="mono">${escapeHtml(entity.id)}</p></div><div class="record"><h4>Applicable context</h4>${contexts.length ? `<ul>${contexts.map((item) => `<li><strong>${escapeHtml(item.purpose)}</strong><br><span class="mono">${escapeHtml(item.id)} · ${escapeHtml(JSON.stringify(item.valid_time || {}))}</span></li>`).join('')}</ul>` : '<p>None recorded.</p>'}</div><div class="record"><h4>Evidence bundle</h4><p class="record-intro">The entity is one atomic claim. Its evidence bundle shows the fuller documented finding, source details, limits, and other claims supported by the same evidence.</p>${evidence.length ? evidence.map((item) => formatEvidence(item, entity.id)).join('') : '<p>No evidence linked.</p>'}</div><div class="record"><h4>Direct relationships</h4>${relationships.length ? `<ul>${relationships.map((item) => `<li><strong>${escapeHtml(item.relationship_type)}</strong> — ${escapeHtml(item.assertion)}${item.status === 'held' ? ' <span class="pill warn">held hypothesis</span>' : ''}</li>`).join('')}</ul>` : '<p>No direct relationships.</p>'}</div>${entity.limitations?.length ? `<div class="record"><h4>Limitations</h4><ul>${entity.limitations.map((item) => `<li>${escapeHtml(item)}</li>`).join('')}</ul></div>` : ''}`;
  $('#inspector').classList.add('open');
  document.querySelectorAll('#inspector [data-entity]').forEach((button) => button.addEventListener('click', () => inspectEntity(button.dataset.entity)));
}

function renderVisualLanguage() {
  const visual = snapshot.visualLanguage;
  $('#visual-language').innerHTML = visual.profiles.map((profile) => {
    const revisions = visual.revisions.filter((revision) => revision.profileId === profile.id);
    return `<article class="profile"><p class="eyebrow">${escapeHtml(profile.status)}</p><h3>${escapeHtml(profile.label)}</h3><p>${escapeHtml(profile.description)}</p>${revisions.map((revision) => `<div class="revision"><h4>${escapeHtml(revision.id)} · ${escapeHtml(revision.validFrom || 'undated')}</h4>${revision.modules.map((module) => { const reference = visual.references.find((item) => item.id === module.referenceId); return `<button class="module" data-reference="${module.referenceId}">${escapeHtml(module.slot)} → ${escapeHtml(reference?.label || module.referenceId)}</button>`; }).join('')}<p class="mono">Gaps: ${escapeHtml((revision.gaps || []).join(', ') || 'none recorded')}</p></div>`).join('')}</article>`;
  }).join('');
  document.querySelectorAll('[data-reference]').forEach((button) => button.addEventListener('click', () => inspectReference(button.dataset.reference)));
}

function inspectReference(id) {
  const reference = snapshot.visualLanguage.references.find((item) => item.id === id); if (!reference) return;
  $('#inspector-content').innerHTML = `<p class="eyebrow">Visual reference</p><h2>${escapeHtml(reference.label)}</h2><div class="metadata"><span class="pill">${escapeHtml(reference.kind)}</span><span class="pill">${escapeHtml(reference.authority)}</span><span class="pill">${escapeHtml(reference.status)}</span></div><div class="record"><h4>Observed payload</h4><pre class="mono">${escapeHtml(JSON.stringify(reference.payload, null, 2))}</pre></div><div class="record"><h4>Scope and time</h4><p class="mono">valid from ${escapeHtml(reference.validFrom || 'not recorded')} · last verified ${escapeHtml(reference.lastVerifiedAt)}</p></div><div class="record"><h4>Rights</h4><p>${escapeHtml(reference.rights.permittedUse)}; generation: ${escapeHtml(reference.rights.generationUse)}</p></div><div class="record"><h4>Limitations</h4><ul>${reference.limitations.map((item) => `<li>${escapeHtml(item)}</li>`).join('')}</ul></div>`;
  $('#inspector').classList.add('open');
}

function renderLearningLoop() {
  const model = snapshot.worldModel;
  if (!model?.available) { $('#learning-loop').innerHTML = '<article class="learning-card warning"><h3>No learning model available</h3><p>This workspace has not yet defined hypotheses or experiments.</p></article>'; return; }
  const hypotheses = model.hypotheses || [];
  const experiments = model.experiments || [];
  const outcomes = model.observed_outcomes || [];
  const updates = model.learning_updates || [];
  const experimentFor = (hypothesis) => experiments.filter((experiment) => (experiment.hypothesis_ids || []).includes(hypothesis.hypothesis_id));
  $('#learning-loop').innerHTML = `<article class="learning-card"><p class="eyebrow">1. Hypotheses</p><h3>${plural(hypotheses.length, 'hypothesis')}</h3>${hypotheses.length ? hypotheses.map((hypothesis) => `<div class="learning-record"><span class="pill">${escapeHtml(hypothesis.status)}</span><strong>${escapeHtml(hypothesis.proposition)}</strong><p>${escapeHtml(hypothesis.mechanism_description)}</p><p class="mono">Falsified when: ${escapeHtml(hypothesis.falsification_conditions.join(' · '))}</p></div>`).join('') : '<p>None recorded.</p>'}</article><article class="learning-card"><p class="eyebrow">2. Experiments</p><h3>${plural(experiments.length, 'draft')}</h3>${hypotheses.flatMap((hypothesis) => experimentFor(hypothesis)).map((experiment) => `<div class="learning-record"><span class="pill">${escapeHtml(experiment.status)}</span><strong>${escapeHtml(experiment.intervention)}</strong><p>Control: ${escapeHtml(experiment.comparison_or_control)}</p><p class="mono">Metrics: ${escapeHtml(experiment.metric_ids.join(', '))}</p></div>`).join('') || '<p>No experiment is linked yet.</p>'}</article><article class="learning-card warning"><p class="eyebrow">3. Observed outcomes</p><h3>${plural(outcomes.length, 'result')}</h3>${outcomes.length ? outcomes.map((outcome) => `<div class="learning-record"><span class="pill">${escapeHtml(outcome.status)}</span><strong>${escapeHtml(outcome.outcome_id)}</strong><p class="mono">${escapeHtml(JSON.stringify(outcome.metric_values))}</p></div>`).join('') : '<p>No measured outcome is recorded. This is correct: the draft experiment must not create a result.</p>'}</article><article class="learning-card warning"><p class="eyebrow">4. Reviewed learning</p><h3>${plural(updates.length, 'update')}</h3>${updates.length ? updates.map((update) => `<div class="learning-record"><span class="pill">${escapeHtml(update.disposition)}</span><strong>${escapeHtml(update.rationale)}</strong></div>`).join('') : '<p>No strategy or creative record has been updated automatically.</p>'}</article>`;
}

function renderAgentResult(result) {
  if (result.status === 'no_hit') { $('#agent-result').innerHTML = `<div class="packet-card warning"><h3>No matching workflow</h3><p>${escapeHtml(result.reason)}</p></div>`; return; }
  const planned = result.planning.selected;
  const view = result.agentPacket.worldView;
  const worldView = view.status === 'no_hit'
    ? `<article class="packet-card warning"><p class="eyebrow">2. Semantic world view</p><h3>Not available</h3><p>${escapeHtml(view.message)}</p></article>`
    : `<article class="packet-card world-view"><p class="eyebrow">2. Semantic world view</p><h3>${escapeHtml(view.status)}</h3><p>${escapeHtml(view.message)}</p><p class="mono">${escapeHtml(view.context_id)}<br>${escapeHtml(view.branch_id)}<br>${view.perspective_ids.length ? escapeHtml(view.perspective_ids.join(', ')) : 'shared records only'}</p><div class="world-records"><strong>${plural(view.records.states.length, 'state')} · ${plural(view.records.perspectives.length, 'perspective')} · ${plural(view.records.relationshipFrames.length, 'relationship frame')}</strong>${view.selected_record_ids.map((id) => `<span class="pill">${escapeHtml(id)}</span>`).join('')}</div>${view.omissions.length ? `<p class="warning-copy">Omissions: ${escapeHtml(view.omissions.join(' · '))}</p>` : ''}</article>`;
  $('#agent-result').innerHTML = `<div class="packet-grid"><article class="packet-card"><p class="eyebrow">1. Interpretation</p><h3>${escapeHtml(result.interpretation.goal)}</h3><p>Status: <strong>${escapeHtml(result.status)}</strong></p>${result.interpretation.missingMaterialInputs.length ? `<p>Missing: ${escapeHtml(result.interpretation.missingMaterialInputs.join(', '))}</p>` : '<p>Required inputs are present.</p>'}</article>${worldView}<article class="packet-card warning"><p class="eyebrow">3. Retrieval</p><h3>Not run</h3><p>${escapeHtml(result.retrieval.message)}</p><p>This prevents planned context from being misrepresented as a live Cognee result.</p></article><article class="packet-card"><p class="eyebrow">4. Planned agent packet</p><h3>${plural(planned.length, 'entity')}</h3>${planned.map((entity) => `<div class="packet-entity" data-entity="${entity.id}"><strong>${escapeHtml(entity.label)}</strong><br><span class="mono">${escapeHtml(entity.id)} · ${escapeHtml(entity.perspective)}</span></div>`).join('')}</article><article class="packet-card"><p class="eyebrow">5. Reasoning instructions</p><h3>How the main agent is guided</h3><ul>${result.agentPacket.reasoningInstructions.map((instruction) => `<li>${escapeHtml(instruction)}</li>`).join('')}</ul><p class="mono">${plural(result.agentPacket.relationships.length, 'direct relationship')} · ${plural(result.agentPacket.evidence.length, 'evidence item')}</p></article></div><div class="packet-card warning" style="margin-top:14px"><p class="eyebrow">Known limitations</p><ul>${result.limitations.map((item) => `<li>${escapeHtml(item)}</li>`).join('')}</ul></div>`;
  document.querySelectorAll('#agent-result [data-entity]').forEach((item) => item.addEventListener('click', () => inspectEntity(item.dataset.entity)));
}

function bindEvents() {
  ['search','context-filter','perspective-filter'].forEach((id) => $(('#' + id)).addEventListener(id === 'search' ? 'input' : 'change', () => { if (id === 'search' && $('#search').value.trim()) { atlasDomain = 'all'; if (atlasDepth < 2) atlasDepth = 2; } renderAtlas(); renderMap(); renderGraph(); }));
  document.querySelectorAll('[data-atlas-depth]').forEach((button) => button.addEventListener('click', () => setAtlasDepth(button.dataset.atlasDepth)));
  document.querySelectorAll('.tab').forEach((tab) => tab.addEventListener('click', () => { document.querySelectorAll('.tab,.view').forEach((item) => item.classList.remove('active')); tab.classList.add('active'); $(`#${tab.dataset.view}-view`).classList.add('active'); if (tab.dataset.view === 'graph') renderGraph(); }));
  $('#close-inspector').addEventListener('click', () => $('#inspector').classList.remove('open'));
  document.querySelectorAll('[data-graph-mode]').forEach((button) => button.addEventListener('click', () => { activeGraphMode = button.dataset.graphMode; document.querySelectorAll('[data-graph-mode]').forEach((item) => { const active = item === button; item.classList.toggle('active', active); item.setAttribute('aria-selected', String(active)); }); graphZoom = 1; renderGraph(); }));
  bindGraphControls();
  window.addEventListener('resize', () => { if ($('#graph-view').classList.contains('active')) renderGraph(); });
  $('#simulation-form').addEventListener('submit', async (event) => { event.preventDefault(); const request = Object.fromEntries(['prompt','stage','assetType','audience','channel'].map((id) => [id, $(`#${id}`).value])); request.contextId = $('#agent-context').value; request.branchId = $('#agent-branch').value; request.perspectiveIds = $('#agent-perspective').value ? [$('#agent-perspective').value] : []; $('#agent-result').textContent = 'Compiling deterministic context…'; const result = await fetch('/api/simulate', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(request)}).then((response) => response.json()); renderAgentResult(result); });
}
initialise().catch((error) => { document.body.innerHTML = `<pre>Unable to load Brand World Explorer: ${escapeHtml(error.message)}</pre>`; });
