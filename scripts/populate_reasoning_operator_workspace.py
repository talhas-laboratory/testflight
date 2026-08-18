#!/usr/bin/env python3
"""Validate and populate the reasoning-operator workspace projection."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_RELATIVE = Path("workspaces/reasoning-operators")
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


@dataclass(frozen=True, slots=True)
class MaterializedDocument:
    """One bounded, provenance-bearing source document for Cognee."""

    document_id: UUID
    source_url: str
    text: str
    metadata: dict[str, Any]


def _read_yaml(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text())
    if not isinstance(loaded, dict):
        raise ValueError(f"{path} must contain a mapping")
    return loaded


def _workspace_paths(root: Path) -> tuple[Path, Path, Path]:
    workspace_dir = root / WORKSPACE_RELATIVE
    return (
        workspace_dir,
        workspace_dir / "WORKSPACE.yaml",
        workspace_dir / "resource_registry.json",
    )


def _resolve_source(root: Path, source_url: str) -> Path:
    prefix = "repo://"
    if not source_url.startswith(prefix):
        raise ValueError(f"source_url must use {prefix}: {source_url}")
    source_path = (root / source_url.removeprefix(prefix)).resolve()
    if root.resolve() not in source_path.parents:
        raise ValueError(f"source escapes repository root: {source_url}")
    if not source_path.is_file():
        raise FileNotFoundError(f"source does not exist: {source_url}")
    return source_path


def _source_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_workspace(root: Path) -> dict[str, Any]:
    """Validate the workspace pack and return its loaded metadata."""

    workspace_dir, manifest_path, registry_path = _workspace_paths(root)
    manifest = _read_yaml(manifest_path)["workspace"]
    if not isinstance(manifest, dict):
        raise ValueError(f"{manifest_path} must contain workspace metadata")
    workspace_id = manifest.get("id")
    if not isinstance(workspace_id, str) or not workspace_id.startswith("world://workspace/"):
        raise ValueError("workspace id must use the world://workspace namespace")
    if manifest.get("status") != "active":
        raise ValueError("workspace must be active before population")

    registry = json.loads(registry_path.read_text())
    if registry.get("workspace_id") != workspace_id:
        raise ValueError("resource registry workspace_id does not match manifest")
    source_records = registry.get("sources")
    if not isinstance(source_records, list) or not source_records:
        raise ValueError("resource registry must contain source records")
    for record in source_records:
        if not isinstance(record, dict) or set(REQUIRED_METADATA) - set(record):
            raise ValueError("every source record must satisfy the metadata contract")
        if not record["source_url"]:
            raise ValueError("source_url must not be empty")
        _resolve_source(root, record["source_url"])

    catalog_path = (workspace_dir / manifest["source_of_truth"]).resolve()
    catalog = _read_yaml(catalog_path)
    entries = catalog.get("operators")
    if not isinstance(entries, list) or len(entries) != 16:
        raise ValueError("the workspace must expose exactly 16 catalog operators")
    categories = {entry.get("category") for entry in entries if isinstance(entry, dict)}
    if len(categories) != 16:
        raise ValueError("operator categories must be unique")

    operator_sources = registry.get("operator_sources")
    if not isinstance(operator_sources, list) or len(operator_sources) != len(entries):
        raise ValueError("operator source registry must cover every catalog operator")
    registered_categories = {record.get("category") for record in operator_sources}
    if registered_categories != categories:
        raise ValueError("operator source registry categories do not match catalog")
    for entry in entries:
        if not isinstance(entry, dict) or not all(
            isinstance(entry.get(field), str) and entry[field].strip()
            for field in ("id", "file", "category")
        ):
            raise ValueError("every catalog operator needs id, file, and category")
        source_path = (catalog_path.parent / entry["file"]).resolve()
        if not source_path.is_file():
            raise FileNotFoundError(f"catalog operator is missing: {source_path}")
        operator = _read_yaml(source_path).get("operator")
        if not isinstance(operator, dict) or operator.get("id") != entry["id"]:
            raise ValueError(f"operator identity mismatch: {entry['file']}")

    probes = _read_yaml(workspace_dir / "certification_cases/probes.yaml").get("probes")
    if not isinstance(probes, list) or len(probes) < 4:
        raise ValueError("workspace needs exact, intent, adversarial, and no-hit probes")
    probe_classes = {probe.get("class") for probe in probes if isinstance(probe, dict)}
    if not {"exact_artifact", "intent", "adversarial", "no_hit"} <= probe_classes:
        raise ValueError("certification probes are incomplete")

    return {
        "manifest": manifest,
        "registry": registry,
        "catalog": catalog,
        "catalog_path": catalog_path,
        "workspace_dir": workspace_dir,
    }


def _metadata_for_source(registry: dict[str, Any], source_url: str) -> dict[str, Any]:
    for record in registry["sources"]:
        if record["source_url"] == source_url:
            return dict(record)
    raise KeyError(f"no metadata record for {source_url}")


def _render_document(
    *, root: Path, source_url: str, metadata: dict[str, Any], workspace_id: str
) -> MaterializedDocument:
    source_path = _resolve_source(root, source_url)
    source_text = source_path.read_text()
    source_hash = _source_hash(source_path)
    enriched = {
        **metadata,
        "workspace_id": workspace_id,
        "source_hash": source_hash,
        "source_path": str(source_path.relative_to(root)),
    }
    header = "\n".join(
        [
            f"WORKSPACE_ID: {workspace_id}",
            f"SOURCE_URL: {source_url}",
            f"SOURCE_HASH: {source_hash}",
            f"DOC_TYPE: {metadata['doc_type']}",
            f"TASK_VIEW: {metadata['task_view']}",
            "SOURCE_BEGIN",
        ]
    )
    text = f"{header}\n{source_text.rstrip()}\nSOURCE_END\n"
    document_id = uuid5(NAMESPACE_URL, f"{workspace_id}:{source_url}:{source_hash}")
    return MaterializedDocument(document_id, source_url, text, enriched)


def build_documents(
    root: Path, validated: dict[str, Any] | None = None
) -> list[MaterializedDocument]:
    """Build deterministic documents from the workspace metadata and sources."""

    validated = validated or validate_workspace(root)
    registry = validated["registry"]
    manifest = validated["manifest"]
    sources = [record["source_url"] for record in registry["sources"]]
    sources.extend(record["source_url"] for record in registry["operator_sources"])
    operator_categories = {
        record["source_url"]: record["category"] for record in registry["operator_sources"]
    }
    documents: list[MaterializedDocument] = []
    for source_url in dict.fromkeys(sources):
        try:
            metadata = _metadata_for_source(registry, source_url)
        except KeyError:
            metadata = {
                "module": "reasoning",
                "unit": "operator",
                "task_view": "none",
                "tool": "testflight",
                "doc_type": "operator",
                "evidence_tier": "T1",
                "experience_type": "canonical",
                "difficulty": "expert",
                "canonical": True,
                "last_verified_at": "2026-08-18",
                "source_url": source_url,
            }
        if source_url in operator_categories:
            category = operator_categories[source_url]
            metadata.update(
                {
                    "module": "reasoning",
                    "unit": f"operator/{category}",
                    "task_view": "none",
                    "tool": "testflight",
                    "doc_type": "operator",
                    "evidence_tier": "T1",
                    "experience_type": "canonical",
                    "difficulty": "expert",
                    "canonical": True,
                    "last_verified_at": "2026-08-18",
                    "source_url": source_url,
                }
            )
        documents.append(
            _render_document(
                root=root,
                source_url=source_url,
                metadata=metadata,
                workspace_id=manifest["id"],
            )
        )
    return documents


def _redacted_report(
    *,
    root: Path,
    validated: dict[str, Any],
    documents: list[MaterializedDocument],
    status: str,
    dataset_name: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "workspace_id": validated["manifest"]["id"],
        "workspace_revision": validated["manifest"]["version"],
        "dataset_name": dataset_name,
        "repository_revision": _git_revision(root),
        "status": status,
        "document_count": len(documents),
        "documents": [
            {
                "document_id": str(document.document_id),
                "source_url": document.source_url,
                "source_hash": document.metadata["source_hash"],
                "doc_type": document.metadata["doc_type"],
            }
            for document in documents
        ],
        "details": details or {},
    }


def _git_revision(root: Path) -> str:
    head_path = root / ".git/HEAD"
    if not head_path.is_file():
        return "unknown"
    return head_path.read_text().strip()


def _write_report(root: Path, report: dict[str, Any], report_path: Path | None) -> Path:
    destination = report_path or root / ".data/reasoning-operator-workspace/population-report.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return destination


def _credential() -> str:
    credential = os.getenv("OPENROUTER_API_KEY") or os.getenv("LLM_API_KEY")
    if not credential:
        raise RuntimeError("OPENROUTER_API_KEY or LLM_API_KEY is required for Cognee population")
    return credential


def _configure_process_environment() -> str:
    """Expose the effective provider route to Cognee's process-global settings."""

    credential = _credential()
    endpoint = os.getenv("TESTFLIGHT_COGNEE_LLM_ENDPOINT", "https://openrouter.ai/api/v1")
    model = os.getenv("TESTFLIGHT_COGNEE_LLM_MODEL", "deepseek/deepseek-chat")
    embedding_endpoint = os.getenv("TESTFLIGHT_COGNEE_EMBEDDING_ENDPOINT", endpoint)
    embedding_model = os.getenv(
        "TESTFLIGHT_COGNEE_EMBEDDING_MODEL", "openai/text-embedding-3-small"
    )
    os.environ.setdefault("LLM_" + "API_" + "KEY", credential)
    os.environ.setdefault("LLM_PROVIDER", os.getenv("TESTFLIGHT_COGNEE_LLM_PROVIDER", "openai"))
    os.environ.setdefault("LLM_MODEL", model)
    os.environ.setdefault("LLM_ENDPOINT", endpoint)
    os.environ.setdefault("EMBEDDING_" + "API_" + "KEY", credential)
    os.environ.setdefault(
        "EMBEDDING_PROVIDER", os.getenv("TESTFLIGHT_COGNEE_EMBEDDING_PROVIDER", "openai")
    )
    os.environ.setdefault("EMBEDDING_MODEL", embedding_model)
    os.environ.setdefault("EMBEDDING_ENDPOINT", embedding_endpoint)
    return credential


def _build_llm_configs(credential: str | None = None) -> tuple[Any, Any]:
    from cognee.infrastructure.databases.vector.embeddings.config import EmbeddingConfig
    from cognee.infrastructure.llm.config import LLMConfig

    credential = credential or _credential()
    endpoint = os.getenv("TESTFLIGHT_COGNEE_LLM_ENDPOINT", "https://openrouter.ai/api/v1")
    llm_kwargs = {
        "llm_provider": os.getenv("TESTFLIGHT_COGNEE_LLM_PROVIDER", "openai"),
        "llm_model": os.getenv("TESTFLIGHT_COGNEE_LLM_MODEL", "deepseek/deepseek-chat"),
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


async def populate(documents: list[MaterializedDocument], dataset_name: str) -> dict[str, Any]:
    """Add and cognify the workspace using the optional Cognee dependency."""

    credential = _configure_process_environment()
    import cognee
    from cognee.tasks.ingestion.data_item import DataItem

    items = [
        DataItem(
            data=document.text,
            label=f"reasoning-operator:{document.metadata['unit']}",
            external_metadata=document.metadata,
            data_id=document.document_id,
        )
        for document in documents
    ]
    llm_config, embedding_config = _build_llm_configs(credential)
    add_result = await cognee.add(
        items,
        dataset_name=dataset_name,
        incremental_loading=True,
        run_in_background=False,
        llm_config=llm_config,
        embedding_config=embedding_config,
    )
    custom_prompt = (
        "This dataset contains versioned reasoning operator contracts. Extract only entities "
        "and relationships explicitly grounded in the source text. Preserve operator ids, "
        "versions, categories, evidence, scope, uncertainty, and hold conditions. Do not "
        "infer personal traits, diagnoses, or private chain-of-thought."
    )
    cognify_result = await cognee.cognify(
        datasets=dataset_name,
        incremental_loading=True,
        run_in_background=False,
        custom_prompt=custom_prompt,
        llm_config=llm_config,
        embedding_config=embedding_config,
    )
    return {
        "add_result_type": type(add_result).__name__,
        "cognify_result_type": type(cognify_result).__name__,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    parser.add_argument("--dataset-name", default=None)
    parser.add_argument("--report", type=Path, default=None)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    root = args.root.resolve()
    validated = validate_workspace(root)
    documents = build_documents(root, validated)
    dataset_name = args.dataset_name or validated["manifest"]["cognee"]["dataset_name"]
    if args.validate_only:
        report = _redacted_report(
            root=root,
            validated=validated,
            documents=documents,
            status="validated",
            dataset_name=dataset_name,
        )
    elif args.dry_run:
        report = _redacted_report(
            root=root,
            validated=validated,
            documents=documents,
            status="dry_run",
            dataset_name=dataset_name,
            details={"would_add": len(documents), "would_cognify": True},
        )
    else:
        details = asyncio.run(populate(documents, dataset_name))
        report = _redacted_report(
            root=root,
            validated=validated,
            documents=documents,
            status="populated",
            dataset_name=dataset_name,
            details=details,
        )
    report_path = _write_report(root, report, args.report)
    print(
        f"{report['status']}: workspace={report['workspace_id']} "
        f"dataset={dataset_name} documents={len(documents)} report={report_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
