"""Core semantic records defined by Brand Ontology Constitution v0.1."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .assertions import Perspective
from .context import Context
from .time import TemporalInterval


class IdentityScope(StrEnum):
    WORKSPACE = "workspace"
    SHARED = "shared"


class EntityLifecycle(StrEnum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


class AssertionStatus(StrEnum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    CHALLENGED = "challenged"
    SUPERSEDED = "superseded"
    REVOKED = "revoked"


class DefinitionKind(StrEnum):
    ENTITY_TYPE = "entity_type"
    RELATIONSHIP = "relationship"
    FACET = "facet"
    VOCABULARY = "vocabulary"


class DefinitionStatus(StrEnum):
    CANDIDATE = "candidate"
    ACCEPTED = "accepted"
    DEPRECATED = "deprecated"


class SemanticEntity(BaseModel):
    """A persistent identity that can recur across contexts and history."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    entity_id: str = Field(min_length=1)
    type_id: str = Field(min_length=1)
    workspace_id: str | None = None
    identity_scope: IdentityScope = IdentityScope.WORKSPACE
    lifecycle_status: EntityLifecycle = EntityLifecycle.PROPOSED
    canonical_label: str = Field(min_length=1)
    definition_version: str = Field(min_length=1)
    entity_version: int = Field(default=1, ge=1)
    derivation_id: str | None = None

    @model_validator(mode="after")
    def validate_identity_scope(self) -> "SemanticEntity":
        if self.identity_scope is IdentityScope.WORKSPACE and not self.workspace_id:
            raise ValueError("workspace-scoped entities require workspace_id")
        return self


class Assertion(BaseModel):
    """A contextualized proposition; direct graph edges are projections of this record."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    assertion_id: str = Field(min_length=1)
    subject_id: str = Field(min_length=1)
    predicate_id: str = Field(min_length=1)
    object_id: str | None = None
    object_value: Any | None = None
    context_id: str = Field(min_length=1)
    perspective: Perspective
    status: AssertionStatus = AssertionStatus.PROPOSED
    valid_time: TemporalInterval | None = None
    known_time: TemporalInterval | None = None
    evidence_refs: tuple[str, ...] = ()
    derivation_id: str | None = None
    authority_grant_id: str | None = None

    @model_validator(mode="after")
    def require_one_object_form(self) -> "Assertion":
        has_id = self.object_id is not None
        has_value = self.object_value is not None
        if has_id == has_value:
            raise ValueError("Assertion requires exactly one of object_id or object_value")
        return self


class Event(BaseModel):
    """A temporally bounded occurrence that may participate in assertions."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    event_id: str = Field(min_length=1)
    type_id: str = Field(min_length=1)
    context_id: str = Field(min_length=1)
    valid_time: TemporalInterval = Field(default_factory=TemporalInterval)
    derivation_id: str | None = None


class OntologyDefinition(BaseModel):
    """Immutable contract for a type, relationship, facet, or vocabulary term."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    definition_id: str = Field(min_length=1)
    kind: DefinitionKind
    version: str = Field(min_length=1)
    status: DefinitionStatus = DefinitionStatus.CANDIDATE
    module: str = Field(min_length=1)
    definition: str = Field(min_length=1)
    examples: tuple[str, ...] = ()
    counterexamples: tuple[str, ...] = ()
    subproperty_of: str | None = None


def context_for_assertion(assertion: Assertion, contexts: dict[str, Context]) -> Context:
    """Resolve an assertion Context without allowing a provider to invent one."""

    try:
        return contexts[assertion.context_id]
    except KeyError as exc:
        raise ValueError(f"assertion references unknown Context: {assertion.context_id}") from exc


__all__ = [
    "Assertion",
    "AssertionStatus",
    "DefinitionKind",
    "DefinitionStatus",
    "EntityLifecycle",
    "Event",
    "IdentityScope",
    "OntologyDefinition",
    "SemanticEntity",
    "context_for_assertion",
]
