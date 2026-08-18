#!/usr/bin/env python3
"""Validate the portable reasoning-operator catalog."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

REQUIRED_FIELDS = {
    "id",
    "version",
    "kind",
    "category",
    "purpose",
    "accepts",
    "requires_context",
    "preconditions",
    "parameters",
    "procedure",
    "returns",
    "invariants",
    "forbidden_shortcuts",
    "hold_when",
    "failure_modes",
    "evaluators",
    "evidence",
}
PARAMETER_AXES = {
    "abstraction_level",
    "depth",
    "context_lens",
    "output_mode",
    "evidence_strictness",
    "uncertainty_policy",
    "proof_demand",
}
EXPECTED_CATEGORIES = {
    "boundary_conflation",
    "ontology_conflation",
    "mention_entity_conflation",
    "occurrence_canonical_conflation",
    "evidence_truth_conflation",
    "confidence_truth_conflation",
    "sequence_causality_conflation",
    "version_state_conflation",
    "retrieval_reasoning_conflation",
    "local_global_conflation",
    "identity_provenance_conflation",
    "validation_persistence_conflation",
    "workspace_isolation",
    "retry_idempotency",
    "configuration_runtime",
    "evaluation_schema",
}


def fail(message: str) -> None:
    raise SystemExit(f"reasoning operator validation failed: {message}")


def require_list(value: Any, label: str, *, allow_empty: bool = False) -> None:
    if not isinstance(value, list) or (not allow_empty and not value):
        fail(f"{label} must be a non-empty list")


def validate_operator(path: Path, expected: dict[str, Any]) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text())
    if not isinstance(loaded, dict) or not isinstance(loaded.get("operator"), dict):
        fail(f"{path} must contain an operator mapping")
    operator = loaded["operator"]
    missing = REQUIRED_FIELDS - set(operator)
    if missing:
        fail(f"{path} is missing fields: {', '.join(sorted(missing))}")

    if operator["id"] != expected["id"]:
        fail(f"{path} id {operator['id']!r} does not match index {expected['id']!r}")
    if operator["category"] != expected["category"]:
        fail(f"{path} category does not match index")
    if operator["version"] != 1:
        fail(f"{path} must currently be version 1")
    if operator["kind"] not in {"control", "transformational"}:
        fail(f"{path} has unsupported kind {operator['kind']!r}")
    if not str(operator["id"]).startswith("world://operator/"):
        fail(f"{path} id must use the portable world://operator namespace")
    if not isinstance(operator["purpose"], str) or not operator["purpose"].strip():
        fail(f"{path} purpose must be non-empty text")

    for field in (
        "accepts",
        "requires_context",
        "preconditions",
        "procedure",
        "returns",
        "invariants",
        "forbidden_shortcuts",
        "hold_when",
        "failure_modes",
        "evaluators",
    ):
        require_list(operator[field], f"{path}:{field}")

    parameters = operator["parameters"]
    if not isinstance(parameters, dict) or set(parameters) != PARAMETER_AXES:
        fail(f"{path}:parameters must declare exactly {sorted(PARAMETER_AXES)}")

    steps = operator["procedure"]
    step_ids: list[str] = []
    for position, step in enumerate(steps, start=1):
        if (
            not isinstance(step, dict)
            or not isinstance(step.get("step"), str)
            or not isinstance(step.get("action"), str)
        ):
            fail(f"{path}:procedure item {position} needs step and action text")
        step_ids.append(step["step"])
    if len(step_ids) != len(set(step_ids)):
        fail(f"{path}:procedure step ids must be unique")

    for position, evaluator in enumerate(operator["evaluators"], start=1):
        if not isinstance(evaluator, dict) or not all(
            isinstance(evaluator.get(field), str) and evaluator[field].strip()
            for field in ("id", "check", "pass_condition")
        ):
            fail(f"{path}:evaluator item {position} needs id, check, and pass_condition")

    evidence = operator["evidence"]
    if not isinstance(evidence, dict):
        fail(f"{path}:evidence must be a mapping")
    if (
        not isinstance(evidence.get("mindscape_operator_refs"), list)
        or not evidence["mindscape_operator_refs"]
    ):
        fail(f"{path}:evidence must cite at least one Mindscape operator reference")
    if not isinstance(evidence.get("source_basis"), list) or not evidence["source_basis"]:
        fail(f"{path}:evidence.source_basis must be non-empty")

    return operator


def validate_catalog(root: Path) -> int:
    index_path = root / "reasoning" / "operators" / "index.yaml"
    loaded = yaml.safe_load(index_path.read_text())
    if not isinstance(loaded, dict) or not isinstance(loaded.get("catalog"), dict):
        fail(f"{index_path} must contain a catalog mapping")
    entries = loaded.get("operators")
    require_list(entries, f"{index_path}:operators")
    if len(entries) != len(EXPECTED_CATEGORIES):
        fail(f"catalog should contain {len(EXPECTED_CATEGORIES)} operators")

    seen_ids: set[str] = set()
    seen_categories: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict) or not all(
            isinstance(entry.get(field), str) and entry[field].strip()
            for field in ("id", "file", "category", "kind")
        ):
            fail(f"{index_path}: every catalog entry needs id, file, category, and kind")
        if entry["id"] in seen_ids:
            fail(f"duplicate operator id {entry['id']}")
        if entry["category"] in seen_categories:
            fail(f"duplicate operator category {entry['category']}")
        seen_ids.add(entry["id"])
        seen_categories.add(entry["category"])
        operator_path = root / "reasoning" / "operators" / entry["file"]
        if not operator_path.is_file():
            fail(f"catalog entry points to missing file {operator_path}")
        validate_operator(operator_path, entry)

    if seen_categories != EXPECTED_CATEGORIES:
        fail(f"catalog categories differ: {sorted(seen_categories ^ EXPECTED_CATEGORIES)}")
    return len(entries)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Testflight repository root (defaults to the script's parent)",
    )
    args = parser.parse_args()
    count = validate_catalog(args.root.resolve())
    print(f"validated {count} reasoning operators")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
