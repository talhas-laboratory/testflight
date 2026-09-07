from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from validate_multimodal_content_fixtures import (  # noqa: E402
    DEFAULT_FIXTURE,
    validate_fixture,
)


def _fixture_payload() -> dict:
    return yaml.safe_load(DEFAULT_FIXTURE.read_text(encoding="utf-8"))


def _write_fixture(path: Path, payload: dict) -> Path:
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return path


def test_golden_multimodal_profile_fixture_is_certified() -> None:
    result = validate_fixture()

    assert result == {
        "status": "certified",
        "content_unit_count": 3,
        "track_count": 14,
        "segment_count": 8,
        "observation_count": 11,
        "pattern_count": 1,
        "gate_case_count": 4,
        "unavailable_modality_count": 1,
    }


def test_fixture_rejects_an_observation_without_anchors(tmp_path: Path) -> None:
    payload = copy.deepcopy(_fixture_payload())
    payload["content_units"][0]["observations"][0]["anchors"] = []

    with pytest.raises(ValueError, match="has no anchors"):
        validate_fixture(_write_fixture(tmp_path / "missing-anchor.yaml", payload))


def test_fixture_rejects_pattern_evidence_from_one_content_unit(tmp_path: Path) -> None:
    payload = copy.deepcopy(_fixture_payload())
    payload["pattern_candidates"][0]["occurrence_ids"] = ["occurrence:calm-expert:reel-01"]

    with pytest.raises(ValueError, match="at least two independent content units"):
        validate_fixture(_write_fixture(tmp_path / "one-unit-pattern.yaml", payload))


def test_fixture_rejects_missing_counterexamples(tmp_path: Path) -> None:
    payload = copy.deepcopy(_fixture_payload())
    payload["pattern_candidates"][0]["counterexample_observation_ids"] = []

    with pytest.raises(ValueError, match="needs valid counterexamples"):
        validate_fixture(_write_fixture(tmp_path / "missing-counterexample.yaml", payload))


def test_fixture_covers_hold_partial_and_no_hit() -> None:
    payload = _fixture_payload()
    statuses = {item["expected_status"] for item in payload["gate_cases"]}
    reasons = {item["expected_reason"] for item in payload["gate_cases"]}

    assert {"hold", "partial", "no_hit"}.issubset(statuses)
    assert {"rights_missing", "causal_evidence_missing", "modality_unavailable"}.issubset(reasons)
