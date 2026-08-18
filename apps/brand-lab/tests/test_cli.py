from pathlib import Path

from testflight_brand_lab.cli import main

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
