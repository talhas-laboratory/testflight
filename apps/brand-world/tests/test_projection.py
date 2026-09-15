from pathlib import Path

import pytest
from testflight_brand_world.projection import (
    SYSTEM_ORDER,
    build_record_dossier,
    build_world_projection,
)

ROOT = Path(__file__).resolve().parents[3]
WORKSPACE = ROOT / "workspaces" / "brand-hellobiotic-research"


def test_projection_starts_with_canonical_brand_systems() -> None:
    projection = build_world_projection(ROOT, WORKSPACE)

    assert tuple(system["id"] for system in projection["systems"]) == SYSTEM_ORDER
    assert tuple(system["label"] for system in projection["systems"]) == tuple(
        system.title() for system in SYSTEM_ORDER
    )
    assert all(system["recordCount"] >= 1 for system in projection["systems"])
    assert projection["meta"]["ontologyVersion"] == "1.0.0"


def test_projection_contains_every_root_entity_and_relation() -> None:
    projection = build_world_projection(ROOT, WORKSPACE)
    node_ids = {node["id"] for node in projection["nodes"]}
    edge_ids = {edge["id"] for edge in projection["edges"]}

    assert {
        "ENT-HB-ID-001",
        "ENT-HB-EX-001",
        "ENT-HB-OF-001",
        "ENT-HB-XP-001",
        "ENT-HB-PE-001",
        "ENT-HB-GV-001",
        "ENT-HB-EN-001",
        "ENT-HB-EV-001",
    }.issubset(node_ids)
    assert {f"REL-HELLOBIOTIC-{index:03d}" for index in range(1, 15)}.issubset(edge_ids)


def test_supplemental_records_remain_discoverable_inside_brand_systems() -> None:
    projection = build_world_projection(ROOT, WORKSPACE)
    node_by_id = {node["id"]: node for node in projection["nodes"]}

    assert node_by_id["CC-HB-VOICE-001"]["system"] == "expression"
    assert node_by_id["VLE-HB-PRODUCT-001"]["system"] == "offering"
    assert node_by_id["AUD-HB-HYP-001"]["system"] == "environment"
    assert node_by_id["AUD-HB-SIGNAL-005"]["system"] == "perception"


def test_every_rendered_relation_endpoint_resolves() -> None:
    projection = build_world_projection(ROOT, WORKSPACE)
    node_ids = {node["id"] for node in projection["nodes"]}

    assert projection["diagnostics"]["danglingRelationIds"] == []
    assert projection["diagnostics"]["missingEvidenceIds"] == []
    assert all(
        edge["source"] in node_ids and edge["target"] in node_ids for edge in projection["edges"]
    )


def test_record_dossier_separates_grounding_context_and_sources() -> None:
    dossier = build_record_dossier(ROOT, WORKSPACE, "ENT-HB-ID-001")

    assert dossier["grounding"]["assertion"].startswith("The public storefront presents")
    assert dossier["grounding"]["interpretation"].startswith(
        "This supports a proposed whole-body-care identity direction"
    )
    assert dossier["grounding"]["permittedUses"]
    assert dossier["grounding"]["constraints"]
    assert dossier["grounding"]["unknowns"]
    assert dossier["context"]["relations"]
    assert dossier["sources"][0]["evidence"][0]["id"] == "EVID-HB-001"


def test_record_dossier_discloses_full_text_policy_and_live_access() -> None:
    dossier = build_record_dossier(ROOT, WORKSPACE, "ENT-HB-OF-001")

    assert dossier["contentPolicy"]["full_text_storage"] == "prohibited"
    assert dossier["sources"][0]["fullText"]["stored"] is False
    assert dossier["sources"][0]["fullText"]["access"] == "live_source"
    assert dossier["sources"][0]["fullText"]["url"].startswith("https://")


def test_supplemental_claim_keeps_assertion_and_use_constraint_separate() -> None:
    dossier = build_record_dossier(ROOT, WORKSPACE, "CC-HB-CLAIM-003")

    assert dossier["grounding"]["assertion"].startswith("Biotic's public product page reports")
    assert "after verifying" in dossier["grounding"]["permittedUses"][0]
    assert "Do not generalize" in dossier["grounding"]["constraints"][0]
    assert dossier["sources"][0]["evidence"][0]["binding"] == "same_source_context"


def test_unknown_record_dossier_is_an_honest_no_hit() -> None:
    with pytest.raises(KeyError):
        build_record_dossier(ROOT, WORKSPACE, "missing-record")
