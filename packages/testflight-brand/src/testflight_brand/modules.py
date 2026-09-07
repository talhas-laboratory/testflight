"""Loader and integrity checks for additive, versioned Brand ontology modules."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class ModuleTypeDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    definition: str = Field(min_length=1)
    examples: tuple[str, ...] = Field(min_length=1)
    counterexamples: tuple[str, ...] = Field(min_length=1)


class ModuleRelationshipDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    definition: str = Field(min_length=1)
    family: str = Field(min_length=1)
    source_type_ids: tuple[str, ...] = Field(min_length=1)
    target_type_ids: tuple[str, ...] = Field(min_length=1)
    examples: tuple[str, ...] = Field(min_length=1)
    counterexamples: tuple[str, ...] = Field(min_length=1)
    allow_inference: bool = False


class BrandOntologyModule(BaseModel):
    """An immutable vocabulary unit. Definitions are candidate until promoted."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    module_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    status: str = Field(min_length=1)
    imports: tuple[str, ...] = ()
    competency_questions: tuple[str, ...] = Field(min_length=1)
    evidence_basis: tuple[str, ...] = Field(min_length=1)
    entity_types: tuple[ModuleTypeDefinition, ...] = ()
    relationship_types: tuple[ModuleRelationshipDefinition, ...] = ()


class BrandOntologyRelease(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    status: str = Field(min_length=1)
    modules: tuple[BrandOntologyModule, ...]

    @model_validator(mode="after")
    def validate_integrity(self) -> "BrandOntologyRelease":
        module_ids = {module.module_id for module in self.modules}
        if len(module_ids) != len(self.modules):
            raise ValueError("duplicate ontology module ID")
        for module in self.modules:
            unknown_imports = set(module.imports) - module_ids
            if unknown_imports:
                raise ValueError(
                    f"module {module.module_id} imports unknown modules: {sorted(unknown_imports)}"
                )
        type_ids = {item.id for module in self.modules for item in module.entity_types}
        if len(type_ids) != sum(len(module.entity_types) for module in self.modules):
            raise ValueError("duplicate ontology type ID")
        relation_ids = {item.id for module in self.modules for item in module.relationship_types}
        if len(relation_ids) != sum(len(module.relationship_types) for module in self.modules):
            raise ValueError("duplicate ontology relationship ID")
        for module in self.modules:
            for relationship in module.relationship_types:
                endpoints = set(relationship.source_type_ids) | set(relationship.target_type_ids)
                unknown_types = endpoints - type_ids
                if unknown_types:
                    raise ValueError(
                        f"relationship {relationship.id} references unknown types: "
                        f"{sorted(unknown_types)}"
                    )
        return self

    def relationship(self, relationship_id: str) -> ModuleRelationshipDefinition:
        for module in self.modules:
            for relationship in module.relationship_types:
                if relationship.id == relationship_id:
                    return relationship
        raise KeyError(relationship_id)


@dataclass(frozen=True, slots=True)
class OntologyModuleSource:
    path: Path
    module_id: str


def _read_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"ontology module must be a mapping: {path}")
    return value


def load_brand_ontology_release(
    root: Path, release: str = "ontology-v2"
) -> tuple[BrandOntologyRelease, tuple[OntologyModuleSource, ...]]:
    """Load a release without altering the existing v1 prototype loader."""

    release_root = root / "domains/brand" / release
    manifest_path = release_root / "manifest.yaml"
    manifest = _read_yaml(manifest_path)
    modules: list[BrandOntologyModule] = []
    sources: list[OntologyModuleSource] = []
    for relative_path in manifest.get("modules", []):
        path = release_root / relative_path
        module = BrandOntologyModule.model_validate(_read_yaml(path))
        modules.append(module)
        sources.append(OntologyModuleSource(path=path, module_id=module.module_id))
    return (
        BrandOntologyRelease(
            id=str(manifest["id"]),
            version=str(manifest["version"]),
            status=str(manifest["status"]),
            modules=tuple(modules),
        ),
        tuple(sources),
    )


__all__ = [
    "BrandOntologyModule",
    "BrandOntologyRelease",
    "ModuleRelationshipDefinition",
    "ModuleTypeDefinition",
    "OntologyModuleSource",
    "load_brand_ontology_release",
]
