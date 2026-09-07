#!/usr/bin/env python3
"""Audit deterministic child-first routing for the Testflight Product workspace."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
LEXICON_RELATIVE = Path("workspaces/testflight-product/artifacts/retrieval-lexicon.yaml")
NOISE = {
    "a",
    "an",
    "and",
    "are",
    "for",
    "from",
    "how",
    "in",
    "is",
    "of",
    "on",
    "the",
    "to",
    "what",
    "which",
    "with",
}

ROUTE_CASES = (
    ("mission portfolio capability surface roadmap", "product-definition"),
    ("why was this proposal decision accepted or superseded", "product-decisions"),
    ("typography spacing component accessibility design tokens", "experience-design"),
    ("application package adapter runtime deployment dependency", "architecture"),
    ("customer segment need journey interview market", "customers-market"),
    ("positioning campaign message channel acquisition retention", "marketing-growth"),
    ("pricing ARR revenue cost forecast unit economics", "finance-commercial"),
    ("role process policy control permission risk compliance incident", "operations-governance"),
    ("research question hypothesis experiment metric outcome learning", "research-learning"),
    ("weather temperature Neptune next Thursday", "NO_HITS"),
)


def _tokens(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*", value.lower())
        if token not in NOISE
    }


def load_lexicon(root: Path = REPO_ROOT) -> dict[str, set[str]]:
    value = yaml.safe_load((root / LEXICON_RELATIVE).read_text(encoding="utf-8"))
    routes = value.get("routes", {})
    return {
        route_id: set().union(*(_tokens(str(term)) for term in route["terms"]))
        for route_id, route in routes.items()
    }


def plan_route(query: str, lexicon: dict[str, set[str]] | None = None) -> dict[str, Any]:
    """Return a route trace based on bounded family-lexicon overlap."""

    lexicon = lexicon or load_lexicon()
    query_tokens = _tokens(query)
    candidates = []
    for route_id, route_tokens in lexicon.items():
        overlap = sorted(query_tokens & route_tokens)
        candidates.append({"route": route_id, "score": len(overlap), "overlap": overlap})
    candidates.sort(key=lambda candidate: (-candidate["score"], candidate["route"]))
    top_score = candidates[0]["score"] if candidates else 0
    selected = candidates[0]["route"] if top_score > 0 else "NO_HITS"
    return {
        "query": query,
        "query_tokens": sorted(query_tokens),
        "selected_route": selected,
        "candidates": candidates,
        "status": "hit" if selected != "NO_HITS" else "no_hit",
    }


def audit_routes(root: Path = REPO_ROOT) -> dict[str, Any]:
    lexicon = load_lexicon(root)
    attempts = []
    for query, expected in ROUTE_CASES:
        trace = plan_route(query, lexicon)
        trace["expected_route"] = expected
        trace["passed"] = trace["selected_route"] == expected
        attempts.append(trace)
    passed = sum(attempt["passed"] for attempt in attempts)
    return {
        "status": "pass" if passed == len(attempts) else "fail",
        "mode": "local_lexical_route_audit",
        "attempt_count": len(attempts),
        "passed": passed,
        "routing_error": (len(attempts) - passed) / len(attempts),
        "no_hit_correctness": 1.0 if attempts[-1]["selected_route"] == "NO_HITS" else 0.0,
        "live_retrieval_certified": False,
        "attempts": attempts,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()
    report = audit_routes(args.root.resolve())
    if args.summary:
        report = {key: value for key, value in report.items() if key != "attempts"}
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
