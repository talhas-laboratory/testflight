let state;
let selectedId;
const isFilePreview = window.location.protocol === 'file:';

const $ = (selector) => document.querySelector(selector);
const escapeHtml = (value = '') => String(value).replace(/[&<>'"]/g, (char) => ({
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  "'": '&#39;',
  '"': '&quot;',
}[char]));

function setStatus(message = '', kind = '') {
  const element = $('#studio-status');
  element.textContent = message;
  element.dataset.kind = kind;
}

async function command(commandName, payload = {}) {
  if (isFilePreview) {
    setStatus('Preview only · open Creative Studio over HTTP for live commands.', 'error');
    return null;
  }
  setStatus('Saving…');
  try {
    const response = await fetch('/api/command', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ command: commandName, payload }),
    });
    const result = await response.json();
    if (!response.ok || result.status === 'held' || result.status === 'failed') {
      setStatus(result.error || 'The command could not be saved.', 'error');
      return null;
    }
    state = result;
    render();
    setStatus('Saved');
    return result;
  } catch (error) {
    setStatus(error instanceof Error ? error.message : 'The command could not be saved.', 'error');
    return null;
  }
}

async function hashFile(file) {
  const buffer = await file.arrayBuffer();
  const digest = await crypto.subtle.digest('SHA-256', buffer);
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, '0')).join('');
}

async function base64File(file) {
  const bytes = new Uint8Array(await file.arrayBuffer());
  let binary = '';
  for (let index = 0; index < bytes.length; index += 1) binary += String.fromCharCode(bytes[index]);
  return btoa(binary);
}

function blobUrl(item) {
  return `/api/blob/${encodeURIComponent(item.content_hash)}`;
}

function render() {
  $('#project-name').textContent = state.project.name;
  $('#project-scope').textContent = `${state.project.project_id} · ${state.project.scope}`;
  $('#board-name').textContent = state.moodboard.name;
  $('#reference-count').textContent = String(state.references.length).padStart(2, '0');
  $('#annotation-count').textContent = String(state.annotations.length).padStart(2, '0');
  $('#revision-count').textContent = String(state.revision ?? state.events.filter((event) => event.revision).length).padStart(2, '0');
  $('#board-status').textContent = state.moodboard.status.toUpperCase();
  renderBoard();
  renderField();
  renderArtifact();
  if (selectedId) renderInspector();
}

function hasLegacyLinearLayout() {
  if (state.references.length < 2) return false;
  const placements = state.references.map((item) => item.placement || {});
  const xs = placements.map((placement) => Number(placement.x || 0));
  const ys = placements.map((placement) => Number(placement.y || 0));
  return Math.max(...ys) - Math.min(...ys) < 2 && Math.max(...xs) - Math.min(...xs) < 180;
}

function currentPlacement(item, index) {
  if (hasLegacyLinearLayout()) {
    return { x: 38 + (index % 3) * 258, y: 38 + Math.floor(index / 3) * 208, width: 236, height: 178, z_index: index, cluster_id: null };
  }
  return item.placement || { x: 32 + index * 18, y: 32, width: 236, height: 178, z_index: index, cluster_id: null };
}

function renderBoard() {
  const board = $('#board');
  if (!state.references.length) {
    board.innerHTML = '<div class="board-empty"><span>↘</span><strong>Your field starts with a reference.</strong><small>Images, words, sounds and fragments are all welcome. The system will keep the source and ask what it means.</small></div>';
    return;
  }
  const clusters = state.clusters || [];
  const clusterById = new Map(clusters.map((cluster) => [cluster.cluster_id, cluster]));
  const grouped = new Map(clusters.map((cluster) => [cluster.cluster_id, []]));
  state.references.forEach((item) => {
    if (item.placement?.cluster_id && grouped.has(item.placement.cluster_id)) grouped.get(item.placement.cluster_id).push(item);
  });
  const clusterHalos = clusters.map((cluster) => {
    const cards = grouped.get(cluster.cluster_id) || [];
    if (!cards.length) return '';
    const left = Math.min(...cards.map((item) => Number(item.placement?.x || 0))) - 18;
    const top = Math.min(...cards.map((item) => Number(item.placement?.y || 0))) - 43;
    const right = Math.max(...cards.map((item) => Number(item.placement?.x || 0) + Number(item.placement?.width || 236))) + 18;
    const bottom = Math.max(...cards.map((item) => Number(item.placement?.y || 0) + Number(item.placement?.height || 178))) + 18;
    return `<section class="cluster-halo" style="left:${left}px;top:${top}px;width:${right - left}px;height:${bottom - top}px"><strong>${escapeHtml(cluster.label)}</strong><small>${cards.length} reference${cards.length === 1 ? '' : 's'}</small></section>`;
  }).join('');
  const cards = state.references.map((item, index) => {
    const placement = currentPlacement(item, index);
    const visual = item.media_type.startsWith('image') && item.source_uri.startsWith('blob://')
      ? `<img src="${blobUrl(item)}" alt="${escapeHtml(item.label)}" loading="lazy" />`
      : `<span class="media-icon">${item.media_type.startsWith('text') ? '≡' : '◌'}</span>`;
    const annotationCount = state.annotations.filter((annotation) => annotation.target_id === item.asset_id).length;
    const sourceKind = item.source_uri.startsWith('blob://') ? 'LOCAL' : 'LINK';
    const cluster = clusterById.get(placement.cluster_id);
    return `<article class="reference-card ${selectedId === item.asset_id ? 'selected' : ''}" data-reference="${escapeHtml(item.asset_id)}" draggable="false" style="left:${Number(placement.x)}px;top:${Number(placement.y)}px;width:${Number(placement.width || 236)}px;height:${Number(placement.height || 178)}px;z-index:${Number(placement.z_index || index) + 2}"><div class="drag-handle" title="Drag to arrange">⠿</div><div class="card-visual">${visual}<small>${escapeHtml(item.media_type)}</small></div><div class="card-body"><strong>${escapeHtml(item.label)}</strong><small>${escapeHtml(cluster?.label || 'Unsorted')}</small><span class="card-signals"><i>${sourceKind}</i><i>${annotationCount ? `${annotationCount} NOTE${annotationCount > 1 ? 'S' : ''}` : 'UNANNOTATED'}</i></span></div></article>`;
  }).join('');
  board.innerHTML = `<div class="canvas-stage" id="canvas-stage">${clusterHalos}${cards}</div>`;
  board.querySelectorAll('[data-reference]').forEach((card) => {
    card.addEventListener('click', () => {
    selectedId = card.dataset.reference;
    render();
    $('#inspector').hidden = false;
    });
    card.addEventListener('pointerdown', startCardDrag);
  });
}

function layoutPayload(overrides = {}) {
  return {
    placements: state.references.map((item, index) => {
      const current = currentPlacement(item, index);
      const override = overrides[item.asset_id] || {};
      return {
        asset_id: item.asset_id,
        x: override.x ?? current.x ?? 32 + index * 24,
        y: override.y ?? current.y ?? 32,
        width: current.width ?? 236,
        height: current.height ?? 178,
        z_index: override.z_index ?? current.z_index ?? index,
        cluster_key: override.cluster_key ?? current.cluster_id ?? null,
      };
    }),
    clusters: (state.clusters || []).map((cluster) => ({ key: cluster.cluster_id, label: cluster.label })),
  };
}

function startCardDrag(event) {
  if (event.button !== 0 || event.target.closest('button, input, select, textarea')) return;
  const card = event.currentTarget;
  const assetId = card.dataset.reference;
  const index = state.references.findIndex((item) => item.asset_id === assetId);
  const placement = currentPlacement(state.references[index], index);
  const boardRect = $('#canvas-stage').getBoundingClientRect();
  const origin = { x: Number(placement.x || 0), y: Number(placement.y || 0) };
  const start = { x: event.clientX, y: event.clientY };
  let moved = false;
  card.setPointerCapture(event.pointerId);
  card.classList.add('dragging-card');
  const move = (moveEvent) => {
    const x = Math.max(0, Math.min(10000, origin.x + moveEvent.clientX - start.x));
    const y = Math.max(0, Math.min(10000, origin.y + moveEvent.clientY - start.y));
    if (Math.abs(x - origin.x) > 3 || Math.abs(y - origin.y) > 3) moved = true;
    card.style.left = `${x}px`;
    card.style.top = `${y}px`;
    card.style.zIndex = String(state.references.length + 10);
  };
  const end = async (endEvent) => {
    card.removeEventListener('pointermove', move);
    card.removeEventListener('pointerup', end);
    card.removeEventListener('pointercancel', end);
    card.classList.remove('dragging-card');
    if (!moved) return;
    const x = Math.max(0, origin.x + endEvent.clientX - start.x);
    const y = Math.max(0, origin.y + endEvent.clientY - start.y);
    await command('update_board_layout', layoutPayload({ [assetId]: { x, y, z_index: state.references.length + 5 } }));
  };
  card.addEventListener('pointermove', move);
  card.addEventListener('pointerup', end);
  card.addEventListener('pointercancel', end);
}

function renderField() {
  const field = state.field;
  $('#field-status strong').textContent = field.status.replaceAll('_', ' ');
  const draw = (id, values, empty) => {
    $(id).innerHTML = values.length
      ? values.map((value) => `<span class="field-chip">${escapeHtml(value)}</span>`).join('')
      : `<span class="empty-state">${empty}</span>`;
  };
  draw('#principles', field.principles, 'No accepted principles yet.');
  draw('#tensions', field.tensions, 'Tensions stay visible; they are never averaged away.');
  draw('#exclusions', field.exclusions, 'No exclusions recorded yet.');
  const progress = Math.min(100, state.references.length * 20 + state.annotations.length * 15);
  $('#readiness-bar').style.width = `${progress}%`;
  $('#readiness-text').textContent = progress ? `${progress}% of the first review gate is represented.` : 'Add and review references to unlock a projection.';
}

function csvValues(id) {
  return $(id).value.split(',').map((value) => value.trim()).filter(Boolean);
}

function projectionPayload() {
  const workspaceId = $('#workspace-id').value.trim();
  const entityIds = csvValues('#target-entity-ids');
  const modality = $('#modality').value;
  const channel = $('#channel').value.trim();
  const disclosureManifestId = $('#disclosure-manifest-id').value.trim();
  return {
    workspace_id: workspaceId,
    context_id: $('#context-id').value.trim(),
    branch_id: $('#branch-id').value.trim(),
    privacy_policy_id: $('#privacy-policy-id').value.trim(),
    authority_grant_id: $('#authority-grant-id').value.trim(),
    target_entity_ids: entityIds,
    entities: entityIds.map((entityId) => ({ entity_id: entityId, workspace_id: workspaceId })),
    request: {
      request_id: `request:${crypto.randomUUID()}`,
      task_type: 'create',
      artifact_type: $('#artifact-type').value.trim(),
      modality,
      target: $('#target').value.trim(),
      permission_context: { disclosure_manifest_id: disclosureManifestId },
    },
    channel: channel || undefined,
    target_manifest: {
      target_id: $('#target-adapter-id').value.trim(),
      adapter_version: '1',
      accepted_modalities: [modality],
      controls: { supported_control_ids: ['principles', 'tensions', 'exclusions', 'dimensions'] },
      privacy_policy_id: $('#privacy-policy-id').value.trim(),
    },
    lens: $('#lens').value.trim(),
    disclosure_manifest_id: disclosureManifestId,
  };
}

function renderArtifact() {
  const projection = state.projection || {};
  const generation = state.generation || {};
  const evaluation = state.evaluation || {};
  const statuses = [
    `context ${projection.status || 'not_started'}`,
    `target ${generation.status || 'not_started'}`,
    `evaluation ${evaluation.status || 'not_started'}`,
  ];
  const ids = [
    projection.context_packet_id && `packet ${projection.context_packet_id}`,
    generation.output_id && `output ${generation.output_id}`,
    evaluation.feedback_ids?.length && `${evaluation.feedback_ids.length} feedback proposal(s)`,
  ].filter(Boolean);
  $('#artifact-result').textContent = [...statuses, ...ids].join(' · ');
}

function renderInspector() {
  const item = state.references.find((reference) => reference.asset_id === selectedId);
  if (!item) return;
  $('#inspector-title').textContent = item.label;
  const notes = state.annotations.filter((annotation) => annotation.target_id === item.asset_id).length;
  $('#inspector-meta').innerHTML = `<span><b>Source</b>${escapeHtml(item.source_id)}</span><span><b>Media</b>${escapeHtml(item.media_type)}</span><span><b>Evidence</b>${escapeHtml(item.source_uri)}</span><span><b>Annotations</b><em>${notes ? `${notes} saved` : 'None yet'}</em></span>`;
  const select = $('#reference-cluster');
  const selectedCluster = item.placement?.cluster_id || '';
  select.innerHTML = `<option value="">Unsorted / independent</option>${(state.clusters || []).map((cluster) => `<option value="${escapeHtml(cluster.cluster_id)}" ${cluster.cluster_id === selectedCluster ? 'selected' : ''}>${escapeHtml(cluster.label)}</option>`).join('')}`;
}

async function addFiles(files) {
  for (const file of [...files]) {
    const contentHash = await hashFile(file);
    const contentBase64 = await base64File(file);
    const payload = {
      asset_id: `asset:${crypto.randomUUID()}`,
      source_id: `upload:${contentHash.slice(0, 16)}`,
      content_hash: contentHash,
      source_uri: `local-upload://${encodeURIComponent(file.name)}`,
      content_base64: contentBase64,
      media_type: file.type || 'application/octet-stream',
      label: file.name,
    };
    if ($('#rights').checked) {
      payload.license_record_id = `license:upload:${contentHash.slice(0, 12)}`;
      payload.license = {
        owner: 'user-declared',
        permitted_use: ['analysis', 'generation'],
        disclosure_allowed: true,
        generation_allowed: true,
        retention_policy: 'project_runtime',
      };
    }
    const result = await command('add_reference', payload);
    if (!result) break;
  }
}

$('#browse').addEventListener('click', () => $('#file-input').click());
$('#file-input').addEventListener('change', (event) => {
  addFiles(event.target.files);
  event.target.value = '';
});
const dropzone = $('#dropzone');
dropzone.addEventListener('dragover', (event) => { event.preventDefault(); dropzone.classList.add('dragging'); });
dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragging'));
dropzone.addEventListener('drop', (event) => {
  event.preventDefault();
  dropzone.classList.remove('dragging');
  addFiles(event.dataTransfer.files);
});
$('#reset').addEventListener('click', () => command('reset_demo'));
$('#analyze-field').addEventListener('click', () => command('analyze_field'));
$('#accept-field').addEventListener('click', () => command('review_field', {
  action: 'accept',
  rationale: 'Approved in Creative Studio.',
  authority_grant_id: $('#authority-grant-id').value.trim(),
}));
$('#hold-field').addEventListener('click', () => command('review_field', { action: 'hold', rationale: 'Held for further evidence.' }));
$('#revise-field').addEventListener('click', () => command('review_field', { action: 'revise', rationale: 'Revision requested in Creative Studio.' }));
$('#projection-form').addEventListener('submit', (event) => {
  event.preventDefault();
  command('project_field', projectionPayload());
});
$('#prepare-generation').addEventListener('click', () => {
  const payload = projectionPayload();
  command('prepare_generation', {
    target_manifest: payload.target_manifest,
    disclosure_manifest_id: payload.disclosure_manifest_id,
    grounding_asset_ids: csvValues('#grounding-asset-ids'),
    permitted_asset_ids: csvValues('#permitted-asset-ids'),
  });
});
$('#invoke-generation').addEventListener('click', () => command('invoke_generation', {
  authority_grant_id: $('#authority-grant-id').value.trim(),
}));
$('#evaluate-output').addEventListener('click', () => command('evaluate_output'));
$('#close-inspector').addEventListener('click', () => {
  $('#inspector').hidden = true;
  selectedId = undefined;
  render();
});
$('#reference-cluster').addEventListener('change', (event) => {
  if (!selectedId) return;
  command('update_board_layout', layoutPayload({ [selectedId]: { cluster_key: event.target.value || null } }));
});
$('#new-cluster').addEventListener('click', () => {
  if (!selectedId) {
    setStatus('Select a reference before creating a cluster.', 'error');
    return;
  }
  const label = window.prompt('Name this visual cluster');
  if (!label?.trim()) return;
  const key = `cluster:${crypto.randomUUID()}`;
  const payload = layoutPayload({ [selectedId]: { cluster_key: key } });
  payload.clusters.push({ key, label: label.trim() });
  command('update_board_layout', payload);
});
$('#layout-board').addEventListener('click', () => {
  const ungrouped = state.references.filter((item) => !item.placement?.cluster_id);
  if (!ungrouped.length) {
    setStatus('Every reference already has a cluster.', 'error');
    return;
  }
  const overrides = Object.fromEntries(ungrouped.map((item, index) => [item.asset_id, {
    x: 38 + (index % 3) * 258,
    y: 38 + Math.floor(index / 3) * 208,
    z_index: index,
  }]));
  command('update_board_layout', layoutPayload(overrides));
});
$('#toggle-artifact').addEventListener('click', () => {
  const panel = $('#artifact-console');
  panel.hidden = !panel.hidden;
  $('#toggle-artifact').setAttribute('aria-expanded', String(!panel.hidden));
  $('#toggle-artifact').innerHTML = panel.hidden ? 'Open artifact workflow <span>↗</span>' : 'Close artifact workflow <span>×</span>';
  if (!panel.hidden) panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
});
$('#annotation-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  if (!selectedId) return;
  const result = await command('annotate_reference', {
    target_id: selectedId,
    text: $('#annotation').value,
    anti_association: $('#anti').value,
  });
  if (result) {
    $('#annotation').value = '';
    $('#anti').value = '';
  }
});
if (isFilePreview) {
  setStatus('Preview only · open Creative Studio over HTTP for live data.', 'error');
} else {
  fetch('/api/state')
    .then((response) => response.json())
    .then((value) => { state = value; render(); })
    .catch((error) => setStatus(error instanceof Error ? error.message : 'Unable to load the board.', 'error'));
}
