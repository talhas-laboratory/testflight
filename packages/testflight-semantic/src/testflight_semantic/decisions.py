"""Decision records that preserve the bridge from evidence to action."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DecisionStatus(StrEnum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    SUPERSEDED = "superseded"
    REJECTED = "rejected"


class DecisionRecord(BaseModel):
    """An authorized choice; it is not evidence and it is not a causal claim.

    A decision makes the transition from a bounded set of inputs to a selected
    strategic option inspectable. The inputs can be evidence, assertions,
    observations, or prior decisions, and retain their own provenance.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    decision_id: str = Field(min_length=1)
    workspace_id: str = Field(min_length=1)
    decision_type_id: str = Field(min_length=1)
    context_id: str = Field(min_length=1)
    input_ids: tuple[str, ...] = Field(min_length=1)
    selected_option_id: str = Field(min_length=1)
    rejected_option_ids: tuple[str, ...] = ()
    rationale: str = Field(min_length=1)
    authority_grant_id: str | None = None
    derivation_id: str | None = None
    decided_at: datetime
    status: DecisionStatus = DecisionStatus.PROPOSED

    @model_validator(mode="after")
    def validate_options(self) -> "DecisionRecord":
        if len(set(self.input_ids)) != len(self.input_ids):
            raise ValueError("DecisionRecord input_ids must be unique")
        if len(set(self.rejected_option_ids)) != len(self.rejected_option_ids):
            raise ValueError("DecisionRecord rejected_option_ids must be unique")
        if self.selected_option_id in self.rejected_option_ids:
            raise ValueError("selected option cannot also be rejected")
        return self


__all__ = ["DecisionRecord", "DecisionStatus"]
