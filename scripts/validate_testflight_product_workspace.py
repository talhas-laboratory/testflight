#!/usr/bin/env python3
"""Validate the canonical Testflight Product workspace family."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_RELATIVE = Path("workspaces/testflight-product")
REQUIRED_CHILD_FILES = (
    "AGENT_INDEX.md",
    "AGENT_CONFIG.yaml",
    "WORKSPACE.yaml",
    "artifacts/source_manifest.yaml",
    "artifacts/module-contract.yaml",
    "certification_cases/probes.yaml",
    "resource_registry.json",
)
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
REQUIRED_PROBE_CLASSES = {
    "exact_artifact",
    "intent_route",
    "adversarial_navigation",
    "out_of_domain_no_hit",
}
REQUIRED_ONTOLOGY_TYPES = {"entity", "event", "state", "relation", "claim", "context", "projection"}


def _yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a mapping")
    return value


def _repo_source(root: Path, source_url: str) -> Path:
    if not source_url.startswith("repo://"):
        raise ValueError(f"source_url must use repo://: {source_url}")
    path = (root / source_url.removeprefix("repo://")).resolve()
    if path != root and root.resolve() not in path.parents:
        raise ValueError(f"source escapes repository root: {source_url}")
    if not path.is_file() and not path.is_dir():
        raise FileNotFoundError(f"source does not exist: {source_url}")
    return path


def _validate_registry(root: Path, path: Path, expected_id: str) -> dict[str, Any]:
    registry = json.loads(path.read_text(encoding="utf-8"))
    registry_id = registry.get("workspace_id", registry.get("containerId"))
    if registry_id != expected_id:
        raise ValueError(f"registry identity mismatch: {path}")
    records = registry.get("sources", registry.get("resources"))
    if not isinstance(records, list) or not records:
        raise ValueError(f"registry must contain source records: {path}")
    source_urls: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            raise ValueError(f"registry source must be a mapping: {path}")
        missing = sorted(key for key in REQUIRED_METADATA if record.get(key) in (None, "", []))
        if missing:
            raise ValueError(f"registry source missing {missing}: {path}")
        if record["source_url"] in source_urls:
            raise ValueError(f"duplicate registry source: {record['source_url']}")
        source_urls.add(record["source_url"])
        _repo_source(root, record["source_url"])
    return registry


def _validate_child(root: Path, child: dict[str, Any], parent_id: str) -> dict[str, Any]:
    workspace_root = root / WORKSPACE_RELATIVE
    child_root = workspace_root / child["path"]
    for relative in REQUIRED_CHILD_FILES:
        if not (child_root / relative).is_file():
            raise FileNotFoundError(f"missing child file: {child['id']}/{relative}")

    manifest = _yaml(child_root / "WORKSPACE.yaml")
    config = _yaml(child_root / "AGENT_CONFIG.yaml")
    source_manifest = _yaml(child_root / "artifacts/source_manifest.yaml")
    contract = _yaml(child_root / "artifacts/module-contract.yaml")
    probes = _yaml(child_root / "certification_cases/probes.yaml")
    child_id = child["workspace_id"]
    if manifest.get("id") != child_id or manifest.get("parent") != parent_id:
        raise ValueError(f"child topology identity mismatch: {child['id']}")
    if manifest.get("type") != "child-knowledge-container":
        raise ValueError(f"child must declare child-knowledge-container: {child['id']}")
    dataset = manifest.get("dataset_name")
    if not isinstance(dataset, str) or not dataset.endswith("_staging"):
        raise ValueError(f"child dataset must be isolated staging: {child['id']}")
    if config.get("container_id") != child_id or config.get("dataset_name") != dataset:
        raise ValueError(f"child config identity mismatch: {child['id']}")
    if config.get("route") != child.get("route") or manifest.get("route") != child.get("route"):
        raise ValueError(f"child route mismatch: {child['id']}")
    if source_manifest.get("container_id") != child_id:
        raise ValueError(f"source manifest identity mismatch: {child['id']}")
    if contract.get("workspace_id") != child_id or contract.get("module_id") != child["id"]:
        raise ValueError(f"module contract identity mismatch: {child['id']}")
    probe_items = probes.get("probes")
    if not isinstance(probe_items, list):
        raise ValueError(f"child probes must be a list: {child['id']}")
    probe_classes = {probe.get("class") for probe in probe_items if isinstance(probe, dict)}
    if not probe_classes >= REQUIRED_PROBE_CLASSES:
        raise ValueError(f"child probe classes incomplete: {child['id']}")
    registry = _validate_registry(root, child_root / "resource_registry.json", child_id)
    manifest_sources = source_manifest.get("sources")
    if not isinstance(manifest_sources, list) or set(manifest_sources) != {
        resource["source_url"] for resource in registry["resources"]
    }:
        raise ValueError(f"source manifest and registry differ: {child['id']}")
    return {
        "id": child["id"],
        "workspace_id": child_id,
        "dataset_name": dataset,
        "resource_count": len(registry["resources"]),
        "probe_count": len(probe_items),
        "status": manifest["status"],
    }


def validate_workspace(root: Path = REPO_ROOT) -> dict[str, Any]:
    """Validate identities, boundaries, ontology, sources, routes, and design projection."""

    root = root.resolve()
    workspace_root = root / WORKSPACE_RELATIVE
    required_parent = (
        "AGENT_INDEX.md",
        "AGENT_CONFIG.yaml",
        "WORKSPACE.yaml",
        "artifacts/product-ontology.yaml",
        "artifacts/module-registry.yaml",
        "artifacts/extension-contract.yaml",
        "artifacts/source-catalog.yaml",
        "artifacts/entity-inventory.yaml",
        "artifacts/relationship-inventory.yaml",
        "artifacts/coverage-audit.yaml",
        "artifacts/retrieval-lexicon.yaml",
        "artifacts/registration-receipt.json",
        "certification_cases/probes.yaml",
        "resource_registry.json",
    )
    for relative in required_parent:
        if not (workspace_root / relative).is_file():
            raise FileNotFoundError(f"missing parent file: {relative}")

    manifest = _yaml(workspace_root / "WORKSPACE.yaml")["workspace"]
    parent_id = manifest.get("id")
    if parent_id != "world://workspace/testflight-product":
        raise ValueError("unexpected Testflight Product workspace id")
    if manifest.get("status") != "active":
        raise ValueError("parent workspace must be active")
    children = manifest.get("topology", {}).get("children")
    if not isinstance(children, list) or not children:
        raise ValueError("parent topology must contain children")
    child_ids = [child.get("id") for child in children if isinstance(child, dict)]
    if len(child_ids) != len(children) or len(set(child_ids)) != len(child_ids):
        raise ValueError("child module ids must be non-empty and unique")

    module_registry = _yaml(workspace_root / "artifacts/module-registry.yaml")
    registered = module_registry.get("modules")
    if not isinstance(registered, list):
        raise ValueError("module registry must contain modules")
    registered_ids = {module.get("id") for module in registered if isinstance(module, dict)}
    if registered_ids != set(child_ids):
        raise ValueError("module registry and parent topology differ")

    ontology = _yaml(workspace_root / "artifacts/product-ontology.yaml")
    semantic_types = ontology.get("semantic_types")
    if not isinstance(semantic_types, dict) or set(semantic_types) != REQUIRED_ONTOLOGY_TYPES:
        raise ValueError("product ontology must preserve all core semantic types")
    distinctions = set(ontology.get("distinctions", []))
    required_distinctions = {
        "knowledge_module_is_not_product_capability",
        "product_capability_is_not_software_component",
        "proposal_is_not_accepted_decision",
        "product_design_rule_is_not_customer_brand_evidence",
    }
    if not required_distinctions <= distinctions:
        raise ValueError("product ontology is missing required distinctions")

    source_catalog = _yaml(workspace_root / "artifacts/source-catalog.yaml")
    catalog_sources = source_catalog.get("sources")
    if not isinstance(catalog_sources, list) or not catalog_sources:
        raise ValueError("source catalog must contain sources")
    source_ids = [source.get("id") for source in catalog_sources if isinstance(source, dict)]
    if len(source_ids) != len(catalog_sources) or len(set(source_ids)) != len(source_ids):
        raise ValueError("source catalog ids must be non-empty and unique")
    for source in catalog_sources:
        _repo_source(root, source["source_url"])

    entity_inventory = _yaml(workspace_root / "artifacts/entity-inventory.yaml")
    entities = entity_inventory.get("entities")
    if not isinstance(entities, list) or len(entities) < 40:
        raise ValueError("product entity inventory is not sufficiently populated")
    entity_ids = [entity.get("id") for entity in entities if isinstance(entity, dict)]
    if len(entity_ids) != len(entities) or len(set(entity_ids)) != len(entity_ids):
        raise ValueError("product entity ids must be non-empty and unique")
    required_entity_fields = {
        "id",
        "semantic_type",
        "module_id",
        "name",
        "status",
        "epistemic_status",
        "source_refs",
    }
    for entity in entities:
        missing = sorted(
            field for field in required_entity_fields if entity.get(field) in (None, "", [])
        )
        if missing:
            raise ValueError(f"entity {entity.get('id')} missing fields: {missing}")
        if entity["module_id"] not in registered_ids:
            raise ValueError(f"entity has unknown module: {entity['id']}")
        semantic_root = entity["semantic_type"].split("/", 1)[0]
        if semantic_root not in REQUIRED_ONTOLOGY_TYPES:
            raise ValueError(f"entity has invalid semantic type: {entity['id']}")
        if set(entity["source_refs"]) - set(source_ids):
            raise ValueError(f"entity has unknown source reference: {entity['id']}")
    required_entities = {
        "product:testflight-integration-laboratory",
        "product:founder-brand-world",
        "offer:world-seeder-pilot",
        "offer:campaign-decision-intelligence",
        "surface:brand-intake",
        "surface:brand-lab",
        "surface:creative-studio",
        "capability:semantic-kernel",
        "capability:creative-field",
        "capability:multimodal-content-substrate",
        "hypothesis:founder-input-produces-useful-world",
        "risk:product-direction-ambiguity",
    }
    if not set(entity_ids) >= required_entities:
        raise ValueError("product entity inventory is missing required project entities")

    relationship_inventory = _yaml(workspace_root / "artifacts/relationship-inventory.yaml")
    relations = relationship_inventory.get("relations")
    if not isinstance(relations, list) or not relations:
        raise ValueError("relationship inventory must contain relations")
    relation_ids = [relation.get("id") for relation in relations if isinstance(relation, dict)]
    if len(relation_ids) != len(relations) or len(set(relation_ids)) != len(relation_ids):
        raise ValueError("relationship ids must be non-empty and unique")
    for relation in relations:
        if (
            relation.get("subject_id") not in entity_ids
            or relation.get("object_id") not in entity_ids
        ):
            raise ValueError(f"relationship endpoint is unknown: {relation.get('id')}")
        if set(relation.get("source_refs", [])) - set(source_ids):
            raise ValueError(f"relationship has unknown source reference: {relation.get('id')}")

    coverage = _yaml(workspace_root / "artifacts/coverage-audit.yaml")
    coverage_modules = coverage.get("module_coverage")
    if not isinstance(coverage_modules, dict) or set(coverage_modules) != registered_ids:
        raise ValueError("coverage audit must report every registered module")

    retrieval_lexicon = _yaml(workspace_root / "artifacts/retrieval-lexicon.yaml")
    routes = retrieval_lexicon.get("routes")
    if not isinstance(routes, dict) or set(routes) != registered_ids:
        raise ValueError("retrieval lexicon must cover every registered module")
    for route_id, route in routes.items():
        if not isinstance(route.get("terms"), list) or not route["terms"]:
            raise ValueError(f"retrieval route has no terms: {route_id}")
        if not isinstance(route.get("artifacts"), list) or not route["artifacts"]:
            raise ValueError(f"retrieval route has no artifacts: {route_id}")

    parent_registry = _validate_registry(root, workspace_root / "resource_registry.json", parent_id)
    child_reports = [_validate_child(root, child, parent_id) for child in children]
    datasets = [report["dataset_name"] for report in child_reports]
    if len(datasets) != len(set(datasets)):
        raise ValueError("child staging datasets must be unique")

    design = _yaml(workspace_root / "experience-design/artifacts/design-language.yaml")
    tokens = json.loads((root / "packages/testflight-design-language/tokens.json").read_text())
    if design.get("version") != tokens.get("revision") or design.get("status") != tokens.get(
        "status"
    ):
        raise ValueError("design-language contract and token projection differ")
    if design.get("tokens_projection") != "repo://packages/testflight-design-language/tokens.json":
        raise ValueError("design-language token projection is not explicit")

    receipt = json.loads(
        (workspace_root / "artifacts/registration-receipt.json").read_text(encoding="utf-8")
    )
    if receipt.get("parent_workspace_id") != parent_id:
        raise ValueError("registration receipt parent identity mismatch")
    if receipt.get("live_population_performed") is not False:
        raise ValueError("registration receipt must reflect that no live population occurred")
    registered_children = set(receipt.get("registered_child_workspace_ids", []))
    if registered_children != {child["workspace_id"] for child in children}:
        raise ValueError("registration receipt does not cover every child")
    registry_hashes = receipt.get("source_registry_sha256", {})
    registry_paths = {"parent": workspace_root / "resource_registry.json"}
    registry_paths.update(
        {
            child["id"]: workspace_root / child["path"] / "resource_registry.json"
            for child in children
        }
    )
    for registry_id, registry_path in registry_paths.items():
        actual_hash = hashlib.sha256(registry_path.read_bytes()).hexdigest()
        if registry_hashes.get(registry_id) != actual_hash:
            raise ValueError(f"registration receipt registry hash mismatch: {registry_id}")

    return {
        "status": "pass",
        "workspace_id": parent_id,
        "workspace_version": manifest["version"],
        "parent_resource_count": len(parent_registry["sources"]),
        "module_count": len(child_reports),
        "modules": child_reports,
        "ontology_types": sorted(semantic_types),
        "source_count": len(catalog_sources),
        "entity_count": len(entities),
        "relationship_count": len(relations),
        "design_revision": design["version"],
        "live_projection_changed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    args = parser.parse_args()
    print(json.dumps(validate_workspace(args.root), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
