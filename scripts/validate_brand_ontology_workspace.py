#!/usr/bin/env python3
"""Validate the tracked Brand ontology research container pack."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_RELATIVE = Path("workspaces/brand-ontology-research")
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
REQUIRED_PROBE_CLASSES = {"exact_artifact", "intent", "adversarial", "no_hit", "pathing"}
REQUIRED_WORLDS = {
    "intended-observed-brand",
    "repositioning-temporal",
    "shared-technology",
    "adaptive-representation",
    "market-positioning",
    "evidence-conflict",
    "bitemporal-reconstruction",
    "causal-guardrails",
    "shared-representation-products",
}


def _load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a mapping")
    return payload


def _resolve_source(root: Path, source_url: str) -> Path:
    prefix = "repo://"
    if not source_url.startswith(prefix):
        raise ValueError(f"source_url must use {prefix}: {source_url}")
    path = (root / source_url.removeprefix(prefix)).resolve()
    if root.resolve() not in path.parents:
        raise ValueError(f"source escapes repository root: {source_url}")
    if not path.is_file():
        raise FileNotFoundError(f"source does not exist: {source_url}")
    return path


def validate_workspace(root: Path = REPO_ROOT) -> dict[str, Any]:
    """Validate the research pack and return its loaded catalogs."""

    root = root.resolve()
    workspace = root / WORKSPACE_RELATIVE
    manifest = _load_yaml(workspace / "WORKSPACE.yaml")["workspace"]
    if manifest.get("id") != "world://workspace/brand-ontology-research":
        raise ValueError("research workspace has unexpected identity")
    if manifest.get("status") != "active":
        raise ValueError("research workspace must be active")

    config_text = (workspace / "AGENT_CONFIG.yaml").read_text(encoding="utf-8")
    for required in (
        "retrieval_defaults:",
        "retrieval_acceptance_policy:",
        "metadata_contract:",
        "certification_policy:",
    ):
        if required not in config_text:
            raise ValueError(f"AGENT_CONFIG missing section: {required}")
    index_text = (workspace / "AGENT_INDEX.md").read_text(encoding="utf-8")
    if "Route to smallest relevant child container" not in index_text:
        raise ValueError("AGENT_INDEX missing child-first route")
    if "bm25" not in index_text or "hybrid" not in index_text:
        raise ValueError("AGENT_INDEX missing lexical/hybrid retrieval policy")

    registry = json.loads((workspace / "resource_registry.json").read_text(encoding="utf-8"))
    sources = registry.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ValueError("resource registry must contain sources")
    source_urls: set[str] = set()
    for source in sources:
        if not isinstance(source, dict):
            raise ValueError("resource registry source must be an object")
        missing = REQUIRED_METADATA - set(source)
        if missing:
            raise ValueError(f"resource source missing metadata: {sorted(missing)}")
        source_url = source["source_url"]
        if source_url in source_urls:
            raise ValueError(f"duplicate source URL: {source_url}")
        source_urls.add(source_url)
        _resolve_source(root, source_url)

    questions = _load_yaml(workspace / "artifacts/competency-questions.yaml").get("questions")
    if not isinstance(questions, list) or len(questions) != 30:
        raise ValueError("competency question catalog must contain exactly 30 questions")
    question_ids: set[str] = set()
    for question in questions:
        if not isinstance(question, dict):
            raise ValueError("competency question must be an object")
        required = {"id", "category", "question", "expected_invariant", "required_kinds"}
        if required - set(question):
            missing = sorted(required - set(question))
            raise ValueError(f"competency question missing fields: {missing}")
        if question["id"] in question_ids:
            raise ValueError(f"duplicate competency question: {question['id']}")
        question_ids.add(question["id"])

    worlds = _load_yaml(workspace / "artifacts/synthetic-worlds.yaml").get("worlds")
    if not isinstance(worlds, list):
        raise ValueError("synthetic worlds must be a list")
    world_slugs = {world.get("slug") for world in worlds if isinstance(world, dict)}
    if world_slugs != REQUIRED_WORLDS:
        raise ValueError(f"synthetic world catalog mismatch: {sorted(world_slugs)}")
    for world in worlds:
        if set(world.get("required_questions", ())) - question_ids:
            raise ValueError(f"world references unknown competency question: {world['id']}")

    probe_cases = json.loads(
        (workspace / "certification_cases/brand_ontology_probe_suite.json").read_text(
            encoding="utf-8"
        )
    )
    probe_classes = {case.get("case_type") for case in probe_cases if isinstance(case, dict)}
    if not probe_classes >= REQUIRED_PROBE_CLASSES:
        raise ValueError(f"probe classes missing: {sorted(REQUIRED_PROBE_CLASSES - probe_classes)}")

    fixture_cases = json.loads(
        (workspace / "certification_cases/fixture_cases.json").read_text(encoding="utf-8")
    )
    if len(fixture_cases) != len(REQUIRED_WORLDS):
        raise ValueError("fixture case catalog must cover every synthetic world")
    for case in fixture_cases:
        if not isinstance(case, dict) or not isinstance(case.get("fixture_builder"), str):
            raise ValueError("every synthetic world fixture needs an executable fixture_builder")

    return {
        "workspace": workspace,
        "manifest": manifest,
        "registry": registry,
        "questions": questions,
        "worlds": worlds,
        "probes": probe_cases,
        "fixture_cases": fixture_cases,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    args = parser.parse_args()
    result = validate_workspace(args.root)
    print(
        "validated Brand ontology research workspace: "
        f"questions={len(result['questions'])} worlds={len(result['worlds'])} "
        f"probes={len(result['probes'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
