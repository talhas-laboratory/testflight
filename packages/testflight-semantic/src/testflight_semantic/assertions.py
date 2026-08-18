"""Evidence-backed relation proposals independent of any graph database."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class Perspective(StrEnum):
    INTENDED = "intended"
    EXPRESSED = "expressed"
    EXPERIENCED = "experienced"
    REPORTED = "reported"
    OBSERVED = "observed"
    INFERRED = "inferred"
    HYPOTHESIZED = "hypothesized"


class EpistemicStatus(StrEnum):
    NORMATIVE = "normative"
    OBSERVED = "observed"
    REPORTED = "reported"
    INFERRED = "inferred"
    HYPOTHESIZED = "hypothesized"
    RETRACTED = "retracted"
    UNRESOLVED = "unresolved"


class AssertionProposal(BaseModel):
    """A scoped proposition awaiting semantic and persistence gates."""

    model_config = ConfigDict(extra="forbid")

    assertion_id: str = Field(min_length=1)
    workspace_id: str = Field(min_length=1)
    subject_id: str = Field(min_length=1)
    predicate: str = Field(min_length=1)
    object_id: str = Field(min_length=1)
    definition_version: str = Field(min_length=1)
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


__all__ = ["AssertionProposal", "EpistemicStatus", "Perspective"]
