"""Backward-compatible imports for deterministic semantic validation."""

from testflight_semantic.validation import (
    EntityOccurrence,
    RelationshipOccurrence,
    ValidationRejection,
    ValidationResult,
    validate_extraction,
)

__all__ = [
    "EntityOccurrence",
    "RelationshipOccurrence",
    "ValidationRejection",
    "ValidationResult",
    "validate_extraction",
]
