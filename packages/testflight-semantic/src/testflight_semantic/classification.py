"""Deterministic candidate classification for the semantic constitution."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class CandidateKind(StrEnum):
    ENTITY = "entity"
    PROPERTY = "property"
    RELATIONSHIP = "relationship"
    ASSERTION = "assertion"
    EVENT = "event"
    EVIDENCE = "evidence"
    OBSERVATION = "observation"
    GOVERNANCE = "governance"


class ClassificationStatus(StrEnum):
    RESOLVED = "resolved"
    AMBIGUOUS = "ambiguous"
    HOLD = "hold"


class CandidateSignals(BaseModel):
    """Observable classification signals; this model does not infer them from text."""

    model_config = ConfigDict(extra="forbid")

    has_persistent_identity: bool = False
    is_temporally_bounded_occurrence: bool = False
    is_proposition: bool = False
    connects_identities: bool = False
    is_source_record: bool = False
    is_observation: bool = False
    governs_interpretation_or_mutation: bool = False
    evidence_ref: str | None = None
    explicitly_unknown: bool = False


class ClassificationResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    semantic_kind: CandidateKind | None = None
    rationale: str = Field(min_length=1)
    alternatives: tuple[CandidateKind, ...] = ()
    status: ClassificationStatus


def classify_candidate(signals: CandidateSignals) -> ClassificationResult:
    """Apply the constitutional classification order without guessing from labels."""

    if not signals.evidence_ref and not signals.explicitly_unknown:
        return ClassificationResult(
            rationale="No evidence-bearing referent or explicit unknown status was supplied.",
            status=ClassificationStatus.HOLD,
        )
    if signals.is_temporally_bounded_occurrence:
        return ClassificationResult(
            semantic_kind=CandidateKind.EVENT,
            rationale="A temporally bounded occurrence is classified as an Event.",
            status=ClassificationStatus.RESOLVED,
        )
    if signals.is_proposition:
        return ClassificationResult(
            semantic_kind=CandidateKind.ASSERTION,
            rationale="A supportable, scoped proposition is classified as an Assertion.",
            status=ClassificationStatus.RESOLVED,
        )
    if signals.has_persistent_identity:
        return ClassificationResult(
            semantic_kind=CandidateKind.ENTITY,
            rationale="Persistent identity and independent history qualify as an Entity.",
            status=ClassificationStatus.RESOLVED,
        )
    if signals.connects_identities:
        return ClassificationResult(
            semantic_kind=CandidateKind.RELATIONSHIP,
            rationale="A reusable connection between identities is a Relationship definition.",
            status=ClassificationStatus.RESOLVED,
        )
    if signals.is_source_record:
        return ClassificationResult(
            semantic_kind=CandidateKind.EVIDENCE,
            rationale="A source record belongs to the Evidence plane, not the ontology.",
            status=ClassificationStatus.RESOLVED,
        )
    if signals.is_observation:
        return ClassificationResult(
            semantic_kind=CandidateKind.OBSERVATION,
            rationale="An act of noticing belongs to the epistemic plane.",
            status=ClassificationStatus.RESOLVED,
        )
    if signals.governs_interpretation_or_mutation:
        return ClassificationResult(
            semantic_kind=CandidateKind.GOVERNANCE,
            rationale="A rule governing interpretation or mutation belongs to governance.",
            status=ClassificationStatus.RESOLVED,
        )
    return ClassificationResult(
        semantic_kind=CandidateKind.PROPERTY,
        rationale="The candidate describes another identity without independent lifecycle.",
        status=ClassificationStatus.RESOLVED,
    )


__all__ = [
    "CandidateKind",
    "CandidateSignals",
    "ClassificationResult",
    "ClassificationStatus",
    "classify_candidate",
]
