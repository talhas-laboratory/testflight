#!/usr/bin/env python3
"""Materialize the Brand research pack for Cognee validation, dry-run or gated population."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

import yaml
from validate_brand_ontology_fixtures import validate_fixtures
from validate_brand_research_corpus import validate_corpus

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_RELATIVE = Path("workspaces/brand-ontology-research")
CONTENT_DOC_TYPES = {
    "protocol",
    "source_catalog",
    "evidence_notes",
    "evidence_spans",
    "playbook",
    "candidate_definitions",
    "competency_questions",
    "fixture_catalog",
    "certification",
    "contract",
    "task_view",
}
DEFAULT_STAGING_SUFFIX = "_staging"
AUTHORIZATION_RECEIPT = Path("certification_cases/projection-certification.json")


@dataclass(frozen=True, slots=True)
class MaterializedDocument:
    document_id: UUID
    source_url: str
    text: str
    metadata: dict[str, Any]


def _read_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a mapping")
    return value


def _resolve_source(root: Path, source_url: str) -> Path:
    if not source_url.startswith("repo://"):
        raise ValueError(f"source_url must use repo://: {source_url}")
    path = (root / source_url.removeprefix("repo://")).resolve()
    if root.resolve() not in path.parents:
        raise ValueError(f"source escapes repository root: {source_url}")
    if not path.is_file():
        raise FileNotFoundError(f"source does not exist: {source_url}")
    return path


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _revision(root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def validate_pack(root: Path = REPO_ROOT) -> dict[str, Any]:
    workspace = root / WORKSPACE_RELATIVE
    manifest = _read_yaml(workspace / "WORKSPACE.yaml")["workspace"]
    registry = json.loads((workspace / "resource_registry.json").read_text(encoding="utf-8"))
    corpus = validate_corpus(root)
    fixtures = validate_fixtures()
    if manifest["id"] != registry["workspace_id"]:
        raise ValueError("workspace and resource registry identities differ")
    return {
        "workspace": workspace,
        "manifest": manifest,
        "registry": registry,
        "corpus": corpus,
        "fixtures": fixtures,
    }


def _authorization_receipt(root: Path) -> dict[str, Any]:
    """Load the tracked projection authorization receipt, if one exists."""

    path = root / WORKSPACE_RELATIVE / AUTHORIZATION_RECEIPT
    if not path.is_file():
        raise RuntimeError(
            "projection population is authorized only by a tracked certification receipt: "
            f"{AUTHORIZATION_RECEIPT}"
        )
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise RuntimeError(f"invalid projection authorization receipt: {path}") from error
    if not isinstance(value, dict):
        raise RuntimeError("projection authorization receipt must contain a JSON object")
    return value


def _require_authorized_release(
    *,
    root: Path,
    validated: dict[str, Any],
    documents: list[MaterializedDocument],
    dataset_name: str,
) -> dict[str, Any]:
    """Require a receipt that matches the exact materialized source set."""

    manifest = validated["manifest"]
    if manifest["cognee"]["population_status"] != "projection_certified":
        raise RuntimeError(
            "Cognee population is gated: certify projection retrieval and change "
            "population_status explicitly"
        )
    receipt = _authorization_receipt(root)
    if receipt.get("status") != "pass" or receipt.get("authorized") is not True:
        raise RuntimeError("projection authorization receipt is not a passing authorized release")
    if receipt.get("workspace_id") != manifest["id"]:
        raise RuntimeError("projection authorization receipt workspace does not match the manifest")
    if receipt.get("dataset_name") != dataset_name:
        raise RuntimeError("projection authorization receipt dataset does not match the target")
    expected_documents = {
        (str(document.document_id), document.source_url, document.metadata["source_hash"])
        for document in documents
    }
    certified_documents = {
        (str(item.get("document_id")), item.get("source_url"), item.get("source_hash"))
        for item in receipt.get("documents", [])
        if isinstance(item, dict)
    }
    if certified_documents != expected_documents:
        raise RuntimeError(
            "projection authorization receipt does not match the current source pack"
        )
    return receipt


def _render_document(
    *, root: Path, workspace_id: str, source_url: str, metadata: dict[str, Any]
) -> MaterializedDocument:
    path = _resolve_source(root, source_url)
    source_hash = _hash(path)
    enriched = {
        **metadata,
        "workspace_id": workspace_id,
        "source_hash": source_hash,
        "source_path": str(path.relative_to(root)),
        "projection_role": "research_evidence_or_candidate",
    }
    header = "\n".join(
        [
            f"WORKSPACE_ID: {workspace_id}",
            f"SOURCE_URL: {source_url}",
            f"SOURCE_HASH: {source_hash}",
            f"DOC_TYPE: {metadata['doc_type']}",
            f"TASK_VIEW: {metadata['task_view']}",
            "PROMOTION_STATUS: proposal_only",
            "SOURCE_BEGIN",
        ]
    )
    text = f"{header}\n{path.read_text(encoding='utf-8').rstrip()}\nSOURCE_END\n"
    document_id = uuid5(NAMESPACE_URL, f"{workspace_id}:{source_url}:{source_hash}")
    return MaterializedDocument(document_id, source_url, text, enriched)


def build_documents(
    root: Path = REPO_ROOT, validated: dict[str, Any] | None = None
) -> list[MaterializedDocument]:
    validated = validated or validate_pack(root)
    manifest = validated["manifest"]
    documents: list[MaterializedDocument] = []
    for record in validated["registry"]["sources"]:
        if record["doc_type"] not in CONTENT_DOC_TYPES:
            continue
        documents.append(
            _render_document(
                root=root,
                workspace_id=manifest["id"],
                source_url=record["source_url"],
                metadata=dict(record),
            )
        )
    if not documents:
        raise ValueError("research projection has no content documents")
    return documents


def _report(
    *,
    root: Path,
    validated: dict[str, Any],
    documents: list[MaterializedDocument],
    status: str,
    dataset_name: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    registry_count = len(validated["registry"]["sources"])
    return {
        "workspace_id": validated["manifest"]["id"],
        "dataset_name": dataset_name,
        "repository_revision": _revision(root),
        "status": status,
        "document_count": len(documents),
        "registry_source_count": registry_count,
        "corpus": validated["corpus"],
        "fixtures": {
            "status": validated["fixtures"]["status"],
            "world_count": validated["fixtures"]["world_count"],
        },
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
        "details": details or {},
    }


def _credential(root: Path) -> str:
    credential = os.getenv("OPENROUTER_API_KEY") or os.getenv("LLM_API_KEY")
    env_path = root / ".env"
    if not credential and env_path.is_file():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            name, separator, value = line.partition("=")
            if separator and name in {"OPENROUTER_API_KEY", "LLM_API_KEY"} and value.strip():
                credential = value.strip()
                break
    if not credential:
        raise RuntimeError("OPENROUTER_API_KEY or LLM_API_KEY is required for population")
    return credential


def _llm_configs(credential: str) -> tuple[Any, Any]:
    from cognee.infrastructure.databases.vector.embeddings.config import EmbeddingConfig
    from cognee.infrastructure.llm.config import LLMConfig

    endpoint = os.getenv("TESTFLIGHT_COGNEE_LLM_ENDPOINT", "https://openrouter.ai/api/v1")
    llm_kwargs = {
        "llm_provider": os.getenv("TESTFLIGHT_COGNEE_LLM_PROVIDER", "openai"),
        "llm_model": os.getenv("TESTFLIGHT_COGNEE_LLM_MODEL", "openai/deepseek/deepseek-chat"),
        "llm_endpoint": endpoint,
        "llm_temperature": 0.0,
        "llm_" + "api_" + "key": credential,
    }
    llm = LLMConfig(**llm_kwargs)
    embedding_kwargs = {
        "embedding_provider": os.getenv("TESTFLIGHT_COGNEE_EMBEDDING_PROVIDER", "openai"),
        "embedding_model": os.getenv(
            "TESTFLIGHT_COGNEE_EMBEDDING_MODEL", "openai/text-embedding-3-small"
        ),
        "embedding_endpoint": os.getenv("TESTFLIGHT_COGNEE_EMBEDDING_ENDPOINT", endpoint),
        "embedding_" + "api_" + "key": credential,
    }
    embedding = EmbeddingConfig(**embedding_kwargs)
    return llm, embedding


async def populate(
    *,
    root: Path,
    documents: list[MaterializedDocument],
    dataset_name: str,
    staging: bool = False,
) -> dict[str, Any]:
    validated = validate_pack(root)
    if staging:
        if not dataset_name.endswith(DEFAULT_STAGING_SUFFIX):
            raise ValueError(f"staging population dataset must end with {DEFAULT_STAGING_SUFFIX!r}")
        authorization = {"mode": "staging", "authorized": False}
    else:
        authorization = _require_authorized_release(
            root=root,
            validated=validated,
            documents=documents,
            dataset_name=dataset_name,
        )
    credential = _credential(root)
    import cognee
    from cognee.tasks.ingestion.data_item import DataItem

    items = [
        DataItem(
            data=document.text,
            label=f"brand-research:{document.metadata['unit']}",
            external_metadata=document.metadata,
            data_id=document.document_id,
        )
        for document in documents
    ]
    llm_config, embedding_config = _llm_configs(credential)
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
            "This is a Brand ontology research dataset. Preserve source URLs, evidence spans, "
            "authority tiers, scope, time, perspectives, contradictions and proposal status. "
            "Do not promote candidates, invent Brand facts, or collapse intended and "
            "observed views."
        ),
        llm_config=llm_config,
        embedding_config=embedding_config,
    )
    return {
        "add_result_type": type(add_result).__name__,
        "cognify_result_type": type(cognify_result).__name__,
        "mode": "staging" if staging else "authorized",
        "authorization": authorization,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    parser.add_argument("--dataset-name", default=None)
    parser.add_argument("--report", type=Path, default=None)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--populate", action="store_true")
    parser.add_argument(
        "--staging-populate",
        action="store_true",
        help="populate an isolated *_staging dataset without changing the manifest status",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if sum((args.validate_only, args.dry_run, args.populate, args.staging_populate)) > 1:
        raise SystemExit(
            "choose only one of --validate-only, --dry-run, --populate or --staging-populate"
        )
    root = args.root.resolve()
    validated = validate_pack(root)
    documents = build_documents(root, validated)
    default_dataset = validated["manifest"]["cognee"]["dataset_name"]
    dataset_name = args.dataset_name or (
        f"{default_dataset}{DEFAULT_STAGING_SUFFIX}" if args.staging_populate else default_dataset
    )
    if args.populate:
        details = asyncio.run(
            populate(root=root, documents=documents, dataset_name=dataset_name, staging=False)
        )
        status = "populated"
    elif args.staging_populate:
        details = asyncio.run(
            populate(root=root, documents=documents, dataset_name=dataset_name, staging=True)
        )
        status = "staging_populated"
    elif args.dry_run:
        details = {"would_add": len(documents), "would_cognify": True, "credentials_read": False}
        status = "dry_run"
    else:
        details = {"credentials_read": False}
        status = "validated"
    report = _report(
        root=root,
        validated=validated,
        documents=documents,
        status=status,
        dataset_name=dataset_name,
        details=details,
    )
    report_path = args.report or root / ".data/brand-research/population-report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"{status}: workspace={report['workspace_id']} dataset={dataset_name} "
        f"documents={len(documents)} report={report_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
