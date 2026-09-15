"""Exact, rebuildable Cognee projection of a Brand World v3 branch.

The World service remains canonical.  This adapter projects a single immutable
workspace/branch snapshot into typed nodes and declared edges, without using an
LLM or ``cognify``.  It therefore preserves the distinctions that matter for
reasoning: record kind, lifecycle, version, evidence, provenance, authority,
time and relation participant roles.
"""

from __future__ import annotations

import json
import os
from collections import deque
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import UUID

from testflight_semantic import (
    WorldClaim,
    WorldDecision,
    WorldEvent,
    WorldEvidence,
    WorldRecordType,
    WorldRelation,
    WorldSource,
    WorldState,
)
from testflight_semantic.ids import stable_id
from testflight_world import canonical_record_hash, snapshot_leaves, snapshot_root


@dataclass(frozen=True, slots=True)
class WorldV3ProjectionNode:
    node_id: UUID
    record_id: str
    record_version: int
    node_type: str
    label: str
    text: str
    metadata: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "node_id": str(self.node_id),
            "record_id": self.record_id,
            "record_version": self.record_version,
            "node_type": self.node_type,
            "label": self.label,
            "text": self.text,
            "metadata": self.metadata,
        }


@dataclass(frozen=True, slots=True)
class WorldV3ProjectionManifest:
    """A pure, inspectable view of one exact World v3 branch revision."""

    workspace_id: str
    branch_id: str
    dataset_name: str
    source_revision: str
    source_hash: str
    snapshot_root: str
    lifecycle_scope: tuple[str, ...]
    nodes: tuple[WorldV3ProjectionNode, ...]
    custom_edges: tuple[tuple[str, str, str, dict[str, Any]], ...]
    canonical: bool = False
    projection_kind: str = "world-v3-exact-graph"

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "projection_kind": self.projection_kind,
            "canonical": self.canonical,
            "workspace_id": self.workspace_id,
            "branch_id": self.branch_id,
            "dataset_name": self.dataset_name,
            "source_revision": self.source_revision,
            "source_hash": self.source_hash,
            "snapshot_root": self.snapshot_root,
            "lifecycle_scope": list(self.lifecycle_scope),
            "node_count": len(self.nodes),
            "edge_count": len(self.custom_edges),
            "nodes": [node.as_dict() for node in self.nodes],
            "custom_edges": [
                {
                    "source_id": source_id,
                    "target_id": target_id,
                    "predicate": predicate,
                    "metadata": metadata,
                }
                for source_id, target_id, predicate, metadata in self.custom_edges
            ],
        }


def _node_id(
    dataset_name: str, workspace_id: str, branch_id: str, record_id: str, version: int = 0
) -> UUID:
    return stable_id(
        "world-v3-cognee-node", dataset_name, workspace_id, branch_id, record_id, version
    )


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _record_payload(record: WorldRecordType) -> dict[str, Any]:
    return record.model_dump(mode="json")


def _record_label(record: WorldRecordType) -> str:
    if hasattr(record, "canonical_label"):
        return str(record.canonical_label)
    if isinstance(record, WorldSource):
        return record.title
    if isinstance(record, WorldClaim):
        return f"{record.predicate_id}: {record.object_id or record.object_value}"
    if isinstance(record, WorldDecision):
        return record.question
    if isinstance(record, WorldEvidence):
        return record.excerpt or record.measurement or record.id
    if isinstance(record, WorldState):
        return record.state_value
    if isinstance(record, WorldEvent):
        return record.event_type_id
    if isinstance(record, WorldRelation):
        return record.relation_type_id
    return record.id


def _index_text(record: WorldRecordType) -> str:
    """Deterministic retrieval text, deliberately smaller than canonical content."""

    fragments = [record.kind, _record_label(record), record.type_id, record.module_id]
    if isinstance(record, WorldClaim):
        fragments.extend(
            [record.predicate_id, record.object_id or record.object_value or "", record.claim_kind]
        )
    elif isinstance(record, WorldSource):
        fragments.extend([record.title, record.locator, record.content_policy])
    elif isinstance(record, WorldEvidence):
        # Source-governed excerpts are hydrated from the World only after selection.
        fragments.extend([record.locator, record.measurement or ""])
    elif isinstance(record, WorldState):
        fragments.extend([record.state_schema_id, record.state_value])
    elif isinstance(record, WorldEvent):
        fragments.append(record.event_type_id)
    elif isinstance(record, WorldRelation):
        fragments.append(record.relation_type_id)
    elif isinstance(record, WorldDecision):
        fragments.extend([record.question, *(item.label for item in record.alternatives)])
    elif hasattr(record, "definition"):
        fragments.append(str(record.definition))
    return "\n".join(fragment for fragment in fragments if fragment)


def _edge_class(record: WorldRecordType, predicate: str) -> tuple[str, str | None]:
    """Only relation-bearing V3 records may produce a canonical relation edge."""

    if isinstance(record, (WorldRelation, WorldEvent)) and predicate == "HAS_PARTICIPANT":
        return "canonical_relation", record.id
    if isinstance(record, WorldClaim) and predicate in {
        "HAS_SUBJECT",
        "HAS_OBJECT",
        "FROM_PERSPECTIVE",
    }:
        return "canonical_relation", record.id
    return "canonical_reference", None


def _reference_pairs(record: WorldRecordType) -> Iterable[tuple[str, str, dict[str, Any]]]:
    """Return only declared semantic references, with roles retained as edge data."""

    for ref in record.context_refs:
        yield "IN_CONTEXT", ref, {"reference_class": "context"}
    for ref in record.provenance_refs:
        yield "HAS_PROVENANCE", ref, {"reference_class": "provenance"}
    if record.derivation_ref:
        yield "DERIVED_FROM", record.derivation_ref, {"reference_class": "derivation"}
    if record.authority_ref:
        yield "AUTHORIZED_BY", record.authority_ref, {"reference_class": "authority"}
    if record.supersedes_ref:
        yield "SUPERSEDES", record.supersedes_ref.split("@", 1)[0], {"reference_class": "history"}
    if isinstance(record, WorldState):
        for subject_id in record.subject_ids:
            yield "STATE_OF", subject_id, {}
        for claim_id in record.described_by_claim_ids:
            yield "DESCRIBED_BY", claim_id, {}
    elif isinstance(record, WorldEvent):
        for participant in record.participants:
            yield "HAS_PARTICIPANT", participant.entity_id, {"role_id": participant.role_id}
        for evidence_id in record.evidence_ids:
            yield "SUPPORTED_BY", evidence_id, {}
    elif isinstance(record, WorldRelation):
        for participant in record.participants:
            yield "HAS_PARTICIPANT", participant.record_id, {"role_id": participant.role_id}
        for evidence_id in record.evidence_ids:
            yield "SUPPORTED_BY", evidence_id, {}
    elif isinstance(record, WorldClaim):
        yield "HAS_SUBJECT", record.subject_id, {}
        if record.object_id:
            yield "HAS_OBJECT", record.object_id, {}
        if record.perspective_id:
            yield "FROM_PERSPECTIVE", record.perspective_id, {}
        for evidence_id in record.evidence_ids:
            yield "SUPPORTED_BY", evidence_id, {"polarity": "support"}
        for evidence_id in record.opposing_evidence_ids:
            yield "OPPOSED_BY", evidence_id, {"polarity": "oppose"}
        for contradiction_id in record.contradiction_ids:
            yield "CONTRADICTS", contradiction_id, {}
    elif isinstance(record, WorldEvidence):
        yield "EXCERPT_OF", record.source_id, {}
    elif isinstance(record, WorldDecision):
        for evidence_id in record.evidence_ids:
            yield "INFORMED_BY", evidence_id, {}
        for affected_id in record.affected_record_ids:
            yield "AFFECTS", affected_id, {}
        if record.selected_alternative_id:
            yield (
                "SELECTED",
                f"{record.id}/alternative/{record.selected_alternative_id}",
                {"reference_class": "decision_alternative"},
            )


def build_world_v3_projection(
    records: Iterable[WorldRecordType],
    *,
    workspace_id: str,
    branch_id: str,
    dataset_name: str,
    source_revision: str,
    snapshot_root_value: str | None = None,
    lifecycle_scope: Iterable[str] = ("accepted",),
) -> WorldV3ProjectionManifest:
    """Build an exact graph projection with deterministic IDs and full declared links."""

    allowed_lifecycles = tuple(sorted(set(lifecycle_scope)))
    if not allowed_lifecycles:
        raise ValueError("World v3 projection requires an explicit lifecycle scope")
    if not dataset_name.endswith("_staging"):
        raise ValueError("World v3 projection requires an isolated *_staging dataset")
    selected = tuple(
        sorted(
            (
                record
                for record in records
                if record.workspace_id == workspace_id
                and record.branch_id == branch_id
                and record.lifecycle_status.value in allowed_lifecycles
            ),
            key=lambda item: (item.kind, item.id, item.record_version),
        )
    )
    if not selected:
        raise ValueError("World v3 projection requires at least one scoped record")
    ids = [record.id for record in selected]
    if len(ids) != len(set(ids)):
        raise ValueError("World v3 projection requires one current version per record id")

    leaves = snapshot_leaves(selected)
    computed_snapshot_root = snapshot_root(
        workspace_id=workspace_id,
        branch_id=branch_id,
        lifecycle_scope=allowed_lifecycles,
        leaves=leaves,
    )
    if snapshot_root_value and snapshot_root_value != computed_snapshot_root:
        raise ValueError("World v3 projection snapshot root does not match supplied records")
    resolved_snapshot_root = snapshot_root_value or computed_snapshot_root
    source_hash = resolved_snapshot_root
    known_ids = {record.id for record in selected}
    nodes: list[WorldV3ProjectionNode] = []
    edges: list[tuple[str, str, str, dict[str, Any]]] = []
    for record in selected:
        node_id = _node_id(dataset_name, workspace_id, branch_id, record.id, record.record_version)
        nodes.append(
            WorldV3ProjectionNode(
                node_id=node_id,
                record_id=record.id,
                record_version=record.record_version,
                node_type=f"world-v3:{record.kind}",
                label=_record_label(record),
                text=_index_text(record),
                metadata={
                    "workspace_id": workspace_id,
                    "branch_id": branch_id,
                    "kind": record.kind,
                    "type_id": record.type_id,
                    "schema_version": record.schema_version,
                    "record_version": record.record_version,
                    "canonical_record_hash": canonical_record_hash(record),
                    "projection_snapshot_root": resolved_snapshot_root,
                    "lifecycle_status": record.lifecycle_status.value,
                    "module_id": record.module_id,
                    "relation_type_id": (
                        record.relation_type_id if isinstance(record, WorldRelation) else None
                    ),
                    "valid_time": (
                        record.valid_time.model_dump(mode="json") if record.valid_time else None
                    ),
                    "known_time": (
                        record.known_time.model_dump(mode="json") if record.known_time else None
                    ),
                },
            )
        )
        for predicate, target_id, metadata in _reference_pairs(record):
            # An external declared reference is still a graph node. This makes missing
            # substrate visible instead of silently deleting the relationship.
            target_version = next(
                (candidate.record_version for candidate in selected if candidate.id == target_id), 0
            )
            edge_metadata = {
                **metadata,
                "source_record_id": record.id,
                "source_record_version": record.record_version,
                "target_record_id": target_id,
                "target_is_materialized": target_id in known_ids,
                "source_revision": source_revision,
                "projection_snapshot_root": resolved_snapshot_root,
            }
            edge_class, canonical_relation_id = _edge_class(record, predicate)
            edge_metadata["edge_class"] = edge_class
            if canonical_relation_id:
                edge_metadata["canonical_relation_id"] = canonical_relation_id
                edge_metadata["canonical_relation_hash"] = canonical_record_hash(record)
                edge_metadata["canonical_relation_type_id"] = (
                    record.relation_type_id
                    if isinstance(record, WorldRelation)
                    else record.event_type_id
                    if isinstance(record, WorldEvent)
                    else record.predicate_id
                    if isinstance(record, WorldClaim)
                    else None
                )
            edges.append(
                (
                    str(node_id),
                    str(
                        _node_id(
                            dataset_name,
                            workspace_id,
                            branch_id,
                            target_id,
                            target_version,
                        )
                    ),
                    predicate,
                    edge_metadata,
                )
            )
        if isinstance(record, WorldDecision):
            for alternative in record.alternatives:
                alternative_id = f"{record.id}/alternative/{alternative.id}"
                nodes.append(
                    WorldV3ProjectionNode(
                        node_id=_node_id(dataset_name, workspace_id, branch_id, alternative_id),
                        record_id=alternative_id,
                        record_version=0,
                        node_type="world-v3:decision-alternative",
                        label=alternative.label,
                        text=_json(alternative.model_dump(mode="json")),
                        metadata={
                            "workspace_id": workspace_id,
                            "branch_id": branch_id,
                            "decision_id": record.id,
                        },
                    )
                )
                edges.append(
                    (
                        str(node_id),
                        str(_node_id(dataset_name, workspace_id, branch_id, alternative_id)),
                        "HAS_ALTERNATIVE",
                        {
                            "alternative_id": alternative.id,
                            "source_revision": source_revision,
                            "projection_snapshot_root": resolved_snapshot_root,
                            "edge_class": "canonical_reference",
                        },
                    )
                )

    materialized_ids = {node.record_id for node in nodes}
    edge_targets = {
        (
            target_id,
            0
            if not metadata["target_is_materialized"]
            else next(record.record_version for record in selected if record.id == target_id),
        )
        for _, _, _, metadata in edges
        if (target_id := str(metadata.get("target_record_id", "")))
        and target_id not in materialized_ids
    }
    for target_id, target_version in sorted(edge_targets):
        nodes.append(
            WorldV3ProjectionNode(
                node_id=_node_id(dataset_name, workspace_id, branch_id, target_id, target_version),
                record_id=target_id,
                record_version=target_version,
                node_type="world-v3:external-reference",
                label=target_id,
                text=f"Declared external reference / {target_id}",
                metadata={
                    "workspace_id": workspace_id,
                    "branch_id": branch_id,
                    "reference_only": True,
                    "source_revision": source_revision,
                    "projection_snapshot_root": resolved_snapshot_root,
                },
            )
        )

    nodes.sort(key=lambda node: (node.node_type, node.record_id, node.record_version))
    edges.sort(key=lambda edge: (edge[0], edge[2], edge[1], _json(edge[3])))
    return WorldV3ProjectionManifest(
        workspace_id=workspace_id,
        branch_id=branch_id,
        dataset_name=dataset_name,
        source_revision=source_revision,
        source_hash=source_hash,
        snapshot_root=resolved_snapshot_root,
        lifecycle_scope=allowed_lifecycles,
        nodes=tuple(nodes),
        custom_edges=tuple(edges),
    )


def world_v3_projection_to_datapoints(manifest: WorldV3ProjectionManifest) -> list[Any]:
    """Turn the pure manifest into Cognee points only at the adapter boundary."""

    try:
        from cognee.infrastructure.engine import DataPoint
    except ModuleNotFoundError as error:
        raise RuntimeError("Cognee is required to populate a World v3 projection") from error

    class WorldV3DataPoint(DataPoint):
        dataset_name: str
        workspace_id: str
        branch_id: str
        record_id: str
        record_version: int
        node_type: str
        label: str
        text: str
        metadata_json: str
        metadata: dict = {"index_fields": ["label", "text"]}

    return [
        WorldV3DataPoint(
            id=node.node_id,
            dataset_name=manifest.dataset_name,
            workspace_id=manifest.workspace_id,
            branch_id=manifest.branch_id,
            record_id=node.record_id,
            record_version=node.record_version,
            node_type=node.node_type,
            label=node.label,
            text=node.text,
            metadata_json=_json(node.metadata),
        )
        for node in manifest.nodes
    ]


async def populate_world_v3_projection(manifest: WorldV3ProjectionManifest) -> dict[str, Any]:
    """Write only the exact graph, never LLM-extracted semantic approximations."""

    if not manifest.dataset_name.endswith("_staging"):
        raise ValueError("World v3 population requires an isolated *_staging dataset")
    try:
        from cognee.tasks.storage.add_data_points import add_data_points
    except ModuleNotFoundError as error:
        raise RuntimeError("Cognee is required to populate a World v3 projection") from error
    points = world_v3_projection_to_datapoints(manifest)
    result = await add_data_points(points, custom_edges=list(manifest.custom_edges))
    return {
        "dataset_name": manifest.dataset_name,
        "source_revision": manifest.source_revision,
        "source_hash": manifest.source_hash,
        "node_count": len(points),
        "edge_count": len(manifest.custom_edges),
        "result_type": type(result).__name__,
    }


def bounded_world_v3_traversal(
    manifest: WorldV3ProjectionManifest, *, source_record_id: str, max_hops: int = 2
) -> tuple[tuple[str, str, str, dict[str, Any]], ...]:
    """Deterministic local traversal for graph consumers and tests; max two hops by policy."""

    if max_hops < 0 or max_hops > 2:
        raise ValueError("max_hops must be between 0 and 2")
    source_nodes = {
        str(node.node_id) for node in manifest.nodes if node.record_id == source_record_id
    }
    if not source_nodes:
        return ()
    edges_by_source: dict[str, list[tuple[str, str, str, dict[str, Any]]]] = {}
    for edge in manifest.custom_edges:
        edges_by_source.setdefault(edge[0], []).append(edge)
    output: list[tuple[str, str, str, dict[str, Any]]] = []
    queue = deque((node_id, 0) for node_id in sorted(source_nodes))
    seen = set(source_nodes)
    while queue:
        node_id, depth = queue.popleft()
        if depth >= max_hops:
            continue
        for edge in edges_by_source.get(node_id, []):
            output.append(edge)
            if edge[1] not in seen:
                seen.add(edge[1])
                queue.append((edge[1], depth + 1))
    return tuple(output)


def validate_world_v3_projection(manifest: WorldV3ProjectionManifest) -> None:
    """Fail before population when a graph would be structurally incomplete."""

    node_ids = {str(node.node_id) for node in manifest.nodes}
    if len(node_ids) != len(manifest.nodes):
        raise ValueError("World v3 projection contains duplicate graph node identities")
    dangling = [
        edge for edge in manifest.custom_edges if edge[0] not in node_ids or edge[1] not in node_ids
    ]
    if dangling:
        raise ValueError("World v3 projection contains dangling graph edges")
    if not manifest.source_hash or not manifest.source_revision or not manifest.snapshot_root:
        raise ValueError("World v3 projection requires source lineage")
    for node in manifest.nodes:
        if node.node_type != "world-v3:external-reference" and not node.metadata.get(
            "canonical_record_hash"
        ):
            raise ValueError("World v3 projection node lacks a canonical record hash")
    for _, _, _, metadata in manifest.custom_edges:
        edge_class = metadata.get("edge_class")
        if edge_class not in {"canonical_relation", "canonical_reference"}:
            raise ValueError("World v3 projection edge lacks a valid classification")
        if edge_class == "canonical_relation" and not metadata.get("canonical_relation_id"):
            raise ValueError("canonical relation edge lacks its canonical relation identity")


def write_world_v3_projection_manifest(manifest: WorldV3ProjectionManifest, path: Path) -> None:
    """Atomically persist derived inspection state outside the canonical World store."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(manifest.as_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def compare_world_v3_projection_drift(
    current: WorldV3ProjectionManifest, previous: dict[str, Any] | None
) -> dict[str, Any]:
    if previous is None:
        return {
            "status": "missing",
            "changed_record_ids": [node.record_id for node in current.nodes],
        }
    if (
        previous.get("source_hash") == current.source_hash
        and previous.get("source_revision") == current.source_revision
    ):
        return {"status": "up_to_date", "changed_record_ids": []}
    previous_nodes = {str(node.get("record_id")): node for node in previous.get("nodes", [])}
    changed = [
        node.record_id
        for node in current.nodes
        if previous_nodes.get(node.record_id, {}).get("metadata") != node.metadata
    ]
    return {"status": "drifted", "changed_record_ids": sorted(set(changed))}


__all__ = [
    "WorldV3ProjectionManifest",
    "WorldV3ProjectionNode",
    "bounded_world_v3_traversal",
    "build_world_v3_projection",
    "compare_world_v3_projection_drift",
    "populate_world_v3_projection",
    "world_v3_projection_to_datapoints",
    "write_world_v3_projection_manifest",
    "validate_world_v3_projection",
]
