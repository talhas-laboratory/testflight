#!/usr/bin/env python3
"""Deterministically validate Concept Lab continuity fixtures."""
from pathlib import Path
import yaml

TARGETS = {"product-definition", "architecture", "research-learning", "product-decisions"}

def validate(root: Path) -> dict[str, list[str]]:
    cases = yaml.safe_load((root / "reasoning/fixtures/concept-lab/cases.yaml").read_text())["cases"]
    results = {}
    for case in cases:
        errors = []
        if case["canonical_write"]: errors.append("canonical_write must be false")
        if case["target_module_id"] and case["target_module_id"] not in TARGETS: errors.append("unknown target module")
        if case["status"] == "pass" and (not case["source_refs"] or not case["selected_branch"]): errors.append("supported continuity lacks lineage")
        if case["status"] == "branch" and len(case["branches"]) < 2: errors.append("ambiguity must retain two branches")
        if case["status"] == "hold" and not (not case["source_refs"] or case.get("requested_traversal")): errors.append("hold lacks boundary reason")
        trace = case["trace"]
        if trace["technical"] and not trace["interpretive"] and "interpretive" not in trace["missing_links"]: errors.append("broken trace must name missing link")
        results[case["id"]] = errors
    return results

if __name__ == "__main__":
    report = validate(Path(__file__).resolve().parents[1])
    assert not any(report.values()), report
    print(f"validated {len(report)} Concept Lab continuity cases")
