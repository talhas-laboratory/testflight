"""Canonical, provider-neutral Moodboard and Creative Field records."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CreativeRecord(BaseModel):
    """Immutable record envelope shared by creative-domain objects."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class LifecycleStatus(StrEnum):
    DRAFT = "draft"
    PROPOSED = "proposed"
    REVIEW_NEEDED = "review_needed"
    ACCEPTED = "accepted"
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    REJECTED = "rejected"
    STALE = "stale"
    DEFERRED = "deferred"
    ARCHIVED = "archived"


class ArtifactStatus(StrEnum):
    SUCCESS = "success"
    PARTIAL = "partial"
    HELD = "held"
    UNAVAILABLE = "unavailable"
    FAILED = "failed"


class ReviewAction(StrEnum):
    ACCEPT = "accept"
    MODIFY = "modify"
    REJECT = "reject"
    SPLIT = "split"
    MERGE = "merge"
    DEFER = "defer"


class TransferPolarity(StrEnum):
    CARRY = "carry"
    AVOID = "avoid"
    CONTEXTUAL = "contextual"


class BindingMode(StrEnum):
    CANONICAL = "canonical"
    ADAPTIVE = "adaptive"
    LOCAL = "local"


class CreativeProject(CreativeRecord):
    project_id: str = Field(min_length=1)
    workspace_id: str = Field(min_length=1)
    context_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    scope_kind: str = "project"
    active_board_ids: tuple[str, ...] = ()
    active_field_binding_id: str | None = None
    status: LifecycleStatus = LifecycleStatus.DRAFT
    privacy_policy_id: str = Field(min_length=1)
    derivation_id: str | None = None


class Moodboard(CreativeRecord):
    moodboard_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    active_revision_id: str | None = None
    lifecycle_status: LifecycleStatus = LifecycleStatus.DRAFT
    privacy_classification: str = Field(min_length=1)
    derivation_id: str | None = None


class SourceLicenseRecord(CreativeRecord):
    license_record_id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    owner: str | None = None
    permitted_use: tuple[str, ...] = ()
    disclosure_allowed: bool = False
    generation_allowed: bool = False
    retention_policy: str = Field(min_length=1)
    attribution: str | None = None
    limitations: tuple[str, ...] = ()


class ReferenceAsset(CreativeRecord):
    asset_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    media_type: str = Field(min_length=1)
    label: str = Field(min_length=1)
    content_hash: str = Field(min_length=1)
    source_uri: str = Field(min_length=1)
    license_record_id: str | None = None
    recorded_at: str = Field(min_length=1)
    lifecycle_status: LifecycleStatus = LifecycleStatus.DRAFT
    derivation_id: str | None = None


class Placement(CreativeRecord):
    placement_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    x: float
    y: float
    width: float = Field(gt=0)
    height: float = Field(gt=0)
    z_index: int = 0
    cluster_id: str | None = None


class ReferenceCluster(CreativeRecord):
    cluster_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    asset_ids: tuple[str, ...] = Field(min_length=1)
    status: LifecycleStatus = LifecycleStatus.DRAFT
    derivation_id: str | None = None

    @model_validator(mode="after")
    def unique_assets(self) -> "ReferenceCluster":
        if len(set(self.asset_ids)) != len(self.asset_ids):
            raise ValueError("ReferenceCluster asset_ids must be unique")
        return self


class UserAnnotation(CreativeRecord):
    annotation_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    target_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    desired_transfer: str | None = None
    anti_association: str | None = None
    actor_id: str = Field(min_length=1)
    created_at: str = Field(min_length=1)


class BoardRevision(CreativeRecord):
    board_revision_id: str = Field(min_length=1)
    moodboard_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    revision: int = Field(ge=1)
    reference_asset_ids: tuple[str, ...] = ()
    placements: tuple[Placement, ...] = ()
    cluster_ids: tuple[str, ...] = ()
    annotation_ids: tuple[str, ...] = ()
    created_at: str = Field(min_length=1)
    created_by: str = Field(min_length=1)
    source_ids: tuple[str, ...] = ()
    omissions: tuple[str, ...] = ()
    derivation_id: str | None = None

    @model_validator(mode="after")
    def validate_references_and_placements(self) -> "BoardRevision":
        if len(set(self.reference_asset_ids)) != len(self.reference_asset_ids):
            raise ValueError("BoardRevision reference_asset_ids must be unique")
        placement_ids = [item.placement_id for item in self.placements]
        if len(set(placement_ids)) != len(placement_ids):
            raise ValueError("BoardRevision placement IDs must be unique")
        unknown = {item.asset_id for item in self.placements} - set(self.reference_asset_ids)
        if unknown:
            raise ValueError(f"placements reference assets outside the revision: {sorted(unknown)}")
        return self


class ObservedFeature(CreativeRecord):
    feature_id: str = Field(min_length=1)
    observation_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    reference_asset_id: str = Field(min_length=1)
    dimension_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    value: Any
    bounded_anchors: tuple[str, ...] = Field(min_length=1)
    observation_status: LifecycleStatus = LifecycleStatus.PROPOSED
    uncertainty: str | None = None
    source_ids: tuple[str, ...] = ()
    derivation_id: str = Field(min_length=1)


class InterpretationAlternative(CreativeRecord):
    alternative_id: str = Field(min_length=1)
    interpretation_id: str = Field(min_length=1)
    proposition: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    status: LifecycleStatus = LifecycleStatus.PROPOSED
    evidence_refs: tuple[str, ...] = ()


class ReferenceContribution(CreativeRecord):
    contribution_id: str = Field(min_length=1)
    interpretation_id: str = Field(min_length=1)
    reference_asset_id: str = Field(min_length=1)
    dimension_id: str = Field(min_length=1)
    role: str = Field(min_length=1)
    transfer_instruction: str = Field(min_length=1)
    anti_transfer_instruction: str = Field(min_length=1)
    polarity: TransferPolarity = TransferPolarity.CONTEXTUAL
    weight: float = Field(default=0.5, ge=0.0, le=1.0)
    evidence_refs: tuple[str, ...] = ()
    derivation_id: str = Field(min_length=1)
    status: LifecycleStatus = LifecycleStatus.PROPOSED


class ReferenceInterpretation(CreativeRecord):
    interpretation_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    reference_asset_id: str = Field(min_length=1)
    observation_ids: tuple[str, ...] = ()
    proposed_role: str = Field(min_length=1)
    dimension_contributions: tuple[ReferenceContribution, ...] = ()
    carry_forward: tuple[str, ...] = ()
    anti_transfer: tuple[str, ...] = ()
    alternatives: tuple[InterpretationAlternative, ...] = ()
    questions: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    authority: str = Field(min_length=1)
    derivation_id: str = Field(min_length=1)
    status: LifecycleStatus = LifecycleStatus.PROPOSED


class ReviewDecision(CreativeRecord):
    review_id: str = Field(min_length=1)
    target_id: str = Field(min_length=1)
    action: ReviewAction
    actor_id: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    created_at: str = Field(min_length=1)
    replacement_ids: tuple[str, ...] = ()
    authority_grant_id: str | None = None
    derivation_id: str | None = None


class FieldDimension(CreativeRecord):
    dimension_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    definition: str = Field(min_length=1)
    schema_version: int = Field(default=1, ge=1)
    status: LifecycleStatus = LifecycleStatus.ACCEPTED
    examples: tuple[str, ...] = ()


class DimensionState(CreativeRecord):
    dimension_id: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    values: dict[str, Any] = Field(default_factory=dict)
    source_contribution_ids: tuple[str, ...] = ()
    status: LifecycleStatus = LifecycleStatus.PROPOSED


class Principle(CreativeRecord):
    principle_id: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    conditions: tuple[str, ...] = ()
    dimension_ids: tuple[str, ...] = Field(min_length=1)
    source_contribution_ids: tuple[str, ...] = ()


class Tension(CreativeRecord):
    tension_id: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    poles: tuple[str, ...] = Field(min_length=2)
    source_contribution_ids: tuple[str, ...] = ()


class Exclusion(CreativeRecord):
    exclusion_id: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    category: str = Field(min_length=1)
    source_contribution_ids: tuple[str, ...] = ()


class FieldConflict(CreativeRecord):
    conflict_id: str = Field(min_length=1)
    record_ids: tuple[str, ...] = Field(min_length=2)
    description: str = Field(min_length=1)
    resolution_status: LifecycleStatus = LifecycleStatus.REVIEW_NEEDED


class MissingDimension(CreativeRecord):
    dimension_id: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    question: str | None = None


class CreativeFieldProposal(CreativeRecord):
    proposal_id: str = Field(min_length=1)
    field_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    source_contribution_ids: tuple[str, ...] = ()
    principles: tuple[Principle, ...] = ()
    tensions: tuple[Tension, ...] = ()
    exclusions: tuple[Exclusion, ...] = ()
    dimension_states: tuple[DimensionState, ...] = ()
    conflicts: tuple[FieldConflict, ...] = ()
    missing_dimensions: tuple[MissingDimension, ...] = ()
    semantic_diff: dict[str, Any] = Field(default_factory=dict)
    evidence_coverage: dict[str, Any] = Field(default_factory=dict)
    derivation_id: str = Field(min_length=1)
    status: LifecycleStatus = LifecycleStatus.PROPOSED


class CreativeFieldRun(CreativeRecord):
    """Canonical replay record for one proposal-producing analysis run."""

    run_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    moodboard_id: str = Field(min_length=1)
    board_revision_id: str | None = None
    status: ArtifactStatus
    proposal_id: str | None = None
    stage_results: tuple[dict[str, Any], ...] = ()
    errors: tuple[str, ...] = ()
    hold_reason: str | None = None
    started_at: str = Field(min_length=1)
    finished_at: str = Field(min_length=1)
    derivation_id: str = Field(min_length=1)


class CreativeFieldVersion(CreativeRecord):
    field_id: str = Field(min_length=1)
    version_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    parent_version_ids: tuple[str, ...] = ()
    principles: tuple[Principle, ...] = ()
    tensions: tuple[Tension, ...] = ()
    exclusions: tuple[Exclusion, ...] = ()
    dimension_states: tuple[DimensionState, ...] = ()
    conflicts: tuple[FieldConflict, ...] = ()
    missing_dimensions: tuple[MissingDimension, ...] = ()
    source_contribution_ids: tuple[str, ...] = ()
    review_record_ids: tuple[str, ...] = ()
    dependency_manifest: dict[str, Any] = Field(default_factory=dict)
    lifecycle_status: LifecycleStatus = LifecycleStatus.ACCEPTED
    created_at: str = Field(min_length=1)
    derivation_id: str | None = None

    @model_validator(mode="after")
    def immutable_version_has_identity(self) -> "CreativeFieldVersion":
        if self.version_id == self.field_id:
            raise ValueError("CreativeFieldVersion version_id must differ from field_id")
        if self.version_id in self.parent_version_ids:
            raise ValueError("CreativeFieldVersion cannot parent itself")
        return self


class ProjectBinding(CreativeRecord):
    binding_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    workspace_id: str = Field(min_length=1)
    context_id: str = Field(min_length=1)
    target_entity_ids: tuple[str, ...] = Field(min_length=1)
    branch_id: str = Field(min_length=1)
    privacy_policy_id: str = Field(min_length=1)
    authority_grant_id: str = Field(min_length=1)
    status: LifecycleStatus = LifecycleStatus.ACTIVE


class FieldBinding(CreativeRecord):
    binding_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    field_version_id: str = Field(min_length=1)
    target_entity_ids: tuple[str, ...] = Field(min_length=1)
    context_id: str = Field(min_length=1)
    artifact_type_selectors: tuple[str, ...] = ()
    channel_selectors: tuple[str, ...] = ()
    valid_from: str | None = None
    valid_until: str | None = None
    precedence: int = Field(default=0, ge=0)
    mode: BindingMode = BindingMode.ADAPTIVE
    authority_grant_id: str = Field(min_length=1)
    status: LifecycleStatus = LifecycleStatus.ACTIVE


class LocalOverride(CreativeRecord):
    override_id: str = Field(min_length=1)
    request_id: str = Field(min_length=1)
    changes: dict[str, Any] = Field(min_length=1)
    reason: str = Field(min_length=1)
    expires_at: str | None = None
    derivation_id: str | None = None


class CreativeRequest(CreativeRecord):
    request_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    task_type: str = Field(min_length=1)
    artifact_type: str = Field(min_length=1)
    modality: str = Field(min_length=1)
    target: str = Field(min_length=1)
    audience: str | None = None
    local_override_id: str | None = None
    permission_context: dict[str, Any] = Field(default_factory=dict)
    expected_evaluation: dict[str, Any] = Field(default_factory=dict)


class ResolvedCreativeRequest(CreativeRecord):
    request_id: str = Field(min_length=1)
    project_binding_id: str = Field(min_length=1)
    field_binding_id: str = Field(min_length=1)
    field_version_id: str = Field(min_length=1)
    world_view_request_id: str = Field(min_length=1)
    lens: str = Field(min_length=1)
    target_capability_manifest_id: str = Field(min_length=1)
    local_override_id: str | None = None
    ambiguity_disposition: str = Field(min_length=1)
    permission_context: dict[str, Any] = Field(default_factory=dict)
    derivation_id: str = Field(min_length=1)


class FieldProjection(CreativeRecord):
    projection_id: str = Field(min_length=1)
    field_version_id: str = Field(min_length=1)
    request_id: str = Field(min_length=1)
    lens: str = Field(min_length=1)
    modality: str = Field(min_length=1)
    principles: tuple[str, ...] = ()
    tensions: tuple[str, ...] = ()
    exclusions: tuple[str, ...] = ()
    dimension_mappings: dict[str, Any] = Field(default_factory=dict)
    grounding_reference_ids: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    omissions: tuple[str, ...] = ()
    sufficiency: str = Field(min_length=1)
    expires_at: str | None = None
    derivation_id: str = Field(min_length=1)
    status: ArtifactStatus = ArtifactStatus.SUCCESS


class CreativeContextPacket(CreativeRecord):
    packet_id: str = Field(min_length=1)
    request_id: str = Field(min_length=1)
    resolved_world_view_id: str = Field(min_length=1)
    field_projection_id: str = Field(min_length=1)
    visual_language_revision_ids: tuple[str, ...] = ()
    selected_record_ids: tuple[str, ...] = ()
    conflicts: tuple[str, ...] = ()
    omissions: tuple[str, ...] = ()
    citations: tuple[str, ...] = ()
    disclosure_manifest_id: str = Field(min_length=1)
    derivation_id: str = Field(min_length=1)
    status: ArtifactStatus = ArtifactStatus.SUCCESS


class TargetCapabilityManifest(CreativeRecord):
    target_id: str = Field(min_length=1)
    adapter_version: str = Field(min_length=1)
    accepted_modalities: tuple[str, ...] = Field(min_length=1)
    controls: dict[str, Any] = Field(default_factory=dict)
    input_limits: dict[str, Any] = Field(default_factory=dict)
    privacy_policy_id: str = Field(min_length=1)


class GenerationPacket(CreativeRecord):
    packet_id: str = Field(min_length=1)
    projection_id: str = Field(min_length=1)
    target_capability_manifest_id: str = Field(min_length=1)
    controls_sent: dict[str, Any] = Field(default_factory=dict)
    grounding_assets_sent: tuple[str, ...] = ()
    capability_limitations: tuple[str, ...] = ()
    disclosure_manifest_id: str = Field(min_length=1)
    expected_output: dict[str, Any] = Field(default_factory=dict)
    adapter_version: str = Field(min_length=1)
    derivation_id: str = Field(min_length=1)


class InvocationReceipt(CreativeRecord):
    """Immutable record of a target invocation, including disclosure and capability limits."""

    invocation_id: str = Field(min_length=1)
    packet_id: str = Field(min_length=1)
    target_id: str = Field(min_length=1)
    adapter_version: str = Field(min_length=1)
    disclosure_manifest_id: str = Field(min_length=1)
    grounding_assets_sent: tuple[str, ...] = ()
    capability_limitations: tuple[str, ...] = ()
    output_id: str | None = None
    authority_grant_id: str = Field(min_length=1)
    status: ArtifactStatus
    errors: tuple[str, ...] = ()
    started_at: str = Field(min_length=1)
    finished_at: str = Field(min_length=1)
    derivation_id: str = Field(min_length=1)


class CreativeOutput(CreativeRecord):
    """Metadata for generated content whose bytes live in content-addressed storage."""

    output_id: str = Field(min_length=1)
    invocation_id: str = Field(min_length=1)
    packet_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    request_id: str = Field(min_length=1)
    media_type: str = Field(min_length=1)
    content_hash: str = Field(min_length=1)
    source_uri: str = Field(min_length=1)
    content_size: int = Field(ge=0)
    adapter_version: str = Field(min_length=1)
    status: ArtifactStatus
    derivation_id: str = Field(min_length=1)


class CreativeEvaluation(CreativeRecord):
    evaluation_id: str = Field(min_length=1)
    output_id: str = Field(min_length=1)
    request_id: str = Field(min_length=1)
    field_version_id: str = Field(min_length=1)
    projection_id: str = Field(min_length=1)
    field_fidelity: dict[str, Any] = Field(default_factory=dict)
    exclusion_findings: tuple[str, ...] = ()
    task_fitness: dict[str, Any] = Field(default_factory=dict)
    execution_quality: dict[str, Any] = Field(default_factory=dict)
    target_limitations: tuple[str, ...] = ()
    disagreements: tuple[str, ...] = ()
    feedback_proposal_ids: tuple[str, ...] = ()
    receipt: dict[str, Any] = Field(default_factory=dict)
    derivation_id: str = Field(min_length=1)
    status: ArtifactStatus = ArtifactStatus.SUCCESS


class FeedbackRecord(CreativeRecord):
    feedback_id: str = Field(min_length=1)
    target_id: str = Field(min_length=1)
    category: str = Field(min_length=1)
    instruction: str = Field(min_length=1)
    actor_id: str = Field(min_length=1)
    created_at: str = Field(min_length=1)
    proposed_change: dict[str, Any] = Field(default_factory=dict)
    derivation_id: str | None = None


__all__ = [
    "ArtifactStatus",
    "BindingMode",
    "BoardRevision",
    "CreativeContextPacket",
    "CreativeEvaluation",
    "CreativeOutput",
    "CreativeFieldProposal",
    "CreativeFieldRun",
    "CreativeFieldVersion",
    "CreativeProject",
    "CreativeRecord",
    "CreativeRequest",
    "DimensionState",
    "Exclusion",
    "FeedbackRecord",
    "FieldBinding",
    "FieldConflict",
    "FieldDimension",
    "FieldProjection",
    "GenerationPacket",
    "InterpretationAlternative",
    "InvocationReceipt",
    "LifecycleStatus",
    "LocalOverride",
    "MissingDimension",
    "Moodboard",
    "ObservedFeature",
    "Placement",
    "Principle",
    "ProjectBinding",
    "ReferenceAsset",
    "ReferenceCluster",
    "ReferenceContribution",
    "ReferenceInterpretation",
    "ResolvedCreativeRequest",
    "ReviewAction",
    "ReviewDecision",
    "SourceLicenseRecord",
    "TargetCapabilityManifest",
    "Tension",
    "TransferPolarity",
    "UserAnnotation",
]
