#!/usr/bin/env python3
"""Materialize and populate a validated concrete Brand workspace into isolated Cognee staging."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

import yaml
from populate_brand_research_workspace import (
    _cognee_data_id,
    _configure_runtime_environment,
    _credential,
    _llm_configs,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True, slots=True)
class Document:
    document_id: UUID
    source_url: str
    text: str
    metadata: dict[str, Any]


def _yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a mapping")
    return value


def _source_path(root: Path, source_url: str) -> Path:
    if not source_url.startswith("repo://"):
        raise ValueError(f"source must use repo://: {source_url}")
    path = (root / source_url.removeprefix("repo://")).resolve()
    if path != root and root not in path.parents:
        raise ValueError(f"source escapes materialization root: {source_url}")
    if not path.is_file():
        raise FileNotFoundError(source_url)
    return path


def build_documents(root: Path, workspace: Path) -> tuple[dict[str, Any], list[Document]]:
    manifest = _yaml(workspace / "WORKSPACE.yaml")["workspace"]
    registry = json.loads((workspace / "resource_registry.json").read_text(encoding="utf-8"))
    if manifest["id"] != registry.get("workspace_id"):
        raise ValueError("manifest and registry workspace identities differ")
    if manifest.get("policy", {}).get("mutation") != "proposal_only":
        raise ValueError("only proposal-only workspaces may use this population path")
    if manifest.get("cognee", {}).get("canonical") is not False:
        raise ValueError("only non-canonical Cognee targets may use this population path")

    documents: list[Document] = []
    for record in registry.get("sources", []):
        path = _source_path(root, record["source_url"])
        source_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        metadata = {
            **record,
            "workspace_id": manifest["id"],
            "brand_id": manifest["brand_id"],
            "source_hash": source_hash,
            "projection_role": "research_evidence_or_proposal",
            "promotion_status": "proposal_only",
        }
        document_id = uuid5(
            NAMESPACE_URL,
            f"{manifest['id']}:{record['source_url']}:{source_hash}",
        )
        header = "\n".join(
            (
                f"WORKSPACE_ID: {manifest['id']}",
                f"BRAND_ID: {manifest['brand_id']}",
                f"SOURCE_URL: {record['source_url']}",
                f"SOURCE_HASH: {source_hash}",
                f"DOC_TYPE: {record['doc_type']}",
                f"TASK_VIEW: {record['task_view']}",
                "PROMOTION_STATUS: proposal_only",
                "SOURCE_BEGIN",
            )
        )
        text = f"{header}\n{path.read_text(encoding='utf-8').rstrip()}\nSOURCE_END\n"
        documents.append(Document(document_id, record["source_url"], text, metadata))
    if not documents:
        raise ValueError("registry has no materializable documents")
    return manifest, documents


async def populate(
    *,
    documents: list[Document],
    dataset_name: str,
    credential_root: Path,
) -> dict[str, Any]:
    if not dataset_name.endswith("_staging"):
        raise ValueError("concrete workspace population requires an isolated *_staging dataset")
    credential = _credential(credential_root)
    llm_config, embedding_config = _llm_configs(credential)
    _configure_runtime_environment(llm_config, embedding_config)

    import cognee
    from cognee.tasks.ingestion.data_item import DataItem

    items = [
        DataItem(
            data=document.text,
            label=f"concrete-brand:{document.metadata['unit']}",
            external_metadata=document.metadata,
            data_id=_cognee_data_id(dataset_name, document.document_id),
        )
        for document in documents
    ]
    add_result = await cognee.add(
        items,
        dataset_name=dataset_name,
        incremental_loading=True,
        run_in_background=False,
        llm_config=llm_config,
        embedding_config=embedding_config,
    )
    cognify_result = await cognee.cognify(
        datasets=dataset_name,
        incremental_loading=True,
        run_in_background=False,
        custom_prompt=(
            "This dataset is an isolated, proposal-only Brand research workspace. Preserve "
            "workspace, brand, source, authority, perspective, epistemic status, valid time, "
            "context, relation status, contradictions, and limitations. Treat held relations as "
            "hypotheses. Never invent a fact, merge portfolio brands, or promote canonical state."
        ),
        llm_config=llm_config,
        embedding_config=embedding_config,
    )
    return {
        "add_result_type": type(add_result).__name__,
        "cognify_result_type": type(cognify_result).__name__,
    }


def _report(
    manifest: dict[str, Any],
    documents: list[Document],
    dataset_name: str,
    status: str,
    details: dict[str, Any],
) -> dict[str, Any]:
    return {
        "workspace_id": manifest["id"],
        "brand_id": manifest["brand_id"],
        "dataset_name": dataset_name,
        "canonical": False,
        "promotion_status": "proposal_only",
        "status": status,
        "document_count": len(documents),
        "documents": [
            {
                "document_id": str(document.document_id),
                "source_url": document.source_url,
                "source_hash": document.metadata["source_hash"],
                "doc_type": document.metadata["doc_type"],
                "task_view": document.metadata["task_view"],
            }
            for document in documents
        ],
        "details": details,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path("workspaces/brand-nike-research"),
    )
    parser.add_argument("--credential-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--dataset-name")
    parser.add_argument("--visual-language-dataset-name")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--staging-populate", action="store_true")
    args = parser.parse_args()
    if args.dry_run == args.staging_populate:
        raise SystemExit("choose exactly one of --dry-run or --staging-populate")

    root = args.root.resolve()
    workspace = args.workspace if args.workspace.is_absolute() else root / args.workspace
    manifest, documents = build_documents(root, workspace.resolve())
    dataset_name = args.dataset_name or manifest["cognee"]["dataset_name"]
    visual_language_dataset_name = args.visual_language_dataset_name or (
        f"{dataset_name.removesuffix('_staging')}_visual_language_staging"
    )
    visual_documents = [
        document
        for document in documents
        if document.metadata.get("task_view") == "visual-language"
    ]
    brand_documents = [document for document in documents if document not in visual_documents]
    if args.staging_populate:
        details = asyncio.run(
            populate(
                documents=brand_documents,
                dataset_name=dataset_name,
                credential_root=args.credential_root.resolve(),
            )
        )
        visual_details = asyncio.run(
            populate(
                documents=visual_documents,
                dataset_name=visual_language_dataset_name,
                credential_root=args.credential_root.resolve(),
            )
        )
        details["visual_language"] = visual_details
        status = "staging_populated"
    else:
        details = {
            "would_add": len(brand_documents),
            "would_cognify": True,
            "credentials_read": False,
            "visual_language": {
                "dataset_name": visual_language_dataset_name,
                "would_add": len(visual_documents),
                "would_cognify": True,
            },
        }
        status = "dry_run"

    report = _report(manifest, documents, dataset_name, status, details)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
