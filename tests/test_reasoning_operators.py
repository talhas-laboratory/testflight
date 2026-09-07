from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.validate_reasoning_operators import validate_catalog  # noqa: E402


def test_reasoning_operator_catalog_is_valid() -> None:
    assert validate_catalog(REPO_ROOT) == 24


def test_every_operator_has_a_procedure_and_evaluator() -> None:
    import yaml

    index = yaml.safe_load((REPO_ROOT / "reasoning/operators/index.yaml").read_text())
    for entry in index["operators"]:
        operator = yaml.safe_load((REPO_ROOT / "reasoning/operators" / entry["file"]).read_text())[
            "operator"
        ]
        assert len(operator["procedure"]) >= 4
        assert len(operator["evaluators"]) >= 2
        assert operator["hold_when"]


def test_creative_gold_fixtures_separate_schema_and_semantic_expectations() -> None:
    import yaml

    fixture_path = REPO_ROOT / "reasoning/fixtures/creative-field/gold.yaml"
    loaded = yaml.safe_load(fixture_path.read_text())
    fixtures = loaded["fixtures"]
    assert len(fixtures) == 11
    assert {item["id"] for item in fixtures} >= {
        "intent",
        "tension",
        "outlier",
        "translation",
        "isolation",
        "correction",
        "no-hit",
        "rights",
        "authority",
        "capability-degradation",
    }
    for fixture in fixtures:
        expected = fixture["expected"]
        assert expected["schema_valid"] is True
        assert expected["semantic_disposition"] in {
            "propose",
            "branch",
            "accept",
            "version",
            "no_hit",
            "hold",
            "partial",
        }
        assert expected["required_invariants"]
        assert expected["semantic_rubric"]


def test_embedded_content_cannot_rewrite_operator_procedure() -> None:
    import yaml

    loaded = yaml.safe_load((REPO_ROOT / "reasoning/fixtures/creative-field/gold.yaml").read_text())
    fixture = next(item for item in loaded["fixtures"] if item["id"] == "embedded-instruction")
    assert fixture["expected"]["semantic_disposition"] == "hold"
    assert "procedure_immutable" in fixture["expected"]["required_invariants"]
