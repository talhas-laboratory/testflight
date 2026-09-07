#!/usr/bin/env python3
"""Create a safe, canonical child-container scaffold.

Dry-run is the default. The helper never edits the parent contract and refuses to overwrite an
existing child.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def yaml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def default_dataset(parent_dir: Path, slug: str) -> str:
    parent_name = re.sub(r"[^a-z0-9]+", "_", parent_dir.name.lower()).strip("_")
    child_name = slug.replace("-", "_")
    return f"testflight_{parent_name}_{child_name}_staging"


def build_files(args: argparse.Namespace, target: Path, workspace_id: str) -> dict[Path, str]:
    dataset_name = args.dataset_name or default_dataset(Path(args.parent_dir), args.slug)
    agent_index = f"""# {args.label}

## Mission

{args.mission}

## Scope

This child is bounded to `{workspace_id}`. Add included intents and explicit exclusions before
population.

## Retrieval

Use exact lookup or BM25 first inside this child. Use bounded same-child hybrid retrieval only
after an in-domain lexical no-hit. Use graph traversal only for explicit path questions with at
most two hops. Return `NO_HITS` for unsupported or out-of-domain requests.

## Navigation

- `AGENT_CONFIG.yaml`: retrieval and quality policy.
- `WORKSPACE.yaml`: identity and parent topology.
- `resource_registry.json`: source metadata and provenance.
- `certification_cases/probes.yaml`: retrieval certification cases.
"""
    agent_config = f"""version: 1
container_id: {yaml_string(workspace_id)}
parent_workspace_id: {yaml_string(args.parent_workspace_id)}
dataset_name: {yaml_string(dataset_name)}
route: {yaml_string(args.route)}
status: draft
retrieval:
  container_ids:
    - {yaml_string(workspace_id)}
  primary: bm25
  fallback: bounded_same_child_hybrid
  graph_max_hops: 2
  out_of_domain: NO_HITS
  reject_navigation_as_answer: true
metadata_contract:
  required:
    - module
    - unit
    - task_view
    - tool
    - doc_type
    - evidence_tier
    - experience_type
    - difficulty
    - canonical
    - last_verified_at
    - source_url
quality_gates:
  top_1_precision_min: 0.90
  routing_error_max: 0.03
  query_failure_max: 0.005
  no_hit_correctness: 1.0
"""
    workspace = f"""version: 1
id: {yaml_string(workspace_id)}
parent: {yaml_string(args.parent_workspace_id)}
type: child-knowledge-container
label: {yaml_string(args.label)}
mission: {yaml_string(args.mission)}
dataset_name: {yaml_string(dataset_name)}
route: {yaml_string(args.route)}
status: draft
source_of_truth: canonical-workspace-files
projection: rebuildable
"""
    source_manifest = f"""version: 1
container_id: {yaml_string(workspace_id)}
sources: []
"""
    probes = f"""version: 1
container_id: {yaml_string(workspace_id)}
status: draft
required_classes:
  - exact_artifact
  - intent_route
  - adversarial_navigation
  - out_of_domain_no_hit
probes: []
"""
    registry = (
        json.dumps(
            {"version": 1, "containerId": workspace_id, "resources": []},
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    )
    return {
        target / "AGENT_INDEX.md": agent_index,
        target / "AGENT_CONFIG.yaml": agent_config,
        target / "WORKSPACE.yaml": workspace,
        target / "artifacts" / "source_manifest.yaml": source_manifest,
        target / "certification_cases" / "probes.yaml": probes,
        target / "resource_registry.json": registry,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent-dir", required=True)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--mission", required=True)
    parser.add_argument("--parent-workspace-id", required=True)
    parser.add_argument("--workspace-id")
    parser.add_argument("--dataset-name")
    parser.add_argument("--route", required=True)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write the scaffold. Without this flag the command is a dry-run.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    parent = Path(args.parent_dir)
    if not parent.is_absolute():
        raise SystemExit("--parent-dir must be an absolute path")
    parent = parent.resolve()
    if not parent.is_dir():
        raise SystemExit(f"parent directory does not exist: {parent}")
    if not SLUG_PATTERN.fullmatch(args.slug):
        raise SystemExit("--slug must use lowercase letters, digits, and single hyphens")
    if not args.parent_workspace_id.strip():
        raise SystemExit("--parent-workspace-id cannot be empty")
    target = parent / args.slug
    if target.exists():
        raise SystemExit(f"refusing to overwrite existing child: {target}")
    workspace_id = args.workspace_id or f"{args.parent_workspace_id.rstrip('/')}/{args.slug}"
    dataset_name = args.dataset_name or default_dataset(parent, args.slug)
    if not dataset_name.endswith("_staging"):
        raise SystemExit("new child datasets must end with _staging")
    args.dataset_name = dataset_name
    files = build_files(args, target, workspace_id)
    if args.apply:
        for path, content in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    report = {
        "status": "created" if args.apply else "dry_run",
        "parentWorkspaceId": args.parent_workspace_id,
        "childWorkspaceId": workspace_id,
        "datasetName": dataset_name,
        "targetPath": str(target),
        "files": [str(path) for path in sorted(files)],
        "requiredParentUpdates": [
            "register child workspace in parent topology",
            "register child canonical sources under the parent's metadata contract",
            "add an explicit child-first retrieval route",
        ],
        "liveProjectionChanged": False,
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
