from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.validate_brand_ontology_workspace import validate_workspace  # noqa: E402


def test_brand_ontology_research_pack_has_question_and_fixture_coverage() -> None:
    result = validate_workspace()

    assert len(result["questions"]) == 30
    assert len(result["worlds"]) == 9
    assert {case["case_type"] for case in result["probes"]} >= {
        "exact_artifact",
        "intent",
        "adversarial",
        "no_hit",
        "pathing",
    }
