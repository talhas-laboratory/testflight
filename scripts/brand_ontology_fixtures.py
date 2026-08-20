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
    ChangeType,
    ComplianceStatus,
    Context,
    Deontic,
    DependencyEdge,
    DependencyEffect,
    DependencyRule,
    EntityLifecycle,
    Event,
    EvidenceEnvelope,
    FreshnessState,
    FreshnessStatus,
    IdentityScope,
    Perspective,
    RepresentationBinding,
    RepresentationEvaluation,
    RepresentationProfile,
    RepresentationRule,
    SemanticEntity,
    StalenessMarker,
    TemporalInterval,
    ValidationMethod,
    resolve_profile_order,
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
                "assertion_id",
                "event_id",
                "source_id",
                "binding_id",
                "profile_id",
                "edge_id",
                "marker_id",
                "manifestation_id",
                "context_id",
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
    "snapshot_at",
    "validate_all_fixture_worlds",
    "validate_fixture",
]
