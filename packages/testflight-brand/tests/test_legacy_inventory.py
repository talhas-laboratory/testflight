from pathlib import Path

from testflight_brand import inventory_legacy_brand_workspace

ROOT = Path(__file__).resolve().parents[3]
BIOTIC = ROOT / "workspaces/brand-hellobiotic-research"


def test_biotic_legacy_inventory_is_hash_bound_and_read_only() -> None:
    inventory = inventory_legacy_brand_workspace(ROOT, BIOTIC)

    assert inventory.workspace_id == "world://workspace/brand/hellobiotic-research"
    assert inventory.legacy_ontology_versions == ("1.0.0", "2.0.0-candidate")
    assert len(inventory.artifacts) == 6
    assert {record.legacy_id for record in inventory.records} >= {
        "ENT-HB-ID-001",
        "REL-HELLOBIOTIC-001",
        "EVID-HB-001",
        "CTX-HELLOBIOTIC-DEODORANT-CURRENT",
    }
    assert "sha256:" in inventory.snapshot_hash
    relationship = next(
        record for record in inventory.records if record.legacy_id == "REL-HELLOBIOTIC-001"
    )
    assert relationship.endpoint_ids == ("world://brand/hellobiotic", "ENT-HB-ID-001")
    assert any(
        consumer.path == "workspaces/brand-hellobiotic-research/WORKSPACE.yaml"
        for consumer in inventory.consumers
    )
