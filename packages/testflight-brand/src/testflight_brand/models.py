"""Brand system records built on the provider-neutral semantic contracts."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field
from testflight_semantic.assertions import EpistemicStatus, Perspective


class BrandSystem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    brand_id: str = Field(min_length=1)
    workspace_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    ontology_version: str = Field(min_length=1)
    version: int = Field(default=1, ge=1)


class AssertionStatus(StrEnum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    HELD = "held"
    PARTIAL = "partial"
    REJECTED = "rejected"
    UNRESOLVED = "unresolved"
    RETRACTED = "retracted"


class BrandComponent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    component_id: str = Field(min_length=1)
    brand_id: str = Field(min_length=1)
    definition_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    perspective: Perspective
    version: int = Field(default=1, ge=1)


class BrandArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact_id: str = Field(min_length=1)
    brand_id: str = Field(min_length=1)
    artifact_type: str = Field(min_length=1)
    label: str = Field(min_length=1)
    source_id: str | None = None


class BrandAssertion(BaseModel):
    """A first-class relation record retaining evidence and score dimensions."""

    model_config = ConfigDict(extra="forbid")

    assertion_id: str = Field(min_length=1)
    workspace_id: str = Field(min_length=1)
    brand_id: str = Field(min_length=1)
    subject_id: str = Field(min_length=1)
    predicate: str = Field(min_length=1)
    object_id: str = Field(min_length=1)
    relationship_definition_id: str = Field(min_length=1)
    perspective: Perspective
    epistemic_status: EpistemicStatus
    evidence_ids: tuple[str, ...] = ()
    contradiction_ids: tuple[str, ...] = ()
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    recorded_at: datetime
    structural_weight: float | None = Field(default=None, ge=0.0, le=1.0)
    evidence_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    source_authority: float | None = Field(default=None, ge=0.0, le=1.0)
    salience: float | None = Field(default=None, ge=0.0, le=1.0)
    valence: float | None = Field(default=None, ge=-1.0, le=1.0)
    weight_policy_id: str | None = None
    status: AssertionStatus = AssertionStatus.PROPOSED


class BrandStateSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    snapshot_id: str = Field(min_length=1)
    workspace_id: str = Field(min_length=1)
    brand_id: str = Field(min_length=1)
    as_of: datetime
    source_assertion_ids: tuple[str, ...] = ()
    derivation_id: str = Field(min_length=1)
    version: int = Field(default=1, ge=1)


__all__ = [
    "AssertionStatus",
    "BrandArtifact",
    "BrandAssertion",
    "BrandComponent",
    "BrandStateSnapshot",
    "BrandSystem",
]
