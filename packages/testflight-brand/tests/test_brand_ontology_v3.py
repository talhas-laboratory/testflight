from datetime import UTC, datetime
from pathlib import Path

import pytest
from testflight_brand import (
    BrandOntologyModule,
    BrandOntologyRelease,
    LegacyDisposition,
    LegacyMigrationLedger,
    LegacyRecordDisposition,
    load_brand_ontology_release,
)

ROOT = Path(__file__).resolve().parents[3]
NOW = datetime(2026, 9, 14, tzinfo=UTC)


def test_v3_brand_ontology_is_modular_and_projects_eight_systems_separately() -> None:
    release, sources = load_brand_ontology_release(ROOT, release="ontology-v3")

    assert release.id == "world://ontology/brand-world"
    assert release.version == "3.0.0-candidate"
    assert len(sources) == 8
    assert (
        release.relationship("world://ontology/brand-world/relation/governs-artifact").family
        == "manifestation"
    )
    assert (
        release.relationship("world://ontology/brand-world/relation/encounters-through").family
        == "experience"
    )


def test_legacy_migration_ledger_requires_one_complete_disposition_per_legacy_record() -> None:
    migrated = LegacyRecordDisposition(
        legacy_id="ENT-HB-ID-001",
        legacy_version="1.0.0",
        disposition=LegacyDisposition.MIGRATED,
        migration_rule_id="migration:identity-brand@1",
        input_hash="sha256:input",
        output_hash="sha256:output",
        target_ids=("entity:biotic",),
        rationale="Stable Brand identity maps to a v3 Entity.",
    )
    archived = LegacyRecordDisposition(
        legacy_id="projection:world-ring",
        legacy_version="1.0.0",
        disposition=LegacyDisposition.ARCHIVED_ONLY,
        migration_rule_id="migration:projection-archive@1",
        input_hash="sha256:projection",
        rationale="Legacy presentation payload is readable only and has no canonical equivalent.",
    )
    ledger = LegacyMigrationLedger(
        ledger_id="ledger:biotic-v3",
        workspace_id="world://workspace/brand/hellobiotic-research",
        snapshot_hash="sha256:snapshot",
        generated_at=NOW,
        entries=(migrated, archived),
    )

    assert ledger.covers(("ENT-HB-ID-001", "projection:world-ring"))
    with pytest.raises(ValueError, match="duplicate legacy IDs"):
        LegacyMigrationLedger(
            ledger_id="ledger:duplicate",
            workspace_id="world://workspace/brand/hellobiotic-research",
            snapshot_hash="sha256:snapshot",
            generated_at=NOW,
            entries=(migrated, migrated),
        )


def test_module_relationships_must_declare_cross_module_imports() -> None:
    identity = BrandOntologyModule.model_validate(
        {
            "module_id": "module:identity",
            "version": "3",
            "status": "candidate",
            "competency_questions": ["Can identity be modeled?"],
            "evidence_basis": ["proposal:test"],
            "entity_types": [
                {
                    "id": "type:brand",
                    "label": "Brand",
                    "definition": "An identity-bearing referent.",
                    "examples": ["Biotic"],
                    "counterexamples": ["A sentence"],
                }
            ],
        }
    )
    offering = BrandOntologyModule.model_validate(
        {
            "module_id": "module:offering",
            "version": "3",
            "status": "candidate",
            "competency_questions": ["Can an offering be modeled?"],
            "evidence_basis": ["proposal:test"],
            "entity_types": [
                {
                    "id": "type:offering",
                    "label": "Offering",
                    "definition": "A value-bearing offer.",
                    "examples": ["A deodorant"],
                    "counterexamples": ["A slogan"],
                }
            ],
            "relationship_types": [
                {
                    "id": "relation:offers",
                    "label": "offers",
                    "definition": "A Brand offers an Offering.",
                    "family": "offering",
                    "source_type_ids": ["type:brand"],
                    "target_type_ids": ["type:offering"],
                    "examples": ["A brand offers a product."],
                    "counterexamples": ["A product owns a brand."],
                }
            ],
        }
    )

    with pytest.raises(ValueError, match="crosses modules without imports"):
        BrandOntologyRelease(
            id="ontology:test",
            version="3",
            status="candidate",
            modules=(identity, offering),
        )
