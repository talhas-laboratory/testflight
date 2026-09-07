"""Small write-capable HTTP composition root for the Creative Studio UI."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import threading
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from testflight_adapter_creative_connectors import (
    ConnectorPreflightError,
    compile_generation_packet,
)
from testflight_adapter_sqlite_semantic import ContentAddressedBlobStore, CreativeRepository
from testflight_creative_field import (
    CREATIVE_OPERATOR_IDS,
    INTERPRET_OPERATOR_ID,
    OBSERVE_OPERATOR_ID,
    OUTPUT_EVALUATION_OPERATOR_ID,
    SYNTHESIS_OPERATOR_ID,
    ArtifactStatus,
    BoardRevision,
    CreativeBindingResolver,
    CreativeContextCompiler,
    CreativeContextPacket,
    CreativeEvaluation,
    CreativeEvaluationWorkflow,
    CreativeFieldLifecycle,
    CreativeFieldProposal,
    CreativeFieldRun,
    CreativeFieldRunCoordinator,
    CreativeFieldVersion,
    CreativeOutput,
    CreativeRequest,
    FeedbackRecord,
    FieldBinding,
    FieldDimension,
    FieldProjection,
    GenerationPacket,
    InvocationReceipt,
    OperatorExecutor,
    OperatorPack,
    Placement,
    ProjectBinding,
    ReferenceAsset,
    ReferenceCluster,
    ResolvedCreativeRequest,
    ReviewAction,
    ReviewDecision,
    SourceLicenseRecord,
    TargetCapabilityManifest,
    UserAnnotation,
    load_dimension_registry,
    load_operator_contracts,
    load_operator_pack,
    operator_pack_configuration,
)

from .operator_http import HttpOperatorExecutor

STATIC_ROOT = Path(__file__).parent / "static"
MAX_UPLOAD_BYTES = 15 * 1024 * 1024
MAX_COMMAND_BODY_BYTES = 20 * 1024 * 1024
MAX_EVALUATION_MEDIA_BYTES = 8 * 1024 * 1024
MAX_OPERATOR_MEDIA_BYTES = 8 * 1024 * 1024
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def create_world_view_resolver(
    world_model_path: Path,
) -> Callable[[Mapping[str, Any]], Mapping[str, Any]]:
    """Adapt the existing bounded Brand-world YAML bridge to the Creative Studio port."""

    from testflight_adapter_cognee.world_view_bridge import resolve_world_view

    def resolve_from_world_model(request: Mapping[str, Any]) -> Mapping[str, Any]:
        request_payload = request.get("request", {})
        request_payload = request_payload if isinstance(request_payload, Mapping) else {}
        permitted_record_ids = request_payload.get(
            "permitted_record_ids", request.get("permitted_record_ids", [])
        )
        if not isinstance(permitted_record_ids, list | tuple):
            permitted_record_ids = []
        return resolve_world_view(
            {
                "workspaceId": request.get("workspace_id"),
                "contextId": request.get("context_id"),
                "branchId": request.get("branch_id"),
                "taskType": request_payload.get("task_type", "create"),
                "perspectiveIds": request_payload.get("perspective_ids", []),
                "permittedRecordIds": [
                    item for item in permitted_record_ids if isinstance(item, str) and item
                ],
                "targetEntityIds": request.get("target_entity_ids", []),
                "assetType": request.get("artifact_type"),
                "channel": request.get("channel"),
                "audience": request_payload.get("audience"),
                "geography": request_payload.get("geography"),
                "occasion": request_payload.get("occasion"),
                "validTime": request.get("at_time"),
            },
            world_model_path,
        )

    return resolve_from_world_model


class _MediaAwareOperatorExecutor:
    """Add bounded, rights-gated local media parts while preserving the executor contract."""

    def __init__(
        self,
        delegate: OperatorExecutor,
        repository: CreativeRepository | None,
        blob_store: ContentAddressedBlobStore | None,
    ) -> None:
        self._delegate = delegate
        self._repository = repository
        self._blob_store = blob_store

    def execute(self, request: Mapping[str, Any]):
        input_payload = request.get("input")
        if not isinstance(input_payload, Mapping):
            return self._delegate.execute(request)
        enriched_input = dict(input_payload)
        asset_payload = input_payload.get("asset")
        if not isinstance(asset_payload, Mapping):
            asset_id = input_payload.get("asset_id")
            if isinstance(asset_id, str) and self._repository is not None:
                asset = self._repository.get(ReferenceAsset, asset_id)
                if asset is not None:
                    asset_payload = asset.model_dump(mode="json")
        if isinstance(asset_payload, Mapping):
            self._attach_asset_media(enriched_input, asset_payload)
        output_payload = input_payload.get("output")
        if isinstance(output_payload, Mapping):
            self._attach_output_media(enriched_input, output_payload)
        enriched_request = dict(request)
        enriched_request["input"] = enriched_input
        return self._delegate.execute(enriched_request)

    def _read_bounded(self, content_hash: Any) -> bytes | None:
        if not isinstance(content_hash, str) or not _SHA256.fullmatch(content_hash):
            return None
        if self._blob_store is None:
            return None
        try:
            content = self._blob_store.read(content_hash)
        except (FileNotFoundError, ValueError):
            return None
        return content if len(content) <= MAX_OPERATOR_MEDIA_BYTES else None

    def _attach_asset_media(
        self, input_payload: dict[str, Any], asset_payload: Mapping[str, Any]
    ) -> None:
        media_type = asset_payload.get("media_type")
        content = self._read_bounded(asset_payload.get("content_hash"))
        if not isinstance(media_type, str) or content is None:
            return
        if media_type.startswith("image/"):
            data_url = f"data:{media_type};base64,{base64.b64encode(content).decode('ascii')}"
            self._append_media_part(input_payload, {"type": "image", "data_url": data_url})
        elif media_type.startswith("text/"):
            try:
                input_payload["text_content"] = content.decode("utf-8")
            except UnicodeDecodeError:
                return

    def _attach_output_media(
        self, input_payload: dict[str, Any], output_payload: Mapping[str, Any]
    ) -> None:
        media_type = output_payload.get("media_type")
        content = self._read_bounded(output_payload.get("content_hash"))
        if not isinstance(media_type, str) or content is None:
            return
        if media_type.startswith("image/"):
            data_url = f"data:{media_type};base64,{base64.b64encode(content).decode('ascii')}"
            self._append_media_part(input_payload, {"type": "image", "data_url": data_url})
        elif media_type.startswith("text/"):
            try:
                input_payload["output_text_content"] = content.decode("utf-8")
            except UnicodeDecodeError:
                return

    @staticmethod
    def _append_media_part(input_payload: dict[str, Any], part: Mapping[str, Any]) -> None:
        existing = input_payload.get("media_parts")
        if isinstance(existing, list):
            input_payload["media_parts"] = [*existing, dict(part)]
        else:
            input_payload["media_parts"] = [dict(part)]


class StudioStore:
    """Own UI commands and delegate canonical record writes to the repository adapter."""

    def __init__(
        self,
        *,
        project_id: str,
        repository: CreativeRepository | None = None,
        blob_store: ContentAddressedBlobStore | None = None,
        operator_executor: OperatorExecutor | None = None,
        dimensions: Sequence[FieldDimension] = (),
        project_purpose: str = "Explore a project-scoped creative direction.",
        authority_grant_id: str | None = None,
        target_adapters: Mapping[str, Any] | None = None,
        operator_pack: OperatorPack | None = None,
        operator_index_path: Path | None = None,
        world_view_resolver: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None,
    ) -> None:
        self.project_id = project_id
        self.repository = repository
        self.blob_store = blob_store
        self.operator_executor = (
            _MediaAwareOperatorExecutor(operator_executor, repository, blob_store)
            if operator_executor is not None
            else None
        )
        self.dimensions = tuple(dimensions)
        self.project_purpose = project_purpose
        self.authority_grant_id = authority_grant_id
        self.target_adapters = dict(target_adapters or {})
        self.operator_pack = operator_pack
        self.operator_contracts = (
            load_operator_contracts(list(CREATIVE_OPERATOR_IDS), index_path=operator_index_path)
            if operator_index_path is not None
            else {}
        )
        self.world_view_resolver = world_view_resolver
        self._lifecycle = CreativeFieldLifecycle()
        self.moodboard_id = f"moodboard:{project_id.removeprefix('project:')}"
        self._lock = threading.RLock()
        self._revision = 0
        self.state: dict[str, Any] = {
            "project": {
                "project_id": project_id,
                "name": "Creative Field project",
                "purpose": project_purpose,
                "scope": "Brand world + project-local creative field",
                "status": "active",
            },
            "moodboard": {
                "moodboard_id": self.moodboard_id,
                "name": "Untitled moodboard",
                "status": "draft",
            },
            "references": [],
            "clusters": [],
            "annotations": [],
            "revision": 0,
            "field": {
                "status": "awaiting_reviewed_synthesis",
                "proposal_id": None,
                "version_id": None,
                "principles": [],
                "tensions": [],
                "exclusions": [],
                "dimension_states": [],
                "omissions": [],
            },
            "analysis": {
                "status": "not_started",
                "run_id": None,
                "board_revision_id": None,
                "proposal_id": None,
                "stages": [],
                "errors": [],
                "hold_reason": None,
            },
            "projection": {
                "status": "not_started",
                "request_id": None,
                "field_version_id": None,
                "projection_id": None,
                "context_packet_id": None,
                "omissions": [],
                "conflicts": [],
                "errors": [],
            },
            "generation": {
                "status": "not_started",
                "packet_id": None,
                "target_id": None,
                "invocation_id": None,
                "output_id": None,
                "controls_sent": {},
                "grounding_assets_sent": [],
                "capability_limitations": [],
                "errors": [],
            },
            "evaluation": {
                "status": "not_started",
                "evaluation_id": None,
                "output_id": None,
                "feedback_ids": [],
                "errors": [],
                "receipt": {},
            },
            "events": [],
        }
        self._hydrate()

    def command(self, name: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        with self._lock:
            if name == "add_reference":
                return self._add_reference(payload)
            if name == "annotate_reference":
                return self._annotate_reference(payload)
            if name == "update_board_layout":
                return self._update_board_layout(payload)
            if name == "analyze_field":
                return self._analyze_field(payload)
            if name == "review_field":
                return self._review_field(payload)
            if name == "project_field":
                return self._project_field(payload)
            if name == "prepare_generation":
                return self._prepare_generation(payload)
            if name == "invoke_generation":
                return self._invoke_generation(payload)
            if name == "evaluate_output":
                return self._evaluate_output(payload)
            if name == "reset_demo":
                return self._reset_demo()
            return {"status": "held", "error": f"unsupported command: {name}"}

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return json.loads(json.dumps(self.state))

    def read_blob(self, content_hash: str) -> tuple[bytes, str] | None:
        """Read a blob only when the current project references its hash."""

        if not _SHA256.fullmatch(content_hash) or not self.blob_store:
            return None
        with self._lock:
            asset = next(
                (
                    item
                    for item in self.state["references"]
                    if item.get("content_hash") == content_hash
                ),
                None,
            )
            if asset is None:
                return None
            try:
                return self.blob_store.read(content_hash), str(asset["media_type"])
            except (FileNotFoundError, ValueError):
                return None

    def read_output(self, output_id: str) -> tuple[bytes, str] | None:
        """Read generated bytes only when the output belongs to the current project."""

        if not output_id or not self.repository or not self.blob_store:
            return None
        with self._lock:
            output = self.repository.get(CreativeOutput, output_id)
            if output is None or output.project_id != self.project_id:
                return None
            try:
                return self.blob_store.read(output.content_hash), output.media_type
            except (FileNotFoundError, ValueError):
                return None

    def _hydrate(self) -> None:
        if not self.repository:
            return
        revisions = self.repository.replay_board(self.moodboard_id)
        latest = revisions[-1] if revisions else None
        assets = self.repository.list(ReferenceAsset, project_id=self.project_id)
        asset_by_id = {item.asset_id: item for item in assets}
        if latest:
            self._revision = latest.revision
            self.state["references"] = [
                {
                    **asset_by_id[asset_id].model_dump(mode="json"),
                    "placement": next(
                        (
                            placement.model_dump(mode="json")
                            for placement in latest.placements
                            if placement.asset_id == asset_id
                        ),
                        {"x": 0, "y": 0},
                    ),
                }
                for asset_id in latest.reference_asset_ids
                if asset_id in asset_by_id
            ]
            clusters = {
                cluster.cluster_id: cluster
                for cluster in self.repository.list(ReferenceCluster, project_id=self.project_id)
            }
            self.state["clusters"] = [
                clusters[cluster_id].model_dump(mode="json")
                for cluster_id in latest.cluster_ids
                if cluster_id in clusters
            ]
        self.state["revision"] = self._revision
        current_asset_ids = {item["asset_id"] for item in self.state["references"]}
        annotations = self.repository.list(UserAnnotation, project_id=self.project_id)
        self.state["annotations"] = [
            item.model_dump(mode="json")
            for item in annotations
            if item.target_id in current_asset_ids or item.target_id == self.moodboard_id
        ]
        self.state["events"] = [
            {
                "command": (
                    "reset_demo"
                    if not revision.reference_asset_ids
                    else "update_board_layout"
                    if revision.cluster_ids
                    else "add_reference"
                ),
                "revision": revision.revision,
            }
            for revision in revisions
        ]
        self.state["events"].extend(
            {"command": "annotate_reference", "target_id": item["target_id"]}
            for item in self.state["annotations"]
        )
        reviews = [
            item
            for item in self.repository.list(ReviewDecision)
            if item.target_id
            in {
                self.moodboard_id,
                self.state["field"].get("proposal_id"),
            }
        ]
        if reviews and not (latest and not latest.reference_asset_ids):
            latest_review = reviews[-1]
            self.state["field"]["status"] = {
                ReviewAction.ACCEPT: "accepted",
                ReviewAction.MODIFY: "revision_requested",
                ReviewAction.DEFER: "held",
            }.get(latest_review.action, "awaiting_reviewed_synthesis")
            self.state["events"].extend(
                {
                    "command": "review_field",
                    "action": {
                        ReviewAction.ACCEPT: "accept",
                        ReviewAction.MODIFY: "revise",
                        ReviewAction.DEFER: "hold",
                    }.get(item.action, item.action.value),
                }
                for item in reviews
            )
        runs = self.repository.list(CreativeFieldRun, project_id=self.project_id)
        if runs:
            latest_run = max(runs, key=lambda item: item.finished_at)
            current_board_id = latest.board_revision_id if latest else None
            if latest_run.board_revision_id == current_board_id:
                self.state["analysis"] = self._run_state(latest_run)
                if latest_run.proposal_id:
                    proposal = self.repository.get(CreativeFieldProposal, latest_run.proposal_id)
                    if proposal is not None:
                        self.state["field"] = self._proposal_state(proposal)
                        version = self._accepted_version_for(proposal)
                        if version is not None:
                            self._apply_version(version)
                        self._apply_latest_review()
        if latest is None or latest.reference_asset_ids:
            self._hydrate_latest_projection()
            self._hydrate_latest_generation()
            self._hydrate_latest_evaluation()

    def _add_reference(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        asset_id = payload.get("asset_id")
        if not isinstance(asset_id, str) or not asset_id.strip():
            return {"status": "held", "error": "asset_id is required"}
        if any(item["asset_id"] == asset_id for item in self.state["references"]):
            return {"status": "held", "error": "asset identity already exists"}
        try:
            content_hash = str(payload.get("content_hash") or "pending-upload")
            source_uri = str(payload.get("source_uri") or f"studio://{asset_id}")
            encoded = payload.get("content_base64")
            if encoded is not None:
                if not self.blob_store or not isinstance(encoded, str):
                    return {"status": "held", "error": "binary upload storage is not configured"}
                max_encoded = ((MAX_UPLOAD_BYTES + 2) // 3) * 4
                if len(encoded) > max_encoded:
                    return {"status": "held", "error": "uploaded content exceeds the size limit"}
                content = base64.b64decode(encoded, validate=True)
                if len(content) > MAX_UPLOAD_BYTES:
                    return {"status": "held", "error": "uploaded content exceeds the size limit"}
                actual_hash = hashlib.sha256(content).hexdigest()
                if content_hash != "pending-upload" and content_hash != actual_hash:
                    return {"status": "held", "error": "content hash does not match uploaded bytes"}
                blob = self.blob_store.put(
                    content,
                    media_type=str(payload.get("media_type") or "application/octet-stream"),
                )
                content_hash = blob.content_hash
                source_uri = blob.uri
            asset = ReferenceAsset(
                asset_id=asset_id,
                project_id=self.project_id,
                source_id=str(payload.get("source_id") or f"source:{asset_id}"),
                media_type=str(payload.get("media_type") or "application/octet-stream"),
                label=str(payload.get("label") or asset_id),
                content_hash=content_hash,
                source_uri=source_uri,
                license_record_id=(
                    str(payload["license_record_id"]) if payload.get("license_record_id") else None
                ),
                recorded_at=str(payload.get("recorded_at") or "studio-now"),
            )
            license_payload = payload.get("license")
            license_record = None
            if license_payload is not None:
                if not isinstance(license_payload, Mapping):
                    return {"status": "held", "error": "license must be an object"}
                license_id = asset.license_record_id or f"license:{asset_id}"
                license_record = SourceLicenseRecord(
                    license_record_id=license_id,
                    source_id=asset.source_id,
                    owner=str(license_payload.get("owner"))
                    if license_payload.get("owner")
                    else None,
                    permitted_use=tuple(
                        item
                        for item in license_payload.get("permitted_use", ())
                        if isinstance(item, str) and item.strip()
                    ),
                    disclosure_allowed=bool(license_payload.get("disclosure_allowed", False)),
                    generation_allowed=bool(license_payload.get("generation_allowed", False)),
                    retention_policy=str(
                        license_payload.get("retention_policy") or "project_runtime"
                    ),
                    attribution=str(license_payload.get("attribution"))
                    if license_payload.get("attribution")
                    else None,
                    limitations=tuple(
                        item
                        for item in license_payload.get("limitations", ())
                        if isinstance(item, str) and item.strip()
                    ),
                )
                if asset.license_record_id != license_id:
                    asset = asset.model_copy(update={"license_record_id": license_id})
            elif asset.license_record_id and self.repository:
                if self.repository.get(SourceLicenseRecord, asset.license_record_id) is None:
                    return {
                        "status": "held",
                        "error": "referenced license record does not exist",
                    }
        except (TypeError, ValueError) as error:
            return {"status": "held", "error": f"reference validation failed: {error}"}
        record = asset.model_dump(mode="json")
        index = len(self.state["references"])
        placement = {
            "x": 44 + (index % 3) * 266,
            "y": 44 + (index // 3) * 218,
            "width": 236,
            "height": 178,
            "z_index": index,
            "cluster_id": None,
        }
        next_references = [*self.state["references"], {**record, "placement": placement}]
        next_revision_number = self._revision + 1
        revision = BoardRevision(
            board_revision_id=f"{self.moodboard_id}:revision:{next_revision_number}",
            moodboard_id=self.moodboard_id,
            project_id=self.project_id,
            revision=next_revision_number,
            reference_asset_ids=tuple(item["asset_id"] for item in next_references),
            placements=tuple(
                Placement(
                    placement_id=f"placement:{item['asset_id']}",
                    asset_id=item["asset_id"],
                    x=float(item["placement"]["x"]),
                    y=float(item["placement"]["y"]),
                    width=float(item["placement"].get("width", 236)),
                    height=float(item["placement"].get("height", 178)),
                    z_index=int(item["placement"].get("z_index", 0)),
                    cluster_id=item["placement"].get("cluster_id"),
                )
                for item in next_references
            ),
            cluster_ids=tuple(item["cluster_id"] for item in self.state["clusters"]),
            created_at="studio-now",
            created_by="studio-user",
        )
        if self.repository:
            records = (asset,) if license_record is None else (license_record, asset)
            self.repository.append_records_with_board_revision(
                records,
                revision,
                expected_revision=self._revision,
            )
        self.state["references"] = next_references
        self._revision = next_revision_number
        self.state["revision"] = self._revision
        self.state["events"].append(
            {"command": "add_reference", "asset_id": asset_id, "revision": self._revision}
        )
        return self.snapshot()

    def _update_board_layout(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        """Persist an intentional spatial layout without inferring creative meaning.

        Clusters are immutable records per BoardRevision.  The UI may use a previous
        cluster ID as a temporary key; this command emits a fresh canonical cluster
        identity for the next revision so replay remains historical and auditable.
        """

        raw_placements = payload.get("placements")
        raw_clusters = payload.get("clusters", [])
        if not isinstance(raw_placements, list) or not isinstance(raw_clusters, list):
            return {"status": "held", "error": "placements and clusters must be lists"}
        asset_ids = [item["asset_id"] for item in self.state["references"]]
        expected_assets = set(asset_ids)
        if not expected_assets:
            return {"status": "held", "error": "the board has no references to arrange"}
        by_asset: dict[str, Mapping[str, Any]] = {}
        for placement in raw_placements:
            if not isinstance(placement, Mapping):
                return {"status": "held", "error": "each placement must be an object"}
            asset_id = placement.get("asset_id")
            if not isinstance(asset_id, str) or asset_id in by_asset:
                return {"status": "held", "error": "placements need unique asset_id values"}
            by_asset[asset_id] = placement
        if set(by_asset) != expected_assets:
            return {"status": "held", "error": "layout must include every current board reference"}

        labels: dict[str, str] = {}
        for cluster in raw_clusters:
            if not isinstance(cluster, Mapping):
                return {"status": "held", "error": "each cluster must be an object"}
            key, label = cluster.get("key"), cluster.get("label")
            if (
                not isinstance(key, str)
                or not key.strip()
                or not isinstance(label, str)
                or not label.strip()
            ):
                return {"status": "held", "error": "clusters need a key and label"}
            if key in labels:
                return {"status": "held", "error": "cluster keys must be unique"}
            labels[key] = label.strip()[:80]

        normalized: list[dict[str, Any]] = []
        members: dict[str, list[str]] = {key: [] for key in labels}
        for asset_id in asset_ids:
            placement = by_asset[asset_id]
            try:
                x = float(placement.get("x"))
                y = float(placement.get("y"))
                width = float(placement.get("width", 236))
                height = float(placement.get("height", 178))
                z_index = int(placement.get("z_index", 0))
            except (TypeError, ValueError):
                return {"status": "held", "error": "placement coordinates must be numeric"}
            if not (
                0 <= x <= 10000 and 0 <= y <= 10000 and 80 <= width <= 1200 and 80 <= height <= 1200
            ):
                return {
                    "status": "held",
                    "error": "placement is outside the supported canvas bounds",
                }
            cluster_key = placement.get("cluster_key")
            if cluster_key is not None and (
                not isinstance(cluster_key, str) or cluster_key not in labels
            ):
                return {"status": "held", "error": "placement refers to an unknown cluster"}
            if cluster_key is not None:
                members[cluster_key].append(asset_id)
            normalized.append(
                {
                    "asset_id": asset_id,
                    "x": x,
                    "y": y,
                    "width": width,
                    "height": height,
                    "z_index": z_index,
                    "cluster_key": cluster_key,
                }
            )
        empty_clusters = [key for key, ids in members.items() if not ids]
        if empty_clusters:
            return {"status": "held", "error": "a cluster must contain at least one reference"}

        next_revision = self._revision + 1
        cluster_ids = {
            key: f"{self.moodboard_id}:revision:{next_revision}:cluster:{index + 1}"
            for index, key in enumerate(labels)
        }
        clusters = tuple(
            ReferenceCluster(
                cluster_id=cluster_ids[key],
                project_id=self.project_id,
                label=labels[key],
                asset_ids=tuple(members[key]),
                derivation_id=None,
            )
            for key in labels
        )
        revision = BoardRevision(
            board_revision_id=f"{self.moodboard_id}:revision:{next_revision}",
            moodboard_id=self.moodboard_id,
            project_id=self.project_id,
            revision=next_revision,
            reference_asset_ids=tuple(asset_ids),
            placements=tuple(
                Placement(
                    placement_id=f"placement:{item['asset_id']}",
                    asset_id=item["asset_id"],
                    x=item["x"],
                    y=item["y"],
                    width=item["width"],
                    height=item["height"],
                    z_index=item["z_index"],
                    cluster_id=cluster_ids[item["cluster_key"]] if item["cluster_key"] else None,
                )
                for item in normalized
            ),
            cluster_ids=tuple(cluster.cluster_id for cluster in clusters),
            annotation_ids=tuple(item["annotation_id"] for item in self.state["annotations"]),
            created_at="studio-now",
            created_by="studio-user",
        )
        if self.repository:
            self.repository.append_records_with_board_revision(
                clusters,
                revision,
                expected_revision=self._revision,
            )
        placements_by_asset = {item["asset_id"]: item for item in normalized}
        self.state["references"] = [
            {
                **reference,
                "placement": {
                    **{
                        key: value
                        for key, value in placements_by_asset[reference["asset_id"]].items()
                        if key != "cluster_key"
                    },
                    "cluster_id": (
                        cluster_ids[placements_by_asset[reference["asset_id"]]["cluster_key"]]
                        if placements_by_asset[reference["asset_id"]]["cluster_key"]
                        else None
                    ),
                },
            }
            for reference in self.state["references"]
        ]
        self.state["clusters"] = [cluster.model_dump(mode="json") for cluster in clusters]
        self._revision = next_revision
        self.state["revision"] = next_revision
        self.state["events"].append({"command": "update_board_layout", "revision": next_revision})
        return self.snapshot()

    def _annotate_reference(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        target_id = payload.get("target_id")
        text = payload.get("text")
        if not isinstance(target_id, str) or not isinstance(text, str) or not text.strip():
            return {"status": "held", "error": "target_id and non-empty text are required"}
        if not any(item["asset_id"] == target_id for item in self.state["references"]):
            return {"status": "held", "error": "annotation target is not on this board"}
        annotation = UserAnnotation(
            annotation_id=f"annotation:{len(self.state['annotations']) + 1}",
            project_id=self.project_id,
            target_id=target_id,
            text=text,
            desired_transfer=str(payload["desired_transfer"])
            if payload.get("desired_transfer")
            else None,
            anti_association=str(payload["anti_association"])
            if payload.get("anti_association")
            else None,
            actor_id=str(payload.get("actor_id") or "studio-user"),
            created_at="studio-now",
        )
        self._persist(annotation)
        self.state["annotations"].append(annotation.model_dump(mode="json"))
        self.state["events"].append({"command": "annotate_reference", "target_id": target_id})
        return self.snapshot()

    def _analyze_field(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        """Run the proposal-only observation → interpretation → synthesis bridge."""

        if self.repository is None:
            return {
                "status": ArtifactStatus.HELD.value,
                "error": "analysis requires canonical repository storage",
            }
        if self.operator_executor is None:
            return {
                "status": ArtifactStatus.HELD.value,
                "error": "operator runtime is not configured",
            }
        if not self.dimensions:
            return {
                "status": ArtifactStatus.HELD.value,
                "error": "creative dimension registry is not configured",
            }
        run_id = payload.get("run_id")
        if run_id is None:
            run_id = f"run:{self.moodboard_id}:revision:{self._revision}"
        if not isinstance(run_id, str) or not run_id.strip():
            return {
                "status": ArtifactStatus.HELD.value,
                "error": "run_id must be a non-empty string",
            }
        existing_run = self.repository.get(CreativeFieldRun, run_id)
        if existing_run is not None:
            if existing_run.project_id != self.project_id:
                return {
                    "status": ArtifactStatus.HELD.value,
                    "error": "run_id belongs to another project",
                }
            self.state["analysis"] = self._run_state(existing_run)
            if existing_run.proposal_id:
                proposal = self.repository.get(CreativeFieldProposal, existing_run.proposal_id)
                if proposal is not None:
                    self.state["field"] = self._proposal_state(proposal)
                    version = self._accepted_version_for(proposal)
                    if version is not None:
                        self._apply_version(version)
                    self._apply_latest_review()
            else:
                self.state["field"]["status"] = f"analysis_{existing_run.status.value}"
            return self.snapshot()
        derivation_id = payload.get("derivation_id")
        if derivation_id is not None and (
            not isinstance(derivation_id, str) or not derivation_id.strip()
        ):
            return {
                "status": ArtifactStatus.HELD.value,
                "error": "derivation_id must be a non-empty string",
            }
        started_at = _utc_now()
        effective_derivation_id = derivation_id or f"derivation:creative-field:{run_id}"
        try:
            result = CreativeFieldRunCoordinator(
                repository=self.repository,
                project_id=self.project_id,
                project_purpose=self.project_purpose,
                dimensions=self.dimensions,
                executor=self.operator_executor,
                operator_configuration=self._operator_configuration(),
            ).run(
                run_id=run_id,
                moodboard_id=self.moodboard_id,
                derivation_id=derivation_id,
            )
        except (TypeError, ValueError) as error:
            return {
                "status": ArtifactStatus.HELD.value,
                "error": f"analysis validation failed: {error}",
            }
        except Exception as error:  # noqa: BLE001 - normalize the command boundary.
            return {
                "status": ArtifactStatus.FAILED.value,
                "error": f"analysis failed: {error}",
            }

        run_record = CreativeFieldRun(
            run_id=result.run_id,
            project_id=result.project_id,
            moodboard_id=result.moodboard_id,
            board_revision_id=result.board_revision_id,
            status=result.status,
            proposal_id=result.proposal_id,
            stage_results=tuple(
                {
                    "stage": stage.stage,
                    "subject_id": stage.subject_id,
                    "status": stage.status.value,
                    "record_ids": list(stage.record_ids),
                    "errors": list(stage.errors),
                    "hold_reason": stage.hold_reason,
                    "receipt": dict(stage.receipt),
                }
                for stage in result.stages
            ),
            errors=result.errors,
            hold_reason=result.hold_reason,
            started_at=started_at,
            finished_at=_utc_now(),
            derivation_id=effective_derivation_id,
        )
        try:
            self.repository.append(run_record)
        except Exception as error:  # noqa: BLE001 - preserve canonical-write failure at the boundary.
            return {
                "status": ArtifactStatus.FAILED.value,
                "error": f"analysis run persistence failed: {error}",
            }

        self.state["analysis"] = self._run_state(run_record)
        if result.proposal is not None:
            self.state["field"] = self._proposal_state(result.proposal)
        else:
            self.state["field"]["status"] = f"analysis_{result.status.value}"
        self.state["events"].append(
            {
                "command": "analyze_field",
                "run_id": result.run_id,
                "status": result.status.value,
                "proposal_id": result.proposal_id,
            }
        )
        return self.snapshot()

    @staticmethod
    def _proposal_state(proposal: CreativeFieldProposal) -> dict[str, Any]:
        return {
            "status": "proposal_ready_for_review",
            "proposal_id": proposal.proposal_id,
            "version_id": None,
            "principles": [item.statement for item in proposal.principles],
            "tensions": [item.statement for item in proposal.tensions],
            "exclusions": [item.statement for item in proposal.exclusions],
            "dimension_states": [
                {
                    "dimension_id": item.dimension_id,
                    "summary": item.summary,
                    "values": item.values,
                }
                for item in proposal.dimension_states
            ],
            "omissions": [
                f"{item.dimension_id}: {item.reason}" for item in proposal.missing_dimensions
            ],
        }

    @staticmethod
    def _run_state(run: CreativeFieldRun) -> dict[str, Any]:
        return {
            "status": run.status.value,
            "run_id": run.run_id,
            "board_revision_id": run.board_revision_id,
            "proposal_id": run.proposal_id,
            "stages": [dict(stage) for stage in run.stage_results],
            "errors": list(run.errors),
            "hold_reason": run.hold_reason,
        }

    def _apply_latest_review(self) -> None:
        if self.repository is None or not self.state["references"]:
            return
        reviews = [
            item
            for item in self.repository.list(ReviewDecision)
            if item.target_id == self.moodboard_id
        ]
        if not reviews:
            return
        latest_review = reviews[-1]
        self.state["field"]["status"] = {
            ReviewAction.ACCEPT: "accepted",
            ReviewAction.MODIFY: "revision_requested",
            ReviewAction.DEFER: "held",
        }.get(latest_review.action, self.state["field"]["status"])

    def _accepted_version_for(self, proposal: CreativeFieldProposal) -> CreativeFieldVersion | None:
        if self.repository is None:
            return None
        versions = [
            item
            for item in self.repository.list(CreativeFieldVersion, project_id=self.project_id)
            if item.field_id == proposal.field_id
            and item.dependency_manifest.get("proposal_id") == proposal.proposal_id
        ]
        return max(versions, key=lambda item: item.created_at) if versions else None

    def _apply_version(self, version: CreativeFieldVersion) -> None:
        self.state["field"]["status"] = "accepted"
        self.state["field"]["version_id"] = version.version_id

    def _review_field(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        action = payload.get("action")
        if action not in {"accept", "hold", "revise"}:
            return {"status": "held", "error": "review action must be accept, hold or revise"}
        review_action = {
            "accept": ReviewAction.ACCEPT,
            "hold": ReviewAction.DEFER,
            "revise": ReviewAction.MODIFY,
        }[action]
        proposal = self._current_proposal()
        if action == "accept" and proposal is not None:
            existing_version = self._accepted_version_for(proposal)
            if existing_version is not None:
                self._apply_version(existing_version)
                return self.snapshot()
            authority_grant_id = payload.get("authority_grant_id") or self.authority_grant_id
            if not isinstance(authority_grant_id, str) or not authority_grant_id.strip():
                return {
                    "status": ArtifactStatus.HELD.value,
                    "error": "accepting a proposal requires authority_grant_id",
                }
            review_id = f"{self.moodboard_id}:review:{len(self._review_events()) + 1:06d}"
            decision = ReviewDecision(
                review_id=review_id,
                target_id=proposal.proposal_id,
                action=review_action,
                actor_id=str(payload.get("actor_id") or "studio-user"),
                rationale=str(payload.get("rationale") or "Approved in Creative Studio."),
                created_at=_utc_now(),
                authority_grant_id=authority_grant_id,
                derivation_id=f"studio:{proposal.proposal_id}:review",
            )
            versions = [
                item
                for item in self.repository.list(CreativeFieldVersion, project_id=self.project_id)
                if item.field_id == proposal.field_id
            ]
            parent_version = max(versions, key=lambda item: item.created_at) if versions else None
            version_result = self._lifecycle.review_and_version(
                proposal=proposal,
                decision=decision,
                version_id=self._next_version_id(proposal.field_id),
                reviewed_at=decision.created_at,
                parent_version=parent_version,
            )
            if (
                version_result.status is not ArtifactStatus.SUCCESS
                or version_result.version is None
            ):
                return {
                    "status": version_result.status.value,
                    "error": "; ".join(version_result.errors) or "field version was not created",
                    "hold_reason": version_result.hold_reason,
                }
            try:
                self.repository.append_many((decision, version_result.version))
            except Exception as error:  # noqa: BLE001 - preserve canonical-write failure at boundary.
                return {
                    "status": ArtifactStatus.FAILED.value,
                    "error": f"field review persistence failed: {error}",
                }
            self.state["field"] = self._proposal_state(proposal)
            self._apply_version(version_result.version)
            self.state["events"].append(
                {
                    "command": "review_field",
                    "action": action,
                    "proposal_id": proposal.proposal_id,
                    "version_id": version_result.version.version_id,
                }
            )
            return self.snapshot()
        review = ReviewDecision(
            review_id=f"{self.moodboard_id}:review:{len(self._review_events()) + 1:06d}",
            target_id=proposal.proposal_id if proposal is not None else self.moodboard_id,
            action=review_action,
            actor_id=str(payload.get("actor_id") or "studio-user"),
            rationale=str(payload.get("rationale") or "Reviewed in Creative Studio."),
            created_at=_utc_now(),
            authority_grant_id=(
                str(payload["authority_grant_id"])
                if payload.get("authority_grant_id")
                else self.authority_grant_id
            ),
            derivation_id=(
                f"studio:{proposal.proposal_id if proposal else self.moodboard_id}:review"
            ),
        )
        self._persist(review)
        self.state["field"]["status"] = {
            "accept": "accepted",
            "hold": "held",
            "revise": "revision_requested",
        }[action]
        self.state["events"].append({"command": "review_field", "action": action})
        return self.snapshot()

    def _current_proposal(self) -> CreativeFieldProposal | None:
        if self.repository is None:
            return None
        proposal_id = self.state["field"].get("proposal_id")
        if not isinstance(proposal_id, str) or not proposal_id.strip():
            return None
        proposal = self.repository.get(CreativeFieldProposal, proposal_id)
        return proposal if proposal is not None and proposal.project_id == self.project_id else None

    def _next_version_id(self, field_id: str) -> str:
        if self.repository is None:
            return f"{field_id}@1"
        versions = [
            item
            for item in self.repository.list(CreativeFieldVersion, project_id=self.project_id)
            if item.field_id == field_id
        ]
        numbers = [
            int(item.version_id.rsplit("@", 1)[1])
            for item in versions
            if item.version_id.rsplit("@", 1)[-1].isdigit()
        ]
        return f"{field_id}@{max(numbers, default=0) + 1}"

    def _project_field(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        """Bind an accepted field to scoped entities and compile one artifact context packet."""

        if self.repository is None:
            return {
                "status": ArtifactStatus.HELD.value,
                "error": "projection requires canonical repository storage",
            }
        version_id = self.state["field"].get("version_id")
        if not isinstance(version_id, str) or not version_id.strip():
            return {
                "status": ArtifactStatus.HELD.value,
                "error": "an accepted field version is required before projection",
            }
        version = self.repository.get(CreativeFieldVersion, version_id)
        if version is None or version.project_id != self.project_id:
            return {
                "status": ArtifactStatus.HELD.value,
                "error": "field version is not available in this project",
            }

        def required_string(name: str) -> str:
            value = payload.get(name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} is required")
            return value

        def string_tuple(name: str, *, required: bool = False) -> tuple[str, ...]:
            value = payload.get(name, ())
            if not isinstance(value, (list, tuple)):
                raise ValueError(f"{name} must be a list")
            result = tuple(item for item in value if isinstance(item, str) and item.strip())
            if required and not result:
                raise ValueError(f"{name} must contain at least one value")
            return result

        try:
            workspace_id = required_string("workspace_id")
            context_id = required_string("context_id")
            branch_id = str(payload.get("branch_id") or "branch:main")
            privacy_policy_id = required_string("privacy_policy_id")
            authority_grant_id = required_string("authority_grant_id")
            target_entity_ids = string_tuple("target_entity_ids", required=True)
            entities_payload = payload.get("entities")
            if not isinstance(entities_payload, list) or any(
                not isinstance(item, Mapping) for item in entities_payload
            ):
                raise ValueError("entities must be a list of objects")
            request_payload = payload.get("request", {})
            if not isinstance(request_payload, Mapping):
                raise ValueError("request must be an object")
            request_id = str(
                request_payload.get("request_id")
                or payload.get("request_id")
                or f"request:{version.version_id}:default"
            )
            task_type = str(request_payload.get("task_type") or "create")
            artifact_type = str(
                request_payload.get("artifact_type") or required_string("artifact_type")
            )
            modality = str(request_payload.get("modality") or required_string("modality"))
            target = str(request_payload.get("target") or required_string("target"))
            audience = request_payload.get("audience")
            if audience is not None and not isinstance(audience, str):
                raise ValueError("request.audience must be a string")
            permission_context = request_payload.get("permission_context", {})
            if not isinstance(permission_context, Mapping):
                raise ValueError("request.permission_context must be an object")
            target_manifest_payload = payload.get("target_manifest")
            if not isinstance(target_manifest_payload, Mapping):
                raise ValueError("target_manifest must be an object")
            target_manifest = TargetCapabilityManifest.model_validate(target_manifest_payload)
            if target_manifest.privacy_policy_id != privacy_policy_id:
                raise ValueError("target manifest privacy policy does not match project policy")
            channel = payload.get("channel", request_payload.get("channel"))
            if channel is not None and not isinstance(channel, str):
                raise ValueError("channel must be a string")
            at_time = payload.get("at_time", request_payload.get("valid_time"))
            if at_time is not None and not isinstance(at_time, str):
                raise ValueError("at_time must be a string")
            world_view = payload.get("world_view")
            if world_view is None and self.world_view_resolver is not None:
                try:
                    world_view = self.world_view_resolver(
                        {
                            "workspace_id": workspace_id,
                            "context_id": context_id,
                            "branch_id": branch_id,
                            "target_entity_ids": list(target_entity_ids),
                            "permitted_record_ids": payload.get("permitted_record_ids", []),
                            "request": dict(request_payload),
                            "artifact_type": artifact_type,
                            "channel": channel,
                            "at_time": at_time,
                        }
                    )
                except Exception as error:  # noqa: BLE001 - resolver failures become held state.
                    raise ValueError(f"world view resolution failed: {error}") from error
            if not isinstance(world_view, Mapping):
                raise ValueError("world_view must be an object")
            view_workspace_id = world_view.get("workspace_id", world_view.get("workspaceId"))
            if view_workspace_id is not None and view_workspace_id != workspace_id:
                raise ValueError("world view workspace does not match project binding")
            view_context_id = world_view.get("context_id", world_view.get("contextId"))
            if view_context_id is not None and view_context_id != context_id:
                raise ValueError("world view context does not match project binding")
            view_branch_id = world_view.get("branch_id", world_view.get("branchId"))
            if view_branch_id is not None and view_branch_id != branch_id:
                raise ValueError("world view branch does not match project binding")
            lens = required_string("lens")
            disclosure_manifest_id = required_string("disclosure_manifest_id")
            project_binding = ProjectBinding(
                binding_id=str(
                    payload.get("project_binding_id") or f"project-binding:{self.project_id}"
                ),
                project_id=self.project_id,
                workspace_id=workspace_id,
                context_id=context_id,
                target_entity_ids=target_entity_ids,
                branch_id=branch_id,
                privacy_policy_id=privacy_policy_id,
                authority_grant_id=authority_grant_id,
            )
            field_binding = FieldBinding(
                binding_id=str(
                    payload.get("field_binding_id") or f"field-binding:{version.version_id}"
                ),
                project_id=self.project_id,
                field_version_id=version.version_id,
                target_entity_ids=target_entity_ids,
                context_id=context_id,
                artifact_type_selectors=(artifact_type,),
                channel_selectors=((channel,) if channel else ()),
                valid_from=payload.get("valid_from")
                if isinstance(payload.get("valid_from"), str)
                else None,
                valid_until=payload.get("valid_until")
                if isinstance(payload.get("valid_until"), str)
                else None,
                precedence=int(payload.get("precedence", 0)),
                authority_grant_id=authority_grant_id,
            )
            request = CreativeRequest(
                request_id=request_id,
                project_id=self.project_id,
                task_type=task_type,
                artifact_type=artifact_type,
                modality=modality,
                target=target,
                audience=audience,
                permission_context=dict(permission_context),
            )
        except (TypeError, ValueError) as error:
            return {
                "status": ArtifactStatus.HELD.value,
                "error": f"projection validation failed: {error}",
            }

        resolver = CreativeBindingResolver()
        binding_result = resolver.resolve_field(
            project_binding=project_binding,
            field_binding=field_binding,
            field_version=version,
            entities=tuple(entities_payload),
            artifact_type=artifact_type,
            channel=channel,
            at_time=at_time,
            existing_bindings=self.repository.list(FieldBinding, project_id=self.project_id),
        )
        if binding_result.status is not ArtifactStatus.SUCCESS:
            return {
                "status": binding_result.status.value,
                "error": "; ".join(binding_result.errors) or "field binding was not resolved",
                "hold_reason": binding_result.hold_reason,
            }
        compiler = CreativeContextCompiler()
        resolved_result = compiler.resolve_request(
            request=request,
            project_binding_id=project_binding.binding_id,
            field_binding=field_binding,
            field_version=version,
            world_view_request_id=str(
                payload.get("world_view_request_id") or f"world-view-request:{request.request_id}"
            ),
            target_capability_manifest_id=target_manifest.target_id,
            lens=lens,
        )
        if resolved_result.resolved_request is None:
            return {
                "status": resolved_result.status.value,
                "error": "; ".join(resolved_result.errors) or "creative request was not resolved",
                "hold_reason": resolved_result.hold_reason,
            }
        compiled = compiler.compile(
            resolved_request=resolved_result.resolved_request,
            request=request,
            field_version=version,
            field_binding=field_binding,
            world_view=world_view,
            target_manifest=target_manifest,
            disclosure_manifest_id=disclosure_manifest_id,
            visual_language_revision_ids=tuple(
                item
                for item in payload.get("visual_language_revision_ids", ())
                if isinstance(item, str)
            ),
        )
        if compiled.status not in {ArtifactStatus.SUCCESS, ArtifactStatus.PARTIAL}:
            return {
                "status": compiled.status.value,
                "error": "; ".join(compiled.errors) or "context packet was not compiled",
                "hold_reason": compiled.hold_reason,
            }
        records = tuple(
            item
            for item in (
                project_binding,
                field_binding,
                resolved_result.resolved_request,
                request,
                target_manifest,
                compiled.projection,
                compiled.packet,
            )
            if item is not None
        )
        try:
            self.repository.append_many(records)
        except Exception as error:  # noqa: BLE001 - preserve canonical-write failure at boundary.
            return {
                "status": ArtifactStatus.FAILED.value,
                "error": f"projection persistence failed: {error}",
            }
        self.state["projection"] = self._projection_state(compiled)
        self.state["events"].append(
            {
                "command": "project_field",
                "request_id": request.request_id,
                "status": compiled.status.value,
                "context_packet_id": compiled.packet.packet_id if compiled.packet else None,
            }
        )
        return self.snapshot()

    @staticmethod
    def _projection_state(result: Any) -> dict[str, Any]:
        return {
            "status": result.status.value,
            "request_id": result.resolved_request.request_id if result.resolved_request else None,
            "field_version_id": result.projection.field_version_id if result.projection else None,
            "projection_id": result.projection.projection_id if result.projection else None,
            "context_packet_id": result.packet.packet_id if result.packet else None,
            "omissions": list(result.omissions),
            "conflicts": list(result.conflicts),
            "errors": list(result.errors),
            "receipt": dict(result.receipt),
        }

    def _hydrate_latest_projection(self) -> None:
        if self.repository is None:
            return
        candidates: list[tuple[CreativeContextPacket, FieldProjection]] = []
        for packet in self.repository.list(CreativeContextPacket):
            resolved = self.repository.get(ResolvedCreativeRequest, packet.request_id)
            if resolved is None:
                continue
            project_binding = self.repository.get(ProjectBinding, resolved.project_binding_id)
            if project_binding is None or project_binding.project_id != self.project_id:
                continue
            projection = self.repository.get(FieldProjection, packet.field_projection_id)
            if projection is not None:
                candidates.append((packet, projection))
        if not candidates:
            return
        packet, projection = max(candidates, key=lambda item: item[0].packet_id)
        self.state["projection"] = {
            "status": packet.status.value,
            "request_id": packet.request_id,
            "field_version_id": projection.field_version_id,
            "projection_id": projection.projection_id,
            "context_packet_id": packet.packet_id,
            "omissions": list(packet.omissions),
            "conflicts": list(packet.conflicts),
            "errors": [],
            "receipt": {},
        }

    def _prepare_generation(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        """Translate the current field projection into a target-specific generation packet."""

        if self.repository is None:
            return {
                "status": ArtifactStatus.HELD.value,
                "error": "generation preparation requires canonical repository storage",
            }
        projection_id = self.state["projection"].get("projection_id")
        if not isinstance(projection_id, str) or not projection_id.strip():
            return {
                "status": ArtifactStatus.HELD.value,
                "error": "a compiled field projection is required before generation",
            }
        projection = self.repository.get(FieldProjection, projection_id)
        if projection is None:
            return {
                "status": ArtifactStatus.HELD.value,
                "error": "compiled field projection is not available",
            }
        manifest_payload = payload.get("target_manifest")
        disclosure_manifest_id = payload.get("disclosure_manifest_id")
        try:
            if not isinstance(manifest_payload, Mapping):
                raise ValueError("target_manifest must be an object")
            if not isinstance(disclosure_manifest_id, str) or not disclosure_manifest_id.strip():
                raise ValueError("disclosure_manifest_id is required")
            manifest = TargetCapabilityManifest.model_validate(manifest_payload)
            grounding_value = payload.get("grounding_asset_ids", ())
            permitted_value = payload.get("permitted_asset_ids", ())
            if not isinstance(grounding_value, (list, tuple)):
                raise ValueError("grounding_asset_ids must be a list")
            if not isinstance(permitted_value, (list, tuple)):
                raise ValueError("permitted_asset_ids must be a list")
            grounding = tuple(item for item in grounding_value if isinstance(item, str))
            permitted = tuple(item for item in permitted_value if isinstance(item, str))
            self._validate_generation_assets(grounding)
            self._validate_generation_assets(permitted)
            packet = compile_generation_packet(
                projection,
                manifest,
                disclosure_manifest_id=disclosure_manifest_id,
                grounding_asset_ids=grounding,
                permitted_asset_ids=permitted,
            )
        except ConnectorPreflightError as error:
            return {
                "status": ArtifactStatus.HELD.value,
                "error": str(error),
                "hold_reason": "target_preflight_failed",
            }
        except (TypeError, ValueError) as error:
            return {
                "status": ArtifactStatus.HELD.value,
                "error": f"generation validation failed: {error}",
            }
        try:
            self.repository.append_many((manifest, packet))
        except Exception as error:  # noqa: BLE001 - preserve canonical-write failure at boundary.
            return {
                "status": ArtifactStatus.FAILED.value,
                "error": f"generation packet persistence failed: {error}",
            }
        self.state["generation"] = self._generation_state(packet)
        self.state["events"].append(
            {
                "command": "prepare_generation",
                "packet_id": packet.packet_id,
                "target_id": manifest.target_id,
            }
        )
        return self.snapshot()

    def _validate_generation_assets(self, asset_ids: Sequence[str]) -> None:
        """Require current-project source assets to explicitly allow target generation."""

        if self.repository is None:
            raise ValueError("generation asset validation requires canonical repository storage")
        for asset_id in asset_ids:
            asset = self.repository.get(ReferenceAsset, asset_id)
            if asset is None or asset.project_id != self.project_id:
                raise ValueError(f"generation asset is not available in this project: {asset_id}")
            if not asset.license_record_id:
                raise ValueError(f"generation asset has no license record: {asset_id}")
            license_record = self.repository.get(SourceLicenseRecord, asset.license_record_id)
            if license_record is None:
                raise ValueError(f"generation asset license is not available: {asset_id}")
            if not license_record.generation_allowed:
                raise ValueError(f"generation asset is not cleared for generation: {asset_id}")
            if not license_record.disclosure_allowed:
                raise ValueError(f"generation asset is not cleared for disclosure: {asset_id}")

    def _invoke_generation(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        """Invoke one configured target adapter and persist its normalized output and receipt."""

        if self.repository is None:
            return {
                "status": ArtifactStatus.HELD.value,
                "error": "generation invocation requires canonical repository storage",
            }
        packet_id = self.state["generation"].get("packet_id")
        if not isinstance(packet_id, str) or not packet_id.strip():
            return {
                "status": ArtifactStatus.HELD.value,
                "error": "a prepared generation packet is required before invocation",
            }
        packet = self.repository.get(GenerationPacket, packet_id)
        if packet is None:
            return {
                "status": ArtifactStatus.HELD.value,
                "error": "prepared generation packet is not available",
            }
        authority_grant_id = payload.get("authority_grant_id") or self.authority_grant_id
        if not isinstance(authority_grant_id, str) or not authority_grant_id.strip():
            return {
                "status": ArtifactStatus.HELD.value,
                "error": "generation invocation requires authority_grant_id",
            }
        adapter = self.target_adapters.get(packet.target_capability_manifest_id)
        if adapter is None:
            return {
                "status": ArtifactStatus.HELD.value,
                "error": (
                    f"target adapter is not configured: {packet.target_capability_manifest_id}"
                ),
            }
        if self.blob_store is None:
            return {
                "status": ArtifactStatus.HELD.value,
                "error": "generated output storage is not configured",
            }
        invocation_value = payload.get("invocation_id")
        if invocation_value is not None and (
            not isinstance(invocation_value, str) or not invocation_value.strip()
        ):
            return {
                "status": ArtifactStatus.HELD.value,
                "error": "invocation_id must be a non-empty string",
            }
        invocation_id = str(invocation_value or f"invocation:{packet.packet_id}")
        existing = self.repository.get(InvocationReceipt, invocation_id)
        if existing is not None:
            if existing.packet_id != packet.packet_id:
                return {
                    "status": ArtifactStatus.HELD.value,
                    "error": "invocation_id is already bound to another generation packet",
                }
            self._apply_invocation_state(packet, existing)
            return self.snapshot()

        started_at = _utc_now()
        output = None
        errors: list[str] = []
        adapter_receipt = None
        try:
            result = adapter.invoke(packet, invocation_id=invocation_id)
            adapter_receipt = getattr(result, "receipt", None)
            status = self._coerce_artifact_status(
                getattr(adapter_receipt, "status", getattr(result, "status", ArtifactStatus.FAILED))
            )
            if adapter_receipt is None:
                errors.append("target adapter returned no invocation receipt")
                status = ArtifactStatus.FAILED
            errors.extend(self._string_values(getattr(adapter_receipt, "errors", ())))
            normalized = getattr(result, "output", None)
            if status in {ArtifactStatus.SUCCESS, ArtifactStatus.PARTIAL}:
                if normalized is None:
                    errors.append("target adapter returned no output")
                    status = ArtifactStatus.FAILED
                elif getattr(normalized, "packet_id", None) != packet.packet_id:
                    errors.append("target adapter output references a different packet")
                    status = ArtifactStatus.FAILED
                else:
                    content = getattr(normalized, "content", None)
                    if isinstance(content, str):
                        content_bytes = content.encode("utf-8")
                    elif isinstance(content, bytes):
                        content_bytes = content
                    else:
                        errors.append("target adapter output content is not text or binary")
                        status = ArtifactStatus.FAILED
                        content_bytes = b""
                    if status in {ArtifactStatus.SUCCESS, ArtifactStatus.PARTIAL}:
                        blob = self.blob_store.put(
                            content_bytes,
                            media_type=str(getattr(normalized, "media_type", "")),
                        )
                        projection = self.repository.get(FieldProjection, packet.projection_id)
                        if projection is None:
                            errors.append("generation packet projection is not available")
                            status = ArtifactStatus.FAILED
                        else:
                            output = CreativeOutput(
                                output_id=str(
                                    getattr(normalized, "output_id", None)
                                    or f"output:{invocation_id}"
                                ),
                                invocation_id=invocation_id,
                                packet_id=packet.packet_id,
                                project_id=self.project_id,
                                request_id=projection.request_id,
                                media_type=blob.media_type,
                                content_hash=blob.content_hash,
                                source_uri=blob.uri,
                                content_size=blob.size,
                                adapter_version=packet.adapter_version,
                                status=status,
                                derivation_id=f"output:{invocation_id}",
                            )
        except ConnectorPreflightError as error:
            status = ArtifactStatus.HELD
            errors.append(str(error))
        except Exception as error:  # noqa: BLE001 - normalize provider/adapter failures at boundary.
            status = ArtifactStatus.FAILED
            errors.append(str(error))

        target_id = str(getattr(adapter_receipt, "target_id", packet.target_capability_manifest_id))
        adapter_version = str(getattr(adapter_receipt, "adapter_version", packet.adapter_version))
        disclosure_manifest_id = str(
            getattr(adapter_receipt, "disclosure_manifest_id", packet.disclosure_manifest_id)
        )
        grounding_assets = tuple(
            item
            for item in getattr(
                adapter_receipt, "grounding_assets_sent", packet.grounding_assets_sent
            )
            if isinstance(item, str)
        )
        limitations = tuple(
            item
            for item in getattr(
                adapter_receipt, "capability_limitations", packet.capability_limitations
            )
            if isinstance(item, str)
        )
        receipt = InvocationReceipt(
            invocation_id=invocation_id,
            packet_id=packet.packet_id,
            target_id=target_id,
            adapter_version=adapter_version,
            disclosure_manifest_id=disclosure_manifest_id,
            grounding_assets_sent=grounding_assets,
            capability_limitations=limitations,
            output_id=output.output_id if output is not None else None,
            authority_grant_id=authority_grant_id,
            status=status,
            errors=tuple(dict.fromkeys(errors)),
            started_at=started_at,
            finished_at=_utc_now(),
            derivation_id=f"invocation:{invocation_id}",
        )
        try:
            records = (receipt,) if output is None else (receipt, output)
            self.repository.append_many(records)
        except Exception as error:  # noqa: BLE001 - preserve canonical-write failure at boundary.
            return {
                "status": ArtifactStatus.FAILED.value,
                "error": f"generation output persistence failed: {error}",
            }
        self._apply_invocation_state(packet, receipt)
        self.state["events"].append(
            {
                "command": "invoke_generation",
                "invocation_id": receipt.invocation_id,
                "status": receipt.status.value,
                "output_id": receipt.output_id,
            }
        )
        return self.snapshot()

    @staticmethod
    def _coerce_artifact_status(value: Any) -> ArtifactStatus:
        if isinstance(value, ArtifactStatus):
            return value
        try:
            return ArtifactStatus(str(value))
        except ValueError:
            return ArtifactStatus.FAILED

    @staticmethod
    def _string_values(value: Any) -> tuple[str, ...]:
        if not isinstance(value, (list, tuple)):
            return ()
        return tuple(item for item in value if isinstance(item, str) and item.strip())

    def _apply_invocation_state(self, packet: GenerationPacket, receipt: InvocationReceipt) -> None:
        state = self._generation_state(packet)
        state.update(
            {
                "status": receipt.status.value,
                "invocation_id": receipt.invocation_id,
                "output_id": receipt.output_id,
                "errors": list(receipt.errors),
            }
        )
        self.state["generation"] = state

    def _evaluate_output(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        """Evaluate one persisted output through the provider-neutral evaluation operator."""

        if self.repository is None:
            return {
                "status": ArtifactStatus.HELD.value,
                "error": "output evaluation requires canonical repository storage",
            }
        output_id_value = payload.get("output_id") or self.state["generation"].get("output_id")
        if not isinstance(output_id_value, str) or not output_id_value.strip():
            return {
                "status": ArtifactStatus.HELD.value,
                "error": "a generated output is required before evaluation",
            }
        output = self.repository.get(CreativeOutput, output_id_value)
        if output is None or output.project_id != self.project_id:
            return {
                "status": ArtifactStatus.HELD.value,
                "error": "generated output is not available in this project",
            }
        packet = self.repository.get(GenerationPacket, output.packet_id)
        if packet is None:
            return {
                "status": ArtifactStatus.HELD.value,
                "error": "output generation packet is not available",
            }
        projection = self.repository.get(FieldProjection, packet.projection_id)
        if projection is None:
            return {
                "status": ArtifactStatus.HELD.value,
                "error": "output field projection is not available",
            }
        request = self.repository.get(CreativeRequest, projection.request_id)
        version = self.repository.get(CreativeFieldVersion, projection.field_version_id)
        if request is None or request.project_id != self.project_id:
            return {
                "status": ArtifactStatus.HELD.value,
                "error": "output creative request is not available in this project",
            }
        if version is None or version.project_id != self.project_id:
            return {
                "status": ArtifactStatus.HELD.value,
                "error": "output field version is not available in this project",
            }
        if self.operator_executor is None:
            return {
                "status": ArtifactStatus.HELD.value,
                "error": "operator runtime is not configured",
            }
        existing = [
            item
            for item in self.repository.list(CreativeEvaluation)
            if item.output_id == output.output_id
        ]
        if existing:
            evaluation = max(existing, key=lambda item: item.evaluation_id)
            self._apply_evaluation_state(evaluation)
            return self.snapshot()

        input_payload: dict[str, Any] = {
            "output": self._evaluation_output_payload(output),
            "generation_packet": packet.model_dump(mode="json"),
            "request": request.model_dump(mode="json"),
            "projection": projection.model_dump(mode="json"),
            "field_version": version.model_dump(mode="json"),
        }
        evaluation_derivation = f"evaluation:{output.output_id}"
        execution_request = {
            "operator_id": OUTPUT_EVALUATION_OPERATOR_ID,
            "operator_version": 1,
            "operation_key": f"evaluate:{output.output_id}:{packet.packet_id}",
            "modality": output.media_type,
            "project_id": self.project_id,
            "input": input_payload,
            "disclosure_refs": [
                packet.disclosure_manifest_id,
                *packet.grounding_assets_sent,
            ],
            "context": {
                "project_purpose": self.project_purpose,
                "field_version_id": version.version_id,
                "projection_id": projection.projection_id,
                "target_id": packet.target_capability_manifest_id,
                "content_is_untrusted": True,
            },
            "configuration": payload.get("configuration", {})
            if isinstance(payload.get("configuration", {}), Mapping)
            else {},
        }
        execution_request["configuration"] = {
            **self._operator_configuration(),
            **execution_request["configuration"],
        }
        try:
            execution = self.operator_executor.execute(execution_request)
            result = CreativeEvaluationWorkflow().run(
                execution=execution,
                output_id=output.output_id,
                request_id=request.request_id,
                field_version_id=version.version_id,
                projection_id=projection.projection_id,
                derivation_id=evaluation_derivation,
                actor_id=str(payload.get("actor_id") or "creative-studio-evaluator"),
                created_at=_utc_now(),
            )
        except Exception as error:  # noqa: BLE001 - normalize evaluation runtime failures.
            self.state["evaluation"] = {
                "status": ArtifactStatus.FAILED.value,
                "evaluation_id": None,
                "output_id": output.output_id,
                "feedback_ids": [],
                "errors": [f"evaluation executor failed: {error}"],
                "receipt": {},
            }
            return self.snapshot()
        if result.evaluation is None:
            self.state["evaluation"] = {
                "status": result.status.value,
                "evaluation_id": None,
                "output_id": output.output_id,
                "feedback_ids": [],
                "errors": list(result.errors),
                "receipt": dict(result.receipt),
            }
            self.state["events"].append(
                {
                    "command": "evaluate_output",
                    "output_id": output.output_id,
                    "status": result.status.value,
                }
            )
            return self.snapshot()
        records = (result.evaluation, *result.feedback)
        try:
            self.repository.append_many(records)
        except Exception as error:  # noqa: BLE001 - preserve canonical-write failure at boundary.
            return {
                "status": ArtifactStatus.FAILED.value,
                "error": f"evaluation persistence failed: {error}",
            }
        self._apply_evaluation_state(result.evaluation, receipt=result.receipt)
        self.state["events"].append(
            {
                "command": "evaluate_output",
                "output_id": output.output_id,
                "evaluation_id": result.evaluation.evaluation_id,
                "status": result.status.value,
            }
        )
        return self.snapshot()

    def _evaluation_output_payload(self, output: CreativeOutput) -> dict[str, Any]:
        payload = output.model_dump(mode="json")
        if not self.blob_store:
            payload["content_available"] = False
            return payload
        try:
            content = self.blob_store.read(output.content_hash)
        except (FileNotFoundError, ValueError):
            payload["content_available"] = False
            return payload
        if len(content) > MAX_EVALUATION_MEDIA_BYTES:
            payload["content_available"] = False
            payload["content_omitted_reason"] = "evaluation media exceeds bounded input size"
            return payload
        payload["content_available"] = True
        payload["content_base64"] = base64.b64encode(content).decode("ascii")
        return payload

    def _operator_configuration(self) -> dict[str, Any]:
        configuration: dict[str, Any] = {}
        if self.operator_contracts:
            configuration["operator_contracts"] = self.operator_contracts
        if self.operator_pack is not None:
            configuration["operator_pack"] = self.operator_pack.model_dump(mode="json")
            configuration["operator_pack_by_operator"] = {
                operator_id: operator_pack_configuration(self.operator_pack, operator_id)
                for operator_id in (
                    OBSERVE_OPERATOR_ID,
                    INTERPRET_OPERATOR_ID,
                    SYNTHESIS_OPERATOR_ID,
                    OUTPUT_EVALUATION_OPERATOR_ID,
                )
            }
        return configuration

    def _apply_evaluation_state(
        self,
        evaluation: CreativeEvaluation,
        *,
        receipt: Mapping[str, Any] | None = None,
    ) -> None:
        feedback_ids = (
            [
                item.feedback_id
                for item in self.repository.list(FeedbackRecord)
                if item.derivation_id == evaluation.derivation_id
            ]
            if self.repository
            else []
        )
        self.state["evaluation"] = {
            "status": evaluation.status.value,
            "evaluation_id": evaluation.evaluation_id,
            "output_id": evaluation.output_id,
            "feedback_ids": feedback_ids,
            "errors": [],
            "receipt": dict(receipt if receipt is not None else evaluation.receipt),
        }

    def _hydrate_latest_evaluation(self) -> None:
        if self.repository is None:
            return
        outputs = {
            item.output_id: item
            for item in self.repository.list(CreativeOutput, project_id=self.project_id)
        }
        candidates = [
            item for item in self.repository.list(CreativeEvaluation) if item.output_id in outputs
        ]
        if candidates:
            self._apply_evaluation_state(max(candidates, key=lambda item: item.evaluation_id))

    @staticmethod
    def _generation_state(packet: GenerationPacket) -> dict[str, Any]:
        return {
            "status": "ready",
            "packet_id": packet.packet_id,
            "target_id": packet.target_capability_manifest_id,
            "invocation_id": None,
            "output_id": None,
            "controls_sent": packet.controls_sent,
            "grounding_assets_sent": list(packet.grounding_assets_sent),
            "capability_limitations": list(packet.capability_limitations),
            "errors": [],
        }

    def _hydrate_latest_generation(self) -> None:
        if self.repository is None:
            return
        candidates: list[GenerationPacket] = []
        for packet in self.repository.list(GenerationPacket):
            projection = self.repository.get(FieldProjection, packet.projection_id)
            if projection is None:
                continue
            resolved = self.repository.get(ResolvedCreativeRequest, projection.request_id)
            if resolved is None:
                continue
            binding = self.repository.get(ProjectBinding, resolved.project_binding_id)
            if binding is not None and binding.project_id == self.project_id:
                candidates.append(packet)
        if candidates:
            packet = max(candidates, key=lambda item: item.packet_id)
            receipt_candidates = [
                item
                for item in self.repository.list(InvocationReceipt)
                if item.packet_id == packet.packet_id
            ]
            if receipt_candidates:
                self._apply_invocation_state(
                    packet,
                    max(receipt_candidates, key=lambda item: item.finished_at),
                )
            else:
                self.state["generation"] = self._generation_state(packet)

    def _reset_demo(self) -> dict[str, Any]:
        next_revision_number = self._revision + 1
        revision = BoardRevision(
            board_revision_id=f"{self.moodboard_id}:revision:{next_revision_number}",
            moodboard_id=self.moodboard_id,
            project_id=self.project_id,
            revision=next_revision_number,
            created_at="studio-now",
            created_by="studio-user",
        )
        if self.repository:
            self.repository.put_board_revision(revision, expected_revision=self._revision)
        self.state["references"] = []
        self.state["clusters"] = []
        self.state["annotations"] = []
        self.state["field"]["status"] = "awaiting_reviewed_synthesis"
        self.state["field"]["proposal_id"] = None
        self.state["field"]["version_id"] = None
        self.state["field"]["principles"] = []
        self.state["field"]["tensions"] = []
        self.state["field"]["exclusions"] = []
        self.state["field"]["dimension_states"] = []
        self.state["field"]["omissions"] = []
        self.state["analysis"] = {
            "status": "not_started",
            "run_id": None,
            "board_revision_id": None,
            "proposal_id": None,
            "stages": [],
            "errors": [],
            "hold_reason": None,
        }
        self.state["projection"] = {
            "status": "not_started",
            "request_id": None,
            "field_version_id": None,
            "projection_id": None,
            "context_packet_id": None,
            "omissions": [],
            "conflicts": [],
            "errors": [],
        }
        self.state["generation"] = {
            "status": "not_started",
            "packet_id": None,
            "target_id": None,
            "invocation_id": None,
            "output_id": None,
            "controls_sent": {},
            "grounding_assets_sent": [],
            "capability_limitations": [],
            "errors": [],
        }
        self.state["evaluation"] = {
            "status": "not_started",
            "evaluation_id": None,
            "output_id": None,
            "feedback_ids": [],
            "errors": [],
            "receipt": {},
        }
        self._revision = next_revision_number
        self.state["revision"] = self._revision
        self.state["events"].append({"command": "reset_demo", "revision": self._revision})
        return self.snapshot()

    def _review_events(self) -> list[dict[str, Any]]:
        return [item for item in self.state["events"] if item.get("command") == "review_field"]

    def _persist(self, record: Any) -> None:
        if self.repository:
            self.repository.append(record)


def create_server(
    *,
    store: StudioStore,
    host: str = "127.0.0.1",
    port: int = 8790,
) -> ThreadingHTTPServer:
    class Handler(BaseHTTPRequestHandler):
        def _json(self, status: HTTPStatus, payload: Mapping[str, Any]) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            if path == "/api/state":
                self._json(HTTPStatus.OK, store.snapshot())
                return
            if path == "/favicon.ico":
                self.send_response(HTTPStatus.NO_CONTENT)
                self.send_header("content-length", "0")
                self.end_headers()
                return
            if path.startswith("/api/blob/"):
                content_hash = path.removeprefix("/api/blob/")
                blob = store.read_blob(content_hash)
                if blob is None:
                    self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})
                    return
                body, media_type = blob
                self.send_response(HTTPStatus.OK)
                self.send_header("content-type", media_type)
                self.send_header("content-length", str(len(body)))
                self.send_header("cache-control", "private, max-age=3600")
                self.end_headers()
                self.wfile.write(body)
                return
            if path.startswith("/api/output/"):
                output_id = path.removeprefix("/api/output/")
                output = store.read_output(output_id)
                if output is None:
                    self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})
                    return
                body, media_type = output
                self.send_response(HTTPStatus.OK)
                self.send_header("content-type", media_type)
                self.send_header("content-length", str(len(body)))
                self.send_header("cache-control", "private, max-age=3600")
                self.end_headers()
                self.wfile.write(body)
                return
            file_name = "index.html" if path == "/" else path.removeprefix("/")
            file_path = (STATIC_ROOT / file_name).resolve()
            if STATIC_ROOT.resolve() not in file_path.parents or not file_path.is_file():
                self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})
                return
            body = file_path.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header(
                "content-type",
                "text/html"
                if file_path.suffix == ".html"
                else "text/css"
                if file_path.suffix == ".css"
                else "text/javascript",
            )
            self.send_header("content-length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self) -> None:  # noqa: N802
            if urlparse(self.path).path != "/api/command":
                self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})
                return
            try:
                try:
                    length = int(self.headers.get("content-length", "0"))
                except (TypeError, ValueError, OverflowError):
                    self._json(
                        HTTPStatus.BAD_REQUEST,
                        {"status": "held", "error": "invalid content length"},
                    )
                    return
                if length < 0 or length > MAX_COMMAND_BODY_BYTES:
                    self._json(
                        HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                        {"status": "held", "error": "command body exceeds the size limit"},
                    )
                    return
                raw_body = self.rfile.read(length)
                if len(raw_body) != length:
                    self._json(
                        HTTPStatus.BAD_REQUEST,
                        {"status": "held", "error": "incomplete request body"},
                    )
                    return
                payload = json.loads(raw_body)
                if not isinstance(payload, dict):
                    raise ValueError("command payload must be an object")
                name = payload["command"]
                args = payload.get("payload", {})
                if not isinstance(name, str) or not isinstance(args, dict):
                    raise ValueError("command and object payload are required")
                result = store.command(name, args)
                self._json(HTTPStatus.OK, result)
            except (ValueError, KeyError, json.JSONDecodeError) as error:
                self._json(HTTPStatus.BAD_REQUEST, {"status": "held", "error": str(error)})
            except Exception as error:  # noqa: BLE001 - normalize command boundary failures.
                self._json(
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    {"status": "failed", "error": str(error)},
                )

        def log_message(self, _format: str, *_args: Any) -> None:
            return

    return ThreadingHTTPServer((host, port), Handler)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="creative-studio")
    parser.add_argument("--project-id", default="project:creative-studio")
    parser.add_argument("--data-root", type=Path, default=None)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8790)
    parser.add_argument(
        "--project-purpose",
        default=os.environ.get(
            "TESTFLIGHT_CREATIVE_PROJECT_PURPOSE",
            "Explore a project-scoped creative direction.",
        ),
    )
    parser.add_argument(
        "--dimensions",
        type=Path,
        default=Path(
            os.environ.get(
                "TESTFLIGHT_CREATIVE_DIMENSIONS",
                "domains/creative-field/dimensions.yaml",
            )
        ),
    )
    parser.add_argument(
        "--operator-endpoint",
        default=os.environ.get("TESTFLIGHT_OPERATOR_ENDPOINT"),
        help="Local operator-runtime /execute endpoint; omit to disable analysis.",
    )
    parser.add_argument(
        "--operator-workspace-id",
        default=os.environ.get(
            "TESTFLIGHT_OPERATOR_WORKSPACE_ID", "world://workspace/creative-studio"
        ),
    )
    parser.add_argument(
        "--operator-pack",
        type=Path,
        default=(
            Path(os.environ["TESTFLIGHT_CREATIVE_OPERATOR_PACK"])
            if os.environ.get("TESTFLIGHT_CREATIVE_OPERATOR_PACK")
            else None
        ),
        help="Versioned client operator-pack YAML; it only configures general operators.",
    )
    parser.add_argument(
        "--operator-index",
        type=Path,
        default=Path(
            os.environ.get("TESTFLIGHT_CREATIVE_OPERATOR_INDEX", "reasoning/operators/index.yaml")
        ),
        help="Canonical reasoning operator catalog used to load semantic YAML contracts.",
    )
    parser.add_argument(
        "--world-model",
        type=Path,
        default=(
            Path(os.environ["TESTFLIGHT_CREATIVE_WORLD_MODEL"])
            if os.environ.get("TESTFLIGHT_CREATIVE_WORLD_MODEL")
            else None
        ),
        help="Canonical Brand world-model YAML used by the bounded world-view resolver.",
    )
    parser.add_argument(
        "--authority-grant-id",
        default=os.environ.get("TESTFLIGHT_CREATIVE_AUTHORITY_GRANT_ID"),
        help="Authority required to promote a proposal into a field version.",
    )
    args = parser.parse_args(argv)
    data_root = (
        args.data_root
        or Path(os.environ.get("TESTFLIGHT_DATA_ROOT", ".data"))
        / "creative-field"
        / args.project_id
    )
    repository = CreativeRepository(data_root / "events.sqlite3")
    blob_store = ContentAddressedBlobStore(data_root)
    operator_executor: OperatorExecutor | None = None
    dimensions: tuple[FieldDimension, ...] = ()
    operator_pack = None
    world_view_resolver = None
    if args.operator_pack:
        operator_pack = load_operator_pack(
            args.operator_pack,
            expected_workspace_id=args.operator_workspace_id,
        )
    if args.world_model:
        world_view_resolver = create_world_view_resolver(args.world_model)
    if args.operator_endpoint:
        operator_executor = HttpOperatorExecutor(
            endpoint=args.operator_endpoint,
            workspace_id=args.operator_workspace_id,
        )
        dimensions = load_dimension_registry(args.dimensions)
    server = create_server(
        store=StudioStore(
            project_id=args.project_id,
            repository=repository,
            blob_store=blob_store,
            operator_executor=operator_executor,
            dimensions=dimensions,
            project_purpose=args.project_purpose,
            authority_grant_id=args.authority_grant_id,
            operator_pack=operator_pack,
            operator_index_path=args.operator_index if args.operator_endpoint else None,
            world_view_resolver=world_view_resolver,
        ),
        host=args.host,
        port=args.port,
    )
    print(f"Creative Studio listening on http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    finally:
        server.server_close()
        repository.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
