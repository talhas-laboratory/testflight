"""N-ary, context-qualified relationship frames over existing records."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .time import TemporalInterval


class RoleBinding(BaseModel):
    """A named role in a complex relationship frame."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    role_id: str = Field(min_length=1)
    record_ids: tuple[str, ...] = ()
    value: Any | None = None

    @model_validator(mode="after")
    def require_ids_or_value(self) -> "RoleBinding":
        if bool(self.record_ids) == (self.value is not None):
            raise ValueError("RoleBinding requires exactly one of record_ids or value")
        if len(set(self.record_ids)) != len(self.record_ids):
            raise ValueError("RoleBinding record_ids must be unique")
        return self


class RelationshipFrame(BaseModel):
    """A context-bound relation with named participants and constraints."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    frame_id: str = Field(min_length=1)
    frame_type_id: str = Field(min_length=1)
    context_id: str = Field(min_length=1)
    role_bindings: tuple[RoleBinding, ...] = Field(min_length=2)
    assertion_ids: tuple[str, ...] = ()
    constraint_ids: tuple[str, ...] = ()
    valid_time: TemporalInterval | None = None
    status: str = Field(min_length=1)
    evidence_link_ids: tuple[str, ...] = ()
    derivation_id: str | None = None

    @model_validator(mode="after")
    def require_unique_roles(self) -> "RelationshipFrame":
        role_ids = [binding.role_id for binding in self.role_bindings]
        if len(role_ids) != len(set(role_ids)):
            raise ValueError("RelationshipFrame role IDs must be unique")
        return self


__all__ = ["RelationshipFrame", "RoleBinding"]
