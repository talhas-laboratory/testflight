"""Immutable source envelopes and exact evidence spans."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EvidenceEnvelope(BaseModel):
    """Metadata for an immutable source payload."""

    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(min_length=1)
    workspace_id: str = Field(min_length=1)
    content_hash: str = Field(min_length=1)
    source_uri: str = Field(min_length=1)
    media_type: str = "text/plain"
    source_time: datetime | None = None
    recorded_time: datetime
    actor_id: str | None = None
    access_classification: str = "workspace"


class EvidenceSpan(BaseModel):
    """A contiguous source quote anchored to an immutable envelope."""

    model_config = ConfigDict(extra="forbid")

    envelope_id: str = Field(min_length=1)
    quote: str = Field(min_length=1)
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    document_path: str = ""
    section_id: str = ""
    window_id: str = ""


__all__ = ["EvidenceEnvelope", "EvidenceSpan"]
