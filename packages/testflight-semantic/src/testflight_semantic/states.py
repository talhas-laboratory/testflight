"""Versioned modeled conditions, kept distinct from claims about them."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .time import TemporalInterval


class StateStatus(StrEnum):
    PROPOSED = "proposed"
    SUPPORTED = "supported"
    CONTESTED = "contested"
    SUPERSEDED = "superseded"
    RETIRED = "retired"


class StateValue(BaseModel):
    """One named qualitative or quantitative condition in a StateSnapshot."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    key: str = Field(min_length=1)
    value: Any
    unit_id: str | None = None
    measurement_method_id: str | None = None

    @model_validator(mode="after")
    def require_method_for_quantitative_value(self) -> "StateValue":
        if isinstance(self.value, bool):
            return self
        if isinstance(self.value, (int, float)) and not self.unit_id:
            raise ValueError("quantitative state values require unit_id")
        return self


class StateSnapshot(BaseModel):
    """A scoped model of a condition, not a speaker's assertion or belief."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    state_id: str = Field(min_length=1)
    version: int = Field(default=1, ge=1)
    subject_ids: tuple[str, ...] = Field(min_length=1)
    state_type_id: str = Field(min_length=1)
    context_id: str = Field(min_length=1)
    values: tuple[StateValue, ...] = Field(min_length=1)
    valid_time: TemporalInterval | None = None
    source_assertion_ids: tuple[str, ...] = ()
    evidence_link_ids: tuple[str, ...] = ()
    status: StateStatus = StateStatus.PROPOSED
    derivation_id: str | None = None

    @model_validator(mode="after")
    def validate_unique_values(self) -> "StateSnapshot":
        if len(set(self.subject_ids)) != len(self.subject_ids):
            raise ValueError("StateSnapshot subject_ids must be unique")
        keys = [value.key for value in self.values]
        if len(keys) != len(set(keys)):
            raise ValueError("StateSnapshot value keys must be unique")
        return self


__all__ = ["StateSnapshot", "StateStatus", "StateValue"]
