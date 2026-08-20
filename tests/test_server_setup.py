from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_cognee_setup_probe_passes_repository_root_to_brand_loader() -> None:
    script = (REPO_ROOT / "scripts/setup_server_cognee.sh").read_text()

    assert "load_brand_ontology(Path.cwd())" in script
