import json
from pathlib import Path

from testflight_brand import (
    assess_migration,
    build_biotic_authority_review_proposal,
    build_biotic_public_research_migration,
    export_biotic_v3_review_bundle,
    inventory_legacy_brand_workspace,
)
from testflight_semantic import (
    DecisionStatus,
    WorldClaim,
    WorldEvidence,
    WorldRelation,
    WorldSource,
)

ROOT = Path(__file__).resolve().parents[3]


def test_biotic_migration_preserves_public_research_as_a_proposed_v3_branch() -> None:
    result = build_biotic_public_research_migration(ROOT)
    records = result.change_set.records

    assert result.change_set.branch_id == "public-research-v3"
    assert all(record.lifecycle_status.value == "proposed" for record in records)
    assert len([record for record in records if isinstance(record, WorldSource)]) == 5
    assert len([record for record in records if isinstance(record, WorldEvidence)]) == 5
    assert len([record for record in records if isinstance(record, WorldClaim)]) == 40
    assert any(
        isinstance(record, WorldRelation)
        and record.relation_type_id == "world://ontology/brand-world/relation/offers"
        for record in records
    )


def test_biotic_migration_disposes_every_legacy_record_without_inventing_relation_types() -> None:
    result = build_biotic_public_research_migration(ROOT)
    inventory = inventory_legacy_brand_workspace(
        ROOT, ROOT / "workspaces/brand-hellobiotic-research"
    )

    assert result.ledger.covers(inventory.record_ids)
    assert any(entry.disposition.value == "migrated" for entry in result.ledger.entries)
    assert not [
        entry for entry in result.ledger.entries if entry.disposition.value == "quarantined"
    ]
    assert any(entry.disposition.value == "archived_only" for entry in result.ledger.entries)


def test_biotic_migration_report_exposes_coverage_and_missing_information() -> None:
    result = build_biotic_public_research_migration(ROOT)
    report = assess_migration(result.change_set, contexts=result.contexts, ledger=result.ledger)

    assert report.record_count == 56
    assert report.disposition_coverage == 1.0
    assert report.evidence_coverage == 1.0
    assert not report.dangling_record_refs
    assert not report.dangling_evidence_refs
    assert not report.dangling_source_refs
    assert not report.dangling_context_refs
    assert not report.dangling_provenance_refs
    assert not report.relation_integrity_errors
    assert not report.unsupported_promotion_ids
    assert report.missing_information
    assert report.contradiction_ids
    assert report.ready_for_authority_review


def test_biotic_v3_records_use_clean_semantic_identifiers() -> None:
    result = build_biotic_public_research_migration(ROOT)

    assert not [
        record
        for record in result.change_set.records
        if "legacy" in record.id
        or "legacy" in record.type_id
        or (isinstance(record, WorldClaim) and "legacy" in record.predicate_id)
    ]
    assert not [
        target
        for entry in result.ledger.entries
        for target in entry.target_ids
        if "legacy" in target
    ]


def test_authority_review_package_cannot_be_mistaken_for_approval() -> None:
    migration = build_biotic_public_research_migration(ROOT)
    review = build_biotic_authority_review_proposal(migration)

    assert review.source_branch_id == "public-research-v3"
    assert review.target_branch_id == "client-approved-v3"
    assert review.review_status == "awaiting_authorized_human"
    assert not review.records_are_accepted
    assert review.decision_template.status == DecisionStatus.PROPOSED
    assert review.decision_template.selected_alternative_id is None
    assert review.decision_template.authority_ref is None


def test_review_bundle_is_deterministic_and_retains_exact_local_source_text(tmp_path: Path) -> None:
    first = export_biotic_v3_review_bundle(ROOT, tmp_path)
    first_contents = {path.name: path.read_bytes() for path in first}
    second = export_biotic_v3_review_bundle(ROOT, tmp_path)

    assert first_contents == {path.name: path.read_bytes() for path in second}
    snapshot = json.loads((tmp_path / "immutable-legacy-source-snapshot.json").read_text())
    source_text = (
        ROOT / "workspaces/brand-hellobiotic-research/artifacts/entity-inventory.yaml"
    ).read_text()
    entity_snapshot = next(
        artifact
        for artifact in snapshot["artifacts"]
        if artifact["path"] == "artifacts/entity-inventory.yaml"
    )
    assert entity_snapshot["content"] == source_text
    assert '"accepted_records": 0' in (tmp_path / "bundle-manifest.json").read_text()
