from datetime import UTC, datetime

import pytest
from testflight_semantic import (
    BranchDelta,
    BranchDeltaKind,
    BranchKind,
    BranchStatus,
    EvidenceLink,
    EvidenceRole,
    ExperimentPlan,
    ExperimentStatus,
    HypothesisRecord,
    HypothesisStatus,
    LearningDisposition,
    LearningUpdate,
    MergeAssessment,
    MetricThreshold,
    ObservedOutcome,
    OutcomeStatus,
    PerspectiveProfile,
    RelationshipFrame,
    RoleBinding,
    StateSnapshot,
    StateStatus,
    StateValue,
    WorldBranch,
    WorldViewRequest,
    WorldViewStatus,
    compile_world_view,
    resolve_branch_records,
)


def test_state_and_evidence_links_keep_condition_claim_and_conflict_separate() -> None:
    state = StateSnapshot(
        state_id="state:onboarding-completion:de:new-runners",
        subject_ids=("offering:nike:app",),
        state_type_id="world://ontology/brand/state/OnboardingCompletion",
        context_id="world://context/nike-app-de-new-runners",
        values=(
            StateValue(
                key="completion_rate",
                value=0.42,
                unit_id="unit:ratio",
                measurement_method_id="method:product-analytics",
            ),
        ),
        source_assertion_ids=("assertion:measurement:completion",),
        evidence_link_ids=("evidence-link:completion-support",),
        status=StateStatus.SUPPORTED,
        derivation_id="derivation:state:completion",
    )
    support = EvidenceLink(
        link_id="evidence-link:completion-support",
        evidence_id="evidence:analytics-export",
        target_id=state.state_id,
        role=EvidenceRole.SUPPORTS,
        context_id=state.context_id,
    )
    qualification = EvidenceLink(
        link_id="evidence-link:completion-qualification",
        evidence_id="evidence:analytics-method-note",
        target_id=state.state_id,
        role=EvidenceRole.QUALIFIES,
        context_id=state.context_id,
    )

    assert state.state_id != state.source_assertion_ids[0]
    assert {support.role, qualification.role} == {
        EvidenceRole.SUPPORTS,
        EvidenceRole.QUALIFIES,
    }
    with pytest.raises(ValueError, match="unit_id"):
        StateValue(key="completion_rate", value=0.42)


def test_branch_resolution_is_an_overlay_and_merge_assessment_is_not_a_mutation() -> None:
    main = WorldBranch(
        branch_id="branch:main",
        workspace_id="world://workspace/brand/nike",
        branch_kind=BranchKind.INTERPRETATION,
        label="Accepted working world",
        created_by="system",
        created_at=datetime(2026, 8, 31, tzinfo=UTC).isoformat(),
        status=BranchStatus.ACTIVE,
    )
    confidence = WorldBranch(
        branch_id="branch:confidence-positioning",
        workspace_id=main.workspace_id,
        parent_branch_id=main.branch_id,
        branch_kind=BranchKind.SCENARIO,
        label="Confidence-first positioning scenario",
        assumption_ids=("assumption:new-runners-value-reassurance",),
        created_by="strategy-team",
        created_at=datetime(2026, 8, 31, tzinfo=UTC).isoformat(),
        status=BranchStatus.ACTIVE,
    )
    deltas = (
        BranchDelta(
            delta_id="delta:exclude-performance",
            branch_id=confidence.branch_id,
            kind=BranchDeltaKind.EXCLUDE,
            target_record_id="positioning:performance-first",
            rationale="Scenario tests reassurance rather than performance framing.",
        ),
        BranchDelta(
            delta_id="delta:add-confidence",
            branch_id=confidence.branch_id,
            kind=BranchDeltaKind.ADD,
            target_record_id="positioning:confidence-first",
            rationale="Scenario-specific selected positioning.",
        ),
    )

    resolved = resolve_branch_records(
        branch_id=confidence.branch_id,
        branches=(main, confidence),
        deltas=deltas,
        base_record_ids=("positioning:performance-first", "product:nike-app"),
    )

    assert resolved == ("product:nike-app", "positioning:confidence-first")
    assessment = MergeAssessment(
        assessment_id="merge-assessment:confidence-to-main",
        source_branch_id=confidence.branch_id,
        target_branch_id=main.branch_id,
        accepted_delta_ids=("delta:add-confidence",),
        unresolved_conflict_ids=("conflict:positioning-evidence",),
    )
    assert assessment.target_branch_id == main.branch_id
    assert main.status is BranchStatus.ACTIVE


def test_perspective_and_relationship_frame_cross_modules_without_flattening_roles() -> None:
    perspective = PerspectiveProfile(
        perspective_id="perspective:customer:new-runner",
        holder_id="audience:nike:first-time-runners",
        perspective_type_id="world://ontology/brand/perspective/Customer",
        context_id="world://context/nike-app-de-new-runners",
        goals=("begin a running routine without intimidation",),
        accessible_record_selectors=("offering:nike:app", "channel:instagram"),
        known_limitations=("Does not include internal campaign budget or approval data.",),
    )
    frame = RelationshipFrame(
        frame_id="frame:nike-app-de-instagram-acquisition",
        frame_type_id="world://ontology/brand/frame/CampaignTargeting",
        context_id=perspective.context_id,
        role_bindings=(
            RoleBinding(role_id="offering", record_ids=("offering:nike:app",)),
            RoleBinding(role_id="audience", record_ids=("audience:nike:first-time-runners",)),
            RoleBinding(role_id="channel", record_ids=("channel:instagram",)),
            RoleBinding(role_id="market", value="DE"),
            RoleBinding(role_id="budget", value={"amount": 200000, "currency": "EUR"}),
        ),
        assertion_ids=("assertion:campaign-targeting",),
        status="proposed",
    )

    assert perspective.holder_id == "audience:nike:first-time-runners"
    assert {binding.role_id for binding in frame.role_bindings} >= {
        "offering",
        "audience",
        "channel",
        "market",
        "budget",
    }
    with pytest.raises(ValueError, match="unique"):
        frame.model_copy(
            update={"role_bindings": (*frame.role_bindings, frame.role_bindings[0])}
        ).require_unique_roles()


def test_world_view_compiler_resolves_branch_before_exposing_a_bounded_packet() -> None:
    context_id = "world://context/nike-app-de-new-runners"
    main = WorldBranch(
        branch_id="branch:main",
        workspace_id="world://workspace/brand/nike",
        branch_kind=BranchKind.INTERPRETATION,
        label="Accepted working world",
        created_by="system",
        created_at="2026-08-31T00:00:00Z",
        status=BranchStatus.ACTIVE,
    )
    scenario = WorldBranch(
        branch_id="branch:confidence",
        workspace_id=main.workspace_id,
        parent_branch_id=main.branch_id,
        branch_kind=BranchKind.SCENARIO,
        label="Confidence-first scenario",
        created_by="strategy-team",
        created_at="2026-08-31T00:00:00Z",
        status=BranchStatus.ACTIVE,
    )
    state = StateSnapshot(
        state_id="state:onboarding-completion",
        subject_ids=("offering:nike:app",),
        state_type_id="state:completion",
        context_id=context_id,
        values=(StateValue(key="completion_rate", value="42%"),),
    )
    perspective = PerspectiveProfile(
        perspective_id="perspective:new-runner",
        holder_id="audience:new-runners",
        perspective_type_id="perspective:customer",
        context_id=context_id,
    )
    frame = RelationshipFrame(
        frame_id="frame:acquisition",
        frame_type_id="frame:campaign-targeting",
        context_id=context_id,
        role_bindings=(
            RoleBinding(role_id="offering", record_ids=("offering:nike:app",)),
            RoleBinding(role_id="audience", record_ids=("audience:new-runners",)),
        ),
        status="proposed",
    )

    view = compile_world_view(
        WorldViewRequest(
            request_id="request:asset",
            workspace_id=main.workspace_id,
            context_id=context_id,
            branch_id=scenario.branch_id,
            task_type="asset_creation",
            perspective_ids=(perspective.perspective_id,),
            permitted_record_ids=(state.state_id, perspective.perspective_id, frame.frame_id),
        ),
        branches=(main, scenario),
        deltas=(),
        states=(state,),
        perspectives=(perspective,),
        relationship_frames=(frame,),
    )

    assert view.status is WorldViewStatus.HIT
    assert view.selected_record_ids == (state.state_id, perspective.perspective_id, frame.frame_id)
    assert view.perspective_ids == (perspective.perspective_id,)
    assert "branch overlay resolved before model synthesis" in view.route_receipt


def test_world_view_compiler_does_not_expose_an_unrequested_perspective() -> None:
    context_id = "world://context/example"
    branch = WorldBranch(
        branch_id="branch:main",
        workspace_id="world://workspace/example",
        branch_kind=BranchKind.INTERPRETATION,
        label="Main",
        created_by="system",
        created_at="2026-08-31T00:00:00Z",
        status=BranchStatus.ACTIVE,
    )
    state = StateSnapshot(
        state_id="state:shared",
        subject_ids=("entity:service",),
        state_type_id="state:service",
        context_id=context_id,
        values=(StateValue(key="status", value="available"),),
    )
    customer = PerspectiveProfile(
        perspective_id="perspective:customer",
        holder_id="audience:customers",
        perspective_type_id="perspective:customer",
        context_id=context_id,
    )
    finance = PerspectiveProfile(
        perspective_id="perspective:finance",
        holder_id="team:finance",
        perspective_type_id="perspective:finance",
        context_id=context_id,
    )

    view = compile_world_view(
        WorldViewRequest(
            request_id="request:customer",
            workspace_id=branch.workspace_id,
            context_id=context_id,
            branch_id=branch.branch_id,
            task_type="brief",
            perspective_ids=(customer.perspective_id,),
        ),
        branches=(branch,),
        deltas=(),
        states=(state,),
        perspectives=(customer, finance),
        relationship_frames=(),
    )

    assert view.perspective_ids == (customer.perspective_id,)
    assert finance.perspective_id not in view.selected_record_ids


def test_learning_layer_keeps_hypothesis_protocol_observation_and_review_distinct() -> None:
    interval = {"from_time": "2026-08-01T00:00:00Z", "to_time": "2026-08-31T00:00:00Z"}
    hypothesis = HypothesisRecord(
        hypothesis_id="hypothesis:member-discovery",
        branch_id="branch:member-discovery",
        context_id="context:membership",
        input_ids=("frame:member-discovery",),
        proposition="Clearer benefit framing may increase qualified membership starts.",
        mechanism_description="Prospective members can connect documented benefits to their needs.",
        falsification_conditions=("Qualified starts do not improve versus the control.",),
        status=HypothesisStatus.TESTABLE,
    )
    plan = ExperimentPlan(
        experiment_id="experiment:member-discovery",
        hypothesis_ids=(hypothesis.hypothesis_id,),
        branch_id=hypothesis.branch_id,
        context_id=hypothesis.context_id,
        intervention="Show documented membership benefits before app discovery.",
        comparison_or_control="Current member discovery sequence.",
        population_selector="Eligible prospective members in the declared market.",
        assignment_method="Randomized assignment where permitted.",
        metric_ids=("metric:qualified-membership-starts",),
        success_thresholds=(
            MetricThreshold(
                metric_id="metric:qualified-membership-starts",
                comparator="greater_than",
                value=0,
                unit_id="unit:percentage-points",
            ),
        ),
        time_window=interval,
        sample_requirements="Determine sample size before approval.",
        risk_and_ethics_constraints=("Use only consented, permitted measurement data.",),
        status=ExperimentStatus.DRAFT,
    )
    outcome = ObservedOutcome(
        outcome_id="outcome:member-discovery",
        experiment_id=plan.experiment_id,
        context_id=plan.context_id,
        metric_values={"metric:qualified-membership-starts": 0.03},
        measurement_method_id="method:experiment-analysis",
        population_description="The experiment population as recorded in the completed run.",
        time_window=interval,
        evidence_link_ids=("evidence-link:experiment-results",),
        status=OutcomeStatus.OBSERVED,
        limitations=("This result may not generalize outside the recorded context.",),
    )
    learning = LearningUpdate(
        learning_id="learning:member-discovery",
        hypothesis_id=hypothesis.hypothesis_id,
        outcome_ids=(outcome.outcome_id,),
        context_id=plan.context_id,
        disposition=LearningDisposition.STRENGTHENS,
        rationale="The measured result is directionally consistent with the hypothesis.",
        affected_record_ids=("decision:member-discovery",),
    )

    assert plan.status is ExperimentStatus.DRAFT
    assert outcome.status is OutcomeStatus.OBSERVED
    assert learning.review_required is True
    with pytest.raises(ValueError, match="confidence_calibration_policy_id"):
        hypothesis.model_copy(update={"confidence": 0.8}).preserve_uncertainty()
    with pytest.raises(ValueError, match="authority_grant_id"):
        plan.model_copy(
            update={"status": ExperimentStatus.RUNNING}
        ).require_authority_for_execution()
    with pytest.raises(ValueError, match="authority_grant_id"):
        plan.model_copy(
            update={"status": ExperimentStatus.COMPLETED}
        ).require_authority_for_execution()
    with pytest.raises(ValueError):
        ObservedOutcome(
            outcome_id="outcome:invalid-value",
            experiment_id=plan.experiment_id,
            context_id=plan.context_id,
            metric_values={"metric:qualified-membership-starts": "three percent"},
            measurement_method_id="method:experiment-analysis",
            population_description="Recorded population.",
            time_window=interval,
            evidence_link_ids=("evidence-link:experiment-results",),
            status=OutcomeStatus.OBSERVED,
            limitations=("Limited scope.",),
        )
    with pytest.raises(ValueError, match="reviewed_by"):
        learning.model_copy(update={"review_status": "reviewed"}).validate_review()
