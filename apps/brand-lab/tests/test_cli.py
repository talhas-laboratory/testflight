from pathlib import Path

from testflight_brand_lab.cli import main
from testflight_brand_lab.explorer import build_graph_data, build_snapshot, simulate_context

ROOT = Path(__file__).resolve().parents[3]


def test_validate_command_reads_canonical_ontology(capsys) -> None:
    assert main(["validate", "--root", str(ROOT)]) == 0
    assert "valid: ontology=world://ontology/brand-system" in capsys.readouterr().out


def test_certify_command_checks_minimal_fixture(capsys) -> None:
    assert main(["certify", "--root", str(ROOT)]) == 0
    assert "certified: workspace=world://workspace/brand/example" in capsys.readouterr().out


def test_init_command_materializes_a_concrete_workspace(tmp_path) -> None:
    destination = tmp_path / "example"

    assert main(["init", "example", "--output", str(destination)]) == 0
    manifest = (destination / "WORKSPACE.yaml").read_text()

    assert "world://workspace/brand/example" in manifest
    assert "testflight_brand_example_p1" in manifest


def test_snapshot_compiles_canonical_nike_world(tmp_path, capsys) -> None:
    destination = tmp_path / "nike-world.json"

    assert (
        main(
            [
                "snapshot",
                "--root",
                str(ROOT),
                "--output",
                str(destination),
            ]
        )
        == 0
    )

    snapshot = destination.read_text()
    assert '"canonical": true' in snapshot
    assert '"id": "ENT-NIKE-OF-005"' in snapshot
    assert '"state_id": "STATE-NIKE-MEMBERSHIP-SERVICE-001"' in snapshot
    assert "diagnostics=0" in capsys.readouterr().out


def test_context_simulation_keeps_planning_and_retrieval_separate() -> None:
    snapshot = build_snapshot(ROOT / "workspaces/brand-nike-research")

    result = simulate_context(
        snapshot,
        {
            "stage": "brief",
            "prompt": "Create a membership landing page for young athletes.",
            "assetType": "landing page",
            "audience": "young athletes",
            "channel": "member app",
            "contextId": "CTX-NIKE-DIGITAL-MEMBERSHIP-CURRENT",
            "branchId": "BR-NIKE-MEMBER-DISCOVERY-LENS-001",
            "perspectiveIds": ["PERS-NIKE-MEMBER-PROSPECTIVE-001"],
        },
    )

    selected_ids = {entity["id"] for entity in result["planning"]["selected"]}
    assert "ENT-NIKE-ID-001" in selected_ids
    assert "ENT-NIKE-EX-003" in selected_ids
    assert "ENT-NIKE-OF-005" in selected_ids
    assert result["retrieval"]["status"] == "unavailable"
    assert result["retrieval"]["returned"] == []
    world_view = result["agentPacket"]["worldView"]
    assert world_view["status"] == "hit"
    assert world_view["branch_id"] == "BR-NIKE-MEMBER-DISCOVERY-LENS-001"
    assert world_view["perspective_ids"] == ["PERS-NIKE-MEMBER-PROSPECTIVE-001"]


def test_graph_data_preserves_held_relations_and_brand_root() -> None:
    snapshot = build_snapshot(ROOT / "workspaces/brand-hellobiotic-research")
    graph = build_graph_data(
        {"brand_id": snapshot["workspace"]["brandId"], "name": snapshot["workspace"]["label"]},
        snapshot["entities"],
        snapshot["relationships"],
    )

    assert graph["nodes"][0] == {
        "id": "world://brand/hellobiotic",
        "label": "Biotic / Hellobiotic Brand Research Sandbox",
        "kind": "brand-root",
        "entityType": "brand",
        "perspective": "structural",
        "status": "structural",
        "contextIds": [],
    }
    held = next(edge for edge in graph["edges"] if edge["id"] == "REL-HELLOBIOTIC-009")
    assert held["status"] == "held"
    assert held["epistemicStatus"] == "inferred"


def test_hellobiotic_visual_graph_is_separate_and_provenance_bound() -> None:
    snapshot = build_snapshot(ROOT / "workspaces/brand-hellobiotic-research")

    graph = snapshot["visualGraph"]
    assert graph["available"] is True
    assert all(node["id"].startswith("VLE-HB-") for node in graph["nodes"])
    principle = next(node for node in graph["nodes"] if node["id"] == "VLE-HB-PRINCIPLE-001")
    assert principle["status"] == "held"
    assert principle["epistemicStatus"] == "inferred"


def test_hellobiotic_copy_and_audience_graphs_keep_hypotheses_held() -> None:
    snapshot = build_snapshot(ROOT / "workspaces/brand-hellobiotic-research")

    copy_graph = snapshot["copyClaimsGraph"]
    audience_graph = snapshot["audienceGraph"]
    assert copy_graph["available"] is True
    assert audience_graph["available"] is True
    assert all(node["id"].startswith("CC-HB-") for node in copy_graph["nodes"])
    assert all(node["id"].startswith("AUD-HB-") for node in audience_graph["nodes"])
    assert (
        next(node for node in copy_graph["nodes"] if node["id"] == "CC-HB-MODULE-001")["status"]
        == "held"
    )
    assert (
        next(node for node in audience_graph["nodes"] if node["id"] == "AUD-HB-HYP-001")["status"]
        == "held"
    )
