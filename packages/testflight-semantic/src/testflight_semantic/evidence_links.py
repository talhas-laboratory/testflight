"""Typed evidence links that preserve support, opposition, and uncertainty."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class EvidenceRole(StrEnum):
    SUPPORTS = "supports"
    OPPOSES = "opposes"
    QUALIFIES = "qualifies"
    MENTIONS = "mentions"
    INCONCLUSIVE = "inconclusive"


class EvidenceLink(BaseModel):
    """A source's role with respect to one claim, state, or hypothesis.

    Evidence does not decide truth. This record describes only how a source is
    being used and keeps conflicting uses visible.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    link_id: str = Field(min_length=1)
    evidence_id: str = Field(min_length=1)
    target_id: str = Field(min_length=1)
    role: EvidenceRole
    context_id: str = Field(min_length=1)
    derivation_id: str | None = None
    note: str | None = None


__all__ = ["EvidenceLink", "EvidenceRole"]
