#!/usr/bin/env python3
"""Build a deterministic, provider-neutral Testflight Product projection."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid5

try:
    from scripts.validate_testflight_product_workspace import (
        REPO_ROOT,
        WORKSPACE_RELATIVE,
        validate_workspace,
    )
except ModuleNotFoundError:
    from validate_testflight_product_workspace import (
        REPO_ROOT,
        WORKSPACE_RELATIVE,
        validate_workspace,
    )


@dataclass(frozen=True, slots=True)
class ProjectionDocument:
    document_id: str
    workspace_id: str
    source_url: str
    source_hash: str
    text: str
    metadata: dict[str, Any]


def _registry_records(path: Path) -> list[dict[str, Any]]:
    registry = json.loads(path.read_text(encoding="utf-8"))
    return registry.get("sources", registry.get("resources", []))


def _source_path(root: Path, source_url: str) -> Path:
    return root / source_url.removeprefix("repo://")


def _documents_for_registry(
    root: Path, workspace_id: str, records: list[dict[str, Any]]
) -> list[ProjectionDocument]:
    documents: list[ProjectionDocument] = []
    for record in records:
        source_url = record["source_url"]
        path = _source_path(root, source_url)
        if path.is_dir():
            continue
        source_bytes = path.read_bytes()
        source_hash = hashlib.sha256(source_bytes).hexdigest()
        document_id = str(uuid5(NAMESPACE_URL, f"{workspace_id}:{source_url}:{source_hash}"))
        doc_type = record["doc_type"]
        role = "content"
        if doc_type in {"config", "runtime_config", "policy"}:
            role = "policy"
        elif doc_type in {"registry", "dependency_registry", "source_catalog"}:
            role = "registry"
        elif doc_type in {"audit", "research_report"}:
            role = "report"
        metadata = {
            **record,
            "workspace_id": workspace_id,
            "source_hash": source_hash,
            "source_path": str(path.relative_to(root)),
            "document_role": role,
            "container_scope": "parent" if workspace_id.endswith("testflight-product") else "child",
            "specificity": "narrow" if record["canonical"] else "medium",
        }
        header = (
            f"WORKSPACE_ID: {workspace_id}\nSOURCE_URL: {source_url}\n"
            f"SOURCE_HASH: {source_hash}\nSOURCE_BEGIN\n"
        )
        text = f"{header}{source_bytes.decode('utf-8').rstrip()}\nSOURCE_END\n"
        documents.append(
            ProjectionDocument(document_id, workspace_id, source_url, source_hash, text, metadata)
        )
    return documents


def build_documents(root: Path = REPO_ROOT) -> list[ProjectionDocument]:
    """Build deterministic documents, preserving parent and child workspace scope."""

    root = root.resolve()
    validated = validate_workspace(root)
    workspace_root = root / WORKSPACE_RELATIVE
    documents = _documents_for_registry(
        root,
        validated["workspace_id"],
        _registry_records(workspace_root / "resource_registry.json"),
    )
    for module in validated["modules"]:
        documents.extend(
            _documents_for_registry(
                root,
                module["workspace_id"],
                _registry_records(workspace_root / module["id"] / "resource_registry.json"),
            )
        )
    return documents


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--materialize", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    documents = build_documents(root)
    if args.materialize:
        destination = args.materialize.resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            "".join(json.dumps(asdict(document), sort_keys=True) + "\n" for document in documents),
            encoding="utf-8",
        )
        status = "materialized"
    elif args.validate_only:
        status = "validated"
    else:
        status = "dry_run"
    report = {
        "status": status,
        "workspace_id": "world://workspace/testflight-product",
        "document_count": len(documents),
        "workspace_ids": sorted({document.workspace_id for document in documents}),
        "live_projection_changed": False,
        "materialized_path": str(args.materialize.resolve()) if args.materialize else None,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
