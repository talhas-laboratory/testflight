from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.validate_reasoning_operators import validate_catalog  # noqa: E402


def test_reasoning_operator_catalog_is_valid() -> None:
    assert validate_catalog(REPO_ROOT) == 16


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
