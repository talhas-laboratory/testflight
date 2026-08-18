"""Conservative identity and canonicalization records."""

from pydantic import BaseModel, ConfigDict, Field


class ReferentHypothesis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mention_id: str = Field(min_length=1)
    candidate_entity_id: str = Field(min_length=1)
    discriminating_evidence_ids: tuple[str, ...] = ()
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    status: str = "unresolved"


class CanonicalEntity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(min_length=1)
    workspace_id: str = Field(min_length=1)
    definition_id: str = Field(min_length=1)
    canonical_label: str = Field(min_length=1)
    occurrence_ids: tuple[str, ...] = ()
    version: int = Field(default=1, ge=1)


__all__ = ["CanonicalEntity", "ReferentHypothesis"]
