"""Provider-neutral semantic definitions."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DefinitionExample:
    """A positive or negative example used when compiling an extractor prompt."""

    text: str
    qualifies: bool
    rationale: str = ""


@dataclass(frozen=True, slots=True)
class RelationshipDefinition:
    """A typed relation permitted between two semantic definitions."""

    name: str
    source_entity: str
    target_entity: str
    definition: str
    examples: tuple[str, ...] = ()
    relation_family: str = "relational"
    allow_inference: bool = False

    def validate(self) -> None:
        fields = {
            "name": self.name,
            "source_entity": self.source_entity,
            "target_entity": self.target_entity,
            "definition": self.definition,
            "relation_family": self.relation_family,
        }
        for field_name, value in fields.items():
            if not value.strip():
                raise ValueError(f"relationship {field_name} must not be empty")


@dataclass(frozen=True, slots=True)
class EntityDefinition:
    """Semantic rules for one entity type."""

    name: str
    definition: str
    version: str = "1.0.0"
    include_rules: tuple[str, ...] = ()
    exclude_rules: tuple[str, ...] = ()
    boundary_rule: str = "Return the smallest span that satisfies the definition."
    inference_rule: str = (
        "Extract explicit mentions; include implied mentions only when strongly supported."
    )
    examples: tuple[DefinitionExample, ...] = ()
    relationships: tuple[RelationshipDefinition, ...] = ()

    def validate(self) -> None:
        fields = {
            "name": self.name,
            "definition": self.definition,
            "version": self.version,
            "boundary_rule": self.boundary_rule,
            "inference_rule": self.inference_rule,
        }
        for field_name, value in fields.items():
            if not value.strip():
                raise ValueError(f"{field_name} must not be empty")

        relationship_names: set[str] = set()
        for relationship in self.relationships:
            relationship.validate()
            key = relationship.name.casefold()
            if key in relationship_names:
                raise ValueError(f"duplicate relationship name: {relationship.name}")
            relationship_names.add(key)


__all__ = ["DefinitionExample", "EntityDefinition", "RelationshipDefinition"]
