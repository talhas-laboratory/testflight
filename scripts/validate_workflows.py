#!/usr/bin/env python3
"""Validate the declarative workflow registry and optionally emit its JSON Schema."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml
from testflight_workflows import load_workflow, workflow_json_schema


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, default=Path("workflows/registry.yaml"))
    parser.add_argument("--schema", action="store_true")
    args = parser.parse_args()
    if args.schema:
        print(json.dumps(workflow_json_schema(), indent=2, sort_keys=True))
        return 0

    registry = yaml.safe_load(args.registry.read_text(encoding="utf-8"))
    root = args.registry.parent
    seen: set[tuple[str, int]] = set()
    for entry in registry.get("definitions", []):
        workflow = load_workflow(root / entry["path"])
        key = (workflow.id, workflow.version)
        if key in seen:
            raise SystemExit(f"duplicate workflow registry entry: {workflow.id}@{workflow.version}")
        seen.add(key)
        if entry["id"] != workflow.id or entry["version"] != workflow.version:
            raise SystemExit(f"registry identity mismatch: {entry['path']}")
        if entry["status"] != workflow.lifecycle.value:
            raise SystemExit(f"registry lifecycle mismatch: {entry['path']}")
    print(f"validated {len(seen)} declarative workflows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
