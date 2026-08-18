"""Versioned YAML ontology loader for Brand workspaces."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field


class ComponentTypeDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    definition: str = Field(min_length=1)
    layer: str = Field(min_length=1)


class RelationshipTypeDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    definition: str = Field(min_length=1)
    family: str = Field(min_length=1)
    source_types: tuple[str, ...] = ()
    target_types: tuple[str, ...] = ()
    allow_inference: bool = False


class BrandOntology(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    component_types: tuple[ComponentTypeDefinition, ...]
    relationship_types: tuple[RelationshipTypeDefinition, ...]

    def validate_integrity(self) -> None:
        component_ids = {item.id for item in self.component_types}
        if len(component_ids) != len(self.component_types):
            raise ValueError("duplicate component type id")
        relation_ids = {item.id for item in self.relationship_types}
        if len(relation_ids) != len(self.relationship_types):
            raise ValueError("duplicate relationship type id")
        known_types = component_ids | {
            "brand",
            "brand-system",
            "artifact",
            "touchpoint",
            "stakeholder",
        }
        for relation in self.relationship_types:
            unknown_sources = set(relation.source_types) - known_types
            unknown_targets = set(relation.target_types) - known_types
            if unknown_sources or unknown_targets:
                raise ValueError(
                    f"relationship {relation.id} references unknown types: "
                    f"sources={sorted(unknown_sources)} targets={sorted(unknown_targets)}"
                )

    def relationship(self, relation_id: str) -> RelationshipTypeDefinition:
        for relation in self.relationship_types:
            if relation.id == relation_id:
                return relation
        raise KeyError(relation_id)


@dataclass(frozen=True, slots=True)
class OntologySource:
    path: Path
    content_hash: str


def _read_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text())
    if not isinstance(payload, dict):
        raise ValueError(f"ontology source must be a mapping: {path}")
    return payload


def load_brand_ontology(root: Path) -> tuple[BrandOntology, tuple[OntologySource, ...]]:
    """Load the indexed Brand ontology and validate all referenced files."""

    index_path = root / "domains/brand/ontology/brand-system.yaml"
    index = _read_yaml(index_path)
    base = index_path.parent
    component_types = []
    relationship_types = []
    sources = [OntologySource(index_path, _sha256(index_path))]
    for relative in index.get("entity_types", []):
        path = base / relative
        component_types.append(ComponentTypeDefinition.model_validate(_read_yaml(path)))
        sources.append(OntologySource(path, _sha256(path)))
    for relative in index.get("relationship_types", []):
        path = base / relative
        relationship_types.append(RelationshipTypeDefinition.model_validate(_read_yaml(path)))
        sources.append(OntologySource(path, _sha256(path)))
    ontology = BrandOntology(
        id=str(index["id"]),
        version=str(index["version"]),
        component_types=tuple(component_types),
        relationship_types=tuple(relationship_types),
    )
    ontology.validate_integrity()
    return ontology, tuple(sources)


def _sha256(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


__all__ = [
    "BrandOntology",
    "ComponentTypeDefinition",
    "OntologySource",
    "RelationshipTypeDefinition",
    "load_brand_ontology",
]
