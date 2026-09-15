#!/usr/bin/env python3
"""Certify the implemented Brand World v3 foundation through the compiler boundary."""

from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any

from testflight_brand import (
    build_biotic_authority_review_proposal,
    build_biotic_public_research_migration,
    export_biotic_v3_review_bundle,
    load_brand_ontology_release,
)
from testflight_brand.migration_report import assess_migration


def certify(repository_root: Path) -> dict[str, Any]:
    root = repository_root.resolve()
    ontology, sources = load_brand_ontology_release(root, release="ontology-v3")
    if ontology.version != "3.0.0-candidate" or len(sources) != 8:
        raise ValueError("Brand World v3 must resolve exactly eight canonical modules")

    migration = build_biotic_public_research_migration(root)
    report = assess_migration(
        migration.change_set,
        contexts=migration.contexts,
        ledger=migration.ledger,
    )
    if report.disposition_coverage != 1 or report.evidence_coverage != 1:
        raise ValueError("Biotic migration coverage is incomplete")
    unresolved = {
        "record": report.dangling_record_refs,
        "evidence": report.dangling_evidence_refs,
        "source": report.dangling_source_refs,
        "context": report.dangling_context_refs,
        "provenance": report.dangling_provenance_refs,
        "relation": report.relation_integrity_errors,
        "unsupported_promotion": report.unsupported_promotion_ids,
    }
    if any(unresolved.values()):
        raise ValueError(f"Biotic migration integrity failed: {unresolved}")

    review = build_biotic_authority_review_proposal(migration)
    if review.records_are_accepted or review.review_status != "awaiting_authorized_human":
        raise ValueError("authority review package must remain proposal-only")
    if review.decision_template.selected_alternative_id is not None:
        raise ValueError("authority decision must not be selected during migration")

    committed = root / "workspaces/brand-hellobiotic-research/v3"
    with tempfile.TemporaryDirectory(prefix="testflight-brand-world-v3-") as directory:
        generated = export_biotic_v3_review_bundle(root, Path(directory))
        generated_by_name = {path.name: path for path in generated}
        committed_names = {path.name for path in committed.iterdir() if path.is_file()}
        if set(generated_by_name) != committed_names:
            raise ValueError("committed Biotic review bundle file set is not deterministic")
        for name, generated_path in generated_by_name.items():
            if generated_path.read_bytes() != (committed / name).read_bytes():
                raise ValueError(f"committed Biotic review bundle is stale: {name}")

    manifest = json.loads((committed / "bundle-manifest.json").read_text())
    if manifest.get("status") != "proposal_only" or manifest.get("accepted_records") != 0:
        raise ValueError("Biotic review bundle must explicitly contain zero accepted records")
    for item in manifest.get("files", []):
        path = committed / item["path"]
        digest = f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"
        if digest != item["sha256"]:
            raise ValueError(f"Biotic review bundle hash mismatch: {path.name}")

    return {
        "status": "pass",
        "scope": "phases-0-through-6-foundation",
        "ontology": {
            "id": ontology.id,
            "version": ontology.version,
            "module_count": len(sources),
        },
        "biotic": {
            "branch": migration.change_set.branch_id,
            "record_count": report.record_count,
            "legacy_dispositions": report.disposition_count,
            "evidence_references": report.evidence_reference_count,
            "contradictions_surfaced": len(report.contradiction_ids),
            "ready_for_authority_review": report.ready_for_authority_review,
            "approved_record_count": 0,
        },
        "human_gate": "Biotic client-approved-v3 branch awaits an authorized record review.",
        "compiler_gate": "Run by the brand-world-v3-certification Make target.",
    }


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    print(json.dumps(certify(root), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
