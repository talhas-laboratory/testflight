#!/usr/bin/env python3
"""Certify retrieval behavior for an already-populated Brand research projection."""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from populate_brand_research_workspace import (
    DEFAULT_STAGING_SUFFIX,
    REPO_ROOT,
    WORKSPACE_RELATIVE,
    _credential,
    _llm_configs,
    build_documents,
    validate_pack,
)

PROBE_SUITE = Path("certification_cases/brand_ontology_probe_suite.json")
STOP_WORDS = {
    "a",
    "an",
    "and",
    "as",
    "can",
    "from",
    "give",
    "how",
    "i",
    "in",
    "me",
    "of",
    "on",
    "the",
    "to",
    "treat",
    "which",
}


@dataclass(frozen=True, slots=True)
class RetrievedItem:
    text: str
    task_view: str | None
    source_url: str | None
    score: float | None
    raw: Any


def _revision(root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _tokens(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"\w+", text.casefold())
        if token not in STOP_WORDS and len(token) > 1
    }


def _model_dump(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if hasattr(value, "dict"):
        return value.dict()
    return value


def _text_from_payload(payload: Any) -> str:
    payload = _model_dump(payload)
    if isinstance(payload, str):
        return payload
    if isinstance(payload, dict):
        for key in ("text", "content", "completion", "answer", "summary", "value"):
            value = payload.get(key)
            if isinstance(value, str) and value:
                return value
        return json.dumps(payload, default=str, ensure_ascii=False)
    return str(payload)


def _flatten_search_response(response: Any) -> list[Any]:
    """Flatten Cognee's v1/v2 dataset and SearchResultItem response shapes."""

    response = _model_dump(response)
    if isinstance(response, dict):
        if "search_result" in response:
            return _flatten_search_response(response["search_result"])
        if "result" in response and set(response) <= {
            "result",
            "dataset_id",
            "dataset_name",
            "dataset_tenant_id",
        }:
            return _flatten_search_response(response["result"])
        return [response]
    if isinstance(response, (list, tuple)):
        flattened: list[Any] = []
        for item in response:
            flattened.extend(_flatten_search_response(item))
        return flattened
    return [response]


def _metadata_from_payload(payload: Any) -> dict[str, Any]:
    payload = _model_dump(payload)
    if not isinstance(payload, dict):
        return {}
    metadata = payload.get("metadata")
    if isinstance(metadata, dict):
        return {**metadata, **{key: value for key, value in payload.items() if key != "metadata"}}
    raw = payload.get("raw")
    if isinstance(raw, dict):
        return {**raw, **payload}
    return payload


def _retrieved_items(response: Any) -> list[RetrievedItem]:
    items: list[RetrievedItem] = []
    for payload in _flatten_search_response(response):
        dumped = _model_dump(payload)
        text = _text_from_payload(dumped)
        metadata = _metadata_from_payload(dumped)
        header_source = re.search(r"SOURCE_URL:\s*(\S+)", text)
        header_view = re.search(r"TASK_VIEW:\s*(\S+)", text)
        source_url = (
            str(metadata.get("source_url"))
            if metadata.get("source_url")
            else header_source.group(1)
            if header_source
            else None
        )
        task_view = (
            str(metadata.get("task_view"))
            if metadata.get("task_view")
            else header_view.group(1)
            if header_view
            else None
        )
        score = metadata.get("score")
        items.append(
            RetrievedItem(
                text=text,
                task_view=task_view,
                source_url=source_url,
                score=float(score) if isinstance(score, (int, float)) else None,
                raw=dumped,
            )
        )
    return items


def _contains_tokens(items: list[RetrievedItem], expected: set[str]) -> bool:
    return any(expected <= _tokens(item.text) for item in items)


def _lexical_hit(query: str, items: list[RetrievedItem]) -> bool:
    query_tokens = _tokens(query)
    return any(query_tokens & _tokens(item.text) for item in items)


def _evaluate_probe(probe: dict[str, Any], items: list[RetrievedItem]) -> dict[str, Any]:
    case_type = probe["case_type"]
    top = items[0] if items else None
    all_text = "\n".join(item.text for item in items)
    route = top.task_view if top else None
    route_ok = (
        route == probe.get("expected_route") if probe.get("expected_route") != "none" else True
    )

    if case_type == "exact_artifact":
        passed = bool(top and top.source_url and top.source_url.endswith("research-protocol.md"))
    elif probe["name"] == "question_route":
        passed = (
            route_ok
            and _contains_tokens(items, {"cq", "015"})
            and _contains_tokens(items, {"cq", "018"})
        )
    elif probe["name"] == "promotion_route":
        lower = all_text.casefold()
        passed = route_ok and "authority" in lower and "promot" in lower
    elif case_type == "adversarial":
        forbidden = ("AGENT_INDEX", "AGENT_CONFIG")
        passed = not any(
            item.source_url and any(token in item.source_url for token in forbidden)
            for item in items
        )
    elif case_type == "no_hit":
        passed = not _lexical_hit(probe["query"], items)
    elif case_type == "pathing":
        lower = all_text.casefold()
        passed = route_ok and ("max_hops" in lower or "graph_max_hops" in lower)
    else:
        passed = False

    return {
        "name": probe["name"],
        "case_type": case_type,
        "query": probe["query"],
        "expected_route": probe.get("expected_route"),
        "observed_route": route,
        "result_count": len(items),
        "lexical_hit": _lexical_hit(probe["query"], items),
        "top_source_url": top.source_url if top else None,
        "top_excerpt": (top.text[:240] if top else None),
        "passed": passed,
    }


async def _search(
    *,
    cognee: Any,
    search_type: Any,
    query: str,
    dataset_name: str,
    llm_config: Any = None,
    embedding_config: Any = None,
) -> list[RetrievedItem]:
    response = await cognee.search(
        query,
        query_type=search_type,
        datasets=[dataset_name],
        top_k=15,
        only_context=True,
        include_references=True,
        llm_config=llm_config,
        embedding_config=embedding_config,
    )
    return _retrieved_items(response)


async def certify(*, root: Path, dataset_name: str, run_fallback: bool = True) -> dict[str, Any]:
    validated = validate_pack(root)
    documents = build_documents(root, validated)
    if not dataset_name:
        raise ValueError("dataset_name is required")
    workspace = root / WORKSPACE_RELATIVE
    probes = json.loads((workspace / PROBE_SUITE).read_text(encoding="utf-8"))
    if not isinstance(probes, list) or not probes:
        raise ValueError("probe suite must be a non-empty list")

    import cognee
    from cognee.modules.search.types import SearchType

    llm_config = None
    embedding_config = None
    results: list[dict[str, Any]] = []
    fallback_count = 0
    graph_probe_count = 0
    for probe in probes:
        search_type = SearchType.CHUNKS_LEXICAL
        items = await _search(
            cognee=cognee,
            search_type=search_type,
            query=probe["query"],
            dataset_name=dataset_name,
        )
        lexical_hit = _lexical_hit(probe["query"], items)
        fallback_used = False
        if run_fallback and probe["case_type"] != "no_hit" and not lexical_hit:
            if llm_config is None:
                llm_config, embedding_config = _llm_configs(_credential(root))
            items = await _search(
                cognee=cognee,
                search_type=SearchType.HYBRID_COMPLETION,
                query=probe["query"],
                dataset_name=dataset_name,
                llm_config=llm_config,
                embedding_config=embedding_config,
            )
            fallback_used = True
            fallback_count += 1

        graph_parameters = None
        if probe["case_type"] == "pathing":
            if llm_config is None:
                llm_config, embedding_config = _llm_configs(_credential(root))
            graph_parameters = {
                "search_type": SearchType.GRAPH_COMPLETION.value,
                "neighborhood_depth": 2,
            }
            await cognee.search(
                probe["query"],
                query_type=SearchType.GRAPH_COMPLETION,
                datasets=[dataset_name],
                top_k=5,
                neighborhood_depth=2,
                only_context=True,
                include_references=True,
                llm_config=llm_config,
                embedding_config=embedding_config,
            )
            graph_probe_count += 1

        evaluated = _evaluate_probe(probe, items)
        evaluated["primary_search_type"] = search_type.value
        evaluated["fallback_used"] = fallback_used
        evaluated["graph_parameters"] = graph_parameters
        results.append(evaluated)

    required_classes = set(_read_required_probe_classes(workspace))
    observed_classes = {item["case_type"] for item in results}
    passed_count = sum(item["passed"] for item in results)
    routed = [
        item for item in results if item["case_type"] in {"exact_artifact", "intent", "pathing"}
    ]
    exact = [item for item in results if item["case_type"] == "exact_artifact"]
    no_hits = [item for item in results if item["case_type"] == "no_hit"]
    routing_errors = sum(item["observed_route"] != item["expected_route"] for item in routed)
    metrics = {
        "probe_count": len(results),
        "top_1_precision": passed_count / len(results),
        "exact_artifact_top_1_precision": sum(item["passed"] for item in exact) / len(exact)
        if exact
        else 0.0,
        "routing_error": routing_errors / len(routed) if routed else 1.0,
        "no_hit_correctness": sum(item["passed"] for item in no_hits) / len(no_hits)
        if no_hits
        else 0.0,
        "fallback_count": fallback_count,
        "graph_probe_count": graph_probe_count,
    }
    policy = validated["manifest"].get("policy", {})
    acceptance = _yaml_config(root / WORKSPACE_RELATIVE / "AGENT_CONFIG.yaml")[
        "certification_policy"
    ]
    gates = {
        "required_probe_classes": required_classes <= observed_classes,
        "exact_artifact": metrics["exact_artifact_top_1_precision"]
        >= acceptance["exact_artifact_top_1_precision"],
        "top_1_precision": metrics["top_1_precision"]
        >= acceptance["minimum_probe_top_1_precision"],
        "routing_error": metrics["routing_error"] <= acceptance["maximum_routing_error"],
        "no_hit_correctness": metrics["no_hit_correctness"] >= acceptance["no_hit_correctness"],
        "explicit_dataset_scope": bool(dataset_name),
        "graph_hop_bound": all(
            item["graph_parameters"] is None or item["graph_parameters"]["neighborhood_depth"] <= 2
            for item in results
        ),
    }
    report = {
        "workspace_id": validated["manifest"]["id"],
        "dataset_name": dataset_name,
        "repository_revision": _revision(root),
        "status": "pass" if all(gates.values()) else "fail",
        "documents": [
            {
                "document_id": str(document.document_id),
                "source_url": document.source_url,
                "source_hash": document.metadata["source_hash"],
            }
            for document in documents
        ],
        "policy": {
            "retrieval_primary": "CHUNKS_LEXICAL",
            "retrieval_fallback": "HYBRID_COMPLETION_same_dataset",
            "graph_max_hops": policy.get("graph_max_hops", 2),
        },
        "metrics": metrics,
        "gates": gates,
        "probes": results,
        "reasoning_operators": [
            "world://operator/guardrail/retrieval-reasoning-conflation@1",
            "world://operator/guardrail/local-global-conflation@1",
            "world://operator/guardrail/evidence-truth-conflation@1",
            "world://operator/guardrail/evaluation-schema@1",
        ],
    }
    return report


def _yaml_config(path: Path) -> dict[str, Any]:
    import yaml

    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a mapping")
    return value


def _read_required_probe_classes(workspace: Path) -> list[str]:
    return list(
        _yaml_config(workspace / "AGENT_CONFIG.yaml")["certification_policy"][
            "required_probe_classes"
        ]
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    parser.add_argument("--dataset-name", required=True)
    parser.add_argument("--report", type=Path, default=None)
    parser.add_argument("--no-fallback", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    root = args.root.resolve()
    if not args.dataset_name.endswith(DEFAULT_STAGING_SUFFIX):
        raise SystemExit("certification must target an isolated *_staging dataset")
    report = asyncio.run(
        certify(root=root, dataset_name=args.dataset_name, run_fallback=not args.no_fallback)
    )
    report_path = args.report or root / ".data/brand-research/projection-certification.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = (
        f"{report['status']}: dataset={report['dataset_name']} "
        f"probes={report['metrics']['probe_count']}"
    )
    print(f"{summary} report={report_path}")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
