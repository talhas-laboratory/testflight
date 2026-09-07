"""Hypotheses, experiments, outcomes, and reviewed learning updates."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .time import TemporalInterval


class HypothesisStatus(StrEnum):
    PROPOSED = "proposed"
    TESTABLE = "testable"
    SUPPORTED = "supported"
    WEAKENED = "weakened"
    REJECTED = "rejected"
    HELD = "held"


class ExperimentStatus(StrEnum):
    DRAFT = "draft"
    APPROVED = "approved"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class OutcomeStatus(StrEnum):
    OBSERVED = "observed"
    INCONCLUSIVE = "inconclusive"
    INVALIDATED = "invalidated"


class LearningDisposition(StrEnum):
    STRENGTHENS = "strengthens"
    WEAKENS = "weakens"
    INCONCLUSIVE = "inconclusive"
    REQUIRES_REVIEW = "requires_review"


class ReviewStatus(StrEnum):
    PENDING = "pending_review"
    REVIEWED = "reviewed"
    REJECTED = "rejected"


class HypothesisRecord(BaseModel):
    """A falsifiable proposal, never a promoted fact or observed outcome."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    hypothesis_id: str = Field(min_length=1)
    branch_id: str = Field(min_length=1)
    context_id: str = Field(min_length=1)
    input_ids: tuple[str, ...] = Field(min_length=1)
    proposition: str = Field(min_length=1)
    mechanism_description: str = Field(min_length=1)
    alternative_hypothesis_ids: tuple[str, ...] = ()
    input_evidence_link_ids: tuple[str, ...] = ()
    supporting_evidence_link_ids: tuple[str, ...] = ()
    opposing_evidence_link_ids: tuple[str, ...] = ()
    assumption_ids: tuple[str, ...] = ()
    confidence: float | None = Field(default=None, ge=0, le=1)
    confidence_calibration_policy_id: str | None = None
    falsification_conditions: tuple[str, ...] = Field(min_length=1)
    status: HypothesisStatus = HypothesisStatus.PROPOSED
    derivation_id: str | None = None

    @model_validator(mode="after")
    def preserve_uncertainty(self) -> "HypothesisRecord":
        if self.hypothesis_id in self.alternative_hypothesis_ids:
            raise ValueError("a hypothesis cannot be its own alternative")
        if set(self.supporting_evidence_link_ids) & set(self.opposing_evidence_link_ids):
            raise ValueError("one evidence link cannot both support and oppose a hypothesis")
        if self.confidence is not None and not self.confidence_calibration_policy_id:
            raise ValueError("confidence requires confidence_calibration_policy_id")
        return self


class MetricThreshold(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    metric_id: str = Field(min_length=1)
    comparator: str = Field(
        pattern=r"^(greater_than|greater_than_or_equal|less_than|less_than_or_equal)$"
    )
    value: float
    unit_id: str = Field(min_length=1)


class ExperimentPlan(BaseModel):
    """A proposed test protocol, explicitly distinct from its observed result."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    experiment_id: str = Field(min_length=1)
    hypothesis_ids: tuple[str, ...] = Field(min_length=1)
    branch_id: str = Field(min_length=1)
    context_id: str = Field(min_length=1)
    intervention: str = Field(min_length=1)
    comparison_or_control: str = Field(min_length=1)
    population_selector: str = Field(min_length=1)
    assignment_method: str = Field(min_length=1)
    metric_ids: tuple[str, ...] = Field(min_length=1)
    success_thresholds: tuple[MetricThreshold, ...] = Field(min_length=1)
    guardrail_metric_ids: tuple[str, ...] = ()
    time_window: TemporalInterval
    sample_requirements: str = Field(min_length=1)
    risk_and_ethics_constraints: tuple[str, ...] = Field(min_length=1)
    status: ExperimentStatus = ExperimentStatus.DRAFT
    authority_grant_id: str | None = None
    derivation_id: str | None = None

    @model_validator(mode="after")
    def require_authority_for_execution(self) -> "ExperimentPlan":
        if (
            self.status
            in {
                ExperimentStatus.APPROVED,
                ExperimentStatus.RUNNING,
                ExperimentStatus.COMPLETED,
            }
            and not self.authority_grant_id
        ):
            raise ValueError(
                "approved, running, or completed experiment requires authority_grant_id"
            )
        if set(threshold.metric_id for threshold in self.success_thresholds) - set(self.metric_ids):
            raise ValueError("success threshold metric_id must appear in metric_ids")
        return self


class ObservedOutcome(BaseModel):
    """A measured result with method and scope; never a simulated or expected result."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    outcome_id: str = Field(min_length=1)
    experiment_id: str = Field(min_length=1)
    context_id: str = Field(min_length=1)
    metric_values: dict[str, float] = Field(min_length=1)
    measurement_method_id: str = Field(min_length=1)
    population_description: str = Field(min_length=1)
    time_window: TemporalInterval
    evidence_link_ids: tuple[str, ...] = Field(min_length=1)
    status: OutcomeStatus
    limitations: tuple[str, ...] = Field(min_length=1)
    derivation_id: str | None = None


class LearningUpdate(BaseModel):
    """A reviewed interpretation of an outcome, not an automatic strategy mutation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    learning_id: str = Field(min_length=1)
    hypothesis_id: str = Field(min_length=1)
    outcome_ids: tuple[str, ...] = Field(min_length=1)
    context_id: str = Field(min_length=1)
    disposition: LearningDisposition
    rationale: str = Field(min_length=1)
    affected_record_ids: tuple[str, ...] = ()
    review_required: bool = True
    review_status: ReviewStatus = ReviewStatus.PENDING
    reviewed_by: str | None = None
    reviewed_at: str | None = None
    authority_grant_id: str | None = None
    derivation_id: str | None = None

    @model_validator(mode="after")
    def forbid_automatic_acceptance(self) -> "LearningUpdate":
        if not self.review_required and not self.authority_grant_id:
            raise ValueError("an unreviewed learning update requires authority_grant_id")
        return self.validate_review()

    def validate_review(self) -> "LearningUpdate":
        if self.review_status == ReviewStatus.REVIEWED and (
            not self.reviewed_by or not self.reviewed_at
        ):
            raise ValueError("reviewed learning update requires reviewed_by and reviewed_at")
        return self


__all__ = [
    "ExperimentPlan",
    "ExperimentStatus",
    "HypothesisRecord",
    "HypothesisStatus",
    "LearningDisposition",
    "LearningUpdate",
    "MetricThreshold",
    "ObservedOutcome",
    "OutcomeStatus",
    "ReviewStatus",
]
