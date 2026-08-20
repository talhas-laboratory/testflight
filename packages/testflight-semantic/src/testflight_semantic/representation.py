"""Generic representation bindings, profiles, and manifestation rules."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class BindingMode(StrEnum):
    CANONICAL = "canonical"
    ADAPTIVE = "adaptive"
    LOCAL = "local"


class Deontic(StrEnum):
    MUST = "must"
    SHOULD = "should"
    MAY = "may"
    MUST_NOT = "must_not"


class ValidationMethod(StrEnum):
    DETERMINISTIC = "deterministic"
    MODEL = "model"
    HYBRID = "hybrid"
    HUMAN = "human"


class RepresentationRule(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    rule_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    selector: dict[str, Any] = Field(default_factory=dict)
    condition: dict[str, Any] = Field(default_factory=dict)
    facet_id: str = Field(min_length=1)
    deontic: Deontic
    constraint: Any
    rationale: str = Field(min_length=1)
    validation_method: ValidationMethod
    severity: str = Field(min_length=1)
    override_policy_id: str | None = None


class RepresentationProfile(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    profile_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    includes: tuple[str, ...] = ()
    rule_ids: tuple[str, ...] = ()

    @model_validator(mode="after")
    def reject_self_cycle(self) -> "RepresentationProfile":
        if self.profile_id in self.includes:
            raise ValueError("RepresentationProfile cannot include itself")
        return self


class RepresentationBinding(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    binding_id: str = Field(min_length=1)
    entity_id: str = Field(min_length=1)
    profile_id: str = Field(min_length=1)
    profile_version: str = Field(min_length=1)
    context_id: str = Field(min_length=1)
    mode: BindingMode
    derivation_id: str | None = None
    authority_grant_id: str | None = None


class ComplianceStatus(StrEnum):
    PASS = "pass"
    PARTIAL = "partial"
    FAIL = "fail"
    UNASSESSABLE = "unassessable"


class FreshnessStatus(StrEnum):
    CURRENT = "current"
    POTENTIALLY_STALE = "potentially_stale"
    STALE = "stale"


class RepresentationEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    manifestation_id: str = Field(min_length=1)
    compliance: ComplianceStatus
    freshness: FreshnessStatus
    findings: tuple[str, ...] = ()
    rule_ids: tuple[str, ...] = ()
    context_id: str = Field(min_length=1)
    derivation_id: str = Field(min_length=1)


def resolve_profile_order(
    profiles: dict[str, RepresentationProfile], root_id: str
) -> tuple[RepresentationProfile, ...]:
    """Return shared-to-specific profile order and reject include cycles."""

    visiting: set[str] = set()
    visited: set[str] = set()
    ordered: list[RepresentationProfile] = []

    def visit(profile_id: str) -> None:
        if profile_id in visiting:
            raise ValueError(f"representation profile cycle detected at: {profile_id}")
        if profile_id in visited:
            return
        try:
            profile = profiles[profile_id]
        except KeyError as exc:
            raise ValueError(f"unknown representation profile: {profile_id}") from exc
        visiting.add(profile_id)
        for parent_id in profile.includes:
            visit(parent_id)
        visiting.remove(profile_id)
        visited.add(profile_id)
        ordered.append(profile)

    visit(root_id)
    return tuple(ordered)


__all__ = [
    "BindingMode",
    "ComplianceStatus",
    "Deontic",
    "FreshnessStatus",
    "RepresentationBinding",
    "RepresentationEvaluation",
    "RepresentationProfile",
    "RepresentationRule",
    "ValidationMethod",
    "resolve_profile_order",
]
