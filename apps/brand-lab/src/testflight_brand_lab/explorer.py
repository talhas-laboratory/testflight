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
ATLAS_WORKSPACE_FILES = {
    "product_index": "product-library/artifacts/product-index.yaml",
    "product_knowledge": "product-library/artifacts/product-knowledge.yaml",
    "product_purpose": "product-library/artifacts/product-purpose-connections.yaml",
    "product_end_user": "product-library/artifacts/product-end-user-connections.yaml",
    "content_model": "content-strategy/artifacts/relational-content-model.yaml",
    "newsletter_agent": "content-strategy/artifacts/newsletter-agent-charter.yaml",
    "content_rubric": "content-strategy/artifacts/evaluation-rubric.yaml",
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


def _first_text(record: dict[str, Any], *keys: str, fallback: str) -> str:
    for key in keys:
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return fallback


def _atlas_node(
    *,
    record_id: str,
    label: str,
    domain: str,
    record_type: str,
    source_path: str,
    payload: dict[str, Any],
    status: str = "recorded",
    epistemic_status: str = "structural",
    description: str = "",
) -> dict[str, Any]:
    return {
        "id": record_id,
        "label": label,
        "domain": domain,
        "recordType": record_type,
        "status": status,
        "epistemicStatus": epistemic_status,
        "description": description,
        "sourcePath": source_path,
        "payload": payload,
    }


def build_atlas_data(
    *,
    manifest: dict[str, Any],
    entities: list[dict[str, Any]],
    relationships: list[dict[str, Any]],
    contexts: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    sources: list[dict[str, Any]],
    visual_language: dict[str, Any],
    world_model: dict[str, Any],
    supplemental_graphs: dict[str, dict[str, Any]],
    atlas_sources: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Project every structured Biotic world record into one boundary-aware atlas.

    The atlas is a read-only navigation projection. Domain identity and source payloads
    are retained so progressive disclosure never replaces the canonical files.
    """

    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    seen_nodes: set[str] = set()
    seen_edges: set[str] = set()

    def add_node(node: dict[str, Any]) -> None:
        node_id = str(node["id"])
        if node_id and node_id not in seen_nodes:
            seen_nodes.add(node_id)
            nodes.append(node)

    def add_edge(
        edge_id: str,
        source_id: str,
        target_id: str,
        relation_type: str,
        domain: str,
        source_path: str,
        *,
        status: str = "recorded",
        epistemic_status: str = "structural",
        payload: dict[str, Any] | None = None,
    ) -> None:
        if edge_id in seen_edges:
            return
        seen_edges.add(edge_id)
        edges.append(
            {
                "id": edge_id,
                "sourceId": source_id,
                "targetId": target_id,
                "relationshipType": relation_type,
                "domain": domain,
                "status": status,
                "epistemicStatus": epistemic_status,
                "sourcePath": source_path,
                "payload": payload or {},
            }
        )

    brand_id = str(manifest.get("brand_id"))
    add_node(
        _atlas_node(
            record_id=brand_id,
            label=str(manifest.get("name", "Biotic / Hellobiotic")),
            domain="public-core",
            record_type="brand-root",
            source_path="WORKSPACE.yaml",
            payload=manifest,
            status=str(manifest.get("status", "active_research")),
            description=str(manifest.get("mission", "")),
        )
    )

    for record in entities:
        record_id = str(record.get("id"))
        add_node(
            _atlas_node(
                record_id=record_id,
                label=_first_text(record, "label", fallback=record_id),
                domain="public-core",
                record_type=str(record.get("entity_type", "entity")),
                source_path="artifacts/entity-inventory.yaml",
                payload=record,
                status=str(record.get("status", "proposed")),
                epistemic_status=str(record.get("epistemic_status", "reported")),
                description=str(record.get("description", "")),
            )
        )
    for record in relationships:
        add_edge(
            str(record.get("id")),
            str(record.get("source_id")),
            str(record.get("target_id")),
            str(record.get("relationship_type", "related_to")),
            "public-core",
            "artifacts/relationship-inventory.yaml",
            status=str(record.get("status", "proposed")),
            epistemic_status=str(record.get("epistemic_status", "reported")),
            payload=record,
        )

    for record in contexts:
        record_id = str(record.get("id"))
        add_node(
            _atlas_node(
                record_id=record_id,
                label=_first_text(record, "purpose", fallback=record_id),
                domain="world-model",
                record_type="context",
                source_path="artifacts/context-profiles.yaml",
                payload=record,
                status="recorded",
                epistemic_status="reported",
                description=str(record.get("purpose", "")),
            )
        )
        for entity in entities:
            if record_id in entity.get("context_ids", []):
                add_edge(
                    f"atlas:context:{record_id}:{entity.get('id')}",
                    record_id,
                    str(entity.get("id")),
                    "applies_to",
                    "world-model",
                    "artifacts/context-profiles.yaml",
                )

    world_keys = {
        "states": ("state_id", "state snapshot"),
        "perspectives": ("perspective_id", "perspective"),
        "relationship_frames": ("frame_id", "relationship frame"),
        "branches": ("branch_id", "world branch"),
        "branch_deltas": ("delta_id", "branch delta"),
        "conflicts": ("conflict_id", "conflict"),
        "hypotheses": ("hypothesis_id", "hypothesis"),
        "experiments": ("experiment_id", "experiment"),
        "observed_outcomes": ("outcome_id", "observed outcome"),
        "learning_updates": ("learning_id", "learning update"),
        "evidence_links": ("link_id", "evidence link"),
    }
    for key, (id_key, record_type) in world_keys.items():
        for record in _as_list(world_model.get(key)):
            record_id = str(record.get(id_key, ""))
            if not record_id:
                continue
            label = _first_text(
                record,
                "label",
                "proposition",
                "state_type_id",
                "perspective_type_id",
                "frame_type_id",
                fallback=record_id,
            )
            add_node(
                _atlas_node(
                    record_id=record_id,
                    label=label.replace("world://ontology/brand/", ""),
                    domain="world-model",
                    record_type=record_type,
                    source_path="artifacts/world-modeling.yaml",
                    payload=record,
                    status=str(record.get("status", "recorded")),
                    epistemic_status=str(record.get("epistemic_status", "structural")),
                    description=_first_text(record, "note", "mechanism_description", fallback=""),
                )
            )
            context_id = record.get("context_id")
            if isinstance(context_id, str) and context_id:
                add_edge(
                    f"atlas:world-context:{record_id}:{context_id}",
                    record_id,
                    context_id,
                    "bounded_by",
                    "world-model",
                    "artifacts/world-modeling.yaml",
                )

    for record in _as_list(world_model.get("evidence_links")):
        link_id = str(record.get("link_id", ""))
        evidence_id = str(record.get("evidence_id", ""))
        target_id = str(record.get("target_id", ""))
        if link_id and evidence_id:
            add_edge(
                f"atlas:evidence-link-source:{link_id}:{evidence_id}",
                link_id,
                evidence_id,
                "links_evidence",
                "world-model",
                "artifacts/world-modeling.yaml",
                status="supported",
                epistemic_status="reported",
                payload=record,
            )
        if link_id and target_id:
            add_edge(
                f"atlas:evidence-link-target:{link_id}:{target_id}",
                link_id,
                target_id,
                str(record.get("role", "supports")),
                "world-model",
                "artifacts/world-modeling.yaml",
                status="supported",
                epistemic_status="reported",
                payload=record,
            )
    for record in _as_list(world_model.get("states")):
        for subject_id in record.get("subject_ids", []):
            add_edge(
                f"atlas:state-subject:{record.get('state_id')}:{subject_id}",
                str(record.get("state_id")),
                str(subject_id),
                "describes_subject",
                "world-model",
                "artifacts/world-modeling.yaml",
                status=str(record.get("status", "recorded")),
                payload=record,
            )
    for record in _as_list(world_model.get("relationship_frames")):
        for binding in _as_list(record.get("role_bindings")):
            for record_id in binding.get("record_ids", []):
                add_edge(
                    f"atlas:frame-role:{record.get('frame_id')}:{binding.get('role_id')}:{record_id}",
                    str(record.get("frame_id")),
                    str(record_id),
                    f"role_{binding.get('role_id')}",
                    "world-model",
                    "artifacts/world-modeling.yaml",
                    status=str(record.get("status", "recorded")),
                    payload=binding,
                )
    for record in _as_list(world_model.get("perspectives")):
        for record_id in record.get("accessible_record_selectors", []):
            add_edge(
                f"atlas:perspective-access:{record.get('perspective_id')}:{record_id}",
                str(record.get("perspective_id")),
                str(record_id),
                "can_interpret",
                "world-model",
                "artifacts/world-modeling.yaml",
                status="bounded",
                payload=record,
            )

    for record in evidence:
        record_id = str(record.get("id"))
        add_node(
            _atlas_node(
                record_id=record_id,
                label=_first_text(record, "evidence_excerpt", fallback=record_id),
                domain="evidence",
                record_type="evidence",
                source_path="artifacts/evidence-notes.yaml",
                payload=record,
                status="recorded",
                epistemic_status=str(record.get("epistemic_status", "reported")),
                description=" ".join(
                    str(value) for value in record.get("paraphrased_findings", [])
                ),
            )
        )
        source_id = str(record.get("source_id", ""))
        if source_id:
            add_edge(
                f"atlas:evidence-source:{record_id}:{source_id}",
                record_id,
                source_id,
                "derived_from",
                "evidence",
                "artifacts/evidence-notes.yaml",
            )
    for record in sources:
        record_id = str(record.get("id"))
        add_node(
            _atlas_node(
                record_id=record_id,
                label=_first_text(record, "title", fallback=record_id),
                domain="evidence",
                record_type="source",
                source_path="artifacts/source-catalog.yaml",
                payload=record,
                status=str(record.get("status", "recorded")),
                epistemic_status="source",
                description=_first_text(
                    record, "notes", fallback=str(record.get("canonical_url", ""))
                ),
            )
        )
    for entity in entities:
        for evidence_id in entity.get("evidence_ids", []):
            add_edge(
                f"atlas:entity-evidence:{entity.get('id')}:{evidence_id}",
                str(entity.get("id")),
                str(evidence_id),
                "supported_by",
                "evidence",
                "artifacts/entity-inventory.yaml",
            )

    for graph_domain, graph in supplemental_graphs.items():
        if not graph.get("available"):
            continue
        for record in _as_list(graph.get("nodes")):
            record_id = str(record.get("id"))
            add_node(
                _atlas_node(
                    record_id=record_id,
                    label=_first_text(record, "label", fallback=record_id),
                    domain=graph_domain,
                    record_type=str(record.get("entityType", "entity")),
                    source_path=f"{graph_domain}/graph.json",
                    payload=record,
                    status=str(record.get("status", "recorded")),
                    epistemic_status=str(record.get("epistemicStatus", "observed")),
                    description=str(record.get("summary", "")),
                )
            )
        for record in _as_list(graph.get("edges")):
            add_edge(
                str(record.get("id")),
                str(record.get("sourceId")),
                str(record.get("targetId")),
                str(record.get("relationshipType", "related_to")),
                graph_domain,
                f"{graph_domain}/graph.json",
                status=str(record.get("status", "recorded")),
                epistemic_status=str(record.get("epistemicStatus", "observed")),
                payload=record,
            )

    visual_groups = {
        "profiles": ("id", "visual profile"),
        "references": ("id", "visual reference"),
        "revisions": ("id", "visual revision"),
        "bindings": ("id", "visual binding"),
    }
    for key, (id_key, record_type) in visual_groups.items():
        for record in _as_list(visual_language.get(key)):
            record_id = str(record.get(id_key, ""))
            if not record_id:
                continue
            add_node(
                _atlas_node(
                    record_id=record_id,
                    label=_first_text(record, "label", "description", fallback=record_id),
                    domain="visual-language",
                    record_type=record_type,
                    source_path="visual-language/manifest.json",
                    payload=record,
                    status=str(record.get("status", "recorded")),
                    epistemic_status=str(
                        record.get("epistemicStatus", record.get("authority", "observed"))
                    ),
                    description=str(record.get("description", "")),
                )
            )
    for revision in _as_list(visual_language.get("revisions")):
        for module in _as_list(revision.get("modules")):
            add_edge(
                f"atlas:visual-module:{revision.get('id')}:{module.get('referenceId')}",
                str(revision.get("id")),
                str(module.get("referenceId")),
                str(module.get("mode", "includes")),
                "visual-language",
                "visual-language/manifest.json",
                payload=module,
            )
    for binding in _as_list(visual_language.get("bindings")):
        add_edge(
            f"atlas:visual-binding:{binding.get('id')}:{binding.get('revisionId')}",
            str(binding.get("id")),
            str(binding.get("revisionId")),
            "selects_revision",
            "visual-language",
            "visual-language/manifest.json",
            payload=binding,
        )

    product_index = atlas_sources.get("product_index", {})
    product_knowledge = atlas_sources.get("product_knowledge", {})
    for record in _as_list(product_index.get("products")):
        record_id = str(record.get("product_uid"))
        add_node(
            _atlas_node(
                record_id=record_id,
                label=_first_text(record, "display_name", fallback=record_id),
                domain="product-library",
                record_type="product",
                source_path="product-library/artifacts/product-index.yaml",
                payload=record,
                status=str(record.get("lifecycle_status", "recorded")),
                epistemic_status=str(record.get("source_status", "reported")),
                description="Stable public product identity.",
            )
        )
        offering_id = record.get("offering_entity_id")
        if isinstance(offering_id, str) and offering_id:
            add_edge(
                f"atlas:product-offering:{record_id}:{offering_id}",
                record_id,
                offering_id,
                "instantiates_offering",
                "product-library",
                "product-library/artifacts/product-index.yaml",
                payload=record,
            )
    for record in _as_list(product_knowledge.get("records")):
        product_id = str(record.get("product_uid"))
        for variant in _as_list(record.get("public_variants")):
            variant_id = str(variant.get("sku_uid"))
            add_node(
                _atlas_node(
                    record_id=variant_id,
                    label=_first_text(variant, "size_label", fallback=variant_id),
                    domain="product-library",
                    record_type="product variant",
                    source_path="product-library/artifacts/product-knowledge.yaml",
                    payload=variant,
                    status="publicly_observed",
                    epistemic_status="reported",
                )
            )
            add_edge(
                f"atlas:product-variant:{product_id}:{variant_id}",
                product_id,
                variant_id,
                "has_variant",
                "product-library",
                "product-library/artifacts/product-knowledge.yaml",
            )
    for key, source_path in (
        ("product_purpose", "product-library/artifacts/product-purpose-connections.yaml"),
        ("product_end_user", "product-library/artifacts/product-end-user-connections.yaml"),
    ):
        for record in _as_list(atlas_sources.get(key, {}).get("relations")):
            target_id = str(record.get("target_entity_id", ""))
            if not target_id and record.get("target_label"):
                target_id = f"concept:product:{str(record.get('target_label')).replace(' ', '-')}"
                add_node(
                    _atlas_node(
                        record_id=target_id,
                        label=str(record.get("target_label")),
                        domain="product-library",
                        record_type="product concern",
                        source_path=source_path,
                        payload={"label": record.get("target_label")},
                        status="proposed",
                        epistemic_status=str(record.get("source_status", "reported")),
                    )
                )
            add_edge(
                str(record.get("relation_id")),
                str(record.get("product_uid")),
                target_id,
                str(record.get("relation", "related_to")),
                "product-library",
                source_path,
                status=("held" if record.get("source_status") == "held_hypothesis" else "recorded"),
                epistemic_status=str(record.get("source_status", "reported")),
                payload=record,
            )

    content_model = atlas_sources.get("content_model", {})
    content_root_id = str(
        content_model.get("model_id", "world://brand/hellobiotic/content-strategy/relational-field")
    )
    add_node(
        _atlas_node(
            record_id=content_root_id,
            label="Relational content field",
            domain="content-strategy",
            record_type="semantic model",
            source_path="content-strategy/artifacts/relational-content-model.yaml",
            payload=content_model,
            status=str(content_model.get("status", "proposed_foundation")),
            epistemic_status="founder-directed",
            description=str(content_model.get("purpose", "")),
        )
    )
    semantic_types = content_model.get("semantic_types", {})
    if isinstance(semantic_types, dict):
        for name, record in semantic_types.items():
            if not isinstance(record, dict):
                continue
            record_id = f"{content_root_id}/type/{name}"
            add_node(
                _atlas_node(
                    record_id=record_id,
                    label=str(name).replace("_", " "),
                    domain="content-strategy",
                    record_type=str(record.get("kind", "semantic type")),
                    source_path="content-strategy/artifacts/relational-content-model.yaml",
                    payload=record,
                    status="proposed",
                    epistemic_status="founder-directed",
                    description=str(record.get("definition", "")),
                )
            )
            add_edge(
                f"atlas:content-type:{content_root_id}:{name}",
                content_root_id,
                record_id,
                "defines",
                "content-strategy",
                "content-strategy/artifacts/relational-content-model.yaml",
            )
    for index, record in enumerate(_as_list(content_model.get("relations")), start=1):
        source_id = f"{content_root_id}/type/{record.get('from')}"
        target_id = f"{content_root_id}/type/{record.get('to')}"
        add_edge(
            f"atlas:content-relation:{index}:{record.get('id')}",
            source_id,
            target_id,
            str(record.get("id", "related_to")),
            "content-strategy",
            "content-strategy/artifacts/relational-content-model.yaml",
            status="proposed",
            epistemic_status="founder-directed",
            payload=record,
        )
    for record in _as_list(content_model.get("biotic_candidate_fields")):
        record_id = str(record.get("id"))
        add_node(
            _atlas_node(
                record_id=record_id,
                label=record_id.replace("field:", "").replace("-", " "),
                domain="content-strategy",
                record_type="candidate field",
                source_path="content-strategy/artifacts/relational-content-model.yaml",
                payload=record,
                status=str(record.get("status", "proposed")),
                epistemic_status="hypothesized",
            )
        )
        add_edge(
            f"atlas:content-field:{content_root_id}:{record_id}",
            content_root_id,
            record_id,
            "proposes_field",
            "content-strategy",
            "content-strategy/artifacts/relational-content-model.yaml",
            status="held",
            epistemic_status="hypothesized",
        )
    agent = atlas_sources.get("newsletter_agent", {})
    if agent.get("agent_id"):
        agent_id = str(agent["agent_id"])
        add_node(
            _atlas_node(
                record_id=agent_id,
                label="Newsletter strategist agent",
                domain="content-strategy",
                record_type="agent charter",
                source_path="content-strategy/artifacts/newsletter-agent-charter.yaml",
                payload=agent,
                status=str(agent.get("status", "proposal_only")),
                epistemic_status="founder-directed",
                description=str(agent.get("mission", "")),
            )
        )
        add_edge(
            f"atlas:agent-model:{agent_id}:{content_root_id}",
            agent_id,
            content_root_id,
            "uses_model",
            "content-strategy",
            "content-strategy/artifacts/newsletter-agent-charter.yaml",
            status="candidate",
            epistemic_status="configured",
        )
        for step in _as_list(agent.get("workflow")):
            step_name = str(step.get("id", ""))
            if not step_name:
                continue
            step_id = f"{agent_id}/step/{step_name}"
            add_node(
                _atlas_node(
                    record_id=step_id,
                    label=step_name.replace("_", " "),
                    domain="content-strategy",
                    record_type="agent step",
                    source_path="content-strategy/artifacts/newsletter-agent-charter.yaml",
                    payload=step,
                    status="proposal_only",
                    epistemic_status="configured",
                    description=str(step.get("action", "")),
                )
            )
            add_edge(
                f"atlas:agent-step:{agent_id}:{step_name}",
                agent_id,
                step_id,
                "performs",
                "content-strategy",
                "content-strategy/artifacts/newsletter-agent-charter.yaml",
                status="candidate",
                epistemic_status="configured",
            )
    rubric = atlas_sources.get("content_rubric", {})
    if rubric.get("rubric_id"):
        rubric_id = str(rubric["rubric_id"])
        add_node(
            _atlas_node(
                record_id=rubric_id,
                label="Newsletter content evaluation",
                domain="content-strategy",
                record_type="evaluation rubric",
                source_path="content-strategy/artifacts/evaluation-rubric.yaml",
                payload=rubric,
                status="candidate",
                epistemic_status="configured",
                description=str(rubric.get("purpose", "")),
            )
        )
        if agent.get("agent_id"):
            add_edge(
                f"atlas:agent-rubric:{agent.get('agent_id')}:{rubric_id}",
                str(agent.get("agent_id")),
                rubric_id,
                "evaluated_by",
                "content-strategy",
                "content-strategy/artifacts/evaluation-rubric.yaml",
                status="candidate",
                epistemic_status="configured",
            )
        dimensions = rubric.get("dimensions", {})
        if isinstance(dimensions, dict):
            for name, dimension in dimensions.items():
                if not isinstance(dimension, dict):
                    continue
                dimension_id = f"{rubric_id}/dimension/{name}"
                add_node(
                    _atlas_node(
                        record_id=dimension_id,
                        label=str(name).replace("_", " "),
                        domain="content-strategy",
                        record_type="evaluation dimension",
                        source_path="content-strategy/artifacts/evaluation-rubric.yaml",
                        payload=dimension,
                        status="candidate",
                        epistemic_status="configured",
                        description=(
                            f"Pass condition: {dimension.get('pass_condition', 'not recorded')}"
                        ),
                    )
                )
                add_edge(
                    f"atlas:rubric-dimension:{rubric_id}:{name}",
                    rubric_id,
                    dimension_id,
                    "evaluates",
                    "content-strategy",
                    "content-strategy/artifacts/evaluation-rubric.yaml",
                    status="candidate",
                    epistemic_status="configured",
                )

    domain_order = [
        (
            "public-core",
            "Public Brand core",
            (
                "Identity, expression, offering, experience, perception, governance, "
                "environment and events."
            ),
        ),
        (
            "world-model",
            "World model",
            "Context, state, perspective, frames, branches, conflicts and learning.",
        ),
        (
            "product-library",
            "Product library",
            (
                "Stable product identity, variants, visible attributes and bounded "
                "product connections."
            ),
        ),
        (
            "audience",
            "Audience evidence",
            "Observed audience signals, information needs, hypotheses and explicit evidence gaps.",
        ),
        (
            "copy-claims",
            "Copy + claims",
            "Public language, claims, modules, attributes and claim boundaries.",
        ),
        (
            "visual-language",
            "Visual language",
            "Observed public visual system, revisions, references, bindings and rights.",
        ),
        (
            "content-strategy",
            "Content strategy",
            "Founder-directed relational model and proposal-only newsletter agent.",
        ),
        (
            "evidence",
            "Evidence substrate",
            "Source records and evidence notes supporting or limiting the modeled world.",
        ),
    ]
    domains = [
        {
            "id": domain_id,
            "label": label,
            "description": description,
            "nodeCount": sum(node["domain"] == domain_id for node in nodes),
            "edgeCount": sum(edge["domain"] == domain_id for edge in edges),
        }
        for domain_id, label, description in domain_order
    ]
    dangling = [
        edge["id"]
        for edge in edges
        if edge["sourceId"] not in seen_nodes or edge["targetId"] not in seen_nodes
    ]
    return {
        "version": 1,
        "projection": "read-only-progressive-atlas",
        "domains": domains,
        "nodes": nodes,
        "edges": edges,
        "coverage": {
            "nodeCount": len(nodes),
            "edgeCount": len(edges),
            "danglingEdgeIds": dangling,
            "complete": not dangling,
        },
    }


def build_snapshot(workspace: Path) -> dict[str, Any]:
    """Compile canonical records into a browser-safe, normalized snapshot."""
    workspace = workspace.resolve()
    paths = {key: _workspace_path(workspace, value) for key, value in WORKSPACE_FILES.items()}
    optional_paths = {
        key: workspace / value
        for key, value in OPTIONAL_WORKSPACE_FILES.items()
        if (workspace / value).is_file()
    }
    atlas_paths = {
        key: workspace / value
        for key, value in ATLAS_WORKSPACE_FILES.items()
        if (workspace / value).is_file()
    }
    atlas_sources = {key: _read_yaml(path) for key, path in atlas_paths.items()}
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

    serialized_world_model = (
        _serialized_world_model(world_model_records)
        if world_model_records is not None
        else {"available": False}
    )
    atlas = build_atlas_data(
        manifest=manifest,
        entities=entities,
        relationships=relationships,
        contexts=contexts,
        evidence=evidence,
        sources=sources,
        visual_language=visual_language,
        world_model=serialized_world_model,
        supplemental_graphs={
            "visual-language": visual_graph,
            "copy-claims": copy_claims_graph,
            "audience": audience_graph,
        },
        atlas_sources=atlas_sources,
    )

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
            "worldModel": (serialized_world_model),
            "atlas": atlas,
            "workflow": workflow_file,
            "intelligence": intelligence,
            "diagnostics": diagnostics,
            "provenance": {
                "generatedAt": datetime.now(UTC).isoformat(),
                "sourceHash": _source_hash(
                    [*paths.values(), *optional_paths.values(), *atlas_paths.values()]
                ),
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
    design_tokens: Path


def serve_explorer(workspace: Path, host: str, port: int) -> None:
    state = _ServerState(
        workspace.resolve(),
        Path(__file__).parent / "static",
        Path(__file__).resolve().parents[4]
        / "packages"
        / "testflight-design-language"
        / "tokens.css",
    )

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
            if path == "/design/tokens.css":
                content = state.design_tokens.read_bytes()
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "text/css; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
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
