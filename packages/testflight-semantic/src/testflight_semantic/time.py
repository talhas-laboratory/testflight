"""Bitemporal time primitives used by the provider-neutral semantic kernel."""

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, model_validator


class BoundSemantics(StrEnum):
    """Meaning of a missing half-open interval bound."""

    KNOWN = "known"
    UNKNOWN = "unknown"
    UNBOUNDED = "unbounded"


class TimePrecision(StrEnum):
    """Precision supplied by a source for a time value."""

    YEAR = "year"
    MONTH = "month"
    DAY = "day"
    INSTANT = "instant"
    UNKNOWN = "unknown"


class TemporalInterval(BaseModel):
    """A UTC half-open interval with explicit null-bound semantics."""

    model_config = ConfigDict(extra="forbid")

    from_time: datetime | None = None
    to_time: datetime | None = None
    from_semantics: BoundSemantics = BoundSemantics.UNKNOWN
    to_semantics: BoundSemantics = BoundSemantics.UNKNOWN
    precision: TimePrecision = TimePrecision.UNKNOWN
    source_timezone: str | None = None

    @model_validator(mode="after")
    def validate_and_normalize(self) -> "TemporalInterval":
        for field_name in ("from_time", "to_time"):
            value = getattr(self, field_name)
            if value is None:
                continue
            if value.tzinfo is None or value.utcoffset() is None:
                raise ValueError(f"{field_name} must be timezone-aware RFC3339 time")
            object.__setattr__(self, field_name, value.astimezone(UTC))

        for time_name, semantics_name in (
            ("from_time", "from_semantics"),
            ("to_time", "to_semantics"),
        ):
            value = getattr(self, time_name)
            semantics = getattr(self, semantics_name)
            if value is None and semantics is BoundSemantics.KNOWN:
                raise ValueError(f"{semantics_name}=known requires {time_name}")
            if value is not None and semantics is not BoundSemantics.KNOWN:
                object.__setattr__(self, semantics_name, BoundSemantics.KNOWN)

        if (
            self.from_time is not None
            and self.to_time is not None
            and self.to_time <= self.from_time
        ):
            raise ValueError("half-open interval requires to_time > from_time")
        return self


__all__ = ["BoundSemantics", "TemporalInterval", "TimePrecision"]
