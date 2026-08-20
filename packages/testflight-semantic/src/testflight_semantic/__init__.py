"""Provider-neutral semantic contracts for Testflight."""

from .assertions import AssertionProposal, EpistemicStatus, Perspective
from .classification import (
    CandidateKind,
    CandidateSignals,
    ClassificationResult,
    ClassificationStatus,
    classify_candidate,
)
from .context import Context
from .definitions import DefinitionExample, EntityDefinition, RelationshipDefinition
from .dependencies import (
    ChangeType,
    DependencyEdge,
    DependencyEffect,
    DependencyRule,
    FreshnessState,
    StalenessMarker,
    selector_matches,
)
from .evidence import EvidenceEnvelope, EvidenceSpan
from .extractor import SemanticExtractor, StructuredOutputCall
from .governance import AuthorityGrant, Capability
from .identity import CanonicalEntity, ReferentHypothesis
from .kernel import (
    Assertion,
    AssertionStatus,
    DefinitionKind,
    DefinitionStatus,
    EntityLifecycle,
    Event,
    IdentityScope,
    OntologyDefinition,
    SemanticEntity,
    context_for_assertion,
)
from .models import EntityMatch, ExtractionResult, MatchType, RelationshipMatch
from .ports import (
    AssertionRepository,
    EvidenceRepository,
    ProjectionCallable,
    SemanticStatus,
    StructuredExtractionProvider,
)
from .prompt import compile_extraction_prompt
from .provenance import DerivationRecord, DerivationResult, validate_derivation_graph
from .representation import (
    BindingMode,
    ComplianceStatus,
    Deontic,
    FreshnessStatus,
    RepresentationBinding,
    RepresentationEvaluation,
    RepresentationProfile,
    RepresentationRule,
    ValidationMethod,
    resolve_profile_order,
)
from .time import BoundSemantics, TemporalInterval, TimePrecision
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
    "Assertion",
    "AssertionStatus",
    "AuthorityGrant",
    "BindingMode",
    "BoundSemantics",
    "CanonicalEntity",
    "CandidateKind",
    "CandidateSignals",
    "Capability",
    "ChangeType",
    "ClassificationResult",
    "ClassificationStatus",
    "ComplianceStatus",
    "Context",
    "DefinitionKind",
    "DefinitionStatus",
    "DefinitionExample",
    "DependencyEffect",
    "DependencyEdge",
    "DependencyRule",
    "DerivationRecord",
    "DerivationResult",
    "Deontic",
    "EntityDefinition",
    "EntityMatch",
    "EntityOccurrence",
    "EntityLifecycle",
    "EpistemicStatus",
    "EvidenceEnvelope",
    "EvidenceRepository",
    "EvidenceSpan",
    "ExtractionResult",
    "Event",
    "FreshnessState",
    "FreshnessStatus",
    "IdentityScope",
    "MatchType",
    "OntologyDefinition",
    "Perspective",
    "ProjectionCallable",
    "ReferentHypothesis",
    "RepresentationBinding",
    "RepresentationEvaluation",
    "RepresentationProfile",
    "RepresentationRule",
    "RelationshipDefinition",
    "RelationshipMatch",
    "RelationshipOccurrence",
    "SemanticExtractor",
    "SemanticEntity",
    "SemanticStatus",
    "StalenessMarker",
    "StructuredExtractionProvider",
    "StructuredOutputCall",
    "TemporalInterval",
    "TimePrecision",
    "ValidationMethod",
    "ValidationRejection",
    "ValidationResult",
    "classify_candidate",
    "compile_extraction_prompt",
    "context_for_assertion",
    "selector_matches",
    "validate_derivation_graph",
    "validate_extraction",
    "resolve_profile_order",
]
