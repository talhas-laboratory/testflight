#!/usr/bin/env python3
"""Validate a concrete, proposal-only Brand research workspace."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

import yaml
from testflight_semantic import (
    BranchConflict,
    BranchDelta,
    EvidenceLink,
    ExperimentPlan,
    HypothesisRecord,
    LearningUpdate,
    ObservedOutcome,
    PerspectiveProfile,
    RelationshipFrame,
    StateSnapshot,
    WorldBranch,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_ENTITY_TYPES = {
    "identity",
    "expression",
    "offering",
    "experience",
    "perception",
    "governance",
    "environment",
    "event",
}
REQUIRED_RELATIONSHIP_TYPES = {
    "has_component",
    "expressed_through",
    "offers",
    "experienced_through",
    "perceived_by",
    "governed_by",
    "situated_in",
    "evolves_through",
    "shapes",
    "updates",
    "feeds_back_into",
    "supports",
    "contradicts",
    "influences",
}
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
    "intent",
    "adversarial",
    "no_hit",
    "pathing",
    "temporal",
    "contradiction",
}
REQUIRED_STAGES = {"brief", "concept", "production", "review", "post_publication_learning"}


def _yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a mapping")
    return value


def _repo_source(root: Path, source_url: str) -> Path:
    if not source_url.startswith("repo://"):
        raise ValueError(f"registry source must use repo://: {source_url}")
    path = (root / source_url.removeprefix("repo://")).resolve()
    if path != root and root not in path.parents:
        raise ValueError(f"registry source escapes repository: {source_url}")
    if not path.is_file():
        raise FileNotFoundError(f"registry source does not exist: {source_url}")
    return path


def _unique(records: list[dict[str, Any]], key: str, label: str) -> set[str]:
    values = [record.get(key) for record in records]
    if any(not isinstance(value, str) or not value for value in values):
        raise ValueError(f"every {label} needs a non-empty {key}")
    if len(values) != len(set(values)):
        raise ValueError(f"duplicate {label} {key}")
    return set(values)


def _refs(record: dict[str, Any], key: str, allowed: set[str], label: str) -> None:
    values = record.get(key, [])
    if not isinstance(values, list):
        raise ValueError(f"{label} {key} must be a list")
    unknown = set(values) - allowed
    if unknown:
        raise ValueError(f"{label} references unknown {key}: {sorted(unknown)}")


def _ontology_relationships(root: Path) -> dict[str, dict[str, Any]]:
    index = _yaml(root / "domains/brand/ontology/brand-system.yaml")
    result: dict[str, dict[str, Any]] = {}
    ontology_root = root / "domains/brand/ontology"
    for relative in index["relationship_types"]:
        descriptor = _yaml(ontology_root / relative)
        result[descriptor["id"]] = descriptor
    return result


def _iter_nested_refs(value: Any, keys: set[str]) -> list[tuple[str, Any]]:
    found: list[tuple[str, Any]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key in keys:
                found.append((key, child))
            found.extend(_iter_nested_refs(child, keys))
    elif isinstance(value, list):
        for child in value:
            found.extend(_iter_nested_refs(child, keys))
    return found


def _validate_visual_language(
    workspace: Path,
    manifest_workspace_id: str,
    manifest_brand_id: str,
    source_ids: set[str],
    evidence_ids: set[str],
) -> dict[str, int]:
    path = workspace / "visual-language/manifest.json"
    if not path.is_file():
        raise FileNotFoundError(f"visual-language manifest is missing: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("version") != 1:
        raise ValueError("visual-language manifest must use version 1")
    if (
        value.get("workspaceId") != manifest_workspace_id
        or value.get("brandId") != manifest_brand_id
    ):
        raise ValueError("visual-language manifest identity differs from workspace")
    collections = {
        "profiles": value.get("profiles", []),
        "revisions": value.get("revisions", []),
        "references": value.get("references", []),
        "bindings": value.get("bindings", []),
    }
    ids: dict[str, set[str]] = {}
    for name, records in collections.items():
        if not isinstance(records, list) or not records:
            raise ValueError(f"visual-language {name} must be a non-empty list")
        values = [record.get("id") for record in records if isinstance(record, dict)]
        if len(values) != len(records) or any(
            not isinstance(item, str) or not item for item in values
        ):
            raise ValueError(f"visual-language {name} records require ids")
        if len(values) != len(set(values)):
            raise ValueError(f"duplicate visual-language {name} id")
        ids[name] = set(values)
    for reference in collections["references"]:
        if not isinstance(reference.get("kind"), str) or not reference.get("kind"):
            raise ValueError(f"visual reference lacks kind: {reference.get('id')}")
        for key, allowed in (("sourceIds", source_ids), ("evidenceIds", evidence_ids)):
            values = reference.get(key, [])
            if not isinstance(values, list) or not values or set(values) - allowed:
                raise ValueError(f"visual reference has invalid {key}: {reference.get('id')}")
        rights = reference.get("rights")
        if not isinstance(rights, dict) or rights.get("permittedUse") not in {
            "analysis_and_reference",
            "generation",
            "production",
            "none",
        }:
            raise ValueError(f"visual reference has invalid rights: {reference.get('id')}")
    for revision in collections["revisions"]:
        if revision.get("profileId") not in ids["profiles"]:
            raise ValueError(f"visual revision references unknown profile: {revision.get('id')}")
        modules = revision.get("modules", [])
        if not isinstance(modules, list) or not modules:
            raise ValueError(f"visual revision has no modules: {revision.get('id')}")
        for module in modules:
            if not isinstance(module, dict) or module.get("referenceId") not in ids["references"]:
                raise ValueError(f"visual revision has invalid module: {revision.get('id')}")
            if module.get("mode") not in {"replace", "extend", "disable"}:
                raise ValueError(f"visual revision has invalid module mode: {revision.get('id')}")
    for binding in collections["bindings"]:
        if (
            binding.get("profileId") not in ids["profiles"]
            or binding.get("revisionId") not in ids["revisions"]
        ):
            raise ValueError(
                f"visual binding references unknown profile or revision: {binding.get('id')}"
            )
        scope = binding.get("scope")
        if not isinstance(scope, dict) or scope.get("brandId") != manifest_brand_id:
            raise ValueError(f"visual binding crosses brand scope: {binding.get('id')}")
        for key in ("audienceSegmentIds", "workflowStages"):
            if key in scope and (
                not isinstance(scope[key], list)
                or any(not isinstance(item, str) or not item for item in scope[key])
            ):
                raise ValueError(f"visual binding has invalid {key}: {binding.get('id')}")
    return {name: len(records) for name, records in collections.items()}


def _validate_world_modeling(
    workspace: Path,
    workspace_id: str,
    entity_ids: set[str],
    relationship_ids: set[str],
    context_ids: set[str],
    evidence_ids: set[str],
) -> dict[str, int]:
    """Validate candidate overlays independently from accepted Brand records."""

    value = _yaml(workspace / "artifacts/world-modeling.yaml")
    if value.get("version") != 1 or value.get("workspace_id") != workspace_id:
        raise ValueError("world-modeling identity or version differs from workspace")
    links = tuple(EvidenceLink.model_validate(item) for item in value.get("evidence_links", []))
    states = tuple(StateSnapshot.model_validate(item) for item in value.get("states", []))
    perspectives = tuple(
        PerspectiveProfile.model_validate(item) for item in value.get("perspectives", [])
    )
    frames = tuple(
        RelationshipFrame.model_validate(item) for item in value.get("relationship_frames", [])
    )
    branches = tuple(WorldBranch.model_validate(item) for item in value.get("branches", []))
    deltas = tuple(BranchDelta.model_validate(item) for item in value.get("branch_deltas", []))
    conflicts = tuple(BranchConflict.model_validate(item) for item in value.get("conflicts", []))
    hypotheses = tuple(
        HypothesisRecord.model_validate(item) for item in value.get("hypotheses", [])
    )
    experiments = tuple(
        ExperimentPlan.model_validate(item) for item in value.get("experiments", [])
    )
    outcomes = tuple(
        ObservedOutcome.model_validate(item) for item in value.get("observed_outcomes", [])
    )
    learning_updates = tuple(
        LearningUpdate.model_validate(item) for item in value.get("learning_updates", [])
    )
    if not all((links, states, perspectives, frames, branches)):
        raise ValueError("world-modeling needs links, states, perspectives, frames, and branches")
    if any(branch.workspace_id != workspace_id for branch in branches):
        raise ValueError("world-modeling branch crosses workspace boundary")
    branch_ids = _unique(
        [branch.model_dump(mode="json") for branch in branches], "branch_id", "world-model branch"
    )
    link_ids = _unique(
        [link.model_dump(mode="json") for link in links], "link_id", "world-model evidence link"
    )
    state_ids = {state.state_id for state in states}
    perspective_ids = {perspective.perspective_id for perspective in perspectives}
    frame_ids = {frame.frame_id for frame in frames}
    hypothesis_ids = {hypothesis.hypothesis_id for hypothesis in hypotheses}
    experiment_ids = {experiment.experiment_id for experiment in experiments}
    outcome_ids = {outcome.outcome_id for outcome in outcomes}
    world_record_ids = state_ids | perspective_ids | frame_ids | hypothesis_ids
    for link in links:
        if link.evidence_id not in evidence_ids or link.context_id not in context_ids:
            raise ValueError(f"world-model evidence link is out of scope: {link.link_id}")
        if link.target_id not in world_record_ids:
            raise ValueError(f"world-model evidence link has unknown target: {link.link_id}")
    for state in states:
        if set(state.subject_ids) - entity_ids or state.context_id not in context_ids:
            raise ValueError(f"world-model state is out of scope: {state.state_id}")
        if set(state.source_assertion_ids) - relationship_ids:
            raise ValueError(f"world-model state has unknown source assertion: {state.state_id}")
        if set(state.evidence_link_ids) - link_ids:
            raise ValueError(f"world-model state has unknown evidence link: {state.state_id}")
    for perspective in perspectives:
        if perspective.holder_id not in entity_ids or perspective.context_id not in context_ids:
            raise ValueError(
                f"world-model perspective is out of scope: {perspective.perspective_id}"
            )
    for frame in frames:
        if frame.context_id not in context_ids or set(frame.assertion_ids) - relationship_ids:
            raise ValueError(f"world-model frame is out of scope: {frame.frame_id}")
        if set(frame.evidence_link_ids) - link_ids:
            raise ValueError(f"world-model frame has unknown evidence link: {frame.frame_id}")
        bound_ids = {
            record_id for binding in frame.role_bindings for record_id in binding.record_ids
        }
        if bound_ids - entity_ids:
            raise ValueError(f"world-model frame binds unknown entity: {frame.frame_id}")
    if any(delta.branch_id not in branch_ids for delta in deltas):
        raise ValueError("world-model delta targets an unknown branch")
    if any(conflict.branch_id not in branch_ids for conflict in conflicts):
        raise ValueError("world-model conflict targets an unknown branch")
    for hypothesis in hypotheses:
        if hypothesis.branch_id not in branch_ids or hypothesis.context_id not in context_ids:
            raise ValueError(f"hypothesis is out of scope: {hypothesis.hypothesis_id}")
        if set(hypothesis.input_ids) - (entity_ids | world_record_ids):
            raise ValueError(f"hypothesis has unknown input: {hypothesis.hypothesis_id}")
        evidence_link_ids = (
            set(hypothesis.input_evidence_link_ids)
            | set(hypothesis.supporting_evidence_link_ids)
            | set(hypothesis.opposing_evidence_link_ids)
        )
        if evidence_link_ids - link_ids:
            raise ValueError(f"hypothesis has unknown evidence link: {hypothesis.hypothesis_id}")
    for experiment in experiments:
        if experiment.branch_id not in branch_ids or experiment.context_id not in context_ids:
            raise ValueError(f"experiment is out of scope: {experiment.experiment_id}")
        if set(experiment.hypothesis_ids) - hypothesis_ids:
            raise ValueError(f"experiment has unknown hypothesis: {experiment.experiment_id}")
    for outcome in outcomes:
        if outcome.experiment_id not in experiment_ids or outcome.context_id not in context_ids:
            raise ValueError(f"outcome is out of scope: {outcome.outcome_id}")
        if set(outcome.evidence_link_ids) - link_ids:
            raise ValueError(f"outcome has unknown evidence link: {outcome.outcome_id}")
    for learning in learning_updates:
        if learning.hypothesis_id not in hypothesis_ids or learning.context_id not in context_ids:
            raise ValueError(f"learning update is out of scope: {learning.learning_id}")
        if set(learning.outcome_ids) - outcome_ids:
            raise ValueError(f"learning update has unknown outcome: {learning.learning_id}")
    return {
        "evidence_links": len(links),
        "states": len(states),
        "perspectives": len(perspectives),
        "relationship_frames": len(frames),
        "branches": len(branches),
        "branch_deltas": len(deltas),
        "conflicts": len(conflicts),
        "hypotheses": len(hypotheses),
        "experiments": len(experiments),
        "observed_outcomes": len(outcomes),
        "learning_updates": len(learning_updates),
    }


def validate_workspace(
    root: Path = REPO_ROOT,
    workspace_relative: Path = Path("workspaces/brand-nike-research"),
) -> dict[str, Any]:
    root = root.resolve()
    workspace = (root / workspace_relative).resolve()
    manifest = _yaml(workspace / "WORKSPACE.yaml")["workspace"]
    workspace_id = manifest.get("id")
    if manifest.get("status") != "active_research":
        raise ValueError("concrete workspace must be active_research")
    if manifest.get("policy", {}).get("mutation") != "proposal_only":
        raise ValueError("concrete workspace must remain proposal_only")
    if manifest.get("cognee", {}).get("canonical") is not False:
        raise ValueError("concrete workspace Cognee target must be non-canonical")

    catalogs = {
        "sources": _yaml(workspace / "artifacts/source-catalog.yaml"),
        "evidence": _yaml(workspace / "artifacts/evidence-notes.yaml"),
        "contexts": _yaml(workspace / "artifacts/context-profiles.yaml"),
        "entities": _yaml(workspace / "artifacts/entity-inventory.yaml"),
        "relationships": _yaml(workspace / "artifacts/relationship-inventory.yaml"),
        "workflow": _yaml(workspace / "artifacts/asset-workflow-context.yaml"),
        "coverage": _yaml(workspace / "artifacts/coverage-matrix.yaml"),
    }
    for name, catalog in catalogs.items():
        if catalog.get("workspace_id") != workspace_id:
            raise ValueError(f"{name} workspace identity differs from manifest")

    sources = catalogs["sources"].get("sources", [])
    evidence = catalogs["evidence"].get("notes", [])
    contexts = catalogs["contexts"].get("contexts", [])
    entities = catalogs["entities"].get("entities", [])
    relationships = catalogs["relationships"].get("relationships", [])
    required_catalogs = (sources, evidence, contexts, entities, relationships)
    if not all(isinstance(records, list) and records for records in required_catalogs):
        raise ValueError(
            "source, evidence, context, entity, and relationship catalogs must be non-empty"
        )

    source_ids = _unique(sources, "id", "source")
    evidence_ids = _unique(evidence, "id", "evidence note")
    context_ids = _unique(contexts, "id", "context")
    entity_ids = _unique(entities, "id", "entity")
    relationship_ids = _unique(relationships, "id", "relationship")
    visual_counts = _validate_visual_language(
        workspace,
        workspace_id,
        manifest["brand_id"],
        source_ids,
        evidence_ids,
    )
    world_modeling_counts = _validate_world_modeling(
        workspace,
        workspace_id,
        entity_ids,
        relationship_ids,
        context_ids,
        evidence_ids,
    )
    for source in sources:
        if source.get("status") != "verified" or not str(
            source.get("canonical_url", "")
        ).startswith("https://"):
            raise ValueError(f"source is not verified HTTPS evidence: {source.get('id')}")
    for note in evidence:
        if note.get("source_id") not in source_ids:
            raise ValueError(f"evidence note references unknown source: {note.get('id')}")
        _refs(note, "context_ids", context_ids, f"evidence {note['id']}")
        if not note.get("evidence_excerpt") or not note.get("limitations"):
            raise ValueError(f"evidence note lacks excerpt or limitation: {note['id']}")

    entity_counts = Counter(entity.get("entity_type") for entity in entities)
    if set(entity_counts) != REQUIRED_ENTITY_TYPES:
        raise ValueError(f"entity type coverage mismatch: {sorted(entity_counts)}")
    for entity in entities:
        if entity.get("status") not in {"proposed", "held"}:
            raise ValueError(f"entity must remain proposed or held: {entity['id']}")
        if entity.get("status") == "held" and not entity.get("limitations"):
            raise ValueError(f"held entity lacks limitations: {entity['id']}")
        _refs(entity, "evidence_ids", evidence_ids, f"entity {entity['id']}")
        _refs(entity, "context_ids", context_ids, f"entity {entity['id']}")

    relation_descriptors = _ontology_relationships(root)
    relationship_counts = Counter(item.get("relationship_type") for item in relationships)
    if set(relationship_counts) != REQUIRED_RELATIONSHIP_TYPES:
        raise ValueError(f"relationship type coverage mismatch: {sorted(relationship_counts)}")
    entity_types = {entity["id"]: entity["entity_type"] for entity in entities}
    brand_id = manifest["brand_id"]
    for relation in relationships:
        relation_id = relation["id"]
        descriptor = relation_descriptors[relation["relationship_type"]]
        source_id, target_id = relation.get("source_id"), relation.get("target_id")
        source_type = "brand-system" if source_id == brand_id else entity_types.get(source_id)
        target_type = "brand-system" if target_id == brand_id else entity_types.get(target_id)
        if source_type not in descriptor["source_types"]:
            raise ValueError(f"{relation_id} invalid source type {source_type}")
        if target_type not in descriptor["target_types"]:
            raise ValueError(f"{relation_id} invalid target type {target_type}")
        if relation.get("status") not in {"proposed", "held"}:
            raise ValueError(f"{relation_id} has invalid proposal status")
        if relation.get("status") == "held" and not relation.get("limitations"):
            raise ValueError(f"held relation lacks limitations: {relation_id}")
        _refs(relation, "evidence_ids", evidence_ids, f"relationship {relation_id}")
        _refs(relation, "context_ids", context_ids, f"relationship {relation_id}")

    workflow = catalogs["workflow"]
    stages = {recipe.get("stage") for recipe in workflow.get("stage_recipes", [])}
    if stages != REQUIRED_STAGES:
        raise ValueError(f"workflow stage coverage mismatch: {sorted(stages)}")
    allowed = {
        "entity_ids": entity_ids,
        "evidence_ids": evidence_ids,
        "context_ids": context_ids,
        "relationship_ids": relationship_ids,
        "relationship_types": REQUIRED_RELATIONSHIP_TYPES,
    }
    for key, values in _iter_nested_refs(workflow, set(allowed)):
        if not isinstance(values, list) or set(values) - allowed[key]:
            raise ValueError(f"workflow has invalid {key}: {values}")

    coverage = catalogs["coverage"]
    measured_coverage = (
        ("entity_coverage", entity_counts),
        ("relationship_coverage", relationship_counts),
    )
    for kind, observed in measured_coverage:
        declared = coverage.get(kind, {})
        for item, count in observed.items():
            if declared.get(item, {}).get("count") != count:
                raise ValueError(f"coverage count mismatch for {item}")

    registry = json.loads((workspace / "resource_registry.json").read_text(encoding="utf-8"))
    if registry.get("workspace_id") != workspace_id:
        raise ValueError("resource registry workspace identity differs")
    registry_urls: set[str] = set()
    for record in registry.get("sources", []):
        missing = REQUIRED_METADATA - set(record)
        if missing:
            raise ValueError(f"registry record missing metadata: {sorted(missing)}")
        if record["canonical"] is not False:
            raise ValueError("research projection record cannot be canonical")
        if record["source_url"] in registry_urls:
            raise ValueError(f"duplicate registry source: {record['source_url']}")
        registry_urls.add(record["source_url"])
        _repo_source(root, record["source_url"])

    probes = _yaml(workspace / "certification_cases/probes.yaml").get("probes", [])
    probe_ids = _unique(probes, "id", "probe")
    del probe_ids
    probe_classes = {probe.get("case_type") for probe in probes}
    if not probe_classes >= REQUIRED_PROBE_CLASSES:
        raise ValueError(f"probe classes missing: {sorted(REQUIRED_PROBE_CLASSES - probe_classes)}")
    expected_reference_keys = {
        "expected_entity_ids",
        "expected_context_ids",
        "expected_relationship_ids",
    }
    expected_references = {
        "expected_entity_ids": entity_ids,
        "expected_context_ids": context_ids,
        "expected_relationship_ids": relationship_ids,
    }
    for key, values in _iter_nested_refs(probes, expected_reference_keys):
        target = expected_references[key]
        if not isinstance(values, list) or set(values) - target:
            raise ValueError(f"probe has invalid {key}: {values}")

    return {
        "status": "pass",
        "workspace_id": workspace_id,
        "source_count": len(sources),
        "evidence_count": len(evidence),
        "context_count": len(contexts),
        "entity_count": len(entities),
        "entity_counts": dict(sorted(entity_counts.items())),
        "relationship_count": len(relationships),
        "relationship_counts": dict(sorted(relationship_counts.items())),
        "held_relationship_count": sum(r.get("status") == "held" for r in relationships),
        "registry_document_count": len(registry.get("sources", [])),
        "probe_count": len(probes),
        "stage_count": len(stages),
        "visual_language_counts": visual_counts,
        "world_modeling_counts": world_modeling_counts,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    parser.add_argument("--workspace", type=Path, default=Path("workspaces/brand-nike-research"))
    args = parser.parse_args()
    print(json.dumps(validate_workspace(args.root, args.workspace), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
