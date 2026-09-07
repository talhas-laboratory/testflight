#!/usr/bin/env python3
"""Dry-run, drift-check and rebuild a Creative Field child projection.

The input is an exported canonical record list.  This command only writes a derived projection
manifest; it never edits the source record file or a canonical SQLite database.  Live Cognee
population remains a separately authorized operation after certification.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import testflight_creative_field as creative
from testflight_adapter_cognee.creative_field_projection import (
    build_creative_field_projection,
    compare_projection_drift,
    read_projection_manifest,
    write_projection_manifest,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
_MODELS: dict[str, type[creative.CreativeRecord]] = {
    name: getattr(creative, name)
    for name in (
        "CreativeProject",
        "Moodboard",
        "SourceLicenseRecord",
        "ReferenceAsset",
        "Placement",
        "ReferenceCluster",
        "UserAnnotation",
        "BoardRevision",
        "ObservedFeature",
        "InterpretationAlternative",
        "ReferenceContribution",
        "ReferenceInterpretation",
        "ReviewDecision",
        "FieldDimension",
        "DimensionState",
        "Principle",
        "Tension",
        "Exclusion",
        "FieldConflict",
        "MissingDimension",
        "CreativeFieldProposal",
        "CreativeFieldRun",
        "CreativeFieldVersion",
        "ProjectBinding",
        "FieldBinding",
        "LocalOverride",
        "CreativeRequest",
        "ResolvedCreativeRequest",
        "FieldProjection",
        "CreativeContextPacket",
        "TargetCapabilityManifest",
        "GenerationPacket",
        "InvocationReceipt",
        "CreativeOutput",
        "CreativeEvaluation",
        "FeedbackRecord",
    )
}


def _load_records(path: Path) -> list[creative.CreativeRecord]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(value, dict):
        value = value.get("records")
    if not isinstance(value, list):
        raise ValueError("records file must contain a JSON list or an object with records")
    records: list[creative.CreativeRecord] = []
    for index, item in enumerate(value, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"record {index} must be an object")
        record_type = item.get("record_type", item.get("recordType"))
        payload = item.get("payload", item.get("record"))
        if not isinstance(record_type, str) or record_type not in _MODELS:
            raise ValueError(f"record {index} has unsupported record_type: {record_type!r}")
        if not isinstance(payload, dict):
            raise ValueError(f"record {index} payload must be an object")
        records.append(_MODELS[record_type].model_validate(payload))
    return records


def _report(
    manifest: Any, *, mode: str, output: Path | None, drift: dict[str, Any]
) -> dict[str, Any]:
    return {
        "status": mode,
        "child_workspace_id": manifest.child_workspace_id,
        "parent_workspace_id": manifest.parent_workspace_id,
        "project_id": manifest.project_id,
        "dataset_name": manifest.dataset_name,
        "source_hash": manifest.source_hash,
        "document_count": len(manifest.documents),
        "edge_count": len(manifest.custom_edges),
        "output": str(output) if output else None,
        "drift": drift,
        "canonical_mutation": False,
        "promotion_status": manifest.promotion_status,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records-file", type=Path, required=True)
    parser.add_argument("--child-workspace-id", required=True)
    parser.add_argument("--parent-workspace-id", required=True)
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--dataset-name", required=True)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--dry-run", action="store_true")
    modes.add_argument("--rebuild", type=Path, metavar="MANIFEST")
    parser.add_argument(
        "--drift-against",
        type=Path,
        metavar="MANIFEST",
        help="compare against an existing derived manifest without writing it",
    )
    args = parser.parse_args()

    records = _load_records(args.records_file.resolve())
    manifest = build_creative_field_projection(
        records,
        child_workspace_id=args.child_workspace_id,
        parent_workspace_id=args.parent_workspace_id,
        project_id=args.project_id,
        dataset_name=args.dataset_name,
    )
    comparison_path = args.drift_against or args.rebuild
    previous = (
        read_projection_manifest(comparison_path.resolve())
        if comparison_path is not None and comparison_path.exists()
        else None
    )
    drift = compare_projection_drift(manifest, previous)
    output = args.rebuild.resolve() if args.rebuild else None
    if args.rebuild:
        write_projection_manifest(manifest, output)
        mode = "rebuilt"
    else:
        mode = "dry_run"
    print(
        json.dumps(
            _report(manifest, mode=mode, output=output, drift=drift),
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
