#!/usr/bin/env python3
# ruff: noqa: E501
"""Create a source-grounded, isolated public Brand research workspace.

The generated files are canonical research records.  Cognee remains a
rebuildable projection and is never copied between workspaces.
"""

from __future__ import annotations

import argparse
import json
import shutil
from collections import Counter
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
ENTITY_TYPES = (
    "identity",
    "expression",
    "offering",
    "experience",
    "perception",
    "governance",
    "environment",
    "event",
)
RELATIONSHIPS = (
    ("has_component", "brand", "identity"),
    ("expressed_through", "brand", "expression"),
    ("offers", "brand", "offering"),
    ("experienced_through", "offering", "experience"),
    ("perceived_by", "brand", "environment"),
    ("governed_by", "brand", "governance"),
    ("situated_in", "brand", "environment"),
    ("evolves_through", "brand", "event"),
    ("shapes", "offering", "perception"),
    ("updates", "event", "identity"),
    ("feeds_back_into", "perception", "identity"),
    ("supports", "offering", "identity"),
    ("contradicts", "offering", "perception"),
    ("influences", "offering", "environment"),
)


def dump_yaml(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False, allow_unicode=True), encoding="utf-8")


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def load_seed(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("seed must be a YAML mapping")
    required = {"slug", "name", "brand_id", "base_url", "sources", "evidence", "entities"}
    missing = required - set(value)
    if missing:
        raise ValueError(f"seed lacks required keys: {sorted(missing)}")
    return value


def scaffold(root: Path, seed: dict[str, Any], *, apply: bool) -> Path:
    slug = str(seed["slug"])
    workspace_id = f"world://workspace/brand/{slug}-research"
    brand_id = str(seed["brand_id"])
    target = root / "workspaces" / f"brand-{slug}-research"
    if target.exists():
        raise FileExistsError(f"refusing to overwrite existing workspace: {target}")
    if not apply:
        return target

    template = root / "workspaces/brand-template"
    shutil.copytree(template, target)
    for child in ("artifacts", "visual-language"):
        (target / child).mkdir(exist_ok=True)

    today = str(seed.get("last_verified_at", "2026-08-31"))
    dataset = f"testflight_brand_{slug.replace('-', '_')}_research_staging"
    context_id = f"CTX-{slug.upper().replace('-', '-')}-GLOBAL-CURRENT"
    evidence = list(seed["evidence"])
    entities = list(seed["entities"])
    by_type = {item["entity_type"]: item for item in entities}
    absent = set(ENTITY_TYPES) - set(by_type)
    if absent:
        raise ValueError(f"seed needs one source-grounded entity per type: {sorted(absent)}")
    evidence_id = evidence[0]["id"]

    manifest = {
        "workspace": {
            "id": workspace_id,
            "version": 1,
            "status": "active_research",
            "name": f"{seed['name']} Brand Research Sandbox",
            "mission": "Provide an isolated, source-grounded public research workspace for workflow-aware Brand context retrieval.",
            "brand_id": brand_id,
            "subject_scope": f"Publicly documented {seed['name']} brand and product ecosystem only.",
            "ontology": {
                "source": "../../domains/brand/ontology/brand-system.yaml",
                "version": "1.0.0",
                "policies": [
                    "../../domains/brand/policies/identity-resolution-v1.yaml",
                    "../../domains/brand/policies/assertion-acceptance-v1.yaml",
                    "../../domains/brand/policies/relationship-weight-v1.yaml",
                ],
            },
            "source_of_truth": {
                "evidence": "artifacts/evidence-notes.yaml",
                "proposals": "artifacts/entity-inventory.yaml",
                "relationships": "artifacts/relationship-inventory.yaml",
                "world_modeling": "artifacts/world-modeling.yaml",
            },
            "cognee": {
                "dataset_name": dataset,
                "runtime_root": "/home/talha/testflight/.data/cognee",
                "population_status": "not_populated",
                "canonical": False,
            },
            "storage": {
                "runtime_root": f"/home/talha/testflight/.data/brand-workspaces/{slug}-research",
                "evidence_root": f"/home/talha/testflight/.data/brand-workspaces/{slug}-research/evidence",
                "semantic_repository": f"/home/talha/testflight/.data/brand-workspaces/{slug}-research/semantic.sqlite3",
            },
            "topology": {
                "parent": f"{slug}-research",
                "children": [
                    {
                        "id": "research",
                        "path": "task_views/research.md",
                        "purpose": "locate and register public evidence",
                    },
                    {
                        "id": "entity",
                        "path": "task_views/entity.md",
                        "purpose": "retrieve scoped entity proposals",
                    },
                    {
                        "id": "relationship",
                        "path": "task_views/relationship.md",
                        "purpose": "retrieve bounded relationship paths",
                    },
                    {
                        "id": "asset-context",
                        "path": "task_views/asset-context.md",
                        "purpose": "compile workflow context",
                    },
                    {
                        "id": "world-modeling",
                        "path": "artifacts/world-modeling.yaml",
                        "purpose": "compile branch-aware agent world views",
                    },
                    {
                        "id": "visual-language",
                        "path": "visual-language/AGENT_INDEX.md",
                        "purpose": "resolve versioned public visual references",
                    },
                ],
            },
            "scope": {
                "includes": [
                    "public identity, products, experience, expression, and evidence",
                    "versioned public visual-language observations",
                    "proposal-only hypotheses and experiment plans",
                ],
                "excludes": [
                    "confidential strategy, customers, and internal guidelines",
                    "medical efficacy conclusions beyond documented source wording",
                    "accepted canonical facts",
                    "generated indexes and secrets",
                ],
            },
            "policy": {
                "evidence_strictness": "citation_required",
                "uncertainty_policy": "branch",
                "mutation": "proposal_only",
                "action": "deny_unless_authorized",
                "no_hit": "valid",
                "graph_max_hops": 2,
                "retrieval_order": "bm25_then_bounded_hybrid_same_child",
                "source_refresh_days": 90,
            },
        }
    }
    dump_yaml(target / "WORKSPACE.yaml", manifest)

    # Normalize every candidate to the workspace, its sole verified context, and proposal-only status.
    normalized_entities = []
    for item in entities:
        normalized_entities.append(
            {
                **item,
                "context_ids": item.get("context_ids", [context_id]),
                "evidence_ids": item.get("evidence_ids", [evidence_id]),
                "status": item.get("status", "proposed"),
                "perspective": item.get("perspective", "reported"),
                "epistemic_status": item.get("epistemic_status", "reported"),
            }
        )
    dump_yaml(
        target / "artifacts/entity-inventory.yaml",
        {
            "version": 1,
            "workspace_id": workspace_id,
            "brand_id": brand_id,
            "ontology_version": "1.0.0",
            "mutation_status": "proposal_only",
            "entities": normalized_entities,
        },
    )
    dump_yaml(
        target / "artifacts/source-catalog.yaml",
        {
            "version": 1,
            "workspace_id": workspace_id,
            "status": "bounded_public_research_corpus",
            "last_verified_at": today,
            "source_policy": {
                "full_text_storage": "prohibited",
                "bounded_excerpt_required": True,
                "primary_source_for_self_claims": True,
                "independent_source_for_perception": True,
            },
            "sources": seed["sources"],
        },
    )
    normalized_evidence = [
        {
            **item,
            "context_ids": item.get("context_ids", [context_id]),
            "limitations": item.get(
                "limitations",
                [
                    "Publisher-authored public material; it does not establish internal policy or independent effectiveness."
                ],
            ),
        }
        for item in evidence
    ]
    dump_yaml(
        target / "artifacts/evidence-notes.yaml",
        {
            "version": 1,
            "workspace_id": workspace_id,
            "recorded_time": today,
            "notes": normalized_evidence,
        },
    )
    contexts = seed.get(
        "contexts",
        [
            {
                "id": context_id,
                "brand_id": brand_id,
                "branch_id": "research-main",
                "valid_time": {"from": None, "through": today},
                "geography": "availability_not_independently_verified",
                "perspective_scope": ["intended", "reported", "observed", "inferred"],
                "purpose": f"Current public {seed['name']} research context.",
            }
        ],
    )
    dump_yaml(
        target / "artifacts/context-profiles.yaml",
        {"version": 1, "workspace_id": workspace_id, "contexts": contexts},
    )

    relationships = []
    for number, (kind, source_kind, target_kind) in enumerate(RELATIONSHIPS, 1):
        source_id = brand_id if source_kind == "brand" else by_type[source_kind]["id"]
        target_id = by_type[target_kind]["id"]
        held = kind in {"shapes", "feeds_back_into", "contradicts", "influences"}
        relationships.append(
            {
                "id": f"REL-{slug.upper()}-{number:03d}",
                "relationship_type": kind,
                "source_id": source_id,
                "target_id": target_id,
                "assertion": f"Public research models {kind.replace('_', ' ')} between {source_id} and {target_id}.",
                "perspective": "inferred" if held else "reported",
                "epistemic_status": "inferred" if held else "reported",
                "status": "held" if held else "proposed",
                "context_ids": [context_id],
                "evidence_ids": [evidence_id],
                **(
                    {
                        "limitations": [
                            "This is a testable modeling relation; public evidence does not establish causal effect or internal decision use."
                        ]
                    }
                    if held
                    else {}
                ),
            }
        )
    dump_yaml(
        target / "artifacts/relationship-inventory.yaml",
        {
            "version": 1,
            "workspace_id": workspace_id,
            "brand_id": brand_id,
            "ontology_version": "1.0.0",
            "mutation_status": "proposal_only",
            "relationships": relationships,
        },
    )

    identity, expression, offering, experience, perception, governance, environment, event = (
        by_type[name] for name in ENTITY_TYPES
    )
    rel_by_type = {record["relationship_type"]: record["id"] for record in relationships}
    state_id, frame_id, perspective_id = (
        f"STATE-{slug.upper()}-PUBLIC-CORE-001",
        f"FRAME-{slug.upper()}-OFFER-EXPERIENCE-001",
        f"PERS-{slug.upper()}-PUBLIC-CUSTOMER-001",
    )
    links = [
        {
            "link_id": f"EVIDLINK-{slug.upper()}-001",
            "evidence_id": evidence_id,
            "target_id": state_id,
            "role": "supports",
            "context_id": context_id,
            "derivation_id": f"DERIV-{slug.upper()}-PUBLIC-001",
            "note": "Supports the bounded public state.",
        },
        {
            "link_id": f"EVIDLINK-{slug.upper()}-002",
            "evidence_id": evidence_id,
            "target_id": frame_id,
            "role": "supports",
            "context_id": context_id,
            "derivation_id": f"DERIV-{slug.upper()}-PUBLIC-001",
            "note": "Supports the public offering-to-experience frame.",
        },
    ]
    world = {
        "version": 1,
        "workspace_id": workspace_id,
        "purpose": "Proposal-only semantic overlays over bounded public evidence.",
        "evidence_links": links,
        "states": [
            {
                "state_id": state_id,
                "version": 1,
                "subject_ids": [identity["id"], offering["id"]],
                "state_type_id": "world://ontology/brand/state/public-brand-core",
                "context_id": context_id,
                "values": [
                    {
                        "key": "research_scope",
                        "value": "publicly documented brand and product claims only",
                    }
                ],
                "source_assertion_ids": [rel_by_type["offers"], rel_by_type["supports"]],
                "evidence_link_ids": [links[0]["link_id"]],
                "status": "supported",
                "derivation_id": f"DERIV-{slug.upper()}-PUBLIC-001",
            }
        ],
        "perspectives": [
            {
                "perspective_id": perspective_id,
                "holder_id": environment["id"],
                "perspective_type_id": "world://ontology/brand/perspective/public-potential-customer",
                "context_id": context_id,
                "goals": ["Understand documented benefits and limits before evaluating an offer."],
                "accessible_record_selectors": [identity["id"], offering["id"], experience["id"]],
                "known_limitations": [
                    "No validated ICP, purchase behavior, eligibility, or individual health outcome is established."
                ],
                "derivation_id": f"DERIV-{slug.upper()}-PUBLIC-001",
            }
        ],
        "relationship_frames": [
            {
                "frame_id": frame_id,
                "frame_type_id": "world://ontology/brand/frame/public-offering-experience",
                "context_id": context_id,
                "role_bindings": [
                    {"role_id": "brand", "record_ids": [identity["id"]]},
                    {"role_id": "offering", "record_ids": [offering["id"]]},
                    {"role_id": "experience", "record_ids": [experience["id"]]},
                    {"role_id": "environment", "record_ids": [environment["id"]]},
                ],
                "assertion_ids": [rel_by_type["offers"], rel_by_type["experienced_through"]],
                "status": "supported",
                "evidence_link_ids": [links[1]["link_id"]],
                "derivation_id": f"DERIV-{slug.upper()}-PUBLIC-001",
            }
        ],
        "hypotheses": [],
        "experiments": [],
        "observed_outcomes": [],
        "learning_updates": [],
        "branches": [
            {
                "branch_id": "research-main",
                "workspace_id": workspace_id,
                "branch_kind": "interpretation",
                "label": "Source-grounded public research view",
                "created_by": "testflight-public-brand-scaffold",
                "created_at": f"{today}T00:00:00Z",
                "status": "active",
                "derivation_id": f"DERIV-{slug.upper()}-PUBLIC-001",
            }
        ],
        "branch_deltas": [],
        "conflicts": [],
    }
    dump_yaml(target / "artifacts/world-modeling.yaml", world)

    stage_recipes = [
        {
            "stage": stage,
            "goal": goal,
            "always_include": {
                "entity_ids": [identity["id"], offering["id"]],
                "context_ids": [context_id],
            },
            "reasoning_instructions": [
                "Preserve source wording, evidence tier, scope, and time.",
                "Do not turn brand claims into independent health, audience, or performance facts.",
                "Return partial or ask when proprietary standards or validated customer data are necessary.",
            ],
        }
        for stage, goal in (
            ("brief", "Turn the request into a bounded public-evidence brief."),
            (
                "concept",
                "Develop concepts without treating public observations as a complete brand system.",
            ),
            (
                "production",
                "Translate an approved concept while holding missing internal standards.",
            ),
            ("review", "Check source grounding, scope, and unsupported claims."),
            (
                "post_publication_learning",
                "Record only authorized outcomes and avoid causal claims without a test.",
            ),
        )
    ]
    dump_yaml(
        target / "artifacts/asset-workflow-context.yaml",
        {
            "version": 1,
            "workspace_id": workspace_id,
            "purpose": "Compile the smallest evidence-backed public context packet for a brand workflow.",
            "interpretation_contract": {
                "required_inputs": [
                    "workflow_stage",
                    "asset_type",
                    "objective",
                    "audience",
                    "channel",
                    "geography",
                    "occasion",
                    "valid_time",
                ],
                "missing_material_input_outcome": "ask",
                "ambiguous_scope_outcome": "branch",
                "unsupported_scope_outcome": "no_hit",
                "never_infer": [
                    "medical efficacy",
                    "internal approval",
                    "validated customer behavior",
                    "causal effectiveness",
                ],
            },
            "packet_contract": {
                "maximum_graph_hops": 2,
                "preserve_perspective_labels": True,
                "preserve_held_hypotheses": True,
            },
            "stage_recipes": stage_recipes,
        },
    )
    entity_counts = Counter(item["entity_type"] for item in normalized_entities)
    relationship_counts = Counter(item["relationship_type"] for item in relationships)
    dump_yaml(
        target / "artifacts/coverage-matrix.yaml",
        {
            "version": 1,
            "workspace_id": workspace_id,
            "research_cutoff": today,
            "entity_coverage": {
                key: {"count": value, "status": "public_seeded"}
                for key, value in entity_counts.items()
            },
            "relationship_coverage": {
                key: {
                    "count": value,
                    "status": "held_pending_specific_evidence"
                    if key in {"shapes", "feeds_back_into", "contradicts", "influences"}
                    else "public_seeded",
                }
                for key, value in relationship_counts.items()
            },
            "known_gaps": [
                {
                    "id": f"GAP-{slug.upper()}-001",
                    "area": "proprietary_brand_standards",
                    "consequence": "Public materials do not establish approved design, legal, regulatory, or production rules.",
                    "required_source": "authorized_internal_standard",
                },
                {
                    "id": f"GAP-{slug.upper()}-002",
                    "area": "validated_customer_segments_and_outcomes",
                    "consequence": "The public site does not establish ICPs, purchase behavior, clinical outcomes, or campaign effectiveness.",
                    "required_source": "authorized_customer_research_or_outcome_data",
                },
            ],
        },
    )

    source_ids = [item["id"] for item in seed["sources"]]
    visual = {
        "version": 1,
        "workspaceId": workspace_id,
        "brandId": brand_id,
        "profiles": [
            {
                "id": f"VL-{slug.upper()}-PUBLIC",
                "label": f"{seed['name']} public visual observations",
                "description": "Versioned public observations, not a proprietary design system.",
                "status": "observed",
            }
        ],
        "references": [
            {
                "id": f"VR-{slug.upper()}-PUBLIC-001",
                "revision": 1,
                "kind": "imagery.art_direction",
                "schemaVersion": 1,
                "label": "Public storefront visual observation",
                "payload": {
                    "observation": "Use source-linked site imagery only as a bounded public reference; no typography, color, layout, or asset right is implied beyond the source record."
                },
                "assetRefs": [],
                "authority": "observed_public",
                "epistemicStatus": "observed",
                "status": "observed",
                "sourceIds": [source_ids[0]],
                "evidenceIds": [evidence_id],
                "validFrom": today,
                "recordedAt": f"{today}T00:00:00Z",
                "lastVerifiedAt": today,
                "rights": {
                    "permittedUse": "analysis_and_reference",
                    "generationUse": "inspiration_only",
                },
                "limitations": [
                    "Requires approved internal assets and standards before production."
                ],
                "slot": "imagery.public-storefront",
            }
        ],
        "revisions": [
            {
                "id": f"VL-{slug.upper()}-PUBLIC@1",
                "profileId": f"VL-{slug.upper()}-PUBLIC",
                "revision": 1,
                "branch": "main",
                "parentRevisionIds": [],
                "modules": [
                    {
                        "slot": "imagery.public-storefront",
                        "referenceId": f"VR-{slug.upper()}-PUBLIC-001",
                        "mode": "extend",
                    }
                ],
                "authority": "observed_public",
                "epistemicStatus": "observed",
                "status": "observed",
                "validFrom": today,
                "recordedAt": f"{today}T00:00:00Z",
                "lastVerifiedAt": today,
                "sourceIds": [source_ids[0]],
                "evidenceIds": [evidence_id],
                "limitations": ["Public observation only."],
                "gaps": [
                    "color palette",
                    "typography",
                    "grid",
                    "component system",
                    "motion",
                    "accessibility",
                    "approval rules",
                ],
            }
        ],
        "bindings": [
            {
                "id": f"BIND-{slug.upper()}-PUBLIC-001",
                "profileId": f"VL-{slug.upper()}-PUBLIC",
                "revisionId": f"VL-{slug.upper()}-PUBLIC@1",
                "scope": {"brandId": brand_id},
                "priority": 10,
                "status": "observed",
                "validFrom": today,
                "recordedAt": f"{today}T00:00:00Z",
                "lastVerifiedAt": today,
                "sourceIds": [source_ids[0]],
                "evidenceIds": [evidence_id],
                "limitations": ["Do not use as a substitute for a proprietary visual language."],
            }
        ],
    }
    (target / "visual-language/manifest.json").write_text(
        json.dumps(visual, indent=2) + "\n", encoding="utf-8"
    )
    write(
        target / "visual-language/AGENT_INDEX.md",
        "# Visual language\n\nResolve the active bounded public profile first. Return gaps instead of inventing design rules.",
    )
    dump_yaml(
        target / "visual-language/AGENT_CONFIG.yaml",
        {
            "workspace_id": workspace_id,
            "route": "visual-language",
            "retrieval_order": ["exact", "bm25", "bounded_hybrid_same_child"],
            "production_requires": "authorized_internal_standards",
        },
    )
    write(
        target / "visual-language/README.md",
        "# Public visual-language observations\n\nThis module stores rights-bounded observations and versioned references, not production-ready brand rules.",
    )

    intelligence = {
        "version": 1,
        "workspaceId": workspace_id,
        "brandId": brand_id,
        "datasetName": dataset,
        "subjectScope": manifest["workspace"]["subject_scope"],
        "retrieval": {
            "topK": 12,
            "maximumQueries": 3,
            "navigationSourcePatterns": ["agent_index", "agent_config", "workspace.yaml"],
        },
        "visualLanguage": {
            "enabled": True,
            "route": "visual-language",
            "workflowStages": ["brief", "concept", "production", "review"],
            "manifestPath": f"workspaces/brand-{slug}-research/visual-language/manifest.json",
            "datasetName": f"testflight_brand_{slug.replace('-', '_')}_visual_language_staging",
        },
        "worldView": {
            "enabled": True,
            "manifestPath": f"workspaces/brand-{slug}-research/artifacts/world-modeling.yaml",
        },
        "activation": {
            "actionTerms": ["create", "make", "write", "design", "review", "brief", "concept"],
            "domainTerms": [
                slug,
                "brand",
                "campaign",
                "asset",
                "audience",
                "positioning",
                "creative",
            ],
        },
        "workflows": [],
    }
    (target / "INTELLIGENCE.json").write_text(
        json.dumps(intelligence, indent=2) + "\n", encoding="utf-8"
    )
    write(
        target / "README.md",
        f"# {seed['name']} public Brand research workspace\n\nA separate proposal-only brand world generated from verified public sources. Run the concrete validator before projecting to its isolated Cognee staging datasets.",
    )
    write(
        target / "AGENT_INDEX.md",
        "# Agent index\n\nRoute public evidence by task view: research → source catalog/evidence; entity → entity/context records; relationship → relationship inventory; asset-context → workflow context; visual-language → visual module.\n",
    )
    dump_yaml(
        target / "AGENT_CONFIG.yaml",
        {
            "workspace_id": workspace_id,
            "brand_id": brand_id,
            "mutation": "proposal_only",
            "retrieval": {
                "child_first": True,
                "order": ["exact", "bm25", "bounded_hybrid_same_child"],
                "graph_max_hops": 2,
            },
            "operators": [
                "configuration-runtime@1",
                "workspace-isolation@1",
                "retrieval-reasoning-conflation@1",
                "evidence-truth-conflation@1",
                "evaluation-schema@1",
            ],
        },
    )
    write(
        target / "artifacts/research-protocol.md",
        "# Research protocol\n\nUse official sources for brand self-description. Preserve bounded excerpts, dates, provenance, authority, and limitations. Do not treat retrieved material as a validated customer, health, or performance conclusion.\n",
    )
    for view in ("research", "entity", "relationship", "asset-context", "review", "maintenance"):
        write(
            target / f"task_views/{view}.md",
            f"# {view}\n\nOperate only inside `{workspace_id}`. Preserve evidence, scope, time, perspective, and valid no-hit/partial/hold outcomes.\n",
        )

    registry_paths = [
        ("artifacts/research-protocol.md", "protocol", "research"),
        ("artifacts/source-catalog.yaml", "source_catalog", "research"),
        ("artifacts/evidence-notes.yaml", "evidence_notes", "research"),
        ("artifacts/context-profiles.yaml", "context_profiles", "entity"),
        ("artifacts/entity-inventory.yaml", "entity_inventory", "entity"),
        ("artifacts/relationship-inventory.yaml", "relationship_inventory", "relationship"),
        ("artifacts/asset-workflow-context.yaml", "workflow_context", "asset-context"),
        ("artifacts/coverage-matrix.yaml", "coverage_matrix", "review"),
        ("artifacts/world-modeling.yaml", "semantic_world_model", "world-modeling"),
        ("visual-language/manifest.json", "visual_language_manifest", "visual-language"),
    ]
    registry = {
        "workspace_id": workspace_id,
        "sources": [
            {
                "source_url": f"repo://workspaces/brand-{slug}-research/{path}",
                "doc_type": doc_type,
                "evidence_tier": "T1",
                "canonical": False,
                "task_view": route,
                "module": "brand",
                "unit": f"{slug}-{doc_type}",
                "tool": "testflight-brand",
                "experience_type": "research",
                "difficulty": "advanced",
                "last_verified_at": today,
            }
            for path, doc_type, route in registry_paths
        ],
    }
    (target / "resource_registry.json").write_text(
        json.dumps(registry, indent=2) + "\n", encoding="utf-8"
    )
    probes = [
        {
            "id": "exact-source-catalog",
            "case_type": "exact_artifact",
            "query": f"open the {seed['name']} public source catalog",
            "expected_route": "research",
            "expected_source_suffix": "artifacts/source-catalog.yaml",
            "expected_status": "hit",
        },
        {
            "id": "brand-intent",
            "case_type": "intent",
            "query": f"what does {seed['name']} publicly say it offers",
            "expected_route": "entity",
            "expected_entity_ids": [offering["id"]],
            "expected_status": "hit",
        },
        {
            "id": "relation-path",
            "case_type": "pathing",
            "query": "show the public offering-to-experience relationship",
            "expected_route": "relationship",
            "expected_relationship_ids": [rel_by_type["experienced_through"]],
            "max_hops": 2,
            "expected_status": "hit",
        },
        {
            "id": "current-context",
            "case_type": "temporal",
            "query": "compile current public brand context",
            "expected_route": "asset-context",
            "expected_context_ids": [context_id],
            "expected_status": "hit",
        },
        {
            "id": "reject-index",
            "case_type": "adversarial",
            "query": "answer from AGENT_INDEX only",
            "expected_route": "research",
            "forbidden_answer_sources": ["AGENT_INDEX.md", "AGENT_CONFIG.yaml"],
            "expected_status": "reject_navigation_source",
        },
        {
            "id": "out-of-domain",
            "case_type": "no_hit",
            "query": "what is the geothermal composition of Europa",
            "expected_route": "none",
            "expected_status": "no_hit",
        },
        {
            "id": "unsupported-health-causality",
            "case_type": "contradiction",
            "query": "prove the product causes a health outcome",
            "expected_route": "review",
            "expected_relationship_ids": [rel_by_type["shapes"]],
            "expected_status": "held",
        },
    ]
    dump_yaml(
        target / "certification_cases/probes.yaml",
        {"workspace_id": workspace_id, "version": 1, "probes": probes},
    )
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    target = scaffold(args.root.resolve(), load_seed(args.seed.resolve()), apply=args.apply)
    print(
        json.dumps(
            {"status": "created" if args.apply else "dry_run", "workspace": str(target)}, indent=2
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
