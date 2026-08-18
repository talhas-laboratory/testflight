"""Configuration objects for semantic entity and relationship extraction.

The objects in this module deliberately contain no Cognee or LLM imports.  They
are the portable semantic contract that can be reused by a different extractor
or persistence backend later.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DefinitionExample:
    """A positive or negative example used when compiling an extractor prompt."""

    text: str
    qualifies: bool
    rationale: str = ""


@dataclass(frozen=True, slots=True)
class RelationshipDefinition:
    """A named relationship that may be emitted between two extracted entities."""

    name: str
    source_entity: str
    target_entity: str
    definition: str
    examples: tuple[str, ...] = ()

    def validate(self) -> None:
        fields = {
            "name": self.name,
            "source_entity": self.source_entity,
            "target_entity": self.target_entity,
            "definition": self.definition,
        }
        for field_name, value in fields.items():
            if not value.strip():
                raise ValueError(f"relationship {field_name} must not be empty")


@dataclass(frozen=True, slots=True)
class EntityDefinition:
    """Semantic rules for one entity type.

    Rules are intentionally plain text.  This keeps the ontology/configuration
    declarative while allowing the prompt compiler to evolve independently from
    the extraction model and storage representation.
    """

    name: str
    definition: str
    include_rules: tuple[str, ...] = ()
    exclude_rules: tuple[str, ...] = ()
    boundary_rule: str = "Return the smallest span that satisfies the definition."
    inference_rule: str = (
        "Extract explicit mentions; include implied mentions only when strongly supported."
    )
    examples: tuple[DefinitionExample, ...] = ()
    relationships: tuple[RelationshipDefinition, ...] = ()

    def validate(self) -> None:
        if not self.name.strip():
            raise ValueError("entity name must not be empty")
        if not self.definition.strip():
            raise ValueError("entity definition must not be empty")
        if not self.boundary_rule.strip():
            raise ValueError("boundary_rule must not be empty")
        if not self.inference_rule.strip():
            raise ValueError("inference_rule must not be empty")

        relationship_names: set[str] = set()
        for relationship in self.relationships:
            relationship.validate()
            key = relationship.name.casefold()
            if key in relationship_names:
                raise ValueError(f"duplicate relationship name: {relationship.name}")
            relationship_names.add(key)


__all__ = ["DefinitionExample", "EntityDefinition", "RelationshipDefinition"]
