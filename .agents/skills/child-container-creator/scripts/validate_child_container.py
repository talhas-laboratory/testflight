#!/usr/bin/env python3
"""Validate a canonical child-container scaffold or certification candidate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

REQUIRED_FILES = (
    "AGENT_INDEX.md",
    "AGENT_CONFIG.yaml",
    "WORKSPACE.yaml",
    "artifacts/source_manifest.yaml",
    "certification_cases/probes.yaml",
    "resource_registry.json",
)
REQUIRED_METADATA = {
    "module",
    "unit",
    "task_view",
    "tool",
    "doc_type",
    "evidence_tier",
    "experience_type",
    "difficulty",
    "canonical",
    "last_verified_at",
    "source_url",
}
REQUIRED_PROBE_CLASSES = {
    "exact_artifact",
    "intent_route",
    "adversarial_navigation",
    "out_of_domain_no_hit",
}


def load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a mapping")
    return value


def nonempty(value: Any) -> bool:
    return value is not None and value != "" and value != []


def validate(root: Path, certify: bool) -> dict[str, Any]:
    errors: list[str] = []
    for relative in REQUIRED_FILES:
        if not (root / relative).is_file():
            errors.append(f"missing required file: {relative}")
    if errors:
        return {"status": "fail", "mode": "certify" if certify else "structure", "errors": errors}

    config = load_yaml(root / "AGENT_CONFIG.yaml")
    workspace = load_yaml(root / "WORKSPACE.yaml")
    probes = load_yaml(root / "certification_cases/probes.yaml")
    source_manifest = load_yaml(root / "artifacts/source_manifest.yaml")
    registry = json.loads((root / "resource_registry.json").read_text(encoding="utf-8"))

    child_id = workspace.get("id")
    if not nonempty(child_id):
        errors.append("WORKSPACE.yaml id is required")
    if not nonempty(workspace.get("parent")):
        errors.append("WORKSPACE.yaml parent is required")
    if workspace.get("type") != "child-knowledge-container":
        errors.append("WORKSPACE.yaml type must be child-knowledge-container")
    dataset_name = workspace.get("dataset_name")
    if not isinstance(dataset_name, str) or not dataset_name.endswith("_staging"):
        errors.append("WORKSPACE.yaml dataset_name must be an isolated *_staging dataset")
    for label, value in (
        ("AGENT_CONFIG container_id", config.get("container_id")),
        ("registry containerId", registry.get("containerId")),
        ("source manifest container_id", source_manifest.get("container_id")),
        ("probe container_id", probes.get("container_id")),
    ):
        if value != child_id:
            errors.append(f"{label} does not match WORKSPACE.yaml id")
    if config.get("dataset_name") != dataset_name:
        errors.append("AGENT_CONFIG dataset_name does not match WORKSPACE.yaml")
    if config.get("parent_workspace_id") != workspace.get("parent"):
        errors.append("AGENT_CONFIG parent_workspace_id does not match WORKSPACE.yaml")

    resources = registry.get("resources")
    if not isinstance(resources, list):
        errors.append("resource_registry.json resources must be an array")
        resources = []
    for index, resource in enumerate(resources):
        if not isinstance(resource, dict):
            errors.append(f"resource {index} must be an object")
            continue
        missing = sorted(key for key in REQUIRED_METADATA if not nonempty(resource.get(key)))
        if missing:
            errors.append(f"resource {index} missing metadata: {', '.join(missing)}")

    probe_items = probes.get("probes")
    if not isinstance(probe_items, list):
        errors.append("probes.yaml probes must be an array")
        probe_items = []
    if certify:
        if not resources:
            errors.append("certification requires at least one source resource")
        classes = {
            probe.get("class")
            for probe in probe_items
            if isinstance(probe, dict) and nonempty(probe.get("class"))
        }
        missing_classes = sorted(REQUIRED_PROBE_CLASSES - classes)
        if missing_classes:
            errors.append(f"certification missing probe classes: {', '.join(missing_classes)}")

    return {
        "status": "pass" if not errors else "fail",
        "mode": "certify" if certify else "structure",
        "containerId": child_id,
        "datasetName": dataset_name,
        "resourceCount": len(resources),
        "probeCount": len(probe_items),
        "errors": errors,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("child_dir")
    parser.add_argument("--certify", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.child_dir).resolve()
    if not root.is_dir():
        raise SystemExit(f"child directory does not exist: {root}")
    report = validate(root, args.certify)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
