"""Scoped authority records for semantic proposals and promotion."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .time import TemporalInterval


class Capability(StrEnum):
    PROPOSE = "propose"
    EVALUATE = "evaluate"
    ACCEPT = "accept"
    SUPERSEDE = "supersede"
    MERGE = "merge"
    SPLIT = "split"
    OVERRIDE = "override"
    PROMOTE = "promote"


class AuthorityGrant(BaseModel):
    """A time- and scope-bound capability grant."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    grant_id: str = Field(min_length=1)
    principal_id: str = Field(min_length=1)
    capabilities: tuple[Capability, ...] = ()
    object_selectors: tuple[str, ...] = ()
    context_selector: tuple[str, ...] = ()
    valid_time: TemporalInterval | None = None
    issued_by: str = Field(min_length=1)
    policy_version: str = Field(min_length=1)

    @model_validator(mode="after")
    def require_scope(self) -> "AuthorityGrant":
        if not self.capabilities:
            raise ValueError("authority grant requires at least one capability")
        if not self.object_selectors:
            raise ValueError("authority grant requires at least one object selector")
        return self

    def allows(
        self,
        capability: Capability,
        object_id: str,
        *,
        context_id: str | None = None,
        at_time: datetime | None = None,
    ) -> bool:
        """Evaluate exact or prefix selectors without inferring authority."""

        if capability not in self.capabilities:
            return False
        if not any(
            selector == "*"
            or selector == object_id
            or selector.endswith("*")
            and object_id.startswith(selector[:-1])
            for selector in self.object_selectors
        ):
            return False
        if self.context_selector and context_id not in self.context_selector:
            return False
        if at_time is not None and self.valid_time is not None:
            if self.valid_time.from_time and at_time < self.valid_time.from_time:
                return False
            if self.valid_time.to_time and at_time >= self.valid_time.to_time:
                return False
        return True


__all__ = ["AuthorityGrant", "Capability"]
