"""Read-only compiler and local server for the Brand World Explorer.

Canonical workspace files remain the source of truth. Cognee retrieval and
context-intelligence execution are intentionally represented as separate views
when adapters are connected; neither is silently merged into this snapshot.
"""

from __future__ import annotations

import hashlib
import json
import mimetypes
from dataclasses import dataclass
from datetime import UTC, datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml
from testflight_semantic import (
    BranchConflict,
    BranchDelta,
    EvidenceLink,
    ExperimentPlan,
    HypothesisRecord,
    LearningUpdate,
    ObservedOutcome,
    PerspectiveProfile,
    RelationshipFrame,
    StateSnapshot,
    WorldBranch,
    WorldViewRequest,
    compile_world_view,
)

WORKSPACE_FILES = {
    "workspace": "WORKSPACE.yaml",
    "entities": "artifacts/entity-inventory.yaml",
    "relationships": "artifacts/relationship-inventory.yaml",
    "contexts": "artifacts/context-profiles.yaml",
    "evidence": "artifacts/evidence-notes.yaml",
    "sources": "artifacts/source-catalog.yaml",
    "workflow": "artifacts/asset-workflow-context.yaml",
    "intelligence": "INTELLIGENCE.json",
    "visual_language": "visual-language/manifest.json",
}
OPTIONAL_WORKSPACE_FILES = {
    "world_model": "artifacts/world-modeling.yaml",
    "visual_graph": "visual-language/graph.json",
    "copy_claims_graph": "copy-claims/graph.json",
    "audience_graph": "audience/graph.json",
}


def _read_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"expected YAML object in {path}")
    return value


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object in {path}")
    return value


def _workspace_path(workspace: Path, filename: str) -> Path:
    path = workspace / filename
    if not path.is_file():
        raise FileNotFoundError(f"required workspace file is missing: {path}")
    return path


def _source_hash(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(path.name.encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _as_list(value: object) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _json_safe(value: object) -> Any:
    """Normalize YAML-native values such as dates for the JSON boundary."""
    return json.loads(json.dumps(value, default=str))


def _world_model_records(source: dict[str, Any]) -> dict[str, tuple[Any, ...]]:
    """Validate a canonical overlay before it can become an agent-facing view."""

    return {
        "evidence_links": tuple(
            EvidenceLink.model_validate(item) for item in _as_list(source.get("evidence_links"))
        ),
        "states": tuple(
            StateSnapshot.model_validate(item) for item in _as_list(source.get("states"))
        ),
        "perspectives": tuple(
            PerspectiveProfile.model_validate(item) for item in _as_list(source.get("perspectives"))
        ),
        "relationship_frames": tuple(
            RelationshipFrame.model_validate(item)
            for item in _as_list(source.get("relationship_frames"))
        ),
        "branches": tuple(
            WorldBranch.model_validate(item) for item in _as_list(source.get("branches"))
        ),
        "branch_deltas": tuple(
            BranchDelta.model_validate(item) for item in _as_list(source.get("branch_deltas"))
        ),
        "conflicts": tuple(
            BranchConflict.model_validate(item) for item in _as_list(source.get("conflicts"))
        ),
        "hypotheses": tuple(
            HypothesisRecord.model_validate(item) for item in _as_list(source.get("hypotheses"))
        ),
        "experiments": tuple(
            ExperimentPlan.model_validate(item) for item in _as_list(source.get("experiments"))
        ),
        "observed_outcomes": tuple(
            ObservedOutcome.model_validate(item)
            for item in _as_list(source.get("observed_outcomes"))
        ),
        "learning_updates": tuple(
            LearningUpdate.model_validate(item) for item in _as_list(source.get("learning_updates"))
        ),
    }


def _serialized_world_model(records: dict[str, tuple[Any, ...]]) -> dict[str, Any]:
    return {
        "available": True,
        **{
            key: [record.model_dump(mode="json") for record in values]
            for key, values in records.items()
        },
    }


def build_graph_data(
    manifest: dict[str, Any],
    entities: list[dict[str, Any]],
    relationships: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Compile browser-safe graph records without changing their epistemic status.

    The brand root is a graph-only anchor for ontology relationships. It is not
    an entity proposal and is deliberately marked as a structural record.
    """

    brand_id = str(manifest.get("brand_id", ""))
    brand_label = str(manifest.get("name", brand_id or "Brand"))
    nodes = [
        {
            "id": brand_id,
            "label": brand_label,
            "kind": "brand-root",
            "entityType": "brand",
            "perspective": "structural",
            "status": "structural",
            "contextIds": [],
        },
        *[
            {
                "id": str(entity.get("id")),
                "label": str(entity.get("label", entity.get("id", "Untitled entity"))),
                "kind": "entity",
                "entityType": str(entity.get("entity_type", "unknown")),
                "perspective": str(entity.get("perspective", "reported")),
                "status": str(entity.get("status", "proposed")),
                "contextIds": [str(item) for item in entity.get("context_ids", [])],
            }
            for entity in entities
        ],
    ]
    known_node_ids = {node["id"] for node in nodes}
    edges = [
        {
            "id": str(relationship.get("id")),
            "sourceId": str(relationship.get("source_id")),
            "targetId": str(relationship.get("target_id")),
            "relationshipType": str(relationship.get("relationship_type", "related_to")),
            "status": str(relationship.get("status", "proposed")),
            "epistemicStatus": str(relationship.get("epistemic_status", "reported")),
            "perspective": str(relationship.get("perspective", "reported")),
            "contextIds": [str(item) for item in relationship.get("context_ids", [])],
            "evidenceIds": [str(item) for item in relationship.get("evidence_ids", [])],
            "limitations": [str(item) for item in relationship.get("limitations", [])],
        }
        for relationship in relationships
        if str(relationship.get("source_id")) in known_node_ids
        and str(relationship.get("target_id")) in known_node_ids
    ]
    return {"nodes": nodes, "edges": edges}


def _supplemental_graph_data(
    source: dict[str, Any], workspace_id: str, brand_id: str, graph_name: str
) -> dict[str, Any]:
    """Validate a separate research graph without promoting it to Brand ontology."""

    if source.get("version") != 1:
        raise ValueError(f"{graph_name} graph must use version 1")
    if source.get("workspaceId") != workspace_id or source.get("brandId") != brand_id:
        raise ValueError(f"{graph_name} graph identity differs from workspace")
    nodes = _as_list(source.get("nodes"))
    edges = _as_list(source.get("relationships"))
    node_ids = {str(node.get("id")) for node in nodes}
    if not nodes or len(node_ids) != len(nodes) or "" in node_ids:
        raise ValueError(f"{graph_name} graph needs unique nodes")
    if any(
        not str(node.get("label", ""))
        or not str(node.get("entityType", ""))
        or not str(node.get("epistemicStatus", ""))
        or not isinstance(node.get("sourceUrls"), list)
        or not node["sourceUrls"]
        for node in nodes
    ):
        raise ValueError(f"{graph_name} graph nodes need label, type, status, and source URLs")
    if any(
        not str(edge.get("id", ""))
        or edge.get("sourceId") not in node_ids
        or edge.get("targetId") not in node_ids
        or not str(edge.get("relationshipType", ""))
        for edge in edges
    ):
        raise ValueError(f"{graph_name} graph edge is incomplete or out of scope")
    return {"available": True, "nodes": nodes, "edges": edges, "purpose": source.get("purpose")}


def build_snapshot(workspace: Path) -> dict[str, Any]:
    """Compile canonical records into a browser-safe, normalized snapshot."""
    workspace = workspace.resolve()
    paths = {key: _workspace_path(workspace, value) for key, value in WORKSPACE_FILES.items()}
    optional_paths = {
        key: workspace / value
        for key, value in OPTIONAL_WORKSPACE_FILES.items()
        if (workspace / value).is_file()
    }
    manifest_file = _read_yaml(paths["workspace"])
    manifest = manifest_file.get("workspace", manifest_file)
    if not isinstance(manifest, dict):
        raise ValueError(f"expected workspace object in {paths['workspace']}")
    entities_file = _read_yaml(paths["entities"])
    relationships_file = _read_yaml(paths["relationships"])
    contexts_file = _read_yaml(paths["contexts"])
    evidence_file = _read_yaml(paths["evidence"])
    sources_file = _read_yaml(paths["sources"])
    workflow_file = _read_yaml(paths["workflow"])
    intelligence = _read_json(paths["intelligence"])
    visual_language = _read_json(paths["visual_language"])
    world_model_records = (
        _world_model_records(_read_yaml(optional_paths["world_model"]))
        if "world_model" in optional_paths
        else None
    )
    visual_graph = (
        _supplemental_graph_data(
            _read_json(optional_paths["visual_graph"]),
            str(manifest.get("id")),
            str(manifest.get("brand_id")),
            "visual-language",
        )
        if "visual_graph" in optional_paths
        else {"available": False, "nodes": [], "edges": []}
    )
    copy_claims_graph = (
        _supplemental_graph_data(
            _read_json(optional_paths["copy_claims_graph"]),
            str(manifest.get("id")),
            str(manifest.get("brand_id")),
            "copy-and-claims",
        )
        if "copy_claims_graph" in optional_paths
        else {"available": False, "nodes": [], "edges": []}
    )
    audience_graph = (
        _supplemental_graph_data(
            _read_json(optional_paths["audience_graph"]),
            str(manifest.get("id")),
            str(manifest.get("brand_id")),
            "audience",
        )
        if "audience_graph" in optional_paths
        else {"available": False, "nodes": [], "edges": []}
    )

    entities = _as_list(entities_file.get("entities"))
    relationships = _as_list(relationships_file.get("relationships"))
    contexts = _as_list(contexts_file.get("contexts"))
    evidence = _as_list(evidence_file.get("notes"))
    sources = _as_list(sources_file.get("sources"))
    diagnostics = _validate_references(
        manifest, entities, relationships, contexts, evidence, sources, visual_language
    )
    type_counts: dict[str, int] = {}
    for entity in entities:
        entity_type = str(entity.get("entity_type", "unknown"))
        type_counts[entity_type] = type_counts.get(entity_type, 0) + 1

    return _json_safe(
        {
            "version": 1,
            "workspace": {
                "id": manifest.get("id"),
                "brandId": manifest.get("brand_id"),
                "label": manifest.get("name", "Nike research world"),
                "status": manifest.get("status"),
            },
            "ontology": {
                "version": entities_file.get("ontology_version"),
                "typeCounts": type_counts,
            },
            "entities": entities,
            "relationships": relationships,
            "graph": build_graph_data(manifest, entities, relationships),
            "contexts": contexts,
            "evidence": evidence,
            "sources": sources,
            "visualLanguage": visual_language,
            "visualGraph": visual_graph,
            "copyClaimsGraph": copy_claims_graph,
            "audienceGraph": audience_graph,
            "worldModel": (
                _serialized_world_model(world_model_records)
                if world_model_records is not None
                else {"available": False}
            ),
            "workflow": workflow_file,
            "intelligence": intelligence,
            "diagnostics": diagnostics,
            "provenance": {
                "generatedAt": datetime.now(UTC).isoformat(),
                "sourceHash": _source_hash([*paths.values(), *optional_paths.values()]),
                "canonical": True,
                "projection": "none",
            },
        }
    )


def _resolve_world_view(snapshot: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    """Compile a deterministic semantic overlay without performing retrieval."""

    raw = snapshot.get("worldModel")
    if not isinstance(raw, dict) or not raw.get("available"):
        return {
            "status": "no_hit",
            "message": "This workspace has no canonical world-model overlay yet.",
        }
    records = _world_model_records(raw)
    context_id = str(request.get("contextId") or "")
    branch_id = str(request.get("branchId") or "research-main")
    perspective_ids = tuple(
        value for value in request.get("perspectiveIds", []) if isinstance(value, str) and value
    )
    if not context_id:
        return {
            "status": "no_hit",
            "message": "Choose a context before compiling a world view.",
        }
    view = compile_world_view(
        WorldViewRequest(
            request_id="brand-lab:context-inspection",
            workspace_id=str(snapshot["workspace"]["id"]),
            context_id=context_id,
            branch_id=branch_id,
            task_type=str(request.get("stage") or "brief"),
            perspective_ids=perspective_ids,
        ),
        branches=records["branches"],
        deltas=records["branch_deltas"],
        states=records["states"],
        perspectives=records["perspectives"],
        relationship_frames=records["relationship_frames"],
        conflicts=records["conflicts"],
    )
    selected_ids = set(view.selected_record_ids)
    linked_ids = set(view.evidence_link_ids)
    return {
        **view.model_dump(mode="json"),
        "message": "Deterministic semantic view compiled before retrieval or model synthesis.",
        "records": {
            "states": [
                item.model_dump(mode="json")
                for item in records["states"]
                if item.state_id in selected_ids
            ],
            "perspectives": [
                item.model_dump(mode="json")
                for item in records["perspectives"]
                if item.perspective_id in selected_ids
            ],
            "relationshipFrames": [
                item.model_dump(mode="json")
                for item in records["relationship_frames"]
                if item.frame_id in selected_ids
            ],
            "evidenceLinks": [
                item.model_dump(mode="json")
                for item in records["evidence_links"]
                if item.link_id in linked_ids
            ],
        },
    }


def _validate_references(
    manifest: dict[str, Any],
    entities: list[dict[str, Any]],
    relationships: list[dict[str, Any]],
    contexts: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    sources: list[dict[str, Any]],
    visual_language: dict[str, Any],
) -> list[dict[str, str]]:
    entity_ids = {str(item.get("id")) for item in entities}
    context_ids = {str(item.get("id")) for item in contexts}
    evidence_ids = {str(item.get("id")) for item in evidence}
    source_ids = {str(item.get("id")) for item in sources}
    brand_id = str(manifest.get("brand_id", ""))
    findings: list[dict[str, str]] = []

    def missing(owner: str, field: str, value: str) -> None:
        findings.append({"severity": "error", "owner": owner, "field": field, "value": value})

    for entity in entities:
        owner = str(entity.get("id"))
        for value in entity.get("context_ids", []):
            if value not in context_ids:
                missing(owner, "context_ids", str(value))
        for value in entity.get("evidence_ids", []):
            if value not in evidence_ids:
                missing(owner, "evidence_ids", str(value))
    for relationship in relationships:
        owner = str(relationship.get("id"))
        for field in ("source_id", "target_id"):
            value = str(relationship.get(field, ""))
            if value not in entity_ids and value != brand_id:
                missing(owner, field, value)
        for value in relationship.get("context_ids", []):
            if value not in context_ids:
                missing(owner, "context_ids", str(value))
        for value in relationship.get("evidence_ids", []):
            if value not in evidence_ids:
                missing(owner, "evidence_ids", str(value))
    for record in evidence:
        source_id = str(record.get("source_id", ""))
        if source_id not in source_ids:
            missing(str(record.get("id")), "source_id", source_id)
    for record in _as_list(visual_language.get("references")):
        for evidence_id in record.get("evidenceIds", []):
            if evidence_id not in evidence_ids:
                missing(str(record.get("id")), "evidenceIds", str(evidence_id))
    return findings


def simulate_context(snapshot: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    """Show the deterministic planning layer without claiming live retrieval occurred."""
    intelligence = snapshot["intelligence"]
    stage = str(request.get("stage") or "brief")
    recipes = _as_list(intelligence.get("workflows"))
    recipe = next((item for item in recipes if item.get("stage") == stage), None)
    if recipe is None:
        return {"status": "no_hit", "reason": f"No workflow recipe exists for stage '{stage}'."}

    fields = {
        "prompt": str(request.get("prompt", "")).lower(),
        "assetType": str(request.get("assetType", "")).lower(),
        "objective": str(request.get("objective", "")).lower(),
        "audience": str(request.get("audience", "")).lower(),
        "channel": str(request.get("channel", "")).lower(),
        "geography": str(request.get("geography", "")).lower(),
        "occasion": str(request.get("occasion", "")).lower(),
    }
    selection = recipe.get("entitySelection", {})
    planned_ids = list(selection.get("always", [])) if isinstance(selection, dict) else []
    selection_reasons: list[dict[str, str]] = [
        {"entityId": item, "reason": "required by workflow recipe"} for item in planned_ids
    ]
    for condition in selection.get("conditions", []) if isinstance(selection, dict) else []:
        if not isinstance(condition, dict):
            continue
        field = str(condition.get("field", ""))
        terms = [str(item).lower() for item in condition.get("includesAny", [])]
        if any(term in fields.get(field, "") for term in terms):
            for entity_id in condition.get("entityIds", []):
                if entity_id not in planned_ids:
                    planned_ids.append(entity_id)
                    selection_reasons.append(
                        {"entityId": entity_id, "reason": f"matched {field}: {', '.join(terms)}"}
                    )
    entities = {str(item.get("id")): item for item in snapshot["entities"]}
    planned = [entities[item] for item in planned_ids if item in entities]
    evidence_ids = sorted({eid for item in planned for eid in item.get("evidence_ids", [])})
    evidence = {str(item.get("id")): item for item in snapshot["evidence"]}
    context_ids = sorted({cid for item in planned for cid in item.get("context_ids", [])})
    contexts = {str(item.get("id")): item for item in snapshot["contexts"]}
    related = [
        relationship
        for relationship in snapshot["relationships"]
        if relationship.get("source_id") in planned_ids
        or relationship.get("target_id") in planned_ids
    ]
    world_view = _resolve_world_view(snapshot, request)
    missing_inputs = [
        field for field in recipe.get("requiredInputs", []) if not fields.get(str(field), "")
    ]
    return {
        "status": "partial" if missing_inputs else "ready",
        "request": request,
        "interpretation": {
            "stage": stage,
            "goal": recipe.get("goal"),
            "missingMaterialInputs": missing_inputs,
        },
        "planning": {"selected": planned, "selectionReasons": selection_reasons},
        "retrieval": {
            "status": "unavailable",
            "message": (
                "No live Cognee adapter is connected. This view shows deterministic planned "
                "context only."
            ),
            "returned": [],
            "accepted": [],
            "rejected": [],
        },
        "agentPacket": {
            "entities": planned,
            "relationships": related,
            "contexts": [contexts[item] for item in context_ids if item in contexts],
            "evidence": [evidence[item] for item in evidence_ids if item in evidence],
            "worldView": world_view,
            "reasoningInstructions": recipe.get("reasoningInstructions", []),
        },
        "limitations": [
            "This simulation has not run a language model.",
            (
                "Public research does not establish proprietary Nike design, legal, accessibility, "
                "or approval standards."
            ),
        ],
    }


@dataclass(frozen=True)
class _ServerState:
    workspace: Path
    static_dir: Path


def serve_explorer(workspace: Path, host: str, port: int) -> None:
    state = _ServerState(workspace.resolve(), Path(__file__).parent / "static")

    class ExplorerHandler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:  # noqa: A003
            print(f"[brand-world-explorer] {format % args}")

        def _json(self, body: object, status: HTTPStatus = HTTPStatus.OK) -> None:
            payload = json.dumps(body, default=str).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            if path == "/api/snapshot":
                self._json(build_snapshot(state.workspace))
                return
            requested = "index.html" if path in {"/", ""} else path.lstrip("/")
            target = (state.static_dir / requested).resolve()
            if state.static_dir not in target.parents or not target.is_file():
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            content = target.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header(
                "Content-Type", mimetypes.guess_type(target.name)[0] or "application/octet-stream"
            )
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        def do_POST(self) -> None:  # noqa: N802
            if urlparse(self.path).path != "/api/simulate":
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            length = int(self.headers.get("Content-Length", "0"))
            try:
                request = json.loads(self.rfile.read(length))
                if not isinstance(request, dict):
                    raise ValueError("request must be an object")
            except (ValueError, json.JSONDecodeError) as error:
                self._json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
                return
            self._json(simulate_context(build_snapshot(state.workspace), request))

    server = ThreadingHTTPServer((host, port), ExplorerHandler)
    print(f"Brand World Explorer: http://{host}:{port}")
    print(f"Workspace: {state.workspace}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nBrand World Explorer stopped.")
    finally:
        server.server_close()
