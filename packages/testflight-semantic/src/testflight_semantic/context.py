"""Immutable, content-addressed semantic Context records."""

import hashlib
import json
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .time import TemporalInterval


class Context(BaseModel):
    """Applicability scope shared by assertions, representations, and dependencies.

    The content-addressed physical encoding is provisional under constitution decision C-01.
    The model is intentionally provider-neutral and can be migrated behind this contract.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    context_id: str = ""
    brand_system_id: str | None = None
    portfolio_id: str | None = None
    brand_id: str | None = None
    offering_id: str | None = None
    audience_ids: tuple[str, ...] = ()
    channel_ids: tuple[str, ...] = ()
    artifact_type_ids: tuple[str, ...] = ()
    locale: str | None = None
    campaign_or_occasion_ids: tuple[str, ...] = ()
    branch_id: str = "main"
    valid_time: TemporalInterval | None = None
    dimensions: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def assign_content_address(self) -> "Context":
        payload = self.model_dump(exclude={"context_id"}, mode="json")
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        expected = f"world://context/sha256:{hashlib.sha256(canonical.encode()).hexdigest()}"
        if self.context_id and self.context_id != expected:
            raise ValueError("context_id does not match canonical Context content")
        object.__setattr__(self, "context_id", expected)
        return self


__all__ = ["Context"]
