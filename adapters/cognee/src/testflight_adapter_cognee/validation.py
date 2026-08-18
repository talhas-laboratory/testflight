"""Deterministic validation and provenance for semantic extraction results."""

from dataclasses import dataclass, field
from uuid import NAMESPACE_URL, UUID, uuid5

from .definitions import EntityDefinition
from .models import ExtractionResult, MatchType


@dataclass(frozen=True, slots=True)
class EntityOccurrence:
    """A validated occurrence, retaining exact source provenance."""

    entity_type: str
    quote: str
    normalized_content: str
    match_type: MatchType
    source_id: str
    start: int
    end: int
    confidence: float | None = None
    occurrence_id: UUID = field(init=False)

    def __post_init__(self) -> None:
        value = f"entity:{self.entity_type}:{self.source_id}:{self.start}:{self.end}"
        object.__setattr__(self, "occurrence_id", uuid5(NAMESPACE_URL, value))


@dataclass(frozen=True, slots=True)
class RelationshipOccurrence:
    """A validated relationship occurrence between two entity occurrences."""

    relationship_type: str
    source_occurrence_id: UUID
    target_occurrence_id: UUID
    evidence_quote: str
    source_id: str
    start: int
    end: int
    confidence: float | None = None
    relationship_id: UUID = field(init=False)

    def __post_init__(self) -> None:
        value = (
            f"relationship:{self.relationship_type}:{self.source_occurrence_id}:"
            f"{self.target_occurrence_id}:{self.source_id}:{self.start}:{self.end}"
        )
        object.__setattr__(self, "relationship_id", uuid5(NAMESPACE_URL, value))


@dataclass(frozen=True, slots=True)
class ValidationRejection:
    kind: str
    index: int
    reason: str


@dataclass(frozen=True, slots=True)
class ValidationResult:
    occurrences: tuple[EntityOccurrence, ...]
    relationships: tuple[RelationshipOccurrence, ...]
    rejections: tuple[ValidationRejection, ...]


def _find_unclaimed(text: str, quote: str, claimed: set[tuple[int, int]]) -> tuple[int, int] | None:
    if not quote:
        return None
    cursor = 0
    while True:
        start = text.find(quote, cursor)
        if start < 0:
            return None
        end = start + len(quote)
        if (start, end) not in claimed:
            return start, end
        cursor = start + 1


def validate_extraction(
    text: str,
    definition: EntityDefinition,
    result: ExtractionResult,
    source_id: str,
) -> ValidationResult:
    """Reject unsupported output and attach deterministic offsets/IDs.

    The LLM is never trusted to provide offsets.  An occurrence is accepted only
    when its quote appears verbatim in the supplied source text.
    """

    definition.validate()
    if not source_id.strip():
        raise ValueError("source_id must not be empty")

    occurrences: list[EntityOccurrence] = []
    relationships: list[RelationshipOccurrence] = []
    rejections: list[ValidationRejection] = []
    claimed: set[tuple[int, int]] = set()

    for index, match in enumerate(result.matches):
        located = _find_unclaimed(text, match.quote, claimed)
        if located is None:
            reason = "quote does not occur verbatim in source text or is a duplicate occurrence"
            rejections.append(ValidationRejection("entity", index, reason))
            continue
        if not match.normalized_content.strip():
            rejections.append(ValidationRejection("entity", index, "normalized_content is blank"))
            continue
        start, end = located
        claimed.add(located)
        occurrences.append(
            EntityOccurrence(
                entity_type=definition.name,
                quote=match.quote,
                normalized_content=match.normalized_content.strip(),
                match_type=match.match_type,
                source_id=source_id,
                start=start,
                end=end,
                confidence=match.confidence,
            )
        )

    by_quote: dict[str, list[EntityOccurrence]] = {}
    for occurrence in occurrences:
        by_quote.setdefault(occurrence.quote, []).append(occurrence)

    relationship_names = {relationship.name.casefold() for relationship in definition.relationships}
    for index, match in enumerate(result.relationships):
        relationship_key = match.relationship_type.strip().casefold()
        if relationship_key not in relationship_names:
            rejections.append(
                ValidationRejection(
                    "relationship",
                    index,
                    f"relationship type is not defined: {match.relationship_type}",
                )
            )
            continue
        source_candidates = by_quote.get(match.source_quote, [])
        target_candidates = by_quote.get(match.target_quote, [])
        if not source_candidates or not target_candidates:
            rejections.append(
                ValidationRejection(
                    "relationship",
                    index,
                    "both endpoint quotes must refer to accepted entity occurrences",
                )
            )
            continue
        if source_candidates[0].occurrence_id == target_candidates[0].occurrence_id:
            rejections.append(
                ValidationRejection("relationship", index, "relationship endpoints must differ")
            )
            continue
        evidence = _find_unclaimed(text, match.evidence_quote, set())
        if evidence is None:
            rejections.append(
                ValidationRejection(
                    "relationship", index, "evidence_quote does not occur verbatim in source text"
                )
            )
            continue
        start, end = evidence
        relationship = RelationshipOccurrence(
            relationship_type=match.relationship_type.strip(),
            source_occurrence_id=source_candidates[0].occurrence_id,
            target_occurrence_id=target_candidates[0].occurrence_id,
            evidence_quote=match.evidence_quote,
            source_id=source_id,
            start=start,
            end=end,
            confidence=match.confidence,
        )
        relationships.append(relationship)

    return ValidationResult(tuple(occurrences), tuple(relationships), tuple(rejections))


__all__ = [
    "EntityOccurrence",
    "RelationshipOccurrence",
    "ValidationRejection",
    "ValidationResult",
    "validate_extraction",
]
