"""Deterministic export of the Biotic v3 migration and authority-review gate."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .biotic_migration import build_biotic_public_research_migration
from .biotic_review import build_biotic_authority_review_proposal
from .migration_report import assess_migration

_SOURCE_PATHS = (
    "artifacts/entity-inventory.yaml",
    "artifacts/relationship-inventory.yaml",
    "artifacts/evidence-notes.yaml",
    "artifacts/source-catalog.yaml",
    "artifacts/context-profiles.yaml",
    "artifacts/world-modeling.yaml",
)


def export_biotic_v3_review_bundle(
    repository_root: Path, output_directory: Path | None = None
) -> tuple[Path, ...]:
    """Write a rebuildable, review-only bundle and return its generated paths."""

    repository_root = repository_root.resolve()
    workspace = repository_root / "workspaces/brand-hellobiotic-research"
    output = (output_directory or workspace / "v3").resolve()
    output.mkdir(parents=True, exist_ok=True)
    migration = build_biotic_public_research_migration(repository_root)
    report = assess_migration(
        migration.change_set, contexts=migration.contexts, ledger=migration.ledger
    )
    authority_review = build_biotic_authority_review_proposal(migration)
    source_snapshot = {
        "snapshot_hash": migration.ledger.snapshot_hash,
        "scope": "Curated local research artifacts only; not full remote web-page content.",
        "artifacts": [
            {
                "path": path,
                "content_hash": _hash_bytes((workspace / path).read_bytes()),
                "content": (workspace / path).read_text(),
            }
            for path in _SOURCE_PATHS
        ],
    }
    payloads: dict[str, Any] = {
        "proposed-public-research-branch.json": migration.change_set.model_dump(mode="json"),
        "contexts.json": [context.model_dump(mode="json") for context in migration.contexts],
        "legacy-disposition-ledger.json": migration.ledger.model_dump(mode="json"),
        "migration-integrity-report.json": report.model_dump(mode="json"),
        "authority-review-proposal.json": authority_review.model_dump(mode="json"),
        "immutable-legacy-source-snapshot.json": source_snapshot,
    }
    generated: list[Path] = []
    for filename, payload in payloads.items():
        path = output / filename
        path.write_text(_json(payload))
        generated.append(path)
    readme = output / "README.md"
    readme.write_text(_readme())
    generated.append(readme)
    manifest = output / "bundle-manifest.json"
    manifest.write_text(
        _json(
            {
                "bundle_id": "biotic-brand-world-v3-review-bundle",
                "status": "proposal_only",
                "accepted_records": 0,
                "files": [
                    {
                        "path": path.name,
                        "sha256": _hash_bytes(path.read_bytes()),
                    }
                    for path in sorted(generated)
                ],
            }
        )
    )
    generated.append(manifest)
    return tuple(generated)


def _json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _hash_bytes(value: bytes) -> str:
    return f"sha256:{hashlib.sha256(value).hexdigest()}"


def _readme() -> str:
    return """# Biotic Brand World v3 review bundle

This is a deterministic, proposal-only export. It contains the v3 public-research proposal,
content-addressed contexts, complete legacy disposition ledger, integrity report, exact local
source-artifact snapshot, and a separate FDE/client authority-review proposal.

No record in this directory is approved. The authority-review proposal deliberately has no
selected decision, reviewer, authority grant, or accepted record. An authorized human must review
each item before a separate `client-approved-v3` branch can be populated through the World service.

The source snapshot retains the exact local curated research artifacts. It does not retain full
remote web-page text because the source policy explicitly prohibits that content.
"""


__all__ = ["export_biotic_v3_review_bundle"]
