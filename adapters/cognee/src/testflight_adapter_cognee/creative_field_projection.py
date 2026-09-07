"""Rebuildable Cognee projection for project-scoped Creative Field records.

The Creative Field package is canonical.  This module only creates a deterministic,
proposal-only projection suitable for an isolated child container.  Cognee imports are
kept lazy so source hashing, dry-runs and certification work without the optional upstream.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import UUID

from testflight_creative_field import CreativeRecord, LifecycleStatus, SourceLicenseRecord
from testflight_semantic.ids import stable_id

_IDENTITY_FIELDS: dict[str, str] = {
    "CreativeProject": "project_id",
    "Moodboard": "moodboard_id",
    "SourceLicenseRecord": "license_record_id",
    "ReferenceAsset": "asset_id",
    "Placement": "placement_id",
    "ReferenceCluster": "cluster_id",
    "UserAnnotation": "annotation_id",
    "BoardRevision": "board_revision_id",
    "ObservedFeature": "feature_id",
    "InterpretationAlternative": "alternative_id",
    "ReferenceContribution": "contribution_id",
    "ReferenceInterpretation": "interpretation_id",
    "ReviewDecision": "review_id",
    "FieldDimension": "dimension_id",
    "DimensionState": "dimension_id",
    "Principle": "principle_id",
    "Tension": "tension_id",
    "Exclusion": "exclusion_id",
    "FieldConflict": "conflict_id",
    "MissingDimension": "dimension_id",
    "CreativeFieldProposal": "proposal_id",
    "CreativeFieldRun": "run_id",
    "CreativeFieldVersion": "version_id",
    "ProjectBinding": "binding_id",
    "FieldBinding": "binding_id",
    "LocalOverride": "override_id",
    "CreativeRequest": "request_id",
    "ResolvedCreativeRequest": "request_id",
    "FieldProjection": "projection_id",
    "CreativeContextPacket": "packet_id",
    "TargetCapabilityManifest": "target_id",
    "GenerationPacket": "packet_id",
    "InvocationReceipt": "invocation_id",
    "CreativeOutput": "output_id",
    "CreativeEvaluation": "evaluation_id",
    "FeedbackRecord": "feedback_id",
}


@dataclass(frozen=True, slots=True)
class CreativeProjectionDocument:
    """One source-bearing document in the child projection."""

    document_id: UUID
    record_type: str
    record_id: str
    source_url: str
    text: str
    metadata: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "document_id": str(self.document_id),
            "record_type": self.record_type,
            "record_id": self.record_id,
            "source_url": self.source_url,
            "text": self.text,
            "metadata": self.metadata,
        }


@dataclass(frozen=True, slots=True)
class CreativeFieldProjectionManifest:
    """Deterministic child-container projection manifest."""

    child_workspace_id: str
    parent_workspace_id: str
    project_id: str
    dataset_name: str
    source_hash: str
    documents: tuple[CreativeProjectionDocument, ...]
    custom_edges: tuple[tuple[str, str, str, dict[str, Any]], ...]
    route: str = "creative-field"
    canonical: bool = False
    promotion_status: str = "proposal_only"

    @property
    def child_container_id(self) -> str:
        return self.child_workspace_id

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "child_workspace_id": self.child_workspace_id,
            "parent_workspace_id": self.parent_workspace_id,
            "project_id": self.project_id,
            "dataset_name": self.dataset_name,
            "source_hash": self.source_hash,
            "route": self.route,
            "canonical": self.canonical,
            "promotion_status": self.promotion_status,
            "document_count": len(self.documents),
            "edge_count": len(self.custom_edges),
            "documents": [document.as_dict() for document in self.documents],
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


def _record_id(record: CreativeRecord) -> str:
    record_type = type(record).__name__
    try:
        identity_field = _IDENTITY_FIELDS[record_type]
    except KeyError as error:
        raise TypeError(f"unsupported Creative Field record type: {record_type}") from error
    return str(getattr(record, identity_field))


def _json(record: CreativeRecord) -> str:
    return json.dumps(
        record.model_dump(mode="json"),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _record_hash(record: CreativeRecord) -> str:
    return hashlib.sha256(_json(record).encode("utf-8")).hexdigest()


def _last_verified(record: CreativeRecord) -> str:
    for field in ("created_at", "recorded_at", "createdAt", "recordedAt"):
        value = getattr(record, field, None)
        if isinstance(value, str) and value:
            return value
    return "canonical-record"


def _status(record: CreativeRecord) -> str:
    value = getattr(record, "lifecycle_status", getattr(record, "status", None))
    if isinstance(value, (LifecycleStatus,)):
        return value.value
    return str(value) if value is not None else "proposal_only"


def _string_values(payload: dict[str, Any], *keys: str) -> tuple[str, ...]:
    values: list[str] = []
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value:
            values.append(value)
        elif isinstance(value, (list, tuple)):
            values.extend(item for item in value if isinstance(item, str) and item)
    return tuple(dict.fromkeys(values))


def _rights(record: CreativeRecord, licenses: dict[str, SourceLicenseRecord]) -> dict[str, Any]:
    license_id = getattr(record, "license_record_id", None)
    if not isinstance(license_id, str) or license_id not in licenses:
        return {}
    license_record = licenses[license_id]
    return {
        "license_record_id": license_record.license_record_id,
        "source_id": license_record.source_id,
        "permitted_use": list(license_record.permitted_use),
        "disclosure_allowed": license_record.disclosure_allowed,
        "generation_allowed": license_record.generation_allowed,
        "retention_policy": license_record.retention_policy,
        "limitations": list(license_record.limitations),
    }


def _references(key: str, value: Any) -> tuple[str, ...]:
    """Extract declared identity references without treating prose as graph edges."""

    if isinstance(value, str) and (key.endswith("_id") or key in {"source_id", "field_id"}):
        return (value,)
    if isinstance(value, list) and key.endswith("_ids"):
        return tuple(item for item in value if isinstance(item, str))
    if isinstance(value, list) and key in {
        "principles",
        "tensions",
        "exclusions",
        "dimension_states",
        "conflicts",
        "missing_dimensions",
        "dimension_contributions",
        "alternatives",
    }:
        identities: list[str] = []
        for nested in value:
            if not isinstance(nested, dict):
                continue
            identities.extend(
                nested_value
                for nested_key, nested_value in nested.items()
                if nested_key.endswith("_id")
                and nested_key not in {"interpretation_id", "reference_asset_id"}
                and isinstance(nested_value, str)
            )
        return tuple(identities)
    return ()


def _scope_check(records: tuple[CreativeRecord, ...], project_id: str) -> None:
    project_source_ids = {
        str(source_id)
        for record in records
        if getattr(record, "project_id", None) == project_id
        for source_id in _string_values(record.model_dump(mode="json"), "source_id")
    }
    for record in records:
        record_project_id = getattr(record, "project_id", None)
        if record_project_id is not None and record_project_id != project_id:
            raise ValueError(
                f"Creative Field projection crosses project boundary: {type(record).__name__}/"
                f"{_record_id(record)} belongs to {record_project_id}, expected {project_id}"
            )
        if isinstance(record, SourceLicenseRecord) and record.source_id not in project_source_ids:
            raise ValueError(
                f"Creative Field projection license is not anchored to project {project_id}: "
                f"{record.license_record_id}"
            )


def build_creative_field_projection(
    records: list[CreativeRecord] | tuple[CreativeRecord, ...],
    *,
    child_workspace_id: str,
    parent_workspace_id: str,
    project_id: str,
    dataset_name: str,
) -> CreativeFieldProjectionManifest:
    """Build a deterministic proposal-only projection from canonical records.

    The function is intentionally pure: it does not import Cognee, write a database, or
    mutate canonical records.  A construction dataset must be explicit and isolated.
    """

    for name, value in (
        ("child_workspace_id", child_workspace_id),
        ("parent_workspace_id", parent_workspace_id),
        ("project_id", project_id),
        ("dataset_name", dataset_name),
    ):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must be a non-empty string")
    if not dataset_name.endswith("_staging"):
        raise ValueError("Creative Field projection requires an isolated *_staging dataset")

    ordered_records = tuple(
        sorted(records, key=lambda item: (type(item).__name__, _record_id(item)))
    )
    if not ordered_records:
        raise ValueError("Creative Field projection requires at least one canonical record")
    _scope_check(ordered_records, project_id)

    identities = [(type(record).__name__, _record_id(record)) for record in ordered_records]
    if len(set(identities)) != len(identities):
        raise ValueError("Creative Field projection contains duplicate record identities")

    source_payload = {
        "child_workspace_id": child_workspace_id,
        "parent_workspace_id": parent_workspace_id,
        "project_id": project_id,
        "records": [
            {
                "record_type": type(record).__name__,
                "record_id": _record_id(record),
                "record": record.model_dump(mode="json"),
            }
            for record in ordered_records
        ],
    }
    source_hash = hashlib.sha256(
        json.dumps(
            source_payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    licenses = {
        _record_id(record): record
        for record in ordered_records
        if isinstance(record, SourceLicenseRecord)
    }
    id_to_documents: dict[str, list[CreativeProjectionDocument]] = {}
    documents: list[CreativeProjectionDocument] = []
    for record in ordered_records:
        record_type = type(record).__name__
        record_id = _record_id(record)
        payload = record.model_dump(mode="json")
        record_hash = _record_hash(record)
        source_url = f"creative://{project_id}/{record_type}/{record_id}"
        field_version_ids = _string_values(
            payload, "field_version_id", "version_id", "parent_version_ids"
        )
        source_ids = _string_values(
            payload,
            "source_ids",
            "source_contribution_ids",
            "evidence_refs",
            "observation_ids",
            "annotation_ids",
            "reference_asset_ids",
            "bounded_anchors",
            "source_id",
            "license_record_id",
        )
        metadata: dict[str, Any] = {
            "child_workspace_id": child_workspace_id,
            "parent_workspace_id": parent_workspace_id,
            "project_id": project_id,
            "scope": "project/creative-field",
            "route": "creative-field",
            "record_type": record_type,
            "record_id": record_id,
            "record_hash": record_hash,
            "source_hash": source_hash,
            "source_url": source_url,
            "evidence_tier": "T2",
            "experience_type": "creative-field-projection",
            "difficulty": "advanced",
            "canonical": False,
            "last_verified_at": _last_verified(record),
            "promotion_status": "proposal_only",
            "lifecycle_status": _status(record),
            "authority": getattr(record, "authority", "project-proposal"),
            "source_ids": list(source_ids),
            "derivation_id": getattr(record, "derivation_id", None),
            "rights": _rights(record, licenses),
        }
        if field_version_ids:
            metadata["field_version_ids"] = list(field_version_ids)
        if (
            getattr(record, "valid_from", None) is not None
            or getattr(record, "valid_until", None) is not None
        ):
            metadata["valid_time"] = {
                "from": getattr(record, "valid_from", None),
                "through": getattr(record, "valid_until", None),
            }
        header = "\n".join(
            (
                f"WORKSPACE_ID: {child_workspace_id}",
                f"PARENT_WORKSPACE_ID: {parent_workspace_id}",
                f"PROJECT_ID: {project_id}",
                f"SOURCE_URL: {source_url}",
                f"SOURCE_HASH: {source_hash}",
                f"RECORD_HASH: {record_hash}",
                f"RECORD_TYPE: {record_type}",
                f"RECORD_ID: {record_id}",
                *([f"FIELD_VERSION_ID: {field_version_ids[0]}"] if field_version_ids else []),
                f"DOC_TYPE: creative_field_{record_type}",
                "TASK_VIEW: creative-field",
                "PROMOTION_STATUS: proposal_only",
                f"STATUS: {_status(record)}",
                "SOURCE_BEGIN",
            )
        )
        text = f"{header}\n{_json(record)}\nSOURCE_END\n"
        document = CreativeProjectionDocument(
            document_id=stable_id(
                "creative-field-document", child_workspace_id, project_id, record_type, record_id
            ),
            record_type=record_type,
            record_id=record_id,
            source_url=source_url,
            text=text,
            metadata=metadata,
        )
        documents.append(document)
        id_to_documents.setdefault(record_id, []).append(document)

    edges: list[tuple[str, str, str, dict[str, Any]]] = []
    for record, document in zip(ordered_records, documents, strict=True):
        payload = record.model_dump(mode="json")
        for key, value in payload.items():
            for reference in _references(key, value):
                if reference == document.record_id:
                    continue
                targets = id_to_documents.get(reference, [])
                if len(targets) != 1:
                    continue
                target = targets[0]
                edges.append(
                    (
                        str(document.document_id),
                        str(target.document_id),
                        key,
                        {
                            "child_workspace_id": child_workspace_id,
                            "project_id": project_id,
                            "source_record_id": document.record_id,
                            "target_record_id": target.record_id,
                            "evidence_refs": list(
                                _string_values(payload, "evidence_refs", "source_ids")
                            ),
                        },
                    )
                )

    edges.sort(key=lambda edge: edge[:3])
    return CreativeFieldProjectionManifest(
        child_workspace_id=child_workspace_id,
        parent_workspace_id=parent_workspace_id,
        project_id=project_id,
        dataset_name=dataset_name,
        source_hash=source_hash,
        documents=tuple(documents),
        custom_edges=tuple(edges),
    )


def creative_field_projection_to_datapoints(
    manifest: CreativeFieldProjectionManifest,
) -> list[Any]:
    """Convert a manifest to lazy Cognee DataPoints at the adapter boundary."""

    try:
        from cognee.infrastructure.engine import DataPoint
    except ModuleNotFoundError as error:
        raise RuntimeError(
            "Cognee is required to build Creative Field DataPoints; install the adapter's "
            "'cognee' extra"
        ) from error

    class CreativeFieldDataPoint(DataPoint):
        child_workspace_id: str
        parent_workspace_id: str
        project_id: str
        record_type: str
        record_id: str
        source_url: str
        text: str
        metadata_json: str
        lifecycle_status: str
        evidence_tier: str
        promotion_status: str
        metadata: dict = {
            "index_fields": ["record_type", "record_id", "text"],
            "identity_fields": ["child_workspace_id", "project_id", "record_type", "record_id"],
        }

    return [
        CreativeFieldDataPoint(
            id=document.document_id,
            child_workspace_id=manifest.child_workspace_id,
            parent_workspace_id=manifest.parent_workspace_id,
            project_id=manifest.project_id,
            record_type=document.record_type,
            record_id=document.record_id,
            source_url=document.source_url,
            text=document.text,
            metadata_json=json.dumps(document.metadata, ensure_ascii=False, sort_keys=True),
            lifecycle_status=str(document.metadata["lifecycle_status"]),
            evidence_tier=str(document.metadata["evidence_tier"]),
            promotion_status=manifest.promotion_status,
        )
        for document in manifest.documents
    ]


async def populate_creative_field_projection(
    manifest: CreativeFieldProjectionManifest,
    *,
    llm_config: Any = None,
    embedding_config: Any = None,
) -> dict[str, Any]:
    """Populate an isolated staging dataset after an explicit caller authorization.

    This is the only function in the adapter that imports Cognee's ingestion API.  It adds
    source-bearing documents incrementally and cognifies them with a prompt that keeps the
    child scope, proposal status, rights and evidence distinctions visible.  Canonical state
    is never passed as a mutable Cognee object and custom edges remain represented in the
    manifest for the adapter's graph-storage seam.
    """

    if not manifest.dataset_name.endswith("_staging"):
        raise ValueError("Creative Field population requires an isolated *_staging dataset")
    try:
        import cognee
        from cognee.tasks.ingestion.data_item import DataItem
    except ModuleNotFoundError as error:
        raise RuntimeError(
            "Cognee is required to populate a Creative Field projection; "
            "install the adapter's 'cognee' extra"
        ) from error

    items = [
        DataItem(
            data=document.text,
            label=f"creative-field:{document.record_type}:{document.record_id}",
            external_metadata=document.metadata,
            data_id=stable_id(
                "creative-field-cognee-data", manifest.dataset_name, document.document_id
            ),
        )
        for document in manifest.documents
    ]
    add_result = await cognee.add(
        items,
        dataset_name=manifest.dataset_name,
        incremental_loading=True,
        run_in_background=False,
        llm_config=llm_config,
        embedding_config=embedding_config,
    )
    cognify_result = await cognee.cognify(
        datasets=manifest.dataset_name,
        incremental_loading=True,
        run_in_background=False,
        custom_prompt=(
            "This is an isolated project Creative Field child projection. Preserve child "
            "workspace, parent workspace, project, field version, lifecycle status, source "
            "anchors, evidence references, authority, rights and valid time. Treat every "
            "record as proposal-only retrieval evidence; never promote, merge projects, "
            "copy references literally, or invent unsupported relations."
        ),
        llm_config=llm_config,
        embedding_config=embedding_config,
    )
    return {
        "dataset_name": manifest.dataset_name,
        "document_count": len(manifest.documents),
        "edge_count": len(manifest.custom_edges),
        "add_result_type": type(add_result).__name__,
        "cognify_result_type": type(cognify_result).__name__,
        "source_hash": manifest.source_hash,
        "promotion_status": manifest.promotion_status,
    }


def write_projection_manifest(manifest: CreativeFieldProjectionManifest, path: Path) -> None:
    """Write only derived projection state, atomically and outside canonical storage."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(manifest.as_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def read_projection_manifest(path: Path) -> dict[str, Any]:
    """Read a previously written derived manifest for drift comparison."""

    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise ValueError("projection manifest must be a schema version 1 object")
    return value


def compare_projection_drift(
    current: CreativeFieldProjectionManifest, previous: dict[str, Any] | None
) -> dict[str, Any]:
    """Report drift without mutating either canonical or derived state."""

    if previous is None:
        return {"status": "missing", "source_hash_changed": True, "changed_record_ids": []}
    previous_hash = previous.get("source_hash")
    previous_documents = {
        (item.get("record_type"), item.get("record_id")): item.get("metadata", {}).get(
            "record_hash"
        )
        for item in previous.get("documents", [])
        if isinstance(item, dict)
    }
    changed = [
        document.record_id
        for document in current.documents
        if previous_documents.get((document.record_type, document.record_id))
        != document.metadata.get("record_hash")
    ]
    previous_ids = set(previous_documents)
    current_ids = {(document.record_type, document.record_id) for document in current.documents}
    changed.extend(
        f"removed:{record_type}/{record_id}"
        for record_type, record_id in sorted(previous_ids - current_ids)
    )
    return {
        "status": "drifted" if current.source_hash != previous_hash else "up_to_date",
        "source_hash_changed": current.source_hash != previous_hash,
        "changed_record_ids": sorted(set(changed)),
        "previous_source_hash": previous_hash,
        "current_source_hash": current.source_hash,
    }


def bounded_creative_field_traversal(
    manifest: CreativeFieldProjectionManifest,
    *,
    source_record_id: str,
    max_hops: int = 2,
) -> tuple[tuple[str, str, str, dict[str, Any]], ...]:
    """Traverse explicit projected relations with a hard two-hop safety bound."""

    if not source_record_id.strip():
        raise ValueError("source_record_id is required")
    if max_hops < 1 or max_hops > 2:
        raise ValueError("Creative Field traversal max_hops must be between 1 and 2")
    document_ids = {
        document.record_id: str(document.document_id) for document in manifest.documents
    }
    start_id = document_ids.get(source_record_id)
    if start_id is None:
        return ()
    outgoing: dict[str, list[tuple[str, str, str, dict[str, Any]]]] = {}
    for edge in manifest.custom_edges:
        outgoing.setdefault(edge[0], []).append(edge)
    frontier = {start_id}
    seen_edges: set[tuple[str, str, str]] = set()
    traversed: list[tuple[str, str, str, dict[str, Any]]] = []
    for _depth in range(max_hops):
        next_frontier: set[str] = set()
        for node_id in sorted(frontier):
            for edge in outgoing.get(node_id, []):
                edge_key = edge[:3]
                if edge_key in seen_edges:
                    continue
                seen_edges.add(edge_key)
                traversed.append(edge)
                next_frontier.add(edge[1])
        frontier = next_frontier
        if not frontier:
            break
    return tuple(traversed)


__all__ = [
    "CreativeFieldProjectionManifest",
    "CreativeProjectionDocument",
    "build_creative_field_projection",
    "bounded_creative_field_traversal",
    "compare_projection_drift",
    "creative_field_projection_to_datapoints",
    "populate_creative_field_projection",
    "read_projection_manifest",
    "write_projection_manifest",
]
