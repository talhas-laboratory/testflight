"""Immutable provider-independent records for multimodal Content."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ContentRecord(BaseModel):
    """Immutable record base; bytes and provider state live behind adapter ports."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class ContentLifecycle(StrEnum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    SUPERSEDED = "superseded"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class ContentEpistemicStatus(StrEnum):
    REPORTED = "reported"
    OBSERVED = "observed"
    INFERRED = "inferred"
    HYPOTHESIZED = "hypothesized"
    SIMULATED = "simulated"
    UNAVAILABLE = "unavailable"
    UNRESOLVED = "unresolved"


class ContentArtifactStatus(StrEnum):
    AVAILABLE = "available"
    PARTIAL = "partial"
    UNAVAILABLE = "unavailable"


class PatternScope(StrEnum):
    LOCAL_ONLY = "local_only"
    SERIES = "series"
    PROFILE_SAMPLE = "profile_sample"
    CAMPAIGN = "campaign"
    CROSS_PROFILE = "cross_profile"
    GLOBAL_CANDIDATE = "global_candidate"


class InferenceDepth(StrEnum):
    DESCRIPTIVE = "descriptive"
    RELATIONAL = "relational"
    STRATEGIC = "strategic"
    CAUSAL = "causal"


class TransformationDisposition(StrEnum):
    PROPOSE = "propose"
    BRANCH = "branch"
    ASK = "ask"
    HOLD = "hold"
    NO_HIT = "no_hit"


class SourceEnvelope(ContentRecord):
    source_envelope_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    workspace_id: str = Field(min_length=1)
    source_system: str = Field(min_length=1)
    provider_source_id: str | None = None
    source_uri: str | None = None
    content_hashes: tuple[str, ...] = ()
    acquisition_method: str = Field(min_length=1)
    acquisition_receipt_id: str = Field(min_length=1)
    recorded_at: str = Field(min_length=1)
    source_published_at: str | None = None
    privacy_classification: str = Field(min_length=1)
    rights_record_id: str = Field(min_length=1)
    retention_policy: str = Field(min_length=1)
    lifecycle_status: ContentLifecycle = ContentLifecycle.PROPOSED
    derivation_id: str = Field(min_length=1)


class ContentUnit(ContentRecord):
    content_unit_id: str = Field(min_length=1)
    source_envelope_id: str = Field(min_length=1)
    content_kind: str = Field(min_length=1)
    parent_content_unit_ids: tuple[str, ...] = ()
    profile_subject_id: str | None = None
    published_at: str | None = None
    recorded_at: str = Field(min_length=1)
    duration_ms: int | None = Field(default=None, gt=0)
    lifecycle_status: ContentLifecycle = ContentLifecycle.PROPOSED
    epistemic_status: ContentEpistemicStatus = ContentEpistemicStatus.REPORTED
    derivation_id: str = Field(min_length=1)


class MediaTrack(ContentRecord):
    track_id: str = Field(min_length=1)
    content_unit_id: str = Field(min_length=1)
    modality: str = Field(min_length=1)
    status: ContentArtifactStatus = ContentArtifactStatus.AVAILABLE
    time_base: str | None = None
    source_ref: str | None = None
    blob_ref: str | None = None
    language: str | None = None
    limitation: str | None = None
    derivation_id: str = Field(min_length=1)

    @model_validator(mode="after")
    def unavailable_requires_limitation(self) -> "MediaTrack":
        if self.status is ContentArtifactStatus.UNAVAILABLE and not self.limitation:
            raise ValueError("unavailable media tracks require a limitation")
        return self


class ContentSegment(ContentRecord):
    segment_id: str = Field(min_length=1)
    content_unit_id: str = Field(min_length=1)
    start_ms: int | None = Field(default=None, ge=0)
    end_ms: int | None = Field(default=None, gt=0)
    text_start: int | None = Field(default=None, ge=0)
    text_end: int | None = Field(default=None, gt=0)
    spatial_region: tuple[float, float, float, float] | None = None
    roles: tuple[str, ...] = ()
    segmentation_method: str = Field(min_length=1)
    boundary_uncertainty: str | None = None
    derivation_id: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_anchor_shape(self) -> "ContentSegment":
        has_time = self.start_ms is not None or self.end_ms is not None
        if has_time and (
            self.start_ms is None or self.end_ms is None or self.start_ms >= self.end_ms
        ):
            raise ValueError("time segments require start_ms < end_ms")
        has_text = self.text_start is not None or self.text_end is not None
        if has_text and (
            self.text_start is None or self.text_end is None or self.text_start >= self.text_end
        ):
            raise ValueError("text segments require text_start < text_end")
        if not has_time and not has_text and self.spatial_region is None:
            raise ValueError("content segments need time, text, or spatial anchors")
        if self.spatial_region is not None and not all(
            0 <= value <= 1 for value in self.spatial_region
        ):
            raise ValueError("spatial_region values must be normalized between 0 and 1")
        return self


class PerceptualObservation(ContentRecord):
    observation_id: str = Field(min_length=1)
    content_unit_id: str = Field(min_length=1)
    modality: str = Field(min_length=1)
    observation_type: str = Field(min_length=1)
    dimension: str = Field(min_length=1)
    value: Any
    anchor_ids: tuple[str, ...] = Field(min_length=1)
    observer_id: str = Field(min_length=1)
    operator_id: str = Field(min_length=1)
    operator_version: int = Field(ge=1)
    epistemic_status: ContentEpistemicStatus = ContentEpistemicStatus.OBSERVED
    uncertainty: str | None = None
    limitations: tuple[str, ...] = ()
    derivation_id: str = Field(min_length=1)

    @model_validator(mode="after")
    def observed_status_is_not_unavailable(self) -> "PerceptualObservation":
        if self.epistemic_status is ContentEpistemicStatus.UNAVAILABLE and self.value not in (
            None,
            "",
        ):
            raise ValueError("unavailable observations cannot contain an observed value")
        return self


class CrossModalRelation(ContentRecord):
    relation_id: str = Field(min_length=1)
    content_unit_id: str = Field(min_length=1)
    relation_type: str = Field(min_length=1)
    participant_ids: tuple[str, ...] = Field(min_length=2)
    alignment_tolerance_ms: int | None = Field(default=None, ge=0)
    evidence_ids: tuple[str, ...] = Field(min_length=1)
    uncertainty: str | None = None
    derivation_id: str = Field(min_length=1)


class ContentOccurrence(ContentRecord):
    occurrence_id: str = Field(min_length=1)
    content_unit_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    observation_ids: tuple[str, ...] = Field(min_length=1)
    segment_ids: tuple[str, ...] = ()
    epistemic_status: ContentEpistemicStatus = ContentEpistemicStatus.OBSERVED
    derivation_id: str = Field(min_length=1)


class PatternCandidate(ContentRecord):
    pattern_id: str = Field(min_length=1)
    target_scope: PatternScope
    sampled_content_unit_ids: tuple[str, ...] = Field(min_length=1)
    occurrence_ids: tuple[str, ...] = Field(min_length=1)
    counterexample_observation_ids: tuple[str, ...] = ()
    proposition: str = Field(min_length=1)
    candidate_invariants: tuple[str, ...] = ()
    transfer_conditions: tuple[str, ...] = ()
    epistemic_status: ContentEpistemicStatus = ContentEpistemicStatus.HYPOTHESIZED
    disposition: TransformationDisposition = TransformationDisposition.PROPOSE
    derivation_id: str = Field(min_length=1)


class InterpretationAlternative(ContentRecord):
    alternative_id: str = Field(min_length=1)
    interpretation_id: str = Field(min_length=1)
    proposition: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    invalidation_condition: str = Field(min_length=1)
    evidence_ids: tuple[str, ...] = ()
    status: ContentLifecycle = ContentLifecycle.PROPOSED


class InterpretationFrame(ContentRecord):
    frame_id: str = Field(min_length=1)
    version: int = Field(ge=1)
    question: str = Field(min_length=1)
    module_id: str = Field(min_length=1)
    module_version: int = Field(ge=1)
    target_scope: str = Field(min_length=1)
    context_id: str = Field(min_length=1)
    branch_id: str = Field(min_length=1)
    perspective_ids: tuple[str, ...] = ()
    requested_dimensions: tuple[str, ...] = Field(min_length=1)
    permitted_epistemic_statuses: tuple[ContentEpistemicStatus, ...] = (
        ContentEpistemicStatus.OBSERVED,
        ContentEpistemicStatus.REPORTED,
    )
    inference_depth: InferenceDepth = InferenceDepth.DESCRIPTIVE
    uncertainty_policy: str = Field(min_length=1)
    prohibited_conclusions: tuple[str, ...] = ()
    output_schema: str = Field(min_length=1)
    evaluator_refs: tuple[str, ...] = Field(min_length=1)
    authority_grant_id: str | None = None
    derivation_id: str = Field(min_length=1)


class TransformationRecipe(ContentRecord):
    recipe_id: str = Field(min_length=1)
    version: int = Field(ge=1)
    operator_id: str = Field(min_length=1)
    operator_version: int = Field(ge=1)
    accepted_input_types: tuple[str, ...] = Field(min_length=1)
    output_types: tuple[str, ...] = Field(min_length=1)
    procedure: tuple[str, ...] = Field(min_length=1)
    invariants: tuple[str, ...] = Field(min_length=1)
    forbidden_shortcuts: tuple[str, ...] = ()
    hold_conditions: tuple[str, ...] = Field(min_length=1)
    evaluator_refs: tuple[str, ...] = Field(min_length=1)
    cache_identity_fields: tuple[str, ...] = Field(min_length=1)
    disclosure_requirements: tuple[str, ...] = ()
    derivation_id: str = Field(min_length=1)


class ContentInterpretation(ContentRecord):
    interpretation_id: str = Field(min_length=1)
    content_unit_ids: tuple[str, ...] = Field(min_length=1)
    frame_id: str = Field(min_length=1)
    proposition: str = Field(min_length=1)
    category: str = Field(min_length=1)
    supporting_evidence_ids: tuple[str, ...] = ()
    opposing_evidence_ids: tuple[str, ...] = ()
    alternatives: tuple[InterpretationAlternative, ...] = ()
    what_evidence_cannot_establish: tuple[str, ...] = ()
    target_scope: str = Field(min_length=1)
    valid_from: str | None = None
    valid_until: str | None = None
    epistemic_status: ContentEpistemicStatus = ContentEpistemicStatus.INFERRED
    invalidation_conditions: tuple[str, ...] = ()
    authority: str = Field(min_length=1)
    disposition: TransformationDisposition = TransformationDisposition.PROPOSE
    derivation_id: str = Field(min_length=1)


class DerivationReceipt(ContentRecord):
    derivation_id: str = Field(min_length=1)
    operator_id: str = Field(min_length=1)
    operator_version: int = Field(ge=1)
    input_record_ids: tuple[str, ...] = Field(min_length=1)
    configuration: dict[str, Any] = Field(default_factory=dict)
    evaluator_results: dict[str, Any] = Field(default_factory=dict)
    status: TransformationDisposition
    branch_decisions: tuple[str, ...] = ()
    omissions: tuple[str, ...] = ()


class ContentBundle(ContentRecord):
    """Cross-record Content graph with deterministic referential validation."""

    bundle_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    workspace_id: str = Field(min_length=1)
    source_envelopes: tuple[SourceEnvelope, ...] = ()
    content_units: tuple[ContentUnit, ...] = Field(min_length=1)
    tracks: tuple[MediaTrack, ...] = ()
    segments: tuple[ContentSegment, ...] = ()
    observations: tuple[PerceptualObservation, ...] = ()
    relations: tuple[CrossModalRelation, ...] = ()
    occurrences: tuple[ContentOccurrence, ...] = ()
    patterns: tuple[PatternCandidate, ...] = ()
    interpretation_frames: tuple[InterpretationFrame, ...] = ()
    recipes: tuple[TransformationRecipe, ...] = ()
    interpretations: tuple[ContentInterpretation, ...] = ()
    derivations: tuple[DerivationReceipt, ...] = ()

    @model_validator(mode="after")
    def validate_references(self) -> "ContentBundle":
        self._validate_unique_ids()
        units = {item.content_unit_id: item for item in self.content_units}
        sources = {item.source_envelope_id: item for item in self.source_envelopes}
        if any(
            item.project_id != self.project_id or item.workspace_id != self.workspace_id
            for item in self.source_envelopes
        ):
            raise ValueError("source envelope scope differs from ContentBundle")
        if any(item.source_envelope_id not in sources for item in self.content_units):
            raise ValueError("content unit references an unknown source envelope")
        track_map = {item.track_id: item for item in self.tracks}
        segment_map = {item.segment_id: item for item in self.segments}
        observation_map = {item.observation_id: item for item in self.observations}
        occurrence_map = {item.occurrence_id: item for item in self.occurrences}
        for track in self.tracks:
            self._require_unit(track.content_unit_id, units, track.track_id)
        for unit in self.content_units:
            if any(parent not in units for parent in unit.parent_content_unit_ids):
                raise ValueError(f"content unit has an unknown parent: {unit.content_unit_id}")
        for segment in self.segments:
            unit = self._require_unit(segment.content_unit_id, units, segment.segment_id)
            if (
                segment.end_ms is not None
                and unit.duration_ms is not None
                and segment.end_ms > unit.duration_ms
            ):
                raise ValueError(f"segment exceeds content duration: {segment.segment_id}")
        for observation in self.observations:
            self._require_unit(observation.content_unit_id, units, observation.observation_id)
            if any(
                anchor not in track_map and anchor not in segment_map
                for anchor in observation.anchor_ids
            ):
                raise ValueError(f"observation has an unknown anchor: {observation.observation_id}")
            anchors = (*observation.anchor_ids,)
            for anchor in anchors:
                anchor_record = track_map.get(anchor) or segment_map.get(anchor)
                if anchor_record and anchor_record.content_unit_id != observation.content_unit_id:
                    raise ValueError(
                        f"observation crosses content-unit boundaries: {observation.observation_id}"
                    )
        for relation in self.relations:
            self._require_unit(relation.content_unit_id, units, relation.relation_id)
            participants = [
                observation_map.get(item) or segment_map.get(item)
                for item in relation.participant_ids
            ]
            if any(item is None for item in participants):
                raise ValueError(f"relation has an unknown participant: {relation.relation_id}")
            if any(
                item.content_unit_id != relation.content_unit_id
                for item in participants
                if item is not None
            ):
                raise ValueError(
                    f"relation crosses content-unit boundaries: {relation.relation_id}"
                )
            evidence = [
                observation_map.get(item) or segment_map.get(item) for item in relation.evidence_ids
            ]
            if any(item is None for item in evidence):
                raise ValueError(f"relation has an unknown evidence item: {relation.relation_id}")
            if any(
                item.content_unit_id != relation.content_unit_id
                for item in evidence
                if item is not None
            ):
                raise ValueError(
                    f"relation evidence crosses content-unit boundaries: {relation.relation_id}"
                )
        for occurrence in self.occurrences:
            self._require_unit(occurrence.content_unit_id, units, occurrence.occurrence_id)
            if any(item not in observation_map for item in occurrence.observation_ids):
                raise ValueError(f"occurrence has unknown observations: {occurrence.occurrence_id}")
            if any(
                observation_map[item].content_unit_id != occurrence.content_unit_id
                for item in occurrence.observation_ids
            ):
                raise ValueError(
                    f"occurrence crosses content-unit boundaries: {occurrence.occurrence_id}"
                )
            if any(item not in segment_map for item in occurrence.segment_ids):
                raise ValueError(f"occurrence has unknown segments: {occurrence.occurrence_id}")
        for pattern in self.patterns:
            if any(item not in units for item in pattern.sampled_content_unit_ids):
                raise ValueError(f"pattern has unknown sampled content: {pattern.pattern_id}")
            if any(item not in occurrence_map for item in pattern.occurrence_ids):
                raise ValueError(f"pattern has unknown occurrences: {pattern.pattern_id}")
            occurrence_units = {
                occurrence_map[item].content_unit_id for item in pattern.occurrence_ids
            }
            if pattern.target_scope is not PatternScope.LOCAL_ONLY and len(occurrence_units) < 2:
                raise ValueError(
                    f"non-local pattern needs independent content units: {pattern.pattern_id}"
                )
            if any(item not in observation_map for item in pattern.counterexample_observation_ids):
                raise ValueError(f"pattern has unknown counterexamples: {pattern.pattern_id}")
            if any(
                observation_map[item].content_unit_id not in pattern.sampled_content_unit_ids
                for item in pattern.counterexample_observation_ids
            ):
                raise ValueError(
                    f"pattern counterexample is outside sampled content: {pattern.pattern_id}"
                )
        frame_ids = {item.frame_id for item in self.interpretation_frames}
        pattern_id_set = pattern_ids(self.patterns)
        for interpretation in self.interpretations:
            if any(item not in units for item in interpretation.content_unit_ids):
                raise ValueError(
                    f"interpretation has unknown content: {interpretation.interpretation_id}"
                )
            if interpretation.frame_id not in frame_ids:
                raise ValueError(
                    f"interpretation has an unknown frame: {interpretation.interpretation_id}"
                )
            if any(
                alternative.interpretation_id != interpretation.interpretation_id
                for alternative in interpretation.alternatives
            ):
                raise ValueError(
                    "interpretation alternative has the wrong parent: "
                    f"{interpretation.interpretation_id}"
                )
            if any(
                item not in observation_map
                and item not in occurrence_map
                and item not in pattern_id_set
                for item in (
                    *interpretation.supporting_evidence_ids,
                    *interpretation.opposing_evidence_ids,
                )
            ):
                raise ValueError(
                    f"interpretation has unknown evidence: {interpretation.interpretation_id}"
                )
        return self

    def _validate_unique_ids(self) -> None:
        groups = {
            "source envelopes": [item.source_envelope_id for item in self.source_envelopes],
            "content units": [item.content_unit_id for item in self.content_units],
            "tracks": [item.track_id for item in self.tracks],
            "segments": [item.segment_id for item in self.segments],
            "observations": [item.observation_id for item in self.observations],
            "relations": [item.relation_id for item in self.relations],
            "occurrences": [item.occurrence_id for item in self.occurrences],
            "patterns": [item.pattern_id for item in self.patterns],
            "interpretation frames": [item.frame_id for item in self.interpretation_frames],
            "recipes": [item.recipe_id for item in self.recipes],
            "interpretations": [item.interpretation_id for item in self.interpretations],
            "derivations": [item.derivation_id for item in self.derivations],
        }
        for label, values in groups.items():
            if len(values) != len(set(values)):
                raise ValueError(f"{label} contain duplicate IDs")

    @staticmethod
    def _require_unit(unit_id: str, units: dict[str, ContentUnit], record_id: str) -> ContentUnit:
        unit = units.get(unit_id)
        if unit is None:
            raise ValueError(f"{record_id} references unknown content unit: {unit_id}")
        return unit


def pattern_ids(patterns: tuple[PatternCandidate, ...]) -> set[str]:
    return {item.pattern_id for item in patterns}


__all__ = [
    "ContentArtifactStatus",
    "ContentBundle",
    "ContentEpistemicStatus",
    "ContentInterpretation",
    "ContentLifecycle",
    "ContentOccurrence",
    "ContentRecord",
    "ContentSegment",
    "ContentUnit",
    "CrossModalRelation",
    "DerivationReceipt",
    "InferenceDepth",
    "InterpretationAlternative",
    "InterpretationFrame",
    "MediaTrack",
    "PatternCandidate",
    "PatternScope",
    "PerceptualObservation",
    "SourceEnvelope",
    "TransformationDisposition",
    "TransformationRecipe",
]
