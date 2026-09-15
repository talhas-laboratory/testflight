"""Deterministic, proposal-only migration for Biotic's bounded public research.

The migration creates clean v3 records and a complete lineage ledger. Legacy identifiers occur
only in the ledger and explicit provenance locators; they never become v3 semantic type or
predicate identifiers. Nothing in this module approves or promotes Brand meaning.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import yaml
from testflight_semantic import (
    BoundSemantics,
    ClaimKind,
    Context,
    EventParticipant,
    RelationParticipant,
    SourceContentPolicy,
    TemporalInterval,
    TimePrecision,
    WorldClaim,
    WorldEntity,
    WorldEvent,
    WorldEvidence,
    WorldRelation,
    WorldSource,
    WorldState,
)
from testflight_world import WorldChangeSet

from .legacy_inventory import LegacyWorldInventory, inventory_legacy_brand_workspace
from .migration import LegacyDisposition, LegacyMigrationLedger, LegacyRecordDisposition

_BRANCH = "public-research-v3"
_MIGRATOR = "operator:biotic-public-research-migration@2"
_MIGRATION_RULE = "migration:biotic-public-research-v3@2"
_CREATED_AT = datetime(2026, 8, 31, tzinfo=UTC)
_BRAND_ID = "entity:biotic"
_OFFERING_ID = "entity:biotic:offering:brightening-probiotic-deodorant"
_AUDIENCE_ID = "entity:biotic:audience:natural-deodorant-evaluators"

_SOURCE_IDS = {
    "SRC-HB-001": "source:biotic:home-page",
    "SRC-HB-002": "source:biotic:brightening-probiotic-deodorant-page",
    "SRC-HB-003": "source:biotic:founder-story",
    "SRC-HB-004": "source:biotic:faq",
    "SRC-HB-005": "source:biotic:daily-sunshine-page",
}
_EVIDENCE_IDS = {
    "EVID-HB-001": "evidence:biotic:home-page-framing",
    "EVID-HB-002": "evidence:biotic:deodorant-product-description",
    "EVID-HB-003": "evidence:biotic:founder-story",
    "EVID-HB-004": "evidence:biotic:faq-product-boundaries",
    "EVID-HB-005": "evidence:biotic:daily-sunshine-description",
}
_EVIDENCE_LOCATORS = {
    "EVID-HB-001": "#bounded-excerpt-home-framing",
    "EVID-HB-002": "#bounded-excerpt-deodorant-description",
    "EVID-HB-003": "#bounded-excerpt-founder-story",
    "EVID-HB-004": "#bounded-excerpt-product-boundaries",
    "EVID-HB-005": "#bounded-excerpt-daily-sunshine-description",
}
_EVIDENCE_FINDING_SLUGS = {
    "EVID-HB-001": "home-page-framing",
    "EVID-HB-002": "deodorant-product-description",
    "EVID-HB-003": "founder-story",
    "EVID-HB-004": "faq-product-boundaries",
    "EVID-HB-005": "daily-sunshine-description",
}
_ENTITY_RECORD_IDS = {
    "ENT-HB-ID-001": "claim:biotic:public-whole-body-care-framing",
    "ENT-HB-EX-001": "claim:biotic:public-verbal-expression-pattern",
    "ENT-HB-OF-001": _OFFERING_ID,
    "ENT-HB-XP-001": "claim:biotic:public-product-education-journey",
    "ENT-HB-PE-001": "claim:biotic:public-testimonial-layer",
    "ENT-HB-GV-001": "claim:biotic:founder-reported-stewardship",
    "ENT-HB-EN-001": _AUDIENCE_ID,
    "ENT-HB-EV-001": "event:biotic:public-product-ecosystem-snapshot:2026-08-31",
}
_RELATION_SLUGS = {
    "REL-HELLOBIOTIC-001": "brand-public-framing",
    "REL-HELLOBIOTIC-002": "brand-public-expression",
    "REL-HELLOBIOTIC-003": "brand-offers-brightening-deodorant",
    "REL-HELLOBIOTIC-004": "offering-public-education-journey",
    "REL-HELLOBIOTIC-005": "brand-audience-perception-frame",
    "REL-HELLOBIOTIC-006": "brand-founder-stewardship-signal",
    "REL-HELLOBIOTIC-007": "brand-natural-deodorant-environment",
    "REL-HELLOBIOTIC-008": "brand-public-portfolio-evolution",
    "REL-HELLOBIOTIC-009": "offering-testimonial-perception-hypothesis",
    "REL-HELLOBIOTIC-010": "portfolio-snapshot-identity-update",
    "REL-HELLOBIOTIC-011": "testimonial-identity-feedback-hypothesis",
    "REL-HELLOBIOTIC-012": "offering-supports-public-framing",
    "REL-HELLOBIOTIC-013": "offering-testimonial-contradiction-hypothesis",
    "REL-HELLOBIOTIC-014": "offering-audience-influence-hypothesis",
}


class BioticMigrationResult:
    """The proposed v3 branch, contexts, and complete legacy disposition ledger."""

    def __init__(
        self,
        change_set: WorldChangeSet,
        contexts: tuple[Context, ...],
        ledger: LegacyMigrationLedger,
    ) -> None:
        self.change_set = change_set
        self.contexts = contexts
        self.ledger = ledger


def build_biotic_public_research_migration(repository_root: Path) -> BioticMigrationResult:
    """Compile bounded public research without promoting it to internal Brand truth.

    Every legacy record receives a deterministic migrated or archived-only disposition. Semantic
    concepts are mapped into the narrowest v3 kind; legacy presentation/routing overlays remain in
    the immutable source snapshot instead of being flattened into canonical records.
    """

    repository_root = repository_root.resolve()
    workspace_path = repository_root / "workspaces/brand-hellobiotic-research"
    inventory = inventory_legacy_brand_workspace(repository_root, workspace_path)
    entities = _yaml(workspace_path / "artifacts/entity-inventory.yaml")["entities"]
    evidence = _yaml(workspace_path / "artifacts/evidence-notes.yaml")["notes"]
    sources = _yaml(workspace_path / "artifacts/source-catalog.yaml")["sources"]
    relations = _yaml(workspace_path / "artifacts/relationship-inventory.yaml")["relationships"]
    context_profiles = _yaml(workspace_path / "artifacts/context-profiles.yaml")["contexts"]
    world_modeling = _yaml(workspace_path / "artifacts/world-modeling.yaml")

    contexts = tuple(_context(profile) for profile in context_profiles)
    context_targets = {
        profile["id"]: context.context_id
        for profile, context in zip(context_profiles, contexts, strict=True)
    }
    records: list[object] = [_brand_entity(inventory.workspace_id)]
    targets: dict[str, tuple[str, ...]] = {}

    for source in sources:
        source_id = _SOURCE_IDS[source["id"]]
        record = WorldSource(
            id=source_id,
            type_id=f"world://semantic/source/{source['source_type'].replace('_', '-')}",
            workspace_id=inventory.workspace_id,
            module_id="world://ontology/module/brand-world/environment",
            branch_id=_BRANCH,
            created_at=_CREATED_AT,
            created_by=_MIGRATOR,
            locator=source["canonical_url"],
            title=source["title"],
            content_policy=SourceContentPolicy.BOUNDED_EXCERPT,
            captured_at=_CREATED_AT,
            content_hash=_hash_mapping(source),
            derivation_ref=_MIGRATOR,
        )
        records.append(record)
        targets[source["id"]] = (record.id,)

    for note in evidence:
        evidence_id = _EVIDENCE_IDS[note["id"]]
        record = WorldEvidence(
            id=evidence_id,
            type_id="world://semantic/evidence/bounded-excerpt",
            workspace_id=inventory.workspace_id,
            module_id="world://ontology/module/brand-world/environment",
            branch_id=_BRANCH,
            created_at=_CREATED_AT,
            created_by=_MIGRATOR,
            source_id=_SOURCE_IDS[note["source_id"]],
            locator=_EVIDENCE_LOCATORS[note["id"]],
            excerpt=note["evidence_excerpt"],
            limitations=tuple(note.get("limitations", ())),
            integrity_hash=_hash_mapping(note),
            context_refs=_context_refs(note, context_targets),
            provenance_refs=(_SOURCE_IDS[note["source_id"]],),
            derivation_ref=_MIGRATOR,
        )
        finding_claims = tuple(
            _evidence_finding_claim(
                note,
                finding,
                index,
                inventory.workspace_id,
                evidence_id,
                context_targets,
            )
            for index, finding in enumerate(note.get("paraphrased_findings", ()), start=1)
        )
        records.extend((record, *finding_claims))
        targets[note["id"]] = (record.id, *(claim.id for claim in finding_claims))

    for legacy in entities:
        mapped_records, additional_targets = _entity_records(
            legacy, inventory.workspace_id, context_targets
        )
        records.extend(mapped_records)
        targets[legacy["id"]] = additional_targets

    for legacy in relations:
        relationship_records = _relationship_records(
            legacy, inventory.workspace_id, targets, context_targets
        )
        records.extend(relationship_records)
        targets[legacy["id"]] = tuple(record.id for record in relationship_records)

    for profile, context in zip(context_profiles, contexts, strict=True):
        targets[profile["id"]] = (context.context_id,)

    for legacy in world_modeling["states"]:
        record = WorldState(
            id="state:biotic:public-brand-core:2026-08-31",
            type_id=legacy["state_type_id"],
            workspace_id=inventory.workspace_id,
            module_id="world://ontology/module/brand-world/evolution-learning",
            branch_id=_BRANCH,
            created_at=_CREATED_AT,
            created_by=_MIGRATOR,
            subject_ids=tuple(_record_target(targets, item) for item in legacy["subject_ids"]),
            state_value=yaml.safe_dump(legacy["values"], sort_keys=True).strip(),
            state_schema_id=legacy["state_type_id"],
            described_by_claim_ids=tuple(
                _record_target(targets, item) for item in legacy["source_assertion_ids"]
            ),
            context_refs=(context_targets[legacy["context_id"]],),
            provenance_refs=tuple(
                _EVIDENCE_IDS[item] for item in _state_evidence_ids(legacy, world_modeling)
            ),
            derivation_ref=_MIGRATOR,
        )
        records.append(record)
        targets[legacy["state_id"]] = (record.id,)

    change_set = WorldChangeSet(
        proposal_id="proposal:biotic-public-research-v3-migration",
        workspace_id=inventory.workspace_id,
        branch_id=_BRANCH,
        proposed_by=_MIGRATOR,
        proposed_at=_CREATED_AT,
        records=tuple(records),
        rationale=(
            "Deterministic migration of bounded Biotic public research. It preserves first-party "
            "evidence, interpretations, context, provenance, and uncertainty as proposed v3 "
            "records; legacy presentation structures remain immutable audit material."
        ),
    )
    ledger = _ledger(inventory, targets, change_set, contexts)
    return BioticMigrationResult(change_set=change_set, contexts=contexts, ledger=ledger)


def _brand_entity(workspace_id: str) -> WorldEntity:
    return WorldEntity(
        id=_BRAND_ID,
        type_id="world://ontology/brand-world/type/Brand",
        workspace_id=workspace_id,
        module_id="world://ontology/module/brand-world/identity",
        branch_id=_BRANCH,
        created_at=_CREATED_AT,
        created_by=_MIGRATOR,
        canonical_label="Biotic / Hellobiotic",
        aliases=("Biotic", "Hellobiotic"),
        definition="The identity-bearing Brand referent scoped to bounded public research.",
        derivation_ref=_MIGRATOR,
    )


def _entity_records(
    legacy: dict[str, Any], workspace_id: str, context_targets: dict[str, str]
) -> tuple[tuple[object, ...], tuple[str, ...]]:
    evidence_ids = tuple(_EVIDENCE_IDS[item] for item in legacy.get("evidence_ids", ()))
    primary_id = _ENTITY_RECORD_IDS[legacy["id"]]
    assertion_id = (
        f"claim:biotic:offering:{_slug(legacy['label'])}:public-description"
        if legacy["entity_type"] == "offering"
        else f"{primary_id}:assertion"
        if legacy["entity_type"] in {"environment", "event"}
        else primary_id
    )
    assertion = WorldClaim(
        id=assertion_id,
        type_id="world://semantic/claim/public-research",
        workspace_id=workspace_id,
        module_id=_module_for(legacy["entity_type"]),
        branch_id=_BRANCH,
        created_at=_CREATED_AT,
        created_by=_MIGRATOR,
        claim_kind=(
            ClaimKind.INTERPRETATION
            if legacy.get("epistemic_status") == "inferred"
            else ClaimKind.FACTUAL_ASSERTION
        ),
        subject_id=(
            primary_id if legacy["entity_type"] in {"offering", "environment"} else _BRAND_ID
        ),
        predicate_id=_predicate_for_entity(legacy["entity_type"]),
        object_value=legacy["assertion"],
        perspective_id=_perspective_id(legacy.get("perspective")),
        evidence_ids=evidence_ids,
        limitations=_typed_limitations(legacy),
        context_refs=_context_refs(legacy, context_targets),
        provenance_refs=evidence_ids,
        derivation_ref=_MIGRATOR,
    )
    interpretation = WorldClaim(
        id=f"claim:biotic:interpretation:{_slug(legacy['label'])}",
        type_id="world://semantic/claim/public-research-interpretation",
        workspace_id=workspace_id,
        module_id=_module_for(legacy["entity_type"]),
        branch_id=_BRANCH,
        created_at=_CREATED_AT,
        created_by=_MIGRATOR,
        claim_kind=ClaimKind.INTERPRETATION,
        subject_id=assertion.id,
        predicate_id="world://semantic/predicate/interpreted-as",
        object_value=legacy["interpretation"],
        perspective_id="perspective:public-researcher",
        evidence_ids=evidence_ids,
        limitations=_typed_limitations(legacy),
        context_refs=_context_refs(legacy, context_targets),
        provenance_refs=(assertion.id, *evidence_ids),
        derivation_ref=_MIGRATOR,
    )
    referent: WorldEntity | WorldEvent | None = None
    if legacy["entity_type"] == "offering":
        referent = WorldEntity(
            id=primary_id,
            type_id="world://ontology/brand-world/type/Offering",
            workspace_id=workspace_id,
            module_id="world://ontology/module/brand-world/offering",
            branch_id=_BRANCH,
            created_at=_CREATED_AT,
            created_by=_MIGRATOR,
            canonical_label=legacy["label"],
            definition=legacy["description"],
            context_refs=_context_refs(legacy, context_targets),
            provenance_refs=evidence_ids,
            derivation_ref=_MIGRATOR,
        )
    elif legacy["entity_type"] == "environment":
        referent = WorldEntity(
            id=primary_id,
            type_id="world://ontology/brand-world/type/Audience",
            workspace_id=workspace_id,
            module_id="world://ontology/module/brand-world/relationships",
            branch_id=_BRANCH,
            created_at=_CREATED_AT,
            created_by=_MIGRATOR,
            canonical_label=legacy["label"],
            definition=legacy["description"],
            context_refs=_context_refs(legacy, context_targets),
            provenance_refs=evidence_ids,
            derivation_ref=_MIGRATOR,
        )
    elif legacy["entity_type"] == "event":
        referent = WorldEvent(
            id=primary_id,
            type_id="world://semantic/event/public-portfolio-snapshot",
            workspace_id=workspace_id,
            module_id="world://ontology/module/brand-world/evolution-learning",
            branch_id=_BRANCH,
            created_at=_CREATED_AT,
            created_by=_MIGRATOR,
            event_type_id="world://semantic/event/public-portfolio-snapshot",
            participants=(EventParticipant(role_id="brand", entity_id=_BRAND_ID),),
            occurred_at=_research_cutoff_interval(),
            evidence_ids=evidence_ids,
            context_refs=_context_refs(legacy, context_targets),
            provenance_refs=evidence_ids,
            derivation_ref=_MIGRATOR,
        )
    if referent:
        return (referent, assertion, interpretation), (referent.id, assertion.id, interpretation.id)
    return (assertion, interpretation), (assertion.id, interpretation.id)


def _evidence_finding_claim(
    note: dict[str, Any],
    finding: str,
    index: int,
    workspace_id: str,
    evidence_id: str,
    context_targets: dict[str, str],
) -> WorldClaim:
    return WorldClaim(
        id=f"claim:biotic:evidence-finding:{_EVIDENCE_FINDING_SLUGS[note['id']]}:{index}",
        type_id="world://semantic/claim/source-paraphrase",
        workspace_id=workspace_id,
        module_id="world://ontology/module/brand-world/environment",
        branch_id=_BRANCH,
        created_at=_CREATED_AT,
        created_by=_MIGRATOR,
        claim_kind=ClaimKind.INTERPRETATION,
        subject_id=_BRAND_ID,
        predicate_id="world://semantic/predicate/source-reports",
        object_value=finding,
        perspective_id=_perspective_id(note.get("perspective")),
        evidence_ids=(evidence_id,),
        limitations=tuple(note.get("limitations", ())),
        context_refs=_context_refs(note, context_targets),
        provenance_refs=(evidence_id,),
        derivation_ref=_MIGRATOR,
    )


def _ledger(
    inventory: LegacyWorldInventory,
    targets: dict[str, tuple[str, ...]],
    change_set: WorldChangeSet,
    contexts: tuple[Context, ...],
) -> LegacyMigrationLedger:
    output_by_id = {record.id: record.model_dump(mode="json") for record in change_set.records} | {
        context.context_id: context.model_dump(mode="json") for context in contexts
    }
    entries = []
    for record in inventory.records:
        mapped = targets.get(record.legacy_id)
        if mapped:
            entries.append(
                LegacyRecordDisposition(
                    legacy_id=record.legacy_id,
                    legacy_version="1.0.0",
                    disposition=LegacyDisposition.MIGRATED,
                    migration_rule_id=_MIGRATION_RULE,
                    input_hash=record.input_hash,
                    output_hash=_hash_mapping([output_by_id[item] for item in mapped]),
                    target_ids=mapped,
                    rationale="Mapped by a deterministic, source-preserving public-research rule.",
                )
            )
        elif record.record_group in {
            "branches",
            "evidence_links",
            "perspectives",
            "relationship_frames",
        }:
            entries.append(
                LegacyRecordDisposition(
                    legacy_id=record.legacy_id,
                    legacy_version="1.0.0",
                    disposition=LegacyDisposition.ARCHIVED_ONLY,
                    migration_rule_id=_MIGRATION_RULE,
                    input_hash=record.input_hash,
                    rationale=(
                        "Legacy presentation or routing structure is retained verbatim in the "
                        "immutable source snapshot; it has no canonical v3 semantic equivalent."
                    ),
                )
            )
        else:
            raise ValueError(f"unclassified legacy record: {record.legacy_id}")
    return LegacyMigrationLedger(
        ledger_id="ledger:biotic-public-research-v3",
        workspace_id=inventory.workspace_id,
        snapshot_hash=inventory.snapshot_hash,
        generated_at=_CREATED_AT,
        entries=tuple(entries),
    )


def _module_for(entity_type: str) -> str:
    return {
        "identity": "world://ontology/module/brand-world/identity",
        "expression": "world://ontology/module/brand-world/expression-manifestation",
        "offering": "world://ontology/module/brand-world/offering",
        "experience": "world://ontology/module/brand-world/relationships",
        "perception": "world://ontology/module/brand-world/relationships",
        "governance": "world://ontology/module/brand-world/governance-decisions",
        "environment": "world://ontology/module/brand-world/relationships",
        "event": "world://ontology/module/brand-world/evolution-learning",
    }[entity_type]


def _predicate_for_entity(entity_type: str) -> str:
    return {
        "identity": "world://ontology/brand-world/predicate/public-identity-framing",
        "expression": "world://ontology/brand-world/predicate/uses-expression-pattern",
        "offering": "world://ontology/brand-world/predicate/public-offering-description",
        "experience": "world://ontology/brand-world/predicate/public-journey-observation",
        "perception": "world://ontology/brand-world/predicate/public-perception-observation",
        "governance": "world://ontology/brand-world/predicate/public-stewardship-signal",
        "environment": "world://ontology/brand-world/predicate/public-audience-hypothesis",
        "event": "world://ontology/brand-world/predicate/public-portfolio-snapshot",
    }[entity_type]


def _relationship_records(
    legacy: dict[str, Any],
    workspace_id: str,
    targets: dict[str, tuple[str, ...]],
    context_targets: dict[str, str],
) -> tuple[WorldRelation | WorldClaim, ...]:
    evidence_ids = tuple(_EVIDENCE_IDS[item] for item in legacy.get("evidence_ids", ()))
    relation_type_id = (
        f"world://ontology/brand-world/relation/{legacy['relationship_type'].replace('_', '-')}"
    )
    if legacy["relationship_type"] == "offers":
        relation = WorldRelation(
            id=f"relation:biotic:{_RELATION_SLUGS[legacy['id']]}",
            type_id="world://ontology/brand-world/relation/offers",
            workspace_id=workspace_id,
            module_id="world://ontology/module/brand-world/offering",
            branch_id=_BRANCH,
            created_at=_CREATED_AT,
            created_by=_MIGRATOR,
            relation_type_id="world://ontology/brand-world/relation/offers",
            participants=(
                RelationParticipant(
                    role_id="brand", record_id=_record_target(targets, legacy["source_id"])
                ),
                RelationParticipant(
                    role_id="offering", record_id=_record_target(targets, legacy["target_id"])
                ),
            ),
            evidence_ids=evidence_ids,
            context_refs=_context_refs(legacy, context_targets),
            provenance_refs=evidence_ids,
            derivation_ref=_MIGRATOR,
        )
        assertion = WorldClaim(
            id=f"claim:biotic:relation:{_RELATION_SLUGS[legacy['id']]}",
            type_id="world://semantic/claim/relation-proposition",
            workspace_id=workspace_id,
            module_id="world://ontology/module/brand-world/offering",
            branch_id=_BRANCH,
            created_at=_CREATED_AT,
            created_by=_MIGRATOR,
            claim_kind=ClaimKind.FACTUAL_ASSERTION,
            subject_id=_record_target(targets, legacy["source_id"]),
            predicate_id=relation_type_id,
            object_id=_record_target(targets, legacy["target_id"]),
            perspective_id=_perspective_id(legacy.get("perspective")),
            evidence_ids=evidence_ids,
            context_refs=_context_refs(legacy, context_targets),
            provenance_refs=(relation.id, *evidence_ids),
            derivation_ref=_MIGRATOR,
        )
        return (assertion, relation)
    limitations = tuple(legacy.get("limitations", ())) + (
        (f"Review state: {legacy['status']}",)
        if legacy.get("status") not in {None, "proposed"}
        else ()
    )
    return (
        WorldClaim(
            id=f"claim:biotic:relation:{_RELATION_SLUGS[legacy['id']]}",
            type_id="world://semantic/claim/relation-proposition",
            workspace_id=workspace_id,
            module_id="world://ontology/module/brand-world/evolution-learning",
            branch_id=_BRANCH,
            created_at=_CREATED_AT,
            created_by=_MIGRATOR,
            claim_kind=(
                ClaimKind.HYPOTHESIS
                if legacy.get("epistemic_status") == "inferred"
                else ClaimKind.FACTUAL_ASSERTION
            ),
            subject_id=_record_target(targets, legacy["source_id"]),
            predicate_id=relation_type_id,
            object_id=_record_target(targets, legacy["target_id"]),
            perspective_id=_perspective_id(legacy.get("perspective")),
            evidence_ids=evidence_ids,
            limitations=limitations,
            context_refs=_context_refs(legacy, context_targets),
            provenance_refs=evidence_ids,
            derivation_ref=_MIGRATOR,
        ),
    )


def _record_target(targets: dict[str, tuple[str, ...]], legacy_id: str) -> str:
    if legacy_id == "world://brand/hellobiotic":
        return _BRAND_ID
    return targets[legacy_id][0]


def _context(profile: dict[str, Any]) -> Context:
    valid_time = profile.get("valid_time", {})
    through = valid_time.get("through") if isinstance(valid_time, dict) else None
    interval = None
    if through:
        through_date = datetime.fromisoformat(str(through)).replace(tzinfo=UTC) + timedelta(days=1)
        interval = TemporalInterval(
            to_time=through_date,
            from_semantics=BoundSemantics.UNKNOWN,
            precision=TimePrecision.DAY,
        )
    return Context(
        brand_id=_BRAND_ID,
        offering_id=_OFFERING_ID,
        audience_ids=(_AUDIENCE_ID,),
        channel_ids=tuple(profile.get("channel_ids", ())),
        artifact_type_ids=tuple(profile.get("artifact_type_ids", ())),
        campaign_or_occasion_ids=tuple(profile.get("campaign_or_occasion_ids", ())),
        branch_id=_BRANCH,
        valid_time=interval,
        dimensions={
            "geography": profile.get("geography"),
            "perspective_scope": profile.get("perspective_scope", []),
            "purpose": profile.get("purpose"),
            "source_context_lineage": profile["id"],
        },
    )


def _context_refs(value: dict[str, Any], context_targets: dict[str, str]) -> tuple[str, ...]:
    return tuple(context_targets[item] for item in value.get("context_ids", ()))


def _typed_limitations(value: dict[str, Any]) -> tuple[str, ...]:
    return (
        tuple(value.get("limitations", ()))
        + tuple(f"Constraint: {item}" for item in value.get("constraints", ()))
        + tuple(f"Unknown: {item}" for item in value.get("unknowns", ()))
        + tuple(f"Permitted-use guidance: {item}" for item in value.get("permitted_uses", ()))
    )


def _perspective_id(value: object) -> str:
    return {
        "intended": "perspective:biotic-public-self-description",
        "reported": "perspective:public-research-report",
        "observed": "perspective:public-research-observation",
        "inferred": "perspective:public-researcher-inference",
    }.get(str(value), "perspective:public-research-report")


def _state_evidence_ids(state: dict[str, Any], world_modeling: dict[str, Any]) -> tuple[str, ...]:
    links = {
        item["link_id"]: item["evidence_id"] for item in world_modeling.get("evidence_links", ())
    }
    return tuple(links[item] for item in state.get("evidence_link_ids", ()) if item in links)


def _research_cutoff_interval() -> TemporalInterval:
    return TemporalInterval(
        from_time=_CREATED_AT,
        to_time=_CREATED_AT + timedelta(days=1),
        precision=TimePrecision.DAY,
    )


def _slug(value: str) -> str:
    normalized = "".join(character.lower() if character.isalnum() else " " for character in value)
    return "-".join(normalized.split())


def _yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"expected mapping: {path}")
    return value


def _hash_mapping(value: Any) -> str:
    return f"sha256:{hashlib.sha256(yaml.safe_dump(value, sort_keys=True).encode()).hexdigest()}"


__all__ = ["BioticMigrationResult", "build_biotic_public_research_migration"]
