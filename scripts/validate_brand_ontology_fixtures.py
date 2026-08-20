#!/usr/bin/env python3
"""Validate all executable synthetic Brand ontology worlds."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from brand_ontology_fixtures import validate_all_fixture_worlds

REPO_ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    "SW-001": {"perspectives_separate", "evidence_attached", "context_scoped"},
    "SW-002": {"bitemporal", "history_preserved", "supersession_not_deletion"},
    "SW-003": {"identity_evidence_required", "local_assertions_scoped"},
    "SW-004": {"binding_profile_rules_separate", "profile_dag", "facet_extensible"},
    "SW-005": {"portfolio_topology", "applicability_scoped", "concurrent_validity"},
    "SW-006": {"conflict_preserved", "weak_evidence_held", "no_silent_winner"},
    "SW-007": {"utc_half_open_time", "knowledge_history", "snapshot_replay"},
    "SW-008": {"causal_gate", "alternatives_preserved", "sequence_not_cause"},
    "SW-009": {"shared_identity", "adaptive_binding", "equal_authority_conflict_explicit"},
}


def validate_fixtures() -> dict[str, Any]:
    worlds = validate_all_fixture_worlds()
    actual = {world.world_id: set(world.required_invariants) for world in worlds}
    if set(actual) != set(EXPECTED):
        raise ValueError(
            f"fixture worlds do not match catalog: {sorted(set(EXPECTED) ^ set(actual))}"
        )
    for world_id, expected in EXPECTED.items():
        if actual[world_id] != expected:
            raise ValueError(f"{world_id} invariant mismatch")
    return {
        "status": "certified",
        "world_count": len(worlds),
        "worlds": [
            {
                "id": world.world_id,
                "slug": world.slug,
                "object_count": len(world.objects),
                "invariants": list(world.required_invariants),
            }
            for world in worlds
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=None)
    args = parser.parse_args()
    result = validate_fixtures()
    if args.report:
        args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"validated executable Brand fixtures: worlds={result['world_count']} status=certified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
