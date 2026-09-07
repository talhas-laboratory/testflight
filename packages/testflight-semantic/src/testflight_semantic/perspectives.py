"""Situated viewpoints with explicit access, assumptions, and limitations."""

from pydantic import BaseModel, ConfigDict, Field

from .time import TemporalInterval


class PerspectiveProfile(BaseModel):
    """A viewpoint that can interpret records without modifying shared state."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    perspective_id: str = Field(min_length=1)
    holder_id: str = Field(min_length=1)
    perspective_type_id: str = Field(min_length=1)
    context_id: str = Field(min_length=1)
    goals: tuple[str, ...] = ()
    accessible_record_selectors: tuple[str, ...] = ()
    assumption_ids: tuple[str, ...] = ()
    salience_rules: tuple[str, ...] = ()
    known_limitations: tuple[str, ...] = ()
    valid_time: TemporalInterval | None = None
    authority_grant_id: str | None = None
    derivation_id: str | None = None


__all__ = ["PerspectiveProfile"]
