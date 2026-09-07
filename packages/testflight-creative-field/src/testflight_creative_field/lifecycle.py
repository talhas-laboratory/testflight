"""Deterministic Creative Field synthesis, review, diff and staleness helpers."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from .models import (
    ArtifactStatus,
    CreativeFieldProposal,
    CreativeFieldVersion,
    DimensionState,
    Exclusion,
    FieldConflict,
    FieldDimension,
    LifecycleStatus,
    MissingDimension,
    Principle,
    ReferenceContribution,
    ReferenceInterpretation,
    ReviewAction,
    ReviewDecision,
    Tension,
)
from .workflows import OperatorExecutor

SYNTHESIS_OPERATOR_ID = "world://operator/creative/field-synthesis"


@dataclass(frozen=True, slots=True)
class FieldDiff:
    """Stable semantic diff between two field representations."""

    added: tuple[str, ...] = ()
    removed: tuple[str, ...] = ()
    changed: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class FieldLifecycleResult:
    status: ArtifactStatus
    proposal: CreativeFieldProposal | None = None
    version: CreativeFieldVersion | None = None
    diff: FieldDiff | None = None
    errors: tuple[str, ...] = ()
    hold_reason: str | None = None
    receipt: Mapping[str, Any] = field(default_factory=dict)


def _status(value: str) -> ArtifactStatus:
    return {
        "proposal": ArtifactStatus.SUCCESS,
        "success": ArtifactStatus.SUCCESS,
        "partial": ArtifactStatus.PARTIAL,
        "branch": ArtifactStatus.PARTIAL,
        "hold": ArtifactStatus.HELD,
        "ask": ArtifactStatus.HELD,
        "no_hit": ArtifactStatus.UNAVAILABLE,
        "failed": ArtifactStatus.FAILED,
    }.get(value, ArtifactStatus.FAILED)


def _strings(value: Any) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(item for item in value if isinstance(item, str) and item.strip())


def _required_strings(value: Any, label: str) -> tuple[str, ...]:
    result = _strings(value)
    if not result:
        raise ValueError(f"{label} must contain at least one source id")
    return result


def _field_diff(
    previous: CreativeFieldVersion | None,
    current: CreativeFieldProposal | CreativeFieldVersion,
) -> FieldDiff:
    if previous is None:
        return FieldDiff(added=("principles", "tensions", "exclusions", "dimensions"))
    previous_map = {
        "principles": previous.principles,
        "tensions": previous.tensions,
        "exclusions": previous.exclusions,
        "dimensions": previous.dimension_states,
        "conflicts": previous.conflicts,
        "missing_dimensions": previous.missing_dimensions,
    }
    current_map = {
        "principles": current.principles,
        "tensions": current.tensions,
        "exclusions": current.exclusions,
        "dimensions": current.dimension_states,
        "conflicts": current.conflicts,
        "missing_dimensions": current.missing_dimensions,
    }
    added = tuple(sorted(key for key in current_map if not previous_map[key] and current_map[key]))
    removed = tuple(
        sorted(key for key in previous_map if previous_map[key] and not current_map[key])
    )
    changed = tuple(
        sorted(
            key
            for key in current_map
            if previous_map[key]
            and current_map[key]
            and [item.model_dump(mode="json") for item in previous_map[key]]
            != [item.model_dump(mode="json") for item in current_map[key]]
        )
    )
    return FieldDiff(added=added, removed=removed, changed=changed)


def _principles(raw: Any, default_sources: tuple[str, ...]) -> tuple[Principle, ...]:
    if not isinstance(raw, list):
        raise ValueError("principles must be a list")
    result: list[Principle] = []
    for position, item in enumerate(raw, start=1):
        if not isinstance(item, Mapping):
            raise ValueError(f"principle {position} is not an object")
        statement = item.get("statement")
        dimensions = _strings(item.get("dimension_ids"))
        if not isinstance(statement, str) or not statement.strip() or not dimensions:
            raise ValueError(f"principle {position} is incomplete")
        result.append(
            Principle(
                principle_id=str(item.get("principle_id") or f"principle:{position}"),
                statement=statement,
                conditions=_strings(item.get("conditions")),
                dimension_ids=dimensions,
                source_contribution_ids=_required_strings(
                    item.get("source_contribution_ids") or default_sources,
                    f"principle {position} source_contribution_ids",
                ),
            )
        )
    return tuple(result)


def _tensions(raw: Any, default_sources: tuple[str, ...]) -> tuple[Tension, ...]:
    if not isinstance(raw, list):
        raise ValueError("tensions must be a list")
    result: list[Tension] = []
    for position, item in enumerate(raw, start=1):
        if not isinstance(item, Mapping):
            raise ValueError(f"tension {position} is not an object")
        statement = item.get("statement")
        poles = _strings(item.get("poles"))
        if not isinstance(statement, str) or not statement.strip() or len(poles) < 2:
            raise ValueError(f"tension {position} must preserve at least two poles")
        result.append(
            Tension(
                tension_id=str(item.get("tension_id") or f"tension:{position}"),
                statement=statement,
                poles=poles,
                source_contribution_ids=_required_strings(
                    item.get("source_contribution_ids") or default_sources,
                    f"tension {position} source_contribution_ids",
                ),
            )
        )
    return tuple(result)


def _exclusions(raw: Any, default_sources: tuple[str, ...]) -> tuple[Exclusion, ...]:
    if not isinstance(raw, list):
        raise ValueError("exclusions must be a list")
    result: list[Exclusion] = []
    for position, item in enumerate(raw, start=1):
        if not isinstance(item, Mapping):
            raise ValueError(f"exclusion {position} is not an object")
        statement = item.get("statement")
        category = item.get("category")
        if (
            not isinstance(statement, str)
            or not statement.strip()
            or not isinstance(category, str)
            or not category.strip()
        ):
            raise ValueError(f"exclusion {position} is incomplete")
        result.append(
            Exclusion(
                exclusion_id=str(item.get("exclusion_id") or f"exclusion:{position}"),
                statement=statement,
                category=category,
                source_contribution_ids=_required_strings(
                    item.get("source_contribution_ids") or default_sources,
                    f"exclusion {position} source_contribution_ids",
                ),
            )
        )
    return tuple(result)


def _dimensions(raw: Any) -> tuple[DimensionState, ...]:
    if not isinstance(raw, list):
        raise ValueError("dimension_states must be a list")
    result: list[DimensionState] = []
    for position, item in enumerate(raw, start=1):
        if not isinstance(item, Mapping):
            raise ValueError(f"dimension state {position} is not an object")
        dimension_id = item.get("dimension_id")
        summary = item.get("summary")
        if (
            not isinstance(dimension_id, str)
            or not dimension_id.strip()
            or not isinstance(summary, str)
            or not summary.strip()
        ):
            raise ValueError(f"dimension state {position} is incomplete")
        result.append(
            DimensionState(
                dimension_id=dimension_id,
                summary=summary,
                values=item.get("values") if isinstance(item.get("values"), dict) else {},
                source_contribution_ids=_strings(item.get("source_contribution_ids")),
                status=LifecycleStatus.PROPOSED,
            )
        )
    return tuple(result)


class CreativeFieldLifecycle:
    """Build reviewable proposals and immutable successor versions."""

    def synthesize(
        self,
        *,
        project_id: str,
        field_id: str,
        interpretations: Sequence[ReferenceInterpretation],
        contributions: Sequence[ReferenceContribution],
        dimensions: Sequence[FieldDimension],
        project_purpose: str,
        derivation_id: str,
        executor: OperatorExecutor,
        parent_version: CreativeFieldVersion | None = None,
        configuration: Mapping[str, Any] | None = None,
    ) -> FieldLifecycleResult:
        if not interpretations or not contributions:
            return FieldLifecycleResult(
                status=ArtifactStatus.UNAVAILABLE,
                errors=("field synthesis requires interpretations and contributions",),
                hold_reason="no_contributions",
            )
        if any(item.project_id != project_id for item in interpretations):
            return FieldLifecycleResult(
                status=ArtifactStatus.HELD,
                errors=("interpretation project scope differs",),
                hold_reason="scope_mismatch",
            )
        source_ids = tuple(item.contribution_id for item in contributions)
        request = {
            "operator_id": SYNTHESIS_OPERATOR_ID,
            "operator_version": 1,
            "operation_key": f"synthesize:{field_id}:{derivation_id}",
            "modality": "multimodal",
            "project_id": project_id,
            "input": {
                "project_purpose": project_purpose,
                "field_id": field_id,
                "interpretations": [item.model_dump(mode="json") for item in interpretations],
                "contributions": [item.model_dump(mode="json") for item in contributions],
                "dimensions": [item.model_dump(mode="json") for item in dimensions],
                "parent_version": parent_version.model_dump(mode="json")
                if parent_version
                else None,
                "content_is_untrusted": True,
            },
            "disclosure_refs": [*source_ids, *[item.interpretation_id for item in contributions]],
            "configuration": dict(configuration or {}),
        }
        execution = executor.execute(request)
        status = _status(execution.status)
        if status not in {ArtifactStatus.SUCCESS, ArtifactStatus.PARTIAL}:
            return FieldLifecycleResult(
                status=status,
                errors=execution.errors,
                hold_reason=execution.hold_reason,
                receipt=execution.receipt,
            )
        if not isinstance(execution.output, Mapping):
            return FieldLifecycleResult(
                status=ArtifactStatus.FAILED,
                errors=("field synthesis operator returned a non-object",),
                receipt=execution.receipt,
            )
        raw = execution.output
        try:
            proposal = CreativeFieldProposal(
                proposal_id=str(raw.get("proposal_id") or f"{derivation_id}:proposal"),
                field_id=field_id,
                project_id=project_id,
                source_contribution_ids=_required_strings(
                    raw.get("source_contribution_ids") or source_ids,
                    "proposal source_contribution_ids",
                ),
                principles=_principles(raw.get("principles", []), source_ids),
                tensions=_tensions(raw.get("tensions", []), source_ids),
                exclusions=_exclusions(raw.get("exclusions", []), source_ids),
                dimension_states=_dimensions(raw.get("dimension_states", [])),
                conflicts=tuple(
                    FieldConflict(
                        conflict_id=str(
                            item.get("conflict_id") or f"{derivation_id}:conflict:{position}"
                        ),
                        record_ids=_strings(item.get("record_ids")),
                        description=item["description"],
                    )
                    for position, item in enumerate(raw.get("conflicts", []), start=1)
                    if isinstance(item, Mapping)
                    and isinstance(item.get("description"), str)
                    and len(_strings(item.get("record_ids"))) >= 2
                ),
                missing_dimensions=tuple(
                    MissingDimension(
                        dimension_id=item["dimension_id"],
                        reason=item["reason"],
                        question=item.get("question")
                        if isinstance(item.get("question"), str)
                        else None,
                    )
                    for item in raw.get("missing_dimensions", [])
                    if isinstance(item, Mapping)
                    and isinstance(item.get("dimension_id"), str)
                    and isinstance(item.get("reason"), str)
                ),
                semantic_diff={},
                evidence_coverage=raw.get("evidence_coverage")
                if isinstance(raw.get("evidence_coverage"), dict)
                else {},
                derivation_id=derivation_id,
            )
        except (TypeError, ValueError, KeyError) as error:
            return FieldLifecycleResult(
                status=ArtifactStatus.FAILED,
                errors=(f"field synthesis output is invalid: {error}",),
                receipt=execution.receipt,
            )
        diff = _field_diff(parent_version, proposal)
        proposal = proposal.model_copy(
            update={
                "semantic_diff": {
                    "added": diff.added,
                    "removed": diff.removed,
                    "changed": diff.changed,
                }
            }
        )
        return FieldLifecycleResult(
            status=ArtifactStatus.PARTIAL
            if status is ArtifactStatus.PARTIAL
            else ArtifactStatus.SUCCESS,
            proposal=proposal,
            diff=diff,
            receipt=execution.receipt,
        )

    def review_and_version(
        self,
        *,
        proposal: CreativeFieldProposal,
        decision: ReviewDecision,
        version_id: str,
        reviewed_at: str,
        parent_version: CreativeFieldVersion | None = None,
        replacement_proposal: CreativeFieldProposal | None = None,
    ) -> FieldLifecycleResult:
        if decision.target_id != proposal.proposal_id:
            return FieldLifecycleResult(
                status=ArtifactStatus.HELD,
                errors=("review decision targets a different proposal",),
                hold_reason="review_target_mismatch",
            )
        if not decision.authority_grant_id:
            return FieldLifecycleResult(
                status=ArtifactStatus.HELD,
                errors=("review decision lacks an authority grant",),
                hold_reason="authority_missing",
            )
        if decision.action not in {ReviewAction.ACCEPT, ReviewAction.MODIFY}:
            return FieldLifecycleResult(
                status=ArtifactStatus.HELD,
                errors=(f"review action {decision.action.value} does not create a version",),
                hold_reason="review_deferred",
            )
        candidate = replacement_proposal if decision.action is ReviewAction.MODIFY else proposal
        if candidate is None:
            return FieldLifecycleResult(
                status=ArtifactStatus.HELD,
                errors=("modify review requires a replacement proposal",),
                hold_reason="replacement_missing",
            )
        if candidate.field_id != proposal.field_id or candidate.project_id != proposal.project_id:
            return FieldLifecycleResult(
                status=ArtifactStatus.HELD,
                errors=("replacement proposal changes field or project identity",),
                hold_reason="identity_changed",
            )
        try:
            version = CreativeFieldVersion(
                field_id=candidate.field_id,
                version_id=version_id,
                project_id=candidate.project_id,
                parent_version_ids=((parent_version.version_id,) if parent_version else ()),
                principles=candidate.principles,
                tensions=candidate.tensions,
                exclusions=candidate.exclusions,
                dimension_states=candidate.dimension_states,
                conflicts=candidate.conflicts,
                missing_dimensions=candidate.missing_dimensions,
                source_contribution_ids=candidate.source_contribution_ids,
                review_record_ids=(decision.review_id,),
                dependency_manifest={"proposal_id": candidate.proposal_id},
                lifecycle_status=LifecycleStatus.ACCEPTED,
                created_at=reviewed_at,
                derivation_id=candidate.derivation_id,
            )
        except (TypeError, ValueError) as error:
            return FieldLifecycleResult(
                status=ArtifactStatus.FAILED,
                errors=(f"field version is invalid: {error}",),
            )
        return FieldLifecycleResult(
            status=ArtifactStatus.SUCCESS,
            version=version,
            diff=_field_diff(parent_version, version),
            proposal=candidate,
        )

    @staticmethod
    def reconstruct(version: CreativeFieldVersion) -> dict[str, Any]:
        """Return a deterministic, JSON-compatible reconstruction of one field version."""

        return version.model_dump(mode="json", exclude={"derivation_id"})

    @staticmethod
    def affected_dependents(
        dependents: Iterable[Mapping[str, Any]], changed_record_ids: Iterable[str]
    ) -> tuple[str, ...]:
        changed = set(changed_record_ids)
        affected = {
            str(item["record_id"])
            for item in dependents
            if isinstance(item.get("record_id"), str)
            and changed.intersection(_strings(item.get("dependency_ids")))
        }
        return tuple(sorted(affected))


__all__ = [
    "CreativeFieldLifecycle",
    "FieldDiff",
    "FieldLifecycleResult",
    "SYNTHESIS_OPERATOR_ID",
]
