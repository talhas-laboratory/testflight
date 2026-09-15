"""Read-only inventory of legacy Brand World sources and consumers.

This module provides migration accounting, not migration. It never turns legacy content into v3
meaning and never writes into a Brand workspace.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, computed_field

from .modules import load_brand_ontology_release
from .ontology import load_brand_ontology


class LegacyRecordInventory(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    legacy_id: str = Field(min_length=1)
    record_group: str = Field(min_length=1)
    source_path: str = Field(min_length=1)
    input_hash: str = Field(min_length=1)
    fields: tuple[str, ...] = ()
    endpoint_ids: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    context_ids: tuple[str, ...] = ()


class LegacyArtifactInventory(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_path: str = Field(min_length=1)
    content_hash: str = Field(min_length=1)
    record_groups: tuple[str, ...] = ()


class LegacyConsumerInventory(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    path: str = Field(min_length=1)
    consumer_kind: str = Field(min_length=1)
    matched_markers: tuple[str, ...] = Field(min_length=1)


class LegacyWorldInventory(BaseModel):
    """A complete, hash-bound snapshot used to prepare a migration ledger."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    workspace_id: str = Field(min_length=1)
    workspace_path: str = Field(min_length=1)
    legacy_ontology_versions: tuple[str, ...] = Field(min_length=1)
    ontology_type_ids: tuple[str, ...] = ()
    ontology_relation_ids: tuple[str, ...] = ()
    records: tuple[LegacyRecordInventory, ...] = ()
    artifacts: tuple[LegacyArtifactInventory, ...] = ()
    consumers: tuple[LegacyConsumerInventory, ...] = ()

    @property
    def record_ids(self) -> tuple[str, ...]:
        return tuple(record.legacy_id for record in self.records)

    @computed_field
    @property
    def snapshot_hash(self) -> str:
        digest = hashlib.sha256()
        for artifact in self.artifacts:
            digest.update(f"{artifact.source_path}:{artifact.content_hash}\n".encode())
        return f"sha256:{digest.hexdigest()}"


_WORKSPACE_ARTIFACTS = (
    "artifacts/entity-inventory.yaml",
    "artifacts/relationship-inventory.yaml",
    "artifacts/evidence-notes.yaml",
    "artifacts/source-catalog.yaml",
    "artifacts/context-profiles.yaml",
    "artifacts/world-modeling.yaml",
)
_LEGACY_MARKERS = (
    "domains/brand/ontology/brand-system.yaml",
    "ontology-v2",
    "ontology_version: 1.0.0",
)


def inventory_legacy_brand_workspace(
    repository_root: Path, workspace_path: Path
) -> LegacyWorldInventory:
    """Return a deterministic, non-mutating inventory for one legacy Brand workspace."""

    repository_root = repository_root.resolve()
    workspace_path = workspace_path.resolve()
    workspace = _read_mapping(workspace_path / "WORKSPACE.yaml")
    workspace_info = workspace.get("workspace")
    if not isinstance(workspace_info, dict) or not isinstance(workspace_info.get("id"), str):
        raise ValueError("workspace manifest must provide workspace.id")

    v1, _ = load_brand_ontology(repository_root)
    v2, _ = load_brand_ontology_release(repository_root, release="ontology-v2")
    artifacts: list[LegacyArtifactInventory] = []
    records: list[LegacyRecordInventory] = []
    for relative_path in _WORKSPACE_ARTIFACTS:
        path = workspace_path / relative_path
        payload = _read_mapping(path)
        source_path = path.relative_to(repository_root).as_posix()
        groups = tuple(sorted(key for key, value in payload.items() if isinstance(value, list)))
        artifacts.append(
            LegacyArtifactInventory(
                source_path=source_path,
                content_hash=_content_hash(path),
                record_groups=groups,
            )
        )
        for group in groups:
            values = payload[group]
            assert isinstance(values, list)
            for index, value in enumerate(values):
                if not isinstance(value, dict):
                    continue
                legacy_id = _record_id(value, source_path, group, index)
                records.append(
                    LegacyRecordInventory(
                        legacy_id=legacy_id,
                        record_group=group,
                        source_path=source_path,
                        input_hash=_mapping_hash(value),
                        fields=tuple(sorted(value)),
                        endpoint_ids=_endpoint_ids(value),
                        evidence_ids=_string_tuple(value.get("evidence_ids")),
                        context_ids=_context_ids(value),
                    )
                )

    duplicate_ids = _duplicates(record.legacy_id for record in records)
    if duplicate_ids:
        raise ValueError(f"legacy inventory contains duplicate record IDs: {sorted(duplicate_ids)}")
    return LegacyWorldInventory(
        workspace_id=workspace_info["id"],
        workspace_path=workspace_path.relative_to(repository_root).as_posix(),
        legacy_ontology_versions=(v1.version, v2.version),
        ontology_type_ids=tuple(
            sorted(
                {component.id for component in v1.component_types}
                | {item.id for module in v2.modules for item in module.entity_types}
            )
        ),
        ontology_relation_ids=tuple(
            sorted(
                {relation.id for relation in v1.relationship_types}
                | {item.id for module in v2.modules for item in module.relationship_types}
            )
        ),
        records=tuple(sorted(records, key=lambda record: record.legacy_id)),
        artifacts=tuple(sorted(artifacts, key=lambda artifact: artifact.source_path)),
        consumers=_find_legacy_consumers(repository_root),
    )


def _find_legacy_consumers(repository_root: Path) -> tuple[LegacyConsumerInventory, ...]:
    consumers: list[LegacyConsumerInventory] = []
    excluded = {".git", ".data", ".venv", "node_modules", "__pycache__"}
    for path in sorted(repository_root.rglob("*")):
        if not path.is_file() or any(part in excluded for part in path.parts):
            continue
        if path.suffix not in {".py", ".yaml", ".yml", ".json", ".md", ".toml"}:
            continue
        try:
            contents = path.read_text()
        except UnicodeDecodeError:
            continue
        matched = tuple(marker for marker in _LEGACY_MARKERS if marker in contents)
        if matched:
            consumers.append(
                LegacyConsumerInventory(
                    path=path.relative_to(repository_root).as_posix(),
                    consumer_kind=_consumer_kind(path.relative_to(repository_root)),
                    matched_markers=matched,
                )
            )
    return tuple(consumers)


def _consumer_kind(relative_path: Path) -> str:
    if "tests" in relative_path.parts:
        return "test"
    if relative_path.parts[0] == "docs":
        return "documentation"
    if relative_path.parts[0] == "apps":
        return "application"
    if relative_path.parts[0] == "scripts":
        return "script"
    if relative_path.parts[0] == "workspaces":
        return "workspace_configuration"
    return "package_or_adapter"


def _read_mapping(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"legacy artifact must be a YAML mapping: {path}")
    return value


def _content_hash(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def _mapping_hash(value: dict[str, Any]) -> str:
    serialized = yaml.safe_dump(value, sort_keys=True).encode()
    return f"sha256:{hashlib.sha256(serialized).hexdigest()}"


def _string_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        return ()
    return tuple(value)


def _record_id(value: dict[str, Any], source_path: str, group: str, index: int) -> str:
    for key in ("id", "link_id", "state_id", "perspective_id", "frame_id", "branch_id"):
        candidate = value.get(key)
        if isinstance(candidate, str) and candidate:
            return candidate
    return f"{source_path}#{group}[{index}]"


def _context_ids(value: dict[str, Any]) -> tuple[str, ...]:
    values = _string_tuple(value.get("context_ids"))
    singular = value.get("context_id")
    if isinstance(singular, str) and singular:
        return values + (singular,)
    return values


def _endpoint_ids(value: dict[str, Any]) -> tuple[str, ...]:
    endpoint_keys = ("source_id", "target_id", "subject_id", "object_id")
    return tuple(value[key] for key in endpoint_keys if isinstance(value.get(key), str))


def _duplicates(values: Any) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return duplicates


__all__ = [
    "LegacyArtifactInventory",
    "LegacyConsumerInventory",
    "LegacyRecordInventory",
    "LegacyWorldInventory",
    "inventory_legacy_brand_workspace",
]
