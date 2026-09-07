"""Deterministic semantic fixtures for the Brand ontology research workspace.

The fixtures are deliberately synthetic. They exercise the constitutional kernel without
introducing real-world Brand facts or generated Cognee state.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from testflight_semantic import (
    Assertion,
    AssertionStatus,
    BindingMode,
    BranchDelta,
    BranchDeltaKind,
    BranchKind,
    BranchStatus,
    ChangeType,
    ComplianceStatus,
    Context,
    DecisionRecord,
    DecisionStatus,
    Deontic,
    DependencyCandidate,
    DependencyEdge,
    DependencyEffect,
    DependencyRule,
    DerivationRecord,
    DerivationResult,
    EntityLifecycle,
    Event,
    EvidenceEnvelope,
    EvidenceLink,
    EvidenceRole,
    FederationBridge,
    FederationPlan,
    FederationPlanStatus,
    FederationRegistry,
    FreshnessState,
    FreshnessStatus,
    IdentityScope,
    KnowledgeContainer,
    Perspective,
    PerspectiveProfile,
    RelationshipFrame,
    RepresentationBinding,
    RepresentationEvaluation,
    RepresentationProfile,
    RepresentationRule,
    RoleBinding,
    SemanticEntity,
    StalenessMarker,
    StateSnapshot,
    StateStatus,
    StateValue,
    TemporalInterval,
    ValidationMethod,
    WorldBranch,
    evaluate_dependency_rule,
    resolve_branch_records,
    resolve_profile_order,
    validate_derivation_graph,
)

WORKSPACE_ID = "world://workspace/brand-ontology-research"
V = "0.1.0"

TYPE = {
    "brand": "world://ontology/type/Brand",
    "organization": "world://ontology/type/Organization",
    "portfolio": "world://ontology/type/Portfolio",
    "offering": "world://ontology/type/Offering",
    "technology": "world://ontology/type/Technology",
    "positioning": "world://ontology/type/Positioning",
    "artifact": "world://ontology/type/Artifact",
    "message": "world://ontology/type/MessagingArtifact",
    "observation": "world://ontology/brand/type/ResearchObservation",
    "insight": "world://ontology/brand/type/CustomerInsight",
    "segment": "world://ontology/brand/type/AudienceSegment",
    "icp": "world://ontology/brand/type/IdealCustomerProfile",
    "need": "world://ontology/brand/type/Need",
    "product_definition": "world://ontology/brand/type/ProductDefinition",
    "campaign_strategy": "world://ontology/brand/type/CampaignStrategy",
    "brief": "world://ontology/brand/type/CreativeBrief",
    "creative_direction": "world://ontology/brand/type/CreativeDirection",
    "asset": "world://ontology/brand/type/Asset",
    "channel": "world://ontology/brand/type/Channel",
}


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def _interval(start: str | None, end: str | None) -> TemporalInterval:
    return TemporalInterval(
        from_time=_dt(start) if start else None,
        to_time=_dt(end) if end else None,
        from_semantics="known" if start else "unknown",
        to_semantics="known" if end else "unbounded",
    )


def _context(slug: str, **kwargs: Any) -> Context:
    return Context(
        brand_system_id=f"brand-system:{slug}",
        dimensions={"fixture": slug, **kwargs.pop("dimensions", {})},
        **kwargs,
    )


def _entity(
    entity_id: str,
    type_key: str,
    label: str,
    *,
    workspace_id: str | None = WORKSPACE_ID,
    identity_scope: IdentityScope = IdentityScope.WORKSPACE,
) -> SemanticEntity:
    return SemanticEntity(
        entity_id=entity_id,
        type_id=TYPE[type_key],
        workspace_id=workspace_id,
        identity_scope=identity_scope,
        lifecycle_status=EntityLifecycle.ACCEPTED,
        canonical_label=label,
        definition_version=V,
    )


def _assertion(
    assertion_id: str,
    subject_id: str,
    predicate: str,
    context: Context,
    *,
    object_id: str | None = None,
    object_value: Any | None = None,
    perspective: Perspective = Perspective.OBSERVED,
    status: AssertionStatus = AssertionStatus.PROPOSED,
    evidence: tuple[str, ...] = (),
    valid: TemporalInterval | None = None,
    known: TemporalInterval | None = None,
) -> Assertion:
    return Assertion(
        assertion_id=assertion_id,
        subject_id=subject_id,
        predicate_id=f"world://ontology/relation/{predicate}",
        object_id=object_id,
        object_value=object_value,
        context_id=context.context_id,
        perspective=perspective,
        status=status,
        valid_time=valid,
        known_time=known,
        evidence_refs=evidence,
    )


def _evidence(source_id: str, fixture: str) -> EvidenceEnvelope:
    return EvidenceEnvelope(
        source_id=source_id,
        workspace_id=WORKSPACE_ID,
        content_hash=f"sha256:synthetic-{fixture}-{source_id}",
        source_uri=f"fixture://{fixture}/{source_id}",
        recorded_time=_dt("2026-08-20T00:00:00Z"),
        actor_id="fixture-author",
    )


@dataclass(frozen=True, slots=True)
class FixtureWorld:
    world_id: str
    slug: str
    required_invariants: tuple[str, ...]
    objects: tuple[Any, ...]
    notes: tuple[str, ...] = ()

    @property
    def object_ids(self) -> tuple[str, ...]:
        values: list[str] = []
        for item in self.objects:
            for field_name in (
                "decision_id",
                "state_id",
                "perspective_id",
                "frame_id",
                "link_id",
                "delta_id",
                "assertion_id",
                "event_id",
                "source_id",
                "binding_id",
                "profile_id",
                "edge_id",
                "marker_id",
                "manifestation_id",
                "context_id",
                "branch_id",
                "entity_id",
                "rule_id",
            ):
                value = getattr(item, field_name, None)
                if isinstance(value, str):
                    values.append(value)
                    break
        return tuple(values)


def intended_observed_brand() -> FixtureWorld:
    context = _context(
        "intended-observed",
        brand_id="brand:aurora",
        audience_ids=("audience:builders",),
        dimensions={"market": "EU"},
    )
    brand = _entity("brand:aurora", "brand", "Aurora")
    intended = _assertion(
        "assertion:aurora:intended",
        brand.entity_id,
        "positioned-as",
        context,
        object_value="calm infrastructure for builders",
        perspective=Perspective.INTENDED,
        evidence=("evidence:aurora:brief",),
    )
    observed = _assertion(
        "assertion:aurora:observed",
        brand.entity_id,
        "associated-with",
        context,
        object_value="reliable but difficult to learn",
        perspective=Perspective.OBSERVED,
        evidence=("evidence:aurora:interview",),
    )
    return FixtureWorld(
        "SW-001",
        "intended-observed-brand",
        ("perspectives_separate", "evidence_attached", "context_scoped"),
        (
            brand,
            context,
            _evidence("evidence:aurora:brief", "sw001"),
            _evidence("evidence:aurora:interview", "sw001"),
            intended,
            observed,
        ),
    )


def repositioning_temporal() -> FixtureWorld:
    context = _context(
        "repositioning",
        brand_id="brand:aurora",
        dimensions={"market": "EU", "audience": "enterprise"},
    )
    brand = _entity("brand:aurora", "brand", "Aurora")
    message = _entity("artifact:aurora:primary-message", "message", "Aurora primary message")
    event = Event(
        event_id="event:aurora:repositioning",
        type_id="world://ontology/type/PositioningChange",
        context_id=context.context_id,
        valid_time=_interval("2025-01-15T00:00:00Z", "2025-02-01T00:00:00Z"),
    )
    old = _assertion(
        "assertion:aurora:positioning:v1",
        brand.entity_id,
        "positioned-as",
        context,
        object_value="calm infrastructure",
        perspective=Perspective.INTENDED,
        status=AssertionStatus.SUPERSEDED,
        evidence=("evidence:positioning:v1",),
        valid=_interval("2024-01-01T00:00:00Z", "2025-02-01T00:00:00Z"),
        known=_interval("2024-01-01T00:00:00Z", "2025-02-10T00:00:00Z"),
    )
    new = _assertion(
        "assertion:aurora:positioning:v2",
        brand.entity_id,
        "positioned-as",
        context,
        object_value="observable infrastructure for regulated teams",
        perspective=Perspective.INTENDED,
        status=AssertionStatus.ACCEPTED,
        evidence=("evidence:positioning:v2",),
        valid=_interval("2025-02-01T00:00:00Z", None),
        known=_interval("2025-02-10T00:00:00Z", None),
    )
    dependency_rule = DependencyRule(
        rule_id="dependency:positioning-to-message",
        version=V,
        upstream_selector={"entity_type": "Positioning"},
        downstream_selector={"entity_type": "MessagingArtifact"},
        trigger_change_types=(ChangeType.ASSERTION_ACCEPTED,),
        effect=DependencyEffect.POTENTIALLY_STALE,
        max_depth=2,
    )
    dependency_edge = DependencyEdge(
        edge_id="edge:positioning-to-message",
        upstream_id=new.assertion_id,
        downstream_id=message.entity_id,
        rule_id=dependency_rule.rule_id,
        rule_version=dependency_rule.version,
        context_id=context.context_id,
        materialization="fixture",
        created_at=_dt("2025-02-10T00:00:00Z"),
    )
    stale_marker = StalenessMarker(
        marker_id="marker:aurora:primary-message",
        downstream_id=message.entity_id,
        state="potentially_stale",
        cause_ids=(new.assertion_id,),
        rule_id=dependency_rule.rule_id,
        rule_version=dependency_rule.version,
        created_at=_dt("2025-02-10T00:00:00Z"),
        review_note="Positioning changed; message requires review, not deletion.",
    )
    return FixtureWorld(
        "SW-002",
        "repositioning-temporal",
        ("bitemporal", "history_preserved", "supersession_not_deletion"),
        (
            brand,
            message,
            context,
            event,
            dependency_rule,
            dependency_edge,
            stale_marker,
            _evidence("evidence:positioning:v1", "sw002"),
            _evidence("evidence:positioning:v2", "sw002"),
            old,
            new,
        ),
    )


def shared_technology() -> FixtureWorld:
    context_a = _context(
        "shared-technology-a", brand_id="brand:aurora", dimensions={"market": "EU"}
    )
    context_b = _context(
        "shared-technology-b", brand_id="brand:beacon", dimensions={"market": "US"}
    )
    brand_a = _entity("brand:aurora", "brand", "Aurora")
    brand_b = _entity("brand:beacon", "brand", "Beacon")
    technology = _entity(
        "technology:vector-engine",
        "technology",
        "Vector Engine",
        workspace_id=None,
        identity_scope=IdentityScope.SHARED,
    )
    uses_a = _assertion(
        "assertion:aurora:uses-vector",
        brand_a.entity_id,
        "uses",
        context_a,
        object_id=technology.entity_id,
        evidence=("evidence:technology:registry",),
    )
    uses_b = _assertion(
        "assertion:beacon:uses-vector",
        brand_b.entity_id,
        "uses",
        context_b,
        object_id=technology.entity_id,
        evidence=("evidence:technology:registry",),
    )
    return FixtureWorld(
        "SW-003",
        "shared-technology",
        ("identity_evidence_required", "local_assertions_scoped"),
        (
            brand_a,
            brand_b,
            technology,
            context_a,
            context_b,
            _evidence("evidence:technology:registry", "sw003"),
            uses_a,
            uses_b,
        ),
    )


def adaptive_representation() -> FixtureWorld:
    context = _context(
        "adaptive-representation",
        brand_id="brand:aurora",
        locale="de-DE",
        channel_ids=("channel:web",),
    )
    brand = _entity("brand:aurora", "brand", "Aurora")
    shared = RepresentationProfile(
        profile_id="profile:aurora:shared", version=V, rule_ids=("rule:semantic:promise",)
    )
    local = RepresentationProfile(
        profile_id="profile:aurora:de-web",
        version=V,
        includes=(shared.profile_id,),
        rule_ids=("rule:verbal:de", "rule:visual:de"),
    )
    campaign = RepresentationProfile(
        profile_id="profile:aurora:campaign",
        version=V,
        includes=(local.profile_id,),
        rule_ids=("rule:motion:campaign",),
    )
    rules = (
        RepresentationRule(
            rule_id="rule:semantic:promise",
            version=V,
            facet_id="semantic",
            deontic=Deontic.MUST,
            constraint="observable infrastructure",
            rationale="Fixture semantic invariant",
            validation_method=ValidationMethod.HUMAN,
            severity="error",
        ),
        RepresentationRule(
            rule_id="rule:verbal:de",
            version=V,
            facet_id="verbal",
            deontic=Deontic.SHOULD,
            constraint={"locale": "de-DE", "tone": "precise"},
            rationale="Locale adaptation",
            validation_method=ValidationMethod.MODEL,
            severity="warning",
        ),
        RepresentationRule(
            rule_id="rule:visual:de",
            version=V,
            facet_id="visual",
            deontic=Deontic.SHOULD,
            constraint={"contrast": "AA"},
            rationale="Accessible visual adaptation",
            validation_method=ValidationMethod.DETERMINISTIC,
            severity="error",
        ),
        RepresentationRule(
            rule_id="rule:motion:campaign",
            version=V,
            facet_id="motion",
            deontic=Deontic.MAY,
            constraint={"duration_ms": 400},
            rationale="Campaign motion",
            validation_method=ValidationMethod.DETERMINISTIC,
            severity="info",
        ),
    )
    binding = RepresentationBinding(
        binding_id="binding:aurora:de-campaign",
        entity_id=brand.entity_id,
        profile_id=campaign.profile_id,
        profile_version=campaign.version,
        context_id=context.context_id,
        mode=BindingMode.ADAPTIVE,
    )
    return FixtureWorld(
        "SW-004",
        "adaptive-representation",
        ("binding_profile_rules_separate", "profile_dag", "facet_extensible"),
        (brand, context, shared, local, campaign, *rules, binding),
    )


def market_positioning() -> FixtureWorld:
    eu = _context(
        "market-positioning-eu",
        brand_id="brand:aurora",
        audience_ids=("audience:regulated",),
        dimensions={"market": "EU"},
    )
    us = _context(
        "market-positioning-us",
        brand_id="brand:aurora",
        audience_ids=("audience:startups",),
        dimensions={"market": "US"},
    )
    organization = _entity("org:northstar", "organization", "Northstar Labs")
    portfolio = _entity("portfolio:platforms", "portfolio", "Platforms")
    brand = _entity("brand:aurora", "brand", "Aurora")
    offering = _entity("offering:control-plane", "offering", "Control Plane")
    owns = _assertion(
        "assertion:org:portfolio",
        organization.entity_id,
        "owns",
        eu,
        object_id=portfolio.entity_id,
        evidence=("evidence:portfolio:registry",),
    )
    contains = _assertion(
        "assertion:portfolio:brand",
        portfolio.entity_id,
        "contains",
        eu,
        object_id=brand.entity_id,
        evidence=("evidence:portfolio:registry",),
    )
    offers = _assertion(
        "assertion:brand:offering",
        brand.entity_id,
        "offers",
        eu,
        object_id=offering.entity_id,
        evidence=("evidence:portfolio:registry",),
    )
    eu_position = _assertion(
        "assertion:aurora:eu-position",
        brand.entity_id,
        "positioned-as",
        eu,
        object_value="compliance-first control plane",
        perspective=Perspective.INTENDED,
        evidence=("evidence:positioning:eu",),
    )
    us_position = _assertion(
        "assertion:aurora:us-position",
        brand.entity_id,
        "positioned-as",
        us,
        object_value="fast control plane for startups",
        perspective=Perspective.INTENDED,
        evidence=("evidence:positioning:us",),
    )
    evidence = tuple(
        _evidence(source_id, "sw005")
        for source_id in (
            "evidence:portfolio:registry",
            "evidence:positioning:eu",
            "evidence:positioning:us",
        )
    )
    return FixtureWorld(
        "SW-005",
        "market-positioning",
        ("portfolio_topology", "applicability_scoped", "concurrent_validity"),
        (
            organization,
            portfolio,
            brand,
            offering,
            eu,
            us,
            *evidence,
            owns,
            contains,
            offers,
            eu_position,
            us_position,
        ),
    )


def evidence_conflict() -> FixtureWorld:
    context = _context("evidence-conflict", brand_id="brand:aurora", dimensions={"market": "EU"})
    brand = _entity("brand:aurora", "brand", "Aurora")
    strong = _assertion(
        "assertion:aurora:reliable",
        brand.entity_id,
        "associated-with",
        context,
        object_value="reliable",
        perspective=Perspective.OBSERVED,
        evidence=("evidence:survey",),
    )
    weak = _assertion(
        "assertion:aurora:difficult",
        brand.entity_id,
        "associated-with",
        context,
        object_value="difficult",
        perspective=Perspective.OBSERVED,
        evidence=("evidence:single-review",),
        status=AssertionStatus.CHALLENGED,
    )
    conflict = _assertion(
        "assertion:aurora:conflict",
        strong.assertion_id,
        "conflicts-with",
        context,
        object_id=weak.assertion_id,
        evidence=("evidence:comparison",),
    )
    evidence = tuple(
        _evidence(source_id, "sw006")
        for source_id in ("evidence:survey", "evidence:single-review", "evidence:comparison")
    )
    return FixtureWorld(
        "SW-006",
        "evidence-conflict",
        ("conflict_preserved", "weak_evidence_held", "no_silent_winner"),
        (brand, context, *evidence, strong, weak, conflict),
    )


def bitemporal_reconstruction() -> FixtureWorld:
    context = _context(
        "bitemporal-reconstruction", brand_id="brand:aurora", dimensions={"market": "EU"}
    )
    brand = _entity("brand:aurora", "brand", "Aurora")
    valid = _interval("2025-01-01T00:00:00Z", None)
    original = _assertion(
        "assertion:aurora:belief:v1",
        brand.entity_id,
        "positioned-as",
        context,
        object_value="calm infrastructure",
        perspective=Perspective.INTENDED,
        status=AssertionStatus.SUPERSEDED,
        evidence=("evidence:brief:v1",),
        valid=valid,
        known=_interval("2025-01-01T00:00:00Z", "2025-03-01T00:00:00Z"),
    )
    correction = _assertion(
        "assertion:aurora:belief:v2",
        brand.entity_id,
        "positioned-as",
        context,
        object_value="observable infrastructure",
        perspective=Perspective.INTENDED,
        status=AssertionStatus.ACCEPTED,
        evidence=("evidence:correction",),
        valid=valid,
        known=_interval("2025-03-01T00:00:00Z", None),
    )
    event = Event(
        event_id="event:aurora:correction",
        type_id="world://ontology/type/Correction",
        context_id=context.context_id,
        valid_time=_interval("2025-02-15T00:00:00Z", "2025-03-01T00:00:00Z"),
    )
    evidence = tuple(
        _evidence(source_id, "sw007") for source_id in ("evidence:brief:v1", "evidence:correction")
    )
    return FixtureWorld(
        "SW-007",
        "bitemporal-reconstruction",
        ("utc_half_open_time", "knowledge_history", "snapshot_replay"),
        (brand, context, event, *evidence, original, correction),
    )


def causal_guardrails() -> FixtureWorld:
    context = _context("causal-guardrails", brand_id="brand:aurora", dimensions={"market": "EU"})
    brand = _entity("brand:aurora", "brand", "Aurora")
    campaign = Event(
        event_id="event:aurora:campaign",
        type_id="world://ontology/type/Campaign",
        context_id=context.context_id,
        valid_time=_interval("2025-04-01T00:00:00Z", "2025-05-01T00:00:00Z"),
    )
    outcome = Event(
        event_id="event:aurora:consideration",
        type_id="world://ontology/type/ConsiderationShift",
        context_id=context.context_id,
        valid_time=_interval("2025-05-01T00:00:00Z", "2025-06-01T00:00:00Z"),
    )
    precedes = _assertion(
        "assertion:campaign:precedes",
        campaign.event_id,
        "precedes",
        context,
        object_id=outcome.event_id,
        perspective=Perspective.OBSERVED,
        evidence=("evidence:timeline",),
    )
    hypothesis_a = _assertion(
        "assertion:campaign:influences",
        campaign.event_id,
        "influences",
        context,
        object_id=outcome.event_id,
        perspective=Perspective.HYPOTHESIZED,
        evidence=("evidence:correlation",),
    )
    hypothesis_b = _assertion(
        "assertion:seasonality:influences",
        "event:seasonality",
        "influences",
        context,
        object_id=outcome.event_id,
        perspective=Perspective.HYPOTHESIZED,
        evidence=("evidence:seasonality",),
        status=AssertionStatus.CHALLENGED,
    )
    evidence = tuple(
        _evidence(source_id, "sw008")
        for source_id in ("evidence:timeline", "evidence:correlation", "evidence:seasonality")
    )
    return FixtureWorld(
        "SW-008",
        "causal-guardrails",
        ("causal_gate", "alternatives_preserved", "sequence_not_cause"),
        (brand, context, campaign, outcome, *evidence, precedes, hypothesis_a, hypothesis_b),
    )


def shared_representation_products() -> FixtureWorld:
    context_a = _context(
        "shared-representation-a",
        brand_id="brand:aurora",
        offering_id="offering:control-plane",
        locale="en-US",
    )
    context_b = _context(
        "shared-representation-b",
        brand_id="brand:aurora",
        offering_id="offering:mobile",
        locale="de-DE",
    )
    brand = _entity("brand:aurora", "brand", "Aurora")
    product_a = _entity("offering:control-plane", "offering", "Control Plane")
    product_b = _entity("offering:mobile", "offering", "Mobile Console")
    shared = RepresentationProfile(
        profile_id="profile:aurora:shared", version=V, rule_ids=("rule:promise",)
    )
    desktop = RepresentationProfile(
        profile_id="profile:aurora:desktop",
        version=V,
        includes=(shared.profile_id,),
        rule_ids=("rule:desktop:visual",),
    )
    mobile = RepresentationProfile(
        profile_id="profile:aurora:mobile",
        version=V,
        includes=(shared.profile_id,),
        rule_ids=("rule:mobile:visual",),
    )
    promise = RepresentationRule(
        rule_id="rule:promise",
        version=V,
        facet_id="semantic",
        deontic=Deontic.MUST,
        constraint="observable infrastructure",
        rationale="Shared semantic identity",
        validation_method=ValidationMethod.HUMAN,
        severity="error",
    )
    desktop_rule = RepresentationRule(
        rule_id="rule:desktop:visual",
        version=V,
        facet_id="visual",
        deontic=Deontic.SHOULD,
        constraint={"density": "high"},
        rationale="Desktop manifestation",
        validation_method=ValidationMethod.HUMAN,
        severity="warning",
    )
    mobile_rule = RepresentationRule(
        rule_id="rule:mobile:visual",
        version=V,
        facet_id="visual",
        deontic=Deontic.SHOULD,
        constraint={"density": "low"},
        rationale="Mobile manifestation",
        validation_method=ValidationMethod.HUMAN,
        severity="warning",
    )
    binding_a = RepresentationBinding(
        binding_id="binding:aurora:desktop",
        entity_id=brand.entity_id,
        profile_id=desktop.profile_id,
        profile_version=desktop.version,
        context_id=context_a.context_id,
        mode=BindingMode.LOCAL,
    )
    binding_b = RepresentationBinding(
        binding_id="binding:aurora:mobile",
        entity_id=brand.entity_id,
        profile_id=mobile.profile_id,
        profile_version=mobile.version,
        context_id=context_b.context_id,
        mode=BindingMode.ADAPTIVE,
    )
    evaluation = RepresentationEvaluation(
        manifestation_id="manifestation:aurora:mobile",
        compliance=ComplianceStatus.UNASSESSABLE,
        freshness=FreshnessStatus.CURRENT,
        findings=("equal-authority-visual-rules",),
        rule_ids=(desktop_rule.rule_id, mobile_rule.rule_id),
        context_id=context_b.context_id,
        derivation_id="derivation:sw009:conflict",
    )
    return FixtureWorld(
        "SW-009",
        "shared-representation-products",
        ("shared_identity", "adaptive_binding", "equal_authority_conflict_explicit"),
        (
            brand,
            product_a,
            product_b,
            context_a,
            context_b,
            shared,
            desktop,
            mobile,
            promise,
            desktop_rule,
            mobile_rule,
            binding_a,
            binding_b,
            evaluation,
        ),
    )


def conditional_icp_to_asset_chain() -> FixtureWorld:
    """Prove a bounded decision path without claiming automatic causation."""

    context = _context(
        "conditional-icp-to-asset",
        brand_id="brand:aurora",
        offering_id="offering:aurora:app",
        audience_ids=("audience:aurora:first-time-runners",),
        channel_ids=("channel:instagram",),
        campaign_or_occasion_ids=("campaign:aurora:fall-2026",),
        valid_time=_interval("2026-09-01T00:00:00Z", "2026-12-01T00:00:00Z"),
        dimensions={"market": "DE", "journey_stage": "consideration"},
    )
    other_audience_context = _context(
        "conditional-icp-to-asset-other-audience",
        brand_id="brand:aurora",
        offering_id="offering:aurora:app",
        audience_ids=("audience:aurora:experienced-runners",),
        channel_ids=("channel:instagram",),
        dimensions={"market": "DE", "journey_stage": "consideration"},
    )
    observation = _entity(
        "observation:aurora:new-runners", "observation", "New-runner interview finding"
    )
    insight = _entity("insight:aurora:new-runners", "insight", "First runs need reassurance")
    segment = _entity(
        "audience:aurora:first-time-runners", "segment", "First-time everyday runners"
    )
    icp = _entity("icp:aurora:first-time-runners", "icp", "Nike App first-time runner ICP")
    need = _entity("need:aurora:confidence", "need", "Confidence to begin a running routine")
    product = _entity(
        "product-definition:aurora:app:new-runners",
        "product_definition",
        "Guided first-run product definition",
    )
    positioning = _entity(
        "positioning:aurora:app:first-run", "positioning", "Confident first-run companion"
    )
    campaign = _entity(
        "campaign-strategy:aurora:fall-2026", "campaign_strategy", "Confidence-first acquisition"
    )
    brief = _entity(
        "brief:aurora:instagram:first-run", "brief", "Instagram first-run creative brief"
    )
    direction = _entity(
        "creative-direction:aurora:first-step",
        "creative_direction",
        "Reassuring first-step direction",
    )
    asset = _entity("asset:aurora:instagram:first-run", "asset", "Instagram first-run video")
    channel = _entity("channel:instagram", "channel", "Instagram")
    assertions = (
        _assertion(
            "assertion:sw010:observation-supports-insight",
            observation.entity_id,
            "supports",
            context,
            object_id=insight.entity_id,
            evidence=("evidence:sw010:interviews",),
        ),
        _assertion(
            "assertion:sw010:segment-has-need",
            segment.entity_id,
            "has-need",
            context,
            object_id=need.entity_id,
            evidence=("evidence:sw010:interviews",),
        ),
        _assertion(
            "assertion:sw010:icp-represents-segment",
            icp.entity_id,
            "represents",
            context,
            object_id=segment.entity_id,
            perspective=Perspective.INTENDED,
            status=AssertionStatus.ACCEPTED,
            evidence=("evidence:sw010:icp-decision",),
        ),
        _assertion(
            "assertion:sw010:product-designed-for-icp",
            product.entity_id,
            "designed-for",
            context,
            object_id=icp.entity_id,
            perspective=Perspective.INTENDED,
            status=AssertionStatus.ACCEPTED,
            evidence=("evidence:sw010:product-decision",),
        ),
        _assertion(
            "assertion:sw010:positioning-positions-product",
            positioning.entity_id,
            "positions",
            context,
            object_id=product.entity_id,
            perspective=Perspective.INTENDED,
            status=AssertionStatus.ACCEPTED,
            evidence=("evidence:sw010:positioning-decision",),
        ),
        _assertion(
            "assertion:sw010:campaign-implements-positioning",
            campaign.entity_id,
            "implements",
            context,
            object_id=positioning.entity_id,
            perspective=Perspective.INTENDED,
            status=AssertionStatus.ACCEPTED,
            evidence=("evidence:sw010:campaign-decision",),
        ),
        _assertion(
            "assertion:sw010:brief-operationalizes-campaign",
            brief.entity_id,
            "operationalizes",
            context,
            object_id=campaign.entity_id,
            perspective=Perspective.INTENDED,
            status=AssertionStatus.ACCEPTED,
            evidence=("evidence:sw010:brief",),
        ),
        _assertion(
            "assertion:sw010:direction-governs-asset",
            direction.entity_id,
            "governs",
            context,
            object_id=asset.entity_id,
            perspective=Perspective.INTENDED,
            status=AssertionStatus.ACCEPTED,
            evidence=("evidence:sw010:creative-review",),
        ),
        _assertion(
            "assertion:sw010:asset-promotes-offering",
            asset.entity_id,
            "promotes",
            context,
            object_id="offering:aurora:app",
            perspective=Perspective.INTENDED,
            status=AssertionStatus.ACCEPTED,
            evidence=("evidence:sw010:brief",),
        ),
        _assertion(
            "assertion:sw010:asset-distributed-via-channel",
            asset.entity_id,
            "distributed-via",
            context,
            object_id=channel.entity_id,
            perspective=Perspective.INTENDED,
            status=AssertionStatus.ACCEPTED,
            evidence=("evidence:sw010:media-plan",),
        ),
    )
    decision = DecisionRecord(
        decision_id="decision:aurora:positioning:first-run",
        workspace_id=WORKSPACE_ID,
        decision_type_id="world://ontology/brand/type/StrategyDecision",
        context_id=context.context_id,
        input_ids=(observation.entity_id, insight.entity_id, product.entity_id),
        selected_option_id=positioning.entity_id,
        rejected_option_ids=("positioning:aurora:app:performance-first",),
        rationale=(
            "The selected positioning addresses the evidenced confidence need for the scoped ICP."
        ),
        authority_grant_id="grant:aurora:strategy",
        derivation_id="derivation:sw010:context-chain",
        decided_at=_dt("2026-08-31T00:00:00Z"),
        status=DecisionStatus.ACCEPTED,
    )
    dependency_rule = DependencyRule(
        rule_id="dependency:sw010:icp-to-asset",
        version=V,
        upstream_selector={"entity_type": TYPE["icp"]},
        downstream_selector={
            "entity_type": TYPE["asset"],
            "relation_path": ("designed-for", "implements", "operationalizes", "governs"),
        },
        trigger_change_types=(ChangeType.ENTITY_REVISION,),
        effect=DependencyEffect.POTENTIALLY_STALE,
        max_depth=4,
    )
    dependency_edges = evaluate_dependency_rule(
        dependency_rule,
        upstream=DependencyCandidate(
            record_id=icp.entity_id,
            entity_id=icp.entity_id,
            entity_type=icp.type_id,
            context=context,
        ),
        downstream=(
            DependencyCandidate(
                record_id=asset.entity_id,
                entity_id=asset.entity_id,
                entity_type=asset.type_id,
                context=context,
                relation_path=("designed-for", "implements", "operationalizes", "governs"),
            ),
            DependencyCandidate(
                record_id="asset:aurora:instagram:experienced",
                entity_id="asset:aurora:instagram:experienced",
                entity_type=asset.type_id,
                context=other_audience_context,
                relation_path=("designed-for", "implements", "operationalizes", "governs"),
            ),
        ),
        change_type=ChangeType.ENTITY_REVISION,
        created_at=_dt("2026-08-31T00:00:00Z"),
        derivation_id="derivation:sw010:context-chain",
    )
    marker = StalenessMarker(
        marker_id="marker:sw010:asset-review",
        downstream_id=asset.entity_id,
        state=FreshnessState.POTENTIALLY_STALE,
        cause_ids=(icp.entity_id,),
        rule_id=dependency_rule.rule_id,
        rule_version=dependency_rule.version,
        created_at=_dt("2026-08-31T00:00:00Z"),
        review_note="ICP revision requires review; it does not rewrite the asset.",
        derivation_id="derivation:sw010:context-chain",
    )
    profile = RepresentationProfile(
        profile_id="profile:aurora:first-run-instagram",
        version=V,
        rule_ids=("rule:aurora:first-run-tone",),
    )
    binding = RepresentationBinding(
        binding_id="binding:aurora:first-run-asset",
        entity_id=asset.entity_id,
        profile_id=profile.profile_id,
        profile_version=profile.version,
        context_id=context.context_id,
        mode=BindingMode.ADAPTIVE,
    )
    parent = KnowledgeContainer(
        workspace_id=WORKSPACE_ID,
        route="brand/aurora",
        dataset_name="Aurora brand world",
        owns_entity_ids=("brand:aurora", "offering:aurora:app"),
    )
    child = KnowledgeContainer(
        workspace_id=f"{WORKSPACE_ID}/offering/app",
        parent_workspace_id=WORKSPACE_ID,
        route="brand/aurora/offering/app",
        dataset_name="Aurora App world",
        augments_entity_ids=("offering:aurora:app", product.entity_id, asset.entity_id),
    )
    plan = FederationRegistry(
        containers=(parent, child),
        bridges=(
            FederationBridge(
                bridge_id="bridge:sw010:app-to-brand",
                source_workspace_id=child.workspace_id,
                target_workspace_id=parent.workspace_id,
                subject_id="offering:aurora:app",
                predicate_id="world://ontology/federation/augments",
                object_id="brand:aurora",
                context_id=context.context_id,
                evidence_refs=("evidence:sw010:container-registration",),
                allow_traversal=True,
            ),
        ),
    ).plan_child_first(
        root_workspace_id=WORKSPACE_ID,
        entity_ids=("offering:aurora:app",),
        permitted_workspace_ids=frozenset((WORKSPACE_ID, child.workspace_id)),
    )
    derivation = DerivationRecord(
        derivation_id="derivation:sw010:context-chain",
        output_ids=(
            decision.decision_id,
            *(edge.edge_id for edge in dependency_edges),
            marker.marker_id,
        ),
        input_ids=("evidence:sw010:interviews",),
        operation_id="fixture:conditional-brand-chain",
        actor_id="fixture-author",
        ontology_version="2.0.0-candidate",
        policy_versions=("dependency-rule:0.1.0", "federation:0.1.0"),
        reasoning_operators=(
            "world://operator/guardrail/sequence-causality-conflation@1",
            "world://operator/guardrail/workspace-isolation@1",
            "world://operator/guardrail/version-state-conflation@1",
        ),
        occurred_at="2026-08-31T00:00:00Z",
        result=DerivationResult.PROPOSED,
    )
    return FixtureWorld(
        "SW-010",
        "conditional-icp-to-asset-chain",
        (
            "decision_lineage",
            "conditional_dependency",
            "child_first_federation",
            "no_automatic_rewrite",
        ),
        (
            observation,
            insight,
            segment,
            icp,
            need,
            product,
            positioning,
            campaign,
            brief,
            direction,
            asset,
            channel,
            context,
            other_audience_context,
            _evidence("evidence:sw010:interviews", "sw010"),
            *assertions,
            decision,
            dependency_rule,
            *dependency_edges,
            marker,
            derivation,
            profile,
            binding,
            parent,
            child,
            plan,
        ),
        ("Synthetic candidate demonstrating bounded ICP-to-asset traceability.",),
    )


def branch_perspective_state_frame() -> FixtureWorld:
    """Prove the first missing layers compose without becoming one record type."""

    context = _context(
        "branch-perspective-state-frame",
        brand_id="brand:aurora",
        offering_id="offering:aurora:app",
        audience_ids=("audience:aurora:first-time-runners",),
        channel_ids=("channel:instagram",),
        dimensions={"market": "DE"},
    )
    state = StateSnapshot(
        state_id="state:aurora:onboarding-completion",
        subject_ids=("offering:aurora:app",),
        state_type_id="world://ontology/brand/type/StateSnapshot",
        context_id=context.context_id,
        values=(
            StateValue(
                key="completion_rate",
                value=0.42,
                unit_id="unit:ratio",
                measurement_method_id="method:fixture-analytics",
            ),
        ),
        source_assertion_ids=("assertion:sw011:completion-measurement",),
        evidence_link_ids=("evidence-link:sw011:support", "evidence-link:sw011:qualifies"),
        status=StateStatus.SUPPORTED,
        derivation_id="derivation:sw011:state",
    )
    evidence_support = EvidenceLink(
        link_id="evidence-link:sw011:support",
        evidence_id="evidence:sw011:analytics",
        target_id=state.state_id,
        role=EvidenceRole.SUPPORTS,
        context_id=context.context_id,
    )
    evidence_qualifies = EvidenceLink(
        link_id="evidence-link:sw011:qualifies",
        evidence_id="evidence:sw011:method",
        target_id=state.state_id,
        role=EvidenceRole.QUALIFIES,
        context_id=context.context_id,
        note="Completion is a product metric, not proof of customer motivation.",
    )
    main = WorldBranch(
        branch_id="branch:aurora:main",
        workspace_id=WORKSPACE_ID,
        branch_kind=BranchKind.INTERPRETATION,
        label="Aurora accepted working view",
        created_by="fixture-author",
        created_at="2026-08-31T00:00:00Z",
        status=BranchStatus.ACTIVE,
    )
    scenario = WorldBranch(
        branch_id="branch:aurora:confidence-first",
        workspace_id=WORKSPACE_ID,
        parent_branch_id=main.branch_id,
        branch_kind=BranchKind.SCENARIO,
        label="Confidence-first acquisition scenario",
        assumption_ids=("assumption:aurora:reassurance-matters",),
        created_by="fixture-author",
        created_at="2026-08-31T00:00:00Z",
        status=BranchStatus.ACTIVE,
    )
    deltas = (
        BranchDelta(
            delta_id="delta:sw011:exclude-performance",
            branch_id=scenario.branch_id,
            kind=BranchDeltaKind.EXCLUDE,
            target_record_id="positioning:aurora:performance-first",
            rationale="Scenario preserves an alternative without deleting it from the main branch.",
        ),
        BranchDelta(
            delta_id="delta:sw011:add-confidence",
            branch_id=scenario.branch_id,
            kind=BranchDeltaKind.ADD,
            target_record_id="positioning:aurora:confidence-first",
            rationale="Scenario-specific positioning candidate.",
        ),
    )
    perspective = PerspectiveProfile(
        perspective_id="perspective:aurora:first-time-runner",
        holder_id="audience:aurora:first-time-runners",
        perspective_type_id="world://ontology/brand/type/PerspectiveProfile",
        context_id=context.context_id,
        goals=("Start a running routine without feeling intimidated.",),
        accessible_record_selectors=("offering:aurora:app", "channel:instagram"),
        known_limitations=("Cannot access internal strategy, budget, or approval records.",),
        derivation_id="derivation:sw011:perspective",
    )
    frame = RelationshipFrame(
        frame_id="frame:aurora:app-de-instagram-acquisition",
        frame_type_id="world://ontology/brand/type/RelationshipFrame",
        context_id=context.context_id,
        role_bindings=(
            RoleBinding(role_id="offering", record_ids=("offering:aurora:app",)),
            RoleBinding(role_id="audience", record_ids=("audience:aurora:first-time-runners",)),
            RoleBinding(role_id="channel", record_ids=("channel:instagram",)),
            RoleBinding(role_id="market", value="DE"),
            RoleBinding(role_id="budget", value={"amount": 200000, "currency": "EUR"}),
        ),
        assertion_ids=("assertion:sw011:campaign-targeting",),
        status="proposed",
        evidence_link_ids=(evidence_support.link_id,),
        derivation_id="derivation:sw011:frame",
    )
    return FixtureWorld(
        "SW-011",
        "branch-perspective-state-frame",
        ("state_claim_separation", "branch_overlay", "perspective_non_interference", "nary_frame"),
        (
            context,
            state,
            evidence_support,
            evidence_qualifies,
            main,
            scenario,
            *deltas,
            perspective,
            frame,
            _evidence("evidence:sw011:analytics", "sw011"),
            _evidence("evidence:sw011:method", "sw011"),
        ),
    )


def all_fixture_worlds() -> tuple[FixtureWorld, ...]:
    return (
        intended_observed_brand(),
        repositioning_temporal(),
        shared_technology(),
        adaptive_representation(),
        market_positioning(),
        evidence_conflict(),
        bitemporal_reconstruction(),
        causal_guardrails(),
        shared_representation_products(),
        conditional_icp_to_asset_chain(),
        branch_perspective_state_frame(),
    )


def _assertions(world: FixtureWorld) -> tuple[Assertion, ...]:
    return tuple(item for item in world.objects if isinstance(item, Assertion))


def _entities(world: FixtureWorld) -> tuple[SemanticEntity, ...]:
    return tuple(item for item in world.objects if isinstance(item, SemanticEntity))


def _contexts(world: FixtureWorld) -> tuple[Context, ...]:
    return tuple(item for item in world.objects if isinstance(item, Context))


def snapshot_at(
    world: FixtureWorld, *, valid_at: datetime, known_at: datetime
) -> tuple[Assertion, ...]:
    """Replay assertions known at one time about propositions valid at another."""

    candidates: list[Assertion] = []
    for assertion in _assertions(world):
        if assertion.valid_time is None or assertion.known_time is None:
            continue
        valid_from = assertion.valid_time.from_time
        valid_until = assertion.valid_time.to_time
        known_from = assertion.known_time.from_time
        known_until = assertion.known_time.to_time
        if valid_from and valid_at < valid_from:
            continue
        if valid_until and valid_at >= valid_until:
            continue
        if known_from and known_at < known_from:
            continue
        if known_until and known_at >= known_until:
            continue
        candidates.append(assertion)
    return tuple(candidates)


def validate_fixture(world: FixtureWorld) -> None:
    """Run deterministic invariants for one synthetic world."""

    if len(set(world.object_ids)) != len(world.object_ids):
        raise AssertionError(f"{world.slug}: duplicate object identity")
    if world.slug == "intended-observed-brand":
        perspectives = {assertion.perspective for assertion in _assertions(world)}
        assert perspectives == {Perspective.INTENDED, Perspective.OBSERVED}
        assert all(assertion.evidence_refs for assertion in _assertions(world))
        assert len({assertion.context_id for assertion in _assertions(world)}) == 1
    elif world.slug == "repositioning-temporal":
        assertions = _assertions(world)
        assert len(assertions) == 2
        assert {assertion.status for assertion in assertions} == {
            AssertionStatus.SUPERSEDED,
            AssertionStatus.ACCEPTED,
        }
        assert assertions[0].valid_time and assertions[1].valid_time
        assert assertions[0].valid_time.to_time == assertions[1].valid_time.from_time
        assert assertions[0].assertion_id != assertions[1].assertion_id
        marker = next(item for item in world.objects if isinstance(item, StalenessMarker))
        assert marker.state is FreshnessState.POTENTIALLY_STALE
        assert marker.downstream_id == "artifact:aurora:primary-message"
    elif world.slug == "shared-technology":
        entities = _entities(world)
        shared = next(
            entity for entity in entities if entity.entity_id == "technology:vector-engine"
        )
        assert shared.identity_scope is IdentityScope.SHARED
        assertions = _assertions(world)
        assert {assertion.object_id for assertion in assertions} == {shared.entity_id}
        assert len({assertion.context_id for assertion in assertions}) == 2
    elif world.slug == "adaptive-representation":
        profiles = {
            item.profile_id: item
            for item in world.objects
            if isinstance(item, RepresentationProfile)
        }
        ordered = resolve_profile_order(profiles, "profile:aurora:campaign")
        assert [profile.profile_id for profile in ordered] == [
            "profile:aurora:shared",
            "profile:aurora:de-web",
            "profile:aurora:campaign",
        ]
        facets = {item.facet_id for item in world.objects if isinstance(item, RepresentationRule)}
        assert {"semantic", "verbal", "visual", "motion"} <= facets
        assert any(
            item.mode is BindingMode.ADAPTIVE
            for item in world.objects
            if isinstance(item, RepresentationBinding)
        )
    elif world.slug == "market-positioning":
        entities = {entity.entity_id: entity for entity in _entities(world)}
        assert {
            entities["org:northstar"].type_id,
            entities["portfolio:platforms"].type_id,
            entities["brand:aurora"].type_id,
            entities["offering:control-plane"].type_id,
        } == {TYPE["organization"], TYPE["portfolio"], TYPE["brand"], TYPE["offering"]}
        positioning = [
            assertion
            for assertion in _assertions(world)
            if assertion.predicate_id.endswith("positioned-as")
        ]
        assert len(positioning) == 2
        assert len({assertion.context_id for assertion in positioning}) == 2
    elif world.slug == "evidence-conflict":
        assertions = _assertions(world)
        claims = [
            assertion
            for assertion in assertions
            if assertion.predicate_id.endswith("associated-with")
        ]
        assert len(claims) == 2
        assert {claim.object_value for claim in claims} == {"reliable", "difficult"}
        assert all(claim.evidence_refs for claim in claims)
        assert any(assertion.predicate_id.endswith("conflicts-with") for assertion in assertions)
        assert AssertionStatus.ACCEPTED not in {claim.status for claim in claims}
    elif world.slug == "bitemporal-reconstruction":
        before = snapshot_at(
            world, valid_at=_dt("2025-02-01T00:00:00Z"), known_at=_dt("2025-02-01T00:00:00Z")
        )
        after = snapshot_at(
            world, valid_at=_dt("2025-02-01T00:00:00Z"), known_at=_dt("2025-04-01T00:00:00Z")
        )
        assert [assertion.object_value for assertion in before] == ["calm infrastructure"]
        assert [assertion.object_value for assertion in after] == ["observable infrastructure"]
        assert len(_assertions(world)) == 2
    elif world.slug == "causal-guardrails":
        assertions = _assertions(world)
        assert any(assertion.predicate_id.endswith("precedes") for assertion in assertions)
        hypotheses = [
            assertion for assertion in assertions if assertion.predicate_id.endswith("influences")
        ]
        assert len(hypotheses) == 2
        assert all(assertion.perspective is Perspective.HYPOTHESIZED for assertion in hypotheses)
        assert not any(
            assertion.predicate_id.endswith("causes")
            and assertion.status is AssertionStatus.ACCEPTED
            for assertion in assertions
        )
    elif world.slug == "shared-representation-products":
        bindings = [item for item in world.objects if isinstance(item, RepresentationBinding)]
        assert {binding.entity_id for binding in bindings} == {"brand:aurora"}
        rules = [
            item
            for item in world.objects
            if isinstance(item, RepresentationRule) and item.facet_id == "visual"
        ]
        assert (
            len(rules) == 2
            and rules[0].override_policy_id is None
            and rules[1].override_policy_id is None
        )
        evaluation = next(
            item for item in world.objects if isinstance(item, RepresentationEvaluation)
        )
        assert evaluation.compliance is ComplianceStatus.UNASSESSABLE
        assert "equal-authority-visual-rules" in evaluation.findings
    elif world.slug == "conditional-icp-to-asset-chain":
        assertions = _assertions(world)
        predicates = {assertion.predicate_id.rsplit("/", 1)[-1] for assertion in assertions}
        assert {"designed-for", "implements", "operationalizes", "governs"} <= predicates
        decision = next(item for item in world.objects if isinstance(item, DecisionRecord))
        assert decision.selected_option_id == "positioning:aurora:app:first-run"
        assert decision.status is DecisionStatus.ACCEPTED
        edges = [item for item in world.objects if isinstance(item, DependencyEdge)]
        assert len(edges) == 1
        assert edges[0].downstream_id == "asset:aurora:instagram:first-run"
        marker = next(item for item in world.objects if isinstance(item, StalenessMarker))
        assert marker.state is FreshnessState.POTENTIALLY_STALE
        assert "does not rewrite" in (marker.review_note or "")
        binding = next(item for item in world.objects if isinstance(item, RepresentationBinding))
        assert binding.entity_id == "asset:aurora:instagram:first-run"
        plan = next(item for item in world.objects if isinstance(item, FederationPlan))
        assert plan.status is FederationPlanStatus.HIT
        assert plan.primary_workspace_id == f"{WORKSPACE_ID}/offering/app"
        assert plan.supplemental_workspace_ids == (WORKSPACE_ID,)
        derivation = next(item for item in world.objects if isinstance(item, DerivationRecord))
        assert derivation.result is DerivationResult.PROPOSED
        validate_derivation_graph((derivation,), source_ids=frozenset(derivation.input_ids))
    elif world.slug == "branch-perspective-state-frame":
        state = next(item for item in world.objects if isinstance(item, StateSnapshot))
        assert state.source_assertion_ids == ("assertion:sw011:completion-measurement",)
        links = [item for item in world.objects if isinstance(item, EvidenceLink)]
        assert {link.role for link in links} == {EvidenceRole.SUPPORTS, EvidenceRole.QUALIFIES}
        branches = tuple(item for item in world.objects if isinstance(item, WorldBranch))
        deltas = tuple(item for item in world.objects if isinstance(item, BranchDelta))
        resolved = resolve_branch_records(
            branch_id="branch:aurora:confidence-first",
            branches=branches,
            deltas=deltas,
            base_record_ids=("positioning:aurora:performance-first", "offering:aurora:app"),
        )
        assert resolved == ("offering:aurora:app", "positioning:aurora:confidence-first")
        perspective = next(item for item in world.objects if isinstance(item, PerspectiveProfile))
        assert perspective.holder_id == "audience:aurora:first-time-runners"
        frame = next(item for item in world.objects if isinstance(item, RelationshipFrame))
        assert {binding.role_id for binding in frame.role_bindings} == {
            "offering",
            "audience",
            "channel",
            "market",
            "budget",
        }
    else:
        raise AssertionError(f"unknown fixture world: {world.slug}")


def validate_all_fixture_worlds() -> tuple[FixtureWorld, ...]:
    worlds = all_fixture_worlds()
    for world in worlds:
        validate_fixture(world)
    return worlds


__all__ = [
    "FixtureWorld",
    "WORKSPACE_ID",
    "all_fixture_worlds",
    "conditional_icp_to_asset_chain",
    "branch_perspective_state_frame",
    "snapshot_at",
    "validate_all_fixture_worlds",
    "validate_fixture",
]
