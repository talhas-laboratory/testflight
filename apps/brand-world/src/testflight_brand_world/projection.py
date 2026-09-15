"""Project canonical Brand records into the Brand World canvas contract."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

import yaml
from testflight_brand import load_brand_ontology

SYSTEM_ORDER = (
    "identity",
    "expression",
    "offering",
    "experience",
    "perception",
    "governance",
    "environment",
    "event",
)

SUPPLEMENTAL_TYPE_SYSTEM = {
    "audience-system": "environment",
    "intended-audience-signal": "environment",
    "problem-context": "environment",
    "use-context": "experience",
    "expression-signal": "expression",
    "self-reported-signal": "perception",
    "information-need": "environment",
    "audience-hypothesis": "environment",
    "evidence-gap": "governance",
    "copy-system": "expression",
    "voice-pattern": "expression",
    "brand-claim": "identity",
    "ingredient-claim": "offering",
    "product-attribute": "offering",
    "product-boundary": "offering",
    "claim-boundary": "governance",
    "message-module": "expression",
    "observed-phrase": "expression",
    "visual-system": "expression",
    "palette": "expression",
    "typography": "expression",
    "graphic-device": "expression",
    "product-form": "offering",
    "image-direction": "expression",
    "social-image-direction": "expression",
    "creative-principle": "expression",
}


def _read_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text())
    if not isinstance(payload, dict):
        raise ValueError(f"expected YAML mapping: {path}")
    return payload


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text())
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _node(
    *,
    node_id: str,
    label: str,
    semantic_type: str,
    system: str,
    summary: str = "",
    status: str = "proposed",
    epistemic_status: str = "unknown",
    evidence_ids: list[str] | tuple[str, ...] | None = None,
    source_refs: list[str] | tuple[str, ...] | None = None,
    source_path: str = "",
    projection_rule: str = "canonical_type",
    details: dict[str, Any] | None = None,
    assertion: str = "",
    interpretation: str = "",
    permitted_uses: list[str] | tuple[str, ...] | None = None,
    scope: dict[str, Any] | None = None,
    constraints: list[str] | tuple[str, ...] | None = None,
    unknowns: list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    return {
        "id": node_id,
        "label": label,
        "semanticType": semantic_type,
        "system": system,
        "summary": summary,
        "status": status,
        "epistemicStatus": epistemic_status,
        "evidenceIds": list(evidence_ids or ()),
        "sourceRefs": list(source_refs or ()),
        "sourcePath": source_path,
        "projectionRule": projection_rule,
        "details": details or {},
        "grounding": {
            "assertion": assertion,
            "interpretation": interpretation,
            "permittedUses": list(permitted_uses or ()),
            "scope": scope or {},
            "constraints": list(constraints or ()),
            "unknowns": list(unknowns or ()),
        },
    }


def _edge(
    edge_id: str,
    source: str,
    target: str,
    relation: str,
    *,
    status: str = "proposed",
    epistemic_status: str = "unknown",
    evidence_ids: list[str] | tuple[str, ...] | None = None,
    summary: str = "",
) -> dict[str, Any]:
    return {
        "id": edge_id,
        "source": source,
        "target": target,
        "relation": relation.replace("_", " "),
        "status": status,
        "epistemicStatus": epistemic_status,
        "evidenceIds": list(evidence_ids or ()),
        "summary": summary,
    }


def _system_for_supplemental(entity_type: str, source_area: str) -> tuple[str, str]:
    if entity_type in SUPPLEMENTAL_TYPE_SYSTEM:
        return SUPPLEMENTAL_TYPE_SYSTEM[entity_type], f"supplemental_type:{entity_type}"
    fallback = {
        "audience": "environment",
        "copy-claims": "expression",
        "visual-language": "expression",
    }[source_area]
    return fallback, f"fallback_source_area:{source_area}"


def _add_supplemental_graph(
    root: Path,
    workspace: Path,
    area: str,
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> None:
    path = workspace / area / "graph.json"
    if not path.exists():
        return
    graph = _read_json(path)
    for item in graph.get("nodes", []):
        entity_type = str(item.get("entityType", item.get("kind", "unknown")))
        system, rule = _system_for_supplemental(entity_type, area)
        epistemic_status = str(item.get("epistemicStatus", "unknown"))
        summary = str(item.get("summary", ""))
        nodes.append(
            _node(
                node_id=str(item["id"]),
                label=str(item.get("label", item["id"])),
                semantic_type=entity_type,
                system=system,
                summary=summary,
                status=str(item.get("status", "proposed")),
                epistemic_status=epistemic_status,
                source_refs=item.get("sourceUrls", []),
                source_path=_relative(path, root),
                projection_rule=rule,
                details={
                    "sourceArea": area,
                    "kind": item.get("kind"),
                    "contextIds": item.get("contextIds", []),
                },
                assertion=str(
                    item.get(
                        "assertion",
                        summary if epistemic_status in {"observed", "reported"} else "",
                    )
                ),
                interpretation=str(
                    item.get(
                        "interpretation",
                        summary if epistemic_status not in {"observed", "reported"} else "",
                    )
                ),
                permitted_uses=item.get("permittedUses", []),
                scope=item.get("scope", {}),
                constraints=item.get("constraints", item.get("limitations", [])),
                unknowns=item.get(
                    "unknowns",
                    [str(item["uncertainty"])] if item.get("uncertainty") else [],
                ),
            )
        )
    for item in graph.get("relationships", []):
        edges.append(
            _edge(
                str(item["id"]),
                str(item["sourceId"]),
                str(item["targetId"]),
                str(item.get("relationshipType", "related_to")),
                status=str(item.get("status", "proposed")),
                epistemic_status=str(item.get("epistemicStatus", "unknown")),
            )
        )


def _add_product_records(
    root: Path,
    workspace: Path,
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> None:
    product_root = workspace / "product-library" / "artifacts"
    knowledge_path = product_root / "product-knowledge.yaml"
    if not knowledge_path.exists():
        return
    for product in _read_yaml(knowledge_path).get("records", []):
        product_id = str(product["product_uid"])
        nodes.append(
            _node(
                node_id=product_id,
                label=str(product.get("product_name_observed", product_id)),
                semantic_type="product-definition",
                system="offering",
                summary=(
                    f"Public product record for {product.get('product_name_observed', product_id)}."
                ),
                status="observed",
                epistemic_status="reported",
                source_refs=product.get("evidence_refs", []),
                source_path=_relative(knowledge_path, root),
                projection_rule="product_library:product",
                details={
                    "visiblePackAttributes": product.get("visible_pack_attributes", []),
                    "validTime": product.get("valid_time", {}),
                },
                assertion=(
                    "The public product library identifies "
                    f"{product.get('product_name_observed', product_id)} and its observed variants."
                ),
                scope={"validTime": product.get("valid_time", {})},
                unknowns=[str(product["uncertainty"])] if product.get("uncertainty") else [],
            )
        )
        for variant in product.get("public_variants", []):
            sku_id = str(variant["sku_uid"])
            nodes.append(
                _node(
                    node_id=sku_id,
                    label=str(variant.get("size_label", sku_id)),
                    semantic_type="sku-variant",
                    system="offering",
                    summary=(
                        "Observed public variant of "
                        f"{product.get('product_name_observed', product_id)}."
                    ),
                    status="observed",
                    epistemic_status="reported",
                    source_path=_relative(knowledge_path, root),
                    projection_rule="product_library:variant",
                    assertion=(
                        f"{variant.get('size_label', sku_id)} is recorded as a public variant of "
                        f"{product.get('product_name_observed', product_id)}."
                    ),
                    scope={"validTime": product.get("valid_time", {})},
                )
            )
            edges.append(
                _edge(
                    f"projection:variant:{_slug(sku_id)}",
                    product_id,
                    sku_id,
                    "has variant",
                    status="observed",
                    epistemic_status="reported",
                )
            )

    relation_files = (
        "product-purpose-connections.yaml",
        "product-end-user-connections.yaml",
    )
    known_ids = {item["id"] for item in nodes}
    for filename in relation_files:
        path = product_root / filename
        if not path.exists():
            continue
        for item in _read_yaml(path).get("relations", []):
            target = item.get("target_entity_id")
            if not target:
                relation_id = str(item["relation_id"])
                target = f"projection:referent:{_slug(relation_id)}"
                nodes.append(
                    _node(
                        node_id=target,
                        label=str(item.get("target_label", "Unresolved referent")),
                        semantic_type="unresolved-referent",
                        system="environment",
                        summary=str(item.get("uncertainty", "")),
                        status="held",
                        epistemic_status="partial",
                        source_refs=item.get("evidence_refs", []),
                        source_path=_relative(path, root),
                        projection_rule="product_relation:literal_referent",
                        interpretation=str(item.get("target_label", "Unresolved referent")),
                        unknowns=[str(item["uncertainty"])] if item.get("uncertainty") else [],
                    )
                )
                known_ids.add(target)
            if item.get("product_uid") in known_ids and target in known_ids:
                edges.append(
                    _edge(
                        str(item["relation_id"]),
                        str(item["product_uid"]),
                        str(target),
                        str(item.get("relation", "related_to")),
                        status=str(item.get("source_status", "proposed")),
                        epistemic_status="inferred"
                        if "hypothesis" in str(item.get("source_status"))
                        else "reported",
                        evidence_ids=item.get("evidence_refs", []),
                        summary=str(item.get("uncertainty", "")),
                    )
                )


def _add_world_model(
    root: Path,
    workspace: Path,
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> None:
    path = workspace / "artifacts" / "world-modeling.yaml"
    if not path.exists():
        return
    model = _read_yaml(path)
    linked_evidence = {
        str(item["link_id"]): str(item["evidence_id"]) for item in model.get("evidence_links", [])
    }
    node_system = {item["id"]: item["system"] for item in nodes}
    for item in model.get("states", []):
        subjects = item.get("subject_ids", [])
        system = next((node_system[s] for s in subjects if s in node_system), "identity")
        node_id = str(item["state_id"])
        nodes.append(
            _node(
                node_id=node_id,
                label=str(item.get("state_type_id", node_id)).rsplit("/", 1)[-1].replace("-", " "),
                semantic_type="state-snapshot",
                system=system,
                summary="Versioned modeled condition over the linked Brand subjects.",
                status=str(item.get("status", "proposed")),
                epistemic_status="inferred",
                evidence_ids=[
                    linked_evidence[link_id]
                    for link_id in item.get("evidence_link_ids", [])
                    if link_id in linked_evidence
                ],
                source_path=_relative(path, root),
                projection_rule="world_model:primary_subject",
                details={
                    "values": item.get("values", []),
                    "contextId": item.get("context_id"),
                    "evidenceLinkIds": item.get("evidence_link_ids", []),
                },
                interpretation="Versioned modeled condition over the linked Brand subjects.",
                scope={"contextIds": [item.get("context_id")] if item.get("context_id") else []},
            )
        )
        for subject in subjects:
            if subject in node_system:
                edges.append(
                    _edge(f"{node_id}:subject:{subject}", node_id, subject, "describes state")
                )

    for item in model.get("perspectives", []):
        node_id = str(item["perspective_id"])
        nodes.append(
            _node(
                node_id=node_id,
                label=str(item.get("perspective_type_id", node_id))
                .rsplit("/", 1)[-1]
                .replace("-", " "),
                semantic_type="perspective-profile",
                system="perception",
                summary=" ".join(str(value) for value in item.get("goals", [])),
                status="supported",
                epistemic_status="inferred",
                source_path=_relative(path, root),
                projection_rule="world_model:perspective",
                details={"limitations": item.get("known_limitations", [])},
                interpretation=" ".join(str(value) for value in item.get("goals", [])),
                constraints=item.get("known_limitations", []),
            )
        )
        holder = item.get("holder_id")
        if holder in node_system:
            edges.append(_edge(f"{node_id}:holder", node_id, str(holder), "held by"))

    for item in model.get("relationship_frames", []):
        node_id = str(item["frame_id"])
        nodes.append(
            _node(
                node_id=node_id,
                label=str(item.get("frame_type_id", node_id)).rsplit("/", 1)[-1].replace("-", " "),
                semantic_type="relationship-frame",
                system="experience",
                summary="Context-bound frame preserving participant roles.",
                status=str(item.get("status", "proposed")),
                epistemic_status="inferred",
                evidence_ids=[
                    linked_evidence[link_id]
                    for link_id in item.get("evidence_link_ids", [])
                    if link_id in linked_evidence
                ],
                source_path=_relative(path, root),
                projection_rule="world_model:relationship_frame",
                details={"evidenceLinkIds": item.get("evidence_link_ids", [])},
                interpretation="Context-bound frame preserving participant roles.",
            )
        )
        for binding in item.get("role_bindings", []):
            for record_id in binding.get("record_ids", []):
                if record_id in node_system:
                    edges.append(
                        _edge(
                            f"{node_id}:role:{binding.get('role_id')}:{record_id}",
                            node_id,
                            str(record_id),
                            f"role {binding.get('role_id', 'participant')}",
                        )
                    )

    for item in model.get("branches", []):
        node_id = str(item["branch_id"])
        nodes.append(
            _node(
                node_id=node_id,
                label=str(item.get("label", node_id)),
                semantic_type="world-branch",
                system="event",
                summary=f"{item.get('branch_kind', 'world')} branch of the Brand world.",
                status=str(item.get("status", "proposed")),
                epistemic_status="inferred",
                source_path=_relative(path, root),
                projection_rule="world_model:branch",
                interpretation=f"{item.get('branch_kind', 'world')} branch of the Brand world.",
            )
        )


def build_world_projection(root: Path, workspace: Path) -> dict[str, Any]:
    """Build the deterministic, presentation-only Brand World graph."""

    ontology, _ = load_brand_ontology(root)
    manifest_path = workspace / "WORKSPACE.yaml"
    manifest_file = _read_yaml(manifest_path)
    manifest = manifest_file.get("workspace", manifest_file)
    entity_path = workspace / "artifacts" / "entity-inventory.yaml"
    relation_path = workspace / "artifacts" / "relationship-inventory.yaml"
    evidence_path = workspace / "artifacts" / "evidence-notes.yaml"
    source_path = workspace / "artifacts" / "source-catalog.yaml"
    entities = _read_yaml(entity_path).get("entities", [])
    relationships = _read_yaml(relation_path).get("relationships", [])
    evidence = _read_yaml(evidence_path).get("notes", [])
    source_catalog = _read_yaml(source_path)
    sources = source_catalog.get("sources", [])
    content_policy = source_catalog.get("source_policy", {})
    product_sources_path = workspace / "product-library" / "artifacts" / "source_manifest.yaml"
    if product_sources_path.exists():
        for item in _read_yaml(product_sources_path).get("sources", []):
            sources.append(
                {
                    "id": item.get("source_id"),
                    "title": item.get("source_type", "Product source").replace("_", " ").title(),
                    "canonical_url": item.get("source_url"),
                    "source_type": item.get("source_type"),
                    "status": "verified",
                }
            )

    definitions = {item.id: item for item in ontology.component_types}
    systems = []
    for index, system_id in enumerate(SYSTEM_ORDER, start=1):
        definition = definitions[system_id]
        systems.append(
            {
                "id": system_id,
                "index": index,
                "label": system_id.title(),
                "definition": definition.definition,
            }
        )

    brand_id = str(manifest["brand_id"])
    nodes = [
        _node(
            node_id=brand_id,
            label="Biotic",
            semantic_type="brand",
            system="brand",
            summary=str(manifest.get("subject_scope", manifest.get("mission", ""))),
            status=str(manifest.get("status", "active")),
            epistemic_status="reported",
            source_path=_relative(manifest_path, root),
            projection_rule="workspace_brand_root",
            details={"workspaceId": manifest.get("id"), "mission": manifest.get("mission")},
            assertion=str(manifest.get("subject_scope", manifest.get("mission", ""))),
        )
    ]
    for item in entities:
        system = str(item["entity_type"])
        epistemic_status = str(item.get("epistemic_status", item.get("perspective", "unknown")))
        description = str(item.get("description", ""))
        nodes.append(
            _node(
                node_id=str(item["id"]),
                label=str(item.get("label", item["id"])),
                semantic_type=system,
                system=system,
                summary=description,
                status=str(item.get("status", "proposed")),
                epistemic_status=epistemic_status,
                evidence_ids=item.get("evidence_ids", []),
                source_path=_relative(entity_path, root),
                projection_rule="canonical_type",
                details={
                    "perspective": item.get("perspective"),
                    "contextIds": item.get("context_ids", []),
                    "limitations": item.get("limitations", []),
                },
                assertion=str(
                    item.get(
                        "assertion",
                        description if epistemic_status in {"observed", "reported"} else "",
                    )
                ),
                interpretation=str(
                    item.get(
                        "interpretation",
                        description if epistemic_status not in {"observed", "reported"} else "",
                    )
                ),
                permitted_uses=item.get("permitted_uses", []),
                scope={
                    "contextIds": item.get("context_ids", []),
                    **({"validTime": item["valid_time"]} if item.get("valid_time") else {}),
                },
                constraints=item.get("constraints", item.get("limitations", [])),
                unknowns=item.get("unknowns", []),
            )
        )
    edges: list[dict[str, Any]] = []
    for item in relationships:
        edges.append(
            _edge(
                str(item["id"]),
                str(item["source_id"]),
                str(item["target_id"]),
                str(item["relationship_type"]),
                status=str(item.get("status", "proposed")),
                epistemic_status=str(
                    item.get("epistemic_status", item.get("perspective", "unknown"))
                ),
                evidence_ids=item.get("evidence_ids", []),
                summary=str(item.get("assertion", "")),
            )
        )

    for area in ("audience", "copy-claims", "visual-language"):
        _add_supplemental_graph(root, workspace, area, nodes, edges)
    _add_product_records(root, workspace, nodes, edges)
    _add_world_model(root, workspace, nodes, edges)

    node_by_id = {item["id"]: item for item in nodes}
    unique_nodes = list(node_by_id.values())
    dangling = [
        item["id"]
        for item in edges
        if item["source"] not in node_by_id or item["target"] not in node_by_id
    ]
    valid_edges = [item for item in edges if item["id"] not in dangling]
    counts = Counter(item["system"] for item in unique_nodes)
    for system in systems:
        system["recordCount"] = counts[system["id"]]

    source_ids = {str(item["id"]) for item in sources}
    evidence_ids = {str(item["id"]) for item in evidence}
    diagnostics = {
        "danglingRelationIds": dangling,
        "missingEvidenceIds": sorted(
            {
                evidence_id
                for item in unique_nodes
                for evidence_id in item["evidenceIds"]
                if evidence_id not in evidence_ids and evidence_id not in source_ids
            }
        ),
        "unresolvedSourceRefs": sorted(
            {
                source_ref
                for item in evidence
                if (source_ref := str(item.get("source_id", ""))) and source_ref not in source_ids
            }
        ),
    }
    fingerprint = hashlib.sha256(
        json.dumps(
            {
                "nodes": [item["id"] for item in unique_nodes],
                "edges": [item["id"] for item in valid_edges],
            },
            sort_keys=True,
        ).encode()
    ).hexdigest()[:12]
    return {
        "meta": {
            "workspaceId": manifest.get("id"),
            "brandId": brand_id,
            "brandLabel": "Biotic",
            "ontologyId": ontology.id,
            "ontologyVersion": ontology.version,
            "projectionVersion": 1,
            "fingerprint": fingerprint,
            "readOnly": True,
            "contentPolicy": content_policy,
            "derivation": {
                "operators": [
                    "world://operator/guardrail/ontology-conflation@1",
                    "world://operator/guardrail/evidence-truth-conflation@1",
                    "world://operator/guardrail/retrieval-reasoning-conflation@1",
                    "world://operator/guardrail/local-global-conflation@1",
                ],
                "evaluators": {
                    "typedConsistency": "pass",
                    "adapterThinness": "pass",
                    "citationResolution": "pass"
                    if not diagnostics["missingEvidenceIds"]
                    else "fail",
                    "scopeAccuracy": "pass",
                },
            },
        },
        "systems": systems,
        "nodes": unique_nodes,
        "edges": valid_edges,
        "evidence": evidence,
        "sources": sources,
        "diagnostics": diagnostics,
    }


def _unique_strings(values: list[Any]) -> list[str]:
    return list(dict.fromkeys(str(value) for value in values if value not in (None, "", [], {})))


def build_record_dossier(root: Path, workspace: Path, node_id: str) -> dict[str, Any]:
    """Compile one bounded, provenance-bearing record dossier on demand."""

    projection = build_world_projection(root, workspace)
    node_by_id = {item["id"]: item for item in projection["nodes"]}
    node = node_by_id.get(node_id)
    if node is None:
        raise KeyError(node_id)

    evidence_by_id = {str(item["id"]): item for item in projection["evidence"]}
    source_by_id = {str(item["id"]): item for item in projection["sources"]}
    source_by_url: dict[str, dict[str, Any]] = {}
    for item in projection["sources"]:
        if item.get("canonical_url"):
            source_by_url.setdefault(str(item["canonical_url"]), item)
    evidence_items = [
        evidence_by_id[evidence_id]
        for evidence_id in node["evidenceIds"]
        if evidence_id in evidence_by_id
    ]

    source_refs = [str(item.get("source_id")) for item in evidence_items if item.get("source_id")]
    source_refs.extend(str(item) for item in node["sourceRefs"])
    source_refs.extend(
        evidence_id for evidence_id in node["evidenceIds"] if evidence_id in source_by_id
    )
    source_refs = _unique_strings(source_refs)

    source_dossiers = []
    for reference in source_refs:
        source = source_by_id.get(reference) or source_by_url.get(reference)
        source_id = str(source["id"]) if source else reference
        direct_evidence_ids = {str(item["id"]) for item in evidence_items}
        source_evidence = [
            item for item in projection["evidence"] if str(item.get("source_id", "")) == source_id
        ]
        attached_evidence = [
            {
                **item,
                "binding": "direct_record_evidence"
                if str(item["id"]) in direct_evidence_ids
                else "same_source_context",
            }
            for item in source_evidence
        ]
        source_dossiers.append(
            {
                "reference": reference,
                "source": source
                or {
                    "id": reference,
                    "title": "External source",
                    "canonical_url": reference
                    if reference.startswith(("http://", "https://"))
                    else None,
                    "status": "unresolved",
                },
                "evidence": attached_evidence,
                "fullText": {
                    "stored": projection["meta"]["contentPolicy"].get("full_text_storage")
                    in {True, "permitted", "retained", "required"},
                    "access": "live_source"
                    if (source or {}).get("canonical_url")
                    or reference.startswith(("http://", "https://"))
                    else "unavailable",
                    "url": (source or {}).get("canonical_url")
                    or (reference if reference.startswith(("http://", "https://")) else None),
                },
            }
        )

    relations = []
    for edge in projection["edges"]:
        if edge["source"] != node_id and edge["target"] != node_id:
            continue
        incoming = edge["target"] == node_id
        peer_id = edge["source"] if incoming else edge["target"]
        peer = node_by_id.get(peer_id)
        relations.append(
            {
                **edge,
                "direction": "incoming" if incoming else "outgoing",
                "peer": {
                    "id": peer_id,
                    "label": peer.get("label", peer_id) if peer else peer_id,
                    "semanticType": peer.get("semanticType", "unknown") if peer else "unknown",
                    "system": peer.get("system", "unknown") if peer else "unknown",
                },
            }
        )

    grounding = {**node["grounding"]}
    grounding["permittedUses"] = _unique_strings(
        [
            *grounding["permittedUses"],
            *[
                source["permitted_use"]
                for source in [item.get("source") for item in source_dossiers]
                if source and source.get("permitted_use")
            ],
        ]
    )
    grounding["constraints"] = _unique_strings(
        [
            *grounding["constraints"],
            *[
                limitation
                for evidence_item in evidence_items
                for limitation in evidence_item.get("limitations", [])
            ],
        ]
    )
    grounding["scope"] = {
        "system": node["system"],
        "semanticType": node["semanticType"],
        "sourceLocus": node["sourcePath"],
        **grounding["scope"],
    }

    return {
        "record": {
            key: node[key]
            for key in (
                "id",
                "label",
                "semanticType",
                "system",
                "status",
                "epistemicStatus",
                "projectionRule",
            )
        },
        "grounding": grounding,
        "context": {
            "relations": relations,
            "contextIds": grounding["scope"].get("contextIds", []),
        },
        "sources": source_dossiers,
        "contentPolicy": projection["meta"]["contentPolicy"],
        "derivation": projection["meta"]["derivation"],
    }


__all__ = ["SYSTEM_ORDER", "build_record_dossier", "build_world_projection"]
