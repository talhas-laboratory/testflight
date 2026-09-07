"""JSON-process boundary for deterministic canonical world-view selection.

The source world-model YAML remains canonical. This bridge only validates and
selects records; it performs no Cognee retrieval, inference, or persistence.
"""

from __future__ import annotations

import argparse
import json
import sys
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
    WorldViewRequest,
    compile_world_view,
)


def _records(source: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = source.get(key, [])
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _camel(value: Any) -> Any:
    if isinstance(value, list):
        return [_camel(item) for item in value]
    if not isinstance(value, dict):
        return value
    return {
        "".join(
            part if index == 0 else part.capitalize() for index, part in enumerate(key.split("_"))
        ): _camel(item)
        for key, item in value.items()
    }


def _normalized(value: object) -> str:
    return "".join(character for character in str(value).lower() if character.isalnum())


def _matches(value: object, candidates: object) -> bool:
    if not isinstance(candidates, list) or not value:
        return False
    requested = _normalized(value)
    return any(
        requested in _normalized(candidate) or _normalized(candidate) in requested
        for candidate in candidates
        if _normalized(candidate)
    )


def _in_time_window(value: object, interval: object) -> bool:
    if not value or not isinstance(interval, dict):
        return True
    requested = str(value)
    start = interval.get("from")
    end = interval.get("through")
    return (not start or requested >= str(start)) and (not end or requested <= str(end))


def _select_context(payload: dict[str, Any], world_model_path: Path) -> tuple[str, str, list[str]]:
    """Select one declared context from request scope; never infer beyond metadata."""

    contexts_path = world_model_path.with_name("context-profiles.yaml")
    contexts_source = yaml.safe_load(contexts_path.read_text())
    if not isinstance(contexts_source, dict):
        raise ValueError(f"expected YAML object in {contexts_path}")
    contexts = _records(contexts_source, "contexts")
    explicit_context_id = str(payload.get("contextId") or "")
    if explicit_context_id:
        selected = next((item for item in contexts if item.get("id") == explicit_context_id), None)
        if selected is None:
            raise ValueError("explicit contextId is not defined in the workspace")
        return (
            explicit_context_id,
            str(payload.get("branchId") or selected.get("branch_id") or ""),
            ["explicit context selection"],
        )

    scored: list[tuple[int, dict[str, Any], list[str]]] = []
    for context in contexts:
        if not _in_time_window(payload.get("validTime"), context.get("valid_time")):
            continue
        score = 0
        reasons: list[str] = []
        for request_key, context_key, label in (
            ("audience", "audience_ids", "audience"),
            ("channel", "channel_ids", "channel"),
            ("occasion", "campaign_or_occasion_ids", "occasion"),
            ("assetType", "artifact_type_ids", "asset type"),
        ):
            value = payload.get(request_key)
            if value and _matches(value, context.get(context_key)):
                score += 1
                reasons.append(f"matched declared {label} scope")
        geography = payload.get("geography")
        if geography and _normalized(geography) == _normalized(context.get("geography")):
            score += 1
            reasons.append("matched declared geography scope")
        if score:
            scored.append((score, context, reasons))
    if not scored:
        return "", "", ["no declared context matched the supplied request scope"]
    scored.sort(key=lambda item: (-item[0], str(item[1].get("id"))))
    top_score, selected, reasons = scored[0]
    if len([item for item in scored if item[0] == top_score]) > 1:
        return "", "", ["multiple declared contexts match equally; explicit contextId is required"]
    return (
        str(selected["id"]),
        str(payload.get("branchId") or selected.get("branch_id") or ""),
        reasons,
    )


def resolve_world_view(payload: dict[str, Any], world_model_path: Path) -> dict[str, Any]:
    """Compile one bounded view and include only its selected canonical records."""

    source = yaml.safe_load(world_model_path.read_text())
    if not isinstance(source, dict):
        raise ValueError(f"expected YAML object in {world_model_path}")
    workspace_id = str(payload.get("workspaceId") or "")
    if workspace_id != str(source.get("workspace_id") or ""):
        raise ValueError("world-view workspace does not match the canonical world model")
    scope = payload.get("scope")
    selection_payload = {**payload, **scope} if isinstance(scope, dict) else payload
    context_id, branch_id, selection_receipt = _select_context(selection_payload, world_model_path)
    if not context_id or not branch_id:
        return {
            "viewId": "world-view:runtime-world-view",
            "status": "no_hit",
            "workspaceId": workspace_id,
            "contextId": context_id,
            "branchId": branch_id,
            "perspectiveIds": [],
            "selectedRecordIds": [],
            "unresolvedConflictIds": [],
            "omissions": selection_receipt,
            "routeReceipt": ["applicability selection held before world-view compilation"],
            "records": {
                "states": [],
                "perspectives": [],
                "relationshipFrames": [],
                "evidenceLinks": [],
                "hypotheses": [],
                "experiments": [],
                "observedOutcomes": [],
                "learningUpdates": [],
            },
        }
    request = WorldViewRequest(
        request_id="runtime-world-view",
        workspace_id=workspace_id,
        context_id=context_id,
        branch_id=branch_id,
        task_type=str(payload.get("taskType") or "brief"),
        perspective_ids=tuple(
            value for value in payload.get("perspectiveIds", []) if isinstance(value, str) and value
        ),
        permitted_record_ids=tuple(
            value
            for value in payload.get("permittedRecordIds", [])
            if isinstance(value, str) and value
        ),
    )
    states = tuple(StateSnapshot.model_validate(item) for item in _records(source, "states"))
    perspectives = tuple(
        PerspectiveProfile.model_validate(item) for item in _records(source, "perspectives")
    )
    frames = tuple(
        RelationshipFrame.model_validate(item) for item in _records(source, "relationship_frames")
    )
    evidence_links = tuple(
        EvidenceLink.model_validate(item) for item in _records(source, "evidence_links")
    )
    hypotheses = tuple(
        HypothesisRecord.model_validate(item) for item in _records(source, "hypotheses")
    )
    experiments = tuple(
        ExperimentPlan.model_validate(item) for item in _records(source, "experiments")
    )
    observed_outcomes = tuple(
        ObservedOutcome.model_validate(item) for item in _records(source, "observed_outcomes")
    )
    learning_updates = tuple(
        LearningUpdate.model_validate(item) for item in _records(source, "learning_updates")
    )
    view = compile_world_view(
        request,
        branches=tuple(WorldBranch.model_validate(item) for item in _records(source, "branches")),
        deltas=tuple(
            BranchDelta.model_validate(item) for item in _records(source, "branch_deltas")
        ),
        states=states,
        perspectives=perspectives,
        relationship_frames=frames,
        hypotheses=hypotheses,
        experiments=experiments,
        observed_outcomes=observed_outcomes,
        learning_updates=learning_updates,
        conflicts=tuple(
            BranchConflict.model_validate(item) for item in _records(source, "conflicts")
        ),
    )
    selected = set(view.selected_record_ids)
    linked = set(view.evidence_link_ids)
    output = _camel(
        {
            **view.model_dump(mode="json"),
            "records": {
                "states": [
                    item.model_dump(mode="json") for item in states if item.state_id in selected
                ],
                "perspectives": [
                    item.model_dump(mode="json")
                    for item in perspectives
                    if item.perspective_id in selected
                ],
                "relationship_frames": [
                    item.model_dump(mode="json") for item in frames if item.frame_id in selected
                ],
                "evidence_links": [
                    item.model_dump(mode="json")
                    for item in evidence_links
                    if item.link_id in linked
                ],
                "hypotheses": [
                    item.model_dump(mode="json")
                    for item in hypotheses
                    if item.hypothesis_id in selected
                ],
                "experiments": [
                    item.model_dump(mode="json")
                    for item in experiments
                    if item.experiment_id in selected
                ],
                "observed_outcomes": [
                    item.model_dump(mode="json")
                    for item in observed_outcomes
                    if item.outcome_id in selected
                ],
                "learning_updates": [
                    item.model_dump(mode="json")
                    for item in learning_updates
                    if item.learning_id in selected
                ],
            },
        }
    )
    output["routeReceipt"] = [*selection_receipt, *output["routeReceipt"]]
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--world-model", required=True, type=Path)
    args = parser.parse_args()
    payload = json.loads(sys.stdin.read())
    if not isinstance(payload, dict):
        raise ValueError("world-view request must be a JSON object")
    print(json.dumps(resolve_world_view(payload, args.world_model), default=str))


if __name__ == "__main__":
    main()
