from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.validate_concrete_brand_workspace import validate_workspace  # noqa: E402


def test_nike_research_workspace_is_complete_and_isolated() -> None:
    result = validate_workspace(ROOT, Path("workspaces/brand-nike-research"))

    assert result["status"] == "pass"
    assert result["workspace_id"] == "world://workspace/brand/nike-research"
    assert result["entity_count"] == 75
    assert result["relationship_count"] == 42
    assert result["held_relationship_count"] == 5
    assert result["source_count"] == result["evidence_count"] == 19
    assert result["context_count"] == 10
    assert result["stage_count"] == 5
    assert result["probe_count"] == 12
    assert result["registry_document_count"] == 13
