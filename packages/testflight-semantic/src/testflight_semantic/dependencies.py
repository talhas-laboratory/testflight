"""Versioned dependency rules and freshness markers."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ChangeType(StrEnum):
    ENTITY_REVISION = "EntityRevision"
    ASSERTION_ACCEPTED = "AssertionAccepted"
    ASSERTION_REVOKED = "AssertionRevoked"
    ASSERTION_SUPERSEDED = "AssertionSuperseded"
    IDENTITY_MERGE = "IdentityMerge"
    IDENTITY_SPLIT = "IdentitySplit"
    RELATION_CHANGED = "RelationChanged"
    REPRESENTATION_CHANGED = "RepresentationChanged"
    POLICY_CHANGED = "PolicyChanged"
    EVIDENCE_AUTHORITY_CHANGED = "EvidenceAuthorityChanged"
    ONTOLOGY_CHANGED = "OntologyChanged"


class DependencyEffect(StrEnum):
    POTENTIALLY_STALE = "potentially_stale"
    REVIEW_REQUIRED = "review_required"
    INVALIDATE = "invalidate"


class FreshnessState(StrEnum):
    CURRENT = "current"
    POTENTIALLY_STALE = "potentially_stale"
    STALE = "stale"
    UNDER_REVIEW = "under_review"
    REAFFIRMED = "reaffirmed"
    REVISED = "revised"
    RETIRED = "retired"


class DependencyRule(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    rule_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    upstream_selector: dict[str, Any] = Field(min_length=1)
    downstream_selector: dict[str, Any] = Field(min_length=1)
    trigger_change_types: tuple[ChangeType, ...] = ()
    scope: dict[str, Any] = Field(default_factory=dict)
    effect: DependencyEffect = DependencyEffect.POTENTIALLY_STALE
    max_depth: int = Field(default=2, ge=0)
    authority_requirement_id: str | None = None

    @model_validator(mode="after")
    def require_trigger(self) -> "DependencyRule":
        if not self.trigger_change_types:
            raise ValueError("DependencyRule requires at least one trigger change type")
        return self


class DependencyEdge(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    edge_id: str = Field(min_length=1)
    upstream_id: str = Field(min_length=1)
    downstream_id: str = Field(min_length=1)
    rule_id: str = Field(min_length=1)
    rule_version: str = Field(min_length=1)
    context_id: str = Field(min_length=1)
    materialization: str = Field(min_length=1)
    created_at: datetime


class StalenessMarker(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    marker_id: str = Field(min_length=1)
    downstream_id: str = Field(min_length=1)
    state: FreshnessState
    cause_ids: tuple[str, ...] = ()
    rule_id: str = Field(min_length=1)
    rule_version: str = Field(min_length=1)
    created_at: datetime
    review_note: str | None = None


def selector_matches(selector: dict[str, Any], *, entity_id: str, entity_type: str) -> bool:
    """Evaluate the deliberately small v0.1 selector subset."""

    if "entity_id" in selector and selector["entity_id"] != entity_id:
        return False
    return "entity_type" not in selector or selector["entity_type"] == entity_type


__all__ = [
    "ChangeType",
    "DependencyEffect",
    "DependencyEdge",
    "DependencyRule",
    "FreshnessState",
    "StalenessMarker",
    "selector_matches",
]
