"""Versioned dependency rules and freshness markers."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .context import Context


class ChangeType(StrEnum):
    ENTITY_REVISION = "EntityRevision"
    ASSERTION_ACCEPTED = "AssertionAccepted"
    ASSERTION_REVOKED = "AssertionRevoked"
    ASSERTION_SUPERSEDED = "AssertionSuperseded"
    IDENTITY_MERGE = "IdentityMerge"
    IDENTITY_SPLIT = "IdentitySplit"
    RELATION_CHANGED = "RelationChanged"
    REPRESENTATION_CHANGED = "RepresentationChanged"
    POLICY_CHANGED = "PolicyChanged"
    EVIDENCE_AUTHORITY_CHANGED = "EvidenceAuthorityChanged"
    ONTOLOGY_CHANGED = "OntologyChanged"


class DependencyEffect(StrEnum):
    POTENTIALLY_STALE = "potentially_stale"
    REVIEW_REQUIRED = "review_required"
    INVALIDATE = "invalidate"


class FreshnessState(StrEnum):
    CURRENT = "current"
    POTENTIALLY_STALE = "potentially_stale"
    STALE = "stale"
    UNDER_REVIEW = "under_review"
    REAFFIRMED = "reaffirmed"
    REVISED = "revised"
    RETIRED = "retired"


class DependencyRule(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    rule_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    upstream_selector: dict[str, Any] = Field(min_length=1)
    downstream_selector: dict[str, Any] = Field(min_length=1)
    trigger_change_types: tuple[ChangeType, ...] = ()
    scope: dict[str, Any] = Field(default_factory=dict)
    effect: DependencyEffect = DependencyEffect.POTENTIALLY_STALE
    max_depth: int = Field(default=2, ge=0)
    authority_requirement_id: str | None = None

    @model_validator(mode="after")
    def require_trigger(self) -> "DependencyRule":
        if not self.trigger_change_types:
            raise ValueError("DependencyRule requires at least one trigger change type")
        return self


class DependencyEdge(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    edge_id: str = Field(min_length=1)
    upstream_id: str = Field(min_length=1)
    downstream_id: str = Field(min_length=1)
    rule_id: str = Field(min_length=1)
    rule_version: str = Field(min_length=1)
    context_id: str = Field(min_length=1)
    materialization: str = Field(min_length=1)
    created_at: datetime
    derivation_id: str | None = None


class StalenessMarker(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    marker_id: str = Field(min_length=1)
    downstream_id: str = Field(min_length=1)
    state: FreshnessState
    cause_ids: tuple[str, ...] = ()
    rule_id: str = Field(min_length=1)
    rule_version: str = Field(min_length=1)
    created_at: datetime
    review_note: str | None = None
    derivation_id: str | None = None


class DependencyCandidate(BaseModel):
    """A context-scoped item evaluated by a dependency rule."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    record_id: str = Field(min_length=1)
    entity_id: str = Field(min_length=1)
    entity_type: str = Field(min_length=1)
    context: Context
    relation_path: tuple[str, ...] = ()


def _intervals_overlap(left: Any, right: Any) -> bool:
    if left is None or right is None:
        return True
    left_start, left_end = left.from_time, left.to_time
    right_start, right_end = right.from_time, right.to_time
    if left_end is not None and right_start is not None and left_end <= right_start:
        return False
    return not (right_end is not None and left_start is not None and right_end <= left_start)


def contexts_overlap(left: Context, right: Context) -> bool:
    """Check whether two applicability scopes can both hold.

    Unspecified dimensions are broad, not conflicting. A shared dimension with
    different explicit values prevents dependency propagation.
    """

    for field in ("brand_system_id", "portfolio_id", "brand_id", "offering_id", "locale"):
        left_value = getattr(left, field)
        right_value = getattr(right, field)
        if left_value is not None and right_value is not None and left_value != right_value:
            return False
    for field in (
        "audience_ids",
        "channel_ids",
        "artifact_type_ids",
        "campaign_or_occasion_ids",
    ):
        left_values = set(getattr(left, field))
        right_values = set(getattr(right, field))
        if left_values and right_values and not left_values & right_values:
            return False
    for key in set(left.dimensions) & set(right.dimensions):
        if left.dimensions[key] != right.dimensions[key]:
            return False
    return _intervals_overlap(left.valid_time, right.valid_time)


def selector_matches(
    selector: dict[str, Any],
    *,
    entity_id: str,
    entity_type: str,
    context: Context | None = None,
    relation_path: tuple[str, ...] = (),
) -> bool:
    """Evaluate a deliberately bounded, explainable selector subset."""

    if "entity_id" in selector and selector["entity_id"] != entity_id:
        return False
    if "entity_type" in selector and selector["entity_type"] != entity_type:
        return False
    expected_path = tuple(selector.get("relation_path", ()))
    if expected_path and expected_path != relation_path:
        return False
    scope = selector.get("scope")
    if scope:
        if context is None:
            return False
        scoped_context = Context.model_validate(scope)
        if not contexts_overlap(context, scoped_context):
            return False
    return True


def evaluate_dependency_rule(
    rule: DependencyRule,
    *,
    upstream: DependencyCandidate,
    downstream: tuple[DependencyCandidate, ...],
    change_type: ChangeType,
    created_at: datetime,
    derivation_id: str | None = None,
) -> tuple[DependencyEdge, ...]:
    """Materialize only bounded, context-overlapping dependency impacts.

    The caller decides whether to persist returned edges. This function never
    changes downstream records and deliberately does not infer a causal claim.
    """

    if change_type not in rule.trigger_change_types:
        return ()
    if not selector_matches(
        rule.upstream_selector,
        entity_id=upstream.entity_id,
        entity_type=upstream.entity_type,
        context=upstream.context,
        relation_path=upstream.relation_path,
    ):
        return ()
    if rule.scope and not selector_matches(
        {"scope": rule.scope},
        entity_id=upstream.entity_id,
        entity_type=upstream.entity_type,
        context=upstream.context,
    ):
        return ()
    impacts: list[DependencyEdge] = []
    for candidate in downstream:
        if len(candidate.relation_path) > rule.max_depth:
            continue
        if not contexts_overlap(upstream.context, candidate.context):
            continue
        if not selector_matches(
            rule.downstream_selector,
            entity_id=candidate.entity_id,
            entity_type=candidate.entity_type,
            context=candidate.context,
            relation_path=candidate.relation_path,
        ):
            continue
        impacts.append(
            DependencyEdge(
                edge_id=f"dependency:{rule.rule_id}:{upstream.record_id}:{candidate.record_id}",
                upstream_id=upstream.record_id,
                downstream_id=candidate.record_id,
                rule_id=rule.rule_id,
                rule_version=rule.version,
                context_id=candidate.context.context_id,
                materialization="rule_evaluation",
                created_at=created_at,
                derivation_id=derivation_id,
            )
        )
    return tuple(impacts)


__all__ = [
    "ChangeType",
    "DependencyEffect",
    "DependencyEdge",
    "DependencyCandidate",
    "DependencyRule",
    "FreshnessState",
    "StalenessMarker",
    "contexts_overlap",
    "evaluate_dependency_rule",
    "selector_matches",
]
