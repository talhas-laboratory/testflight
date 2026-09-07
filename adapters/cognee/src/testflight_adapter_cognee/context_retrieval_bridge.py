"""One-shot JSON process bridge for read-only, dataset-scoped Cognee retrieval."""

from __future__ import annotations

import asyncio
import hashlib
import json
import re
import sys
from typing import Any


def _dump(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if hasattr(value, "dict"):
        return value.dict()
    return value


def _flatten(value: Any) -> list[Any]:
    value = _dump(value)
    if isinstance(value, dict):
        if "search_result" in value:
            return _flatten(value["search_result"])
        if "result" in value and set(value) <= {
            "result",
            "dataset_id",
            "dataset_name",
            "dataset_tenant_id",
        }:
            return _flatten(value["result"])
        return [value]
    if isinstance(value, (list, tuple)):
        return [item for child in value for item in _flatten(child)]
    return [value]


def _text(payload: Any) -> str:
    payload = _dump(payload)
    if isinstance(payload, str):
        return payload
    if isinstance(payload, dict):
        for key in ("text", "content", "completion", "answer", "summary", "value"):
            value = payload.get(key)
            if isinstance(value, str) and value:
                return value
        return json.dumps(payload, default=str, ensure_ascii=False)
    return str(payload)


def _metadata(payload: Any) -> dict[str, Any]:
    payload = _dump(payload)
    if not isinstance(payload, dict):
        return {}
    metadata = payload.get("metadata")
    if isinstance(metadata, dict):
        return {**metadata, **{key: value for key, value in payload.items() if key != "metadata"}}
    raw = payload.get("raw")
    if isinstance(raw, dict):
        return {**raw, **payload}
    return payload


def _header(text: str, name: str) -> str | None:
    match = re.search(rf"^{re.escape(name)}:\s*(.+?)\s*$", text, re.MULTILINE)
    return match.group(1) if match else None


def _string_list(value: Any) -> list[str] | None:
    if isinstance(value, str) and value:
        return [value]
    if isinstance(value, (list, tuple)):
        return [item for item in value if isinstance(item, str) and item]
    return None


def normalize_items(response: Any) -> list[dict[str, Any]]:
    """Normalize supported Cognee response shapes into the stable bridge contract."""

    normalized: list[dict[str, Any]] = []
    for payload in _flatten(response):
        text = _text(payload)
        metadata = _metadata(payload)
        source_url = metadata.get("source_url") or _header(text, "SOURCE_URL")
        workspace_id = metadata.get("workspace_id") or _header(text, "WORKSPACE_ID")
        brand_id = metadata.get("brand_id") or _header(text, "BRAND_ID")
        source_key = str(source_url or "unanchored")
        item_id = hashlib.sha256(f"{source_key}\n{text}".encode()).hexdigest()[:24]
        item: dict[str, Any] = {"id": item_id, "text": text}
        optional = {
            "sourceUrl": source_url,
            "workspaceId": workspace_id,
            "projectId": metadata.get("project_id") or _header(text, "PROJECT_ID"),
            "brandId": brand_id,
            "recordId": metadata.get("record_id") or _header(text, "RECORD_ID"),
            "recordType": metadata.get("record_type") or _header(text, "RECORD_TYPE"),
            "fieldVersionId": metadata.get("field_version_id") or _header(text, "FIELD_VERSION_ID"),
            "taskView": metadata.get("task_view") or _header(text, "TASK_VIEW"),
            "docType": metadata.get("doc_type") or _header(text, "DOC_TYPE"),
            "validFrom": metadata.get("valid_from"),
            "validThrough": metadata.get("valid_through"),
            "promotionStatus": metadata.get("promotion_status")
            or _header(text, "PROMOTION_STATUS"),
            "score": metadata.get("score"),
            "branchId": metadata.get("branch_id") or _header(text, "BRANCH_ID"),
            "perspectiveIds": _string_list(metadata.get("perspective_ids")),
        }
        item.update({key: value for key, value in optional.items() if value is not None})
        normalized.append(item)
    return normalized


def _entity_documents(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Recover structured entity inventories from Cognee-returned source spans."""

    import yaml

    documents: list[dict[str, Any]] = []
    for item in items:
        text = item.get("text")
        if not isinstance(text, str):
            continue
        for segment in text.split("WORKSPACE_ID: ")[1:]:
            header, marker, remainder = segment.partition("SOURCE_BEGIN\n")
            if not marker or "DOC_TYPE: entity_inventory" not in header:
                continue
            body, end, _tail = remainder.partition("SOURCE_END")
            if not end:
                continue
            try:
                parsed = yaml.safe_load(body)
            except yaml.YAMLError:
                continue
            if not isinstance(parsed, dict) or not isinstance(parsed.get("entities"), list):
                continue
            source_match = re.search(r"^SOURCE_URL:\s*(.+)$", header, re.MULTILINE)
            workspace_match = re.search(r"^([^\n]+)\n", segment)
            brand_match = re.search(r"^BRAND_ID:\s*(.+)$", header, re.MULTILINE)
            documents.append(
                {
                    "entities": parsed["entities"],
                    "sourceUrl": source_match.group(1).strip()
                    if source_match
                    else item.get("sourceUrl"),
                    "workspaceId": workspace_match.group(1).strip()
                    if workspace_match
                    else item.get("workspaceId"),
                    "brandId": brand_match.group(1).strip() if brand_match else item.get("brandId"),
                }
            )
    return documents


def exact_entity_items(items: list[dict[str, Any]], entity_ids: list[str]) -> list[dict[str, Any]]:
    """Return only exact structured entity records, never mere identifier mentions."""

    requested = set(entity_ids)
    found: dict[str, dict[str, Any]] = {}
    for document in _entity_documents(items):
        for entity in document["entities"]:
            if not isinstance(entity, dict) or entity.get("id") not in requested:
                continue
            entity_id = str(entity["id"])
            text = json.dumps(entity, ensure_ascii=False, sort_keys=True)
            source_url = document.get("sourceUrl")
            item_id = hashlib.sha256(f"{source_url}\n{entity_id}\n{text}".encode()).hexdigest()[:24]
            found[entity_id] = {
                "id": item_id,
                "text": text,
                "sourceUrl": source_url,
                "workspaceId": document.get("workspaceId"),
                "brandId": document.get("brandId"),
                "taskView": "entity",
                "docType": "entity_record",
                "promotionStatus": "proposal_only",
                "retrievalKind": "exact_entity",
                "entityIds": [entity_id],
            }
    return [found[entity_id] for entity_id in entity_ids if entity_id in found]


def _visual_language_documents(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Recover versioned visual-language manifests from Cognee source spans."""

    documents: list[dict[str, Any]] = []
    for item in items:
        text = item.get("text")
        if not isinstance(text, str):
            continue
        for segment in text.split("WORKSPACE_ID: ")[1:]:
            header, marker, remainder = segment.partition("SOURCE_BEGIN\n")
            if not marker or "DOC_TYPE: visual_language_manifest" not in header:
                continue
            body, end, _tail = remainder.partition("SOURCE_END")
            if not end:
                continue
            try:
                parsed = json.loads(body)
            except json.JSONDecodeError:
                continue
            if not isinstance(parsed, dict):
                continue
            source_match = re.search(r"^SOURCE_URL:\s*(.+)$", header, re.MULTILINE)
            workspace_match = re.search(r"^([^\n]+)\n", segment)
            brand_match = re.search(r"^BRAND_ID:\s*(.+)$", header, re.MULTILINE)
            documents.append(
                {
                    "manifest": parsed,
                    "sourceUrl": source_match.group(1).strip()
                    if source_match
                    else item.get("sourceUrl"),
                    "workspaceId": workspace_match.group(1).strip()
                    if workspace_match
                    else item.get("workspaceId"),
                    "brandId": brand_match.group(1).strip() if brand_match else item.get("brandId"),
                }
            )
    return documents


def exact_visual_language_items(
    items: list[dict[str, Any]],
    profile_ids: list[str],
    revision_ids: list[str],
    reference_ids: list[str],
) -> list[dict[str, Any]]:
    """Return exact visual-language records from a manifest, never nearby text mentions."""

    profiles = set(profile_ids)
    revisions = set(revision_ids)
    references = set(reference_ids)
    found: dict[str, dict[str, Any]] = {}
    for document in _visual_language_documents(items):
        manifest = document["manifest"]
        records = [
            ("profile", record, "id")
            for record in manifest.get("profiles", [])
            if isinstance(record, dict) and record.get("id") in profiles
        ]
        records.extend(
            ("revision", record, "id")
            for record in manifest.get("revisions", [])
            if isinstance(record, dict) and record.get("id") in revisions
        )
        records.extend(
            ("reference", record, "id")
            for record in manifest.get("references", [])
            if isinstance(record, dict) and record.get("id") in references
        )
        for record_kind, record, _key in records:
            record_id = str(record["id"])
            text = json.dumps(record, ensure_ascii=False, sort_keys=True)
            source_url = document.get("sourceUrl")
            item_id = hashlib.sha256(
                f"{source_url}\n{record_kind}\n{record_id}\n{text}".encode()
            ).hexdigest()[:24]
            found[record_id] = {
                "id": item_id,
                "text": text,
                "sourceUrl": source_url,
                "workspaceId": document.get("workspaceId"),
                "brandId": document.get("brandId"),
                "taskView": "visual-language",
                "docType": f"visual_language_{record_kind}",
                "promotionStatus": "proposal_only",
                "retrievalKind": "visual_reference",
                **({"profileId": record_id} if record_kind == "profile" else {}),
                **({"revisionId": record_id} if record_kind == "revision" else {}),
                **({"referenceId": record_id} if record_kind == "reference" else {}),
                **({"referenceKind": record.get("kind")} if record_kind == "reference" else {}),
            }
    ordered_ids = [*profile_ids, *revision_ids, *reference_ids]
    return [found[record_id] for record_id in ordered_ids if record_id in found]


def exact_creative_field_items(
    items: list[dict[str, Any]], record_ids: list[str], *, project_id: str | None = None
) -> list[dict[str, Any]]:
    """Return exact project-scoped Creative Field records, never identifier mentions."""

    requested = set(record_ids)
    found: dict[str, dict[str, Any]] = {}
    for item in items:
        record_id = item.get("recordId")
        if not isinstance(record_id, str) or record_id not in requested:
            continue
        if project_id and item.get("projectId") != project_id:
            continue
        item = {**item, "retrievalKind": "exact_creative_field"}
        found[record_id] = item
    return [found[record_id] for record_id in record_ids if record_id in found]


async def retrieve(request: dict[str, Any]) -> list[dict[str, Any]]:
    dataset_name = request.get("datasetName")
    query = request.get("text")
    top_k = request.get("topK", 10)
    if not isinstance(dataset_name, str) or not dataset_name.endswith("_staging"):
        raise ValueError("datasetName must be an explicit isolated *_staging dataset")
    if not isinstance(query, str) or not query.strip():
        raise ValueError("text must be a non-empty query")
    if not isinstance(top_k, int) or not 1 <= top_k <= 30:
        raise ValueError("topK must be an integer from 1 through 30")

    import cognee
    from cognee.modules.search.types import SearchType

    entity_ids = request.get("entityIds")
    if entity_ids is not None and (
        not isinstance(entity_ids, list)
        or any(not isinstance(entity_id, str) for entity_id in entity_ids)
    ):
        raise ValueError("entityIds must be an array of strings")
    visual_id_fields = ("profileIds", "revisionIds", "referenceIds")
    for field in visual_id_fields:
        value = request.get(field)
        if value is not None and (
            not isinstance(value, list)
            or any(not isinstance(record_id, str) for record_id in value)
        ):
            raise ValueError(f"{field} must be an array of strings")

    response = await cognee.search(
        query,
        query_type=SearchType.CHUNKS_LEXICAL,
        datasets=[dataset_name],
        top_k=top_k,
        only_context=True,
        include_references=True,
    )
    items = normalize_items(response)
    if request.get("retrievalKind") == "exact_entity":
        return exact_entity_items(items, entity_ids or [])
    if request.get("retrievalKind") == "visual_reference":
        return exact_visual_language_items(
            items,
            request.get("profileIds") or [],
            request.get("revisionIds") or [],
            request.get("referenceIds") or [],
        )
    if request.get("retrievalKind") == "exact_creative_field":
        record_ids = request.get("recordIds")
        if record_ids is None or (
            not isinstance(record_ids, list)
            or any(not isinstance(record_id, str) for record_id in record_ids)
        ):
            raise ValueError(
                "recordIds must be an array of strings for exact Creative Field retrieval"
            )
        return exact_creative_field_items(
            items,
            record_ids,
            project_id=request.get("projectId")
            if isinstance(request.get("projectId"), str)
            else None,
        )
    for item in items:
        item["retrievalKind"] = "lexical_chunk"
    return items


def main() -> int:
    try:
        request = json.loads(sys.stdin.read())
        if not isinstance(request, dict):
            raise ValueError("request must be a JSON object")
        items = asyncio.run(retrieve(request))
        print(json.dumps({"items": items}, ensure_ascii=False))
        return 0
    except Exception as error:  # noqa: BLE001 - process boundary converts failures to stderr
        print(f"context retrieval failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
