from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / ".agents" / "skills" / "child-container-creator"
SCAFFOLD = SKILL_ROOT / "scripts" / "scaffold_child_container.py"
VALIDATE = SKILL_ROOT / "scripts" / "validate_child_container.py"


def scaffold_args(parent: Path) -> list[str]:
    return [
        sys.executable,
        str(SCAFFOLD),
        "--parent-dir",
        str(parent),
        "--slug",
        "visual-language",
        "--label",
        "Visual language",
        "--mission",
        "Resolve scoped visual direction",
        "--parent-workspace-id",
        "world://workspace/brand/example",
        "--route",
        "visual-language",
    ]


def test_scaffold_is_dry_run_by_default_and_apply_is_non_overwriting(tmp_path: Path) -> None:
    parent = tmp_path / "brand-example"
    parent.mkdir()
    dry_run = subprocess.run(scaffold_args(parent), check=True, capture_output=True, text=True)
    report = json.loads(dry_run.stdout)
    assert report["status"] == "dry_run"
    assert not (parent / "visual-language").exists()

    created = subprocess.run(
        [*scaffold_args(parent), "--apply"], check=True, capture_output=True, text=True
    )
    assert json.loads(created.stdout)["status"] == "created"
    child = parent / "visual-language"
    assert (child / "AGENT_INDEX.md").is_file()
    assert (child / "resource_registry.json").is_file()

    repeated = subprocess.run(
        [*scaffold_args(parent), "--apply"], check=False, capture_output=True, text=True
    )
    assert repeated.returncode != 0
    assert "refusing to overwrite" in repeated.stderr


def test_structure_passes_but_empty_child_cannot_be_certified(tmp_path: Path) -> None:
    parent = tmp_path / "brand-example"
    parent.mkdir()
    subprocess.run([*scaffold_args(parent), "--apply"], check=True, capture_output=True, text=True)
    child = parent / "visual-language"

    structural = subprocess.run(
        [sys.executable, str(VALIDATE), str(child)], check=True, capture_output=True, text=True
    )
    assert json.loads(structural.stdout)["status"] == "pass"

    certification = subprocess.run(
        [sys.executable, str(VALIDATE), str(child), "--certify"],
        check=False,
        capture_output=True,
        text=True,
    )
    report = json.loads(certification.stdout)
    assert certification.returncode != 0
    assert report["status"] == "fail"
    assert "certification requires at least one source resource" in report["errors"]


def test_repo_local_skill_catalog_is_valid() -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_skill_catalog.py")], check=True
    )
