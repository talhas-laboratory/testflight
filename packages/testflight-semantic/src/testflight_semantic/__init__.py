"""Provider-neutral semantic contracts for Testflight."""

from .assertions import AssertionProposal, EpistemicStatus, Perspective
from .definitions import DefinitionExample, EntityDefinition, RelationshipDefinition
from .evidence import EvidenceEnvelope, EvidenceSpan
from .extractor import SemanticExtractor, StructuredOutputCall
from .identity import CanonicalEntity, ReferentHypothesis
from .models import EntityMatch, ExtractionResult, MatchType, RelationshipMatch
from .ports import (
    AssertionRepository,
    EvidenceRepository,
    ProjectionCallable,
    SemanticStatus,
    StructuredExtractionProvider,
)
from .prompt import compile_extraction_prompt
from .validation import (
    EntityOccurrence,
    RelationshipOccurrence,
    ValidationRejection,
    ValidationResult,
    validate_extraction,
)

__all__ = [
    "AssertionProposal",
    "AssertionRepository",
    "CanonicalEntity",
    "DefinitionExample",
    "EntityDefinition",
    "EntityMatch",
    "EntityOccurrence",
    "EpistemicStatus",
    "EvidenceEnvelope",
    "EvidenceRepository",
    "EvidenceSpan",
    "ExtractionResult",
    "MatchType",
    "Perspective",
    "ProjectionCallable",
    "ReferentHypothesis",
    "RelationshipDefinition",
    "RelationshipMatch",
    "RelationshipOccurrence",
    "SemanticExtractor",
    "SemanticStatus",
    "StructuredExtractionProvider",
    "StructuredOutputCall",
    "ValidationRejection",
    "ValidationResult",
    "compile_extraction_prompt",
    "validate_extraction",
]
