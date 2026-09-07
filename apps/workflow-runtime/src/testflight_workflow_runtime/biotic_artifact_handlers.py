"""Local, proposal-only artifact handlers for the Biotic workflow vertical slice.

These handlers deliberately read tracked public-workspace artifacts and write only to the
configured local runtime root. They neither call an image provider nor publish externally.
"""

from __future__ import annotations

import html
import json
import os
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from testflight_adapter_sqlite_semantic import ContentAddressedBlobStore, CreativeRepository
from testflight_creative_field import ArtifactBundle, ArtifactStatus, CreativeOutput
from testflight_workflows import HandlerRegistry, ResultStatus, StepExecutionContext, StepResult

WORKSPACE_ID = "world://workspace/brand/hellobiotic-research"
PERSIST_ACTION = "action://testflight/creative/local-artifact-persist"
PROJECT_ID = "project:biotic:public-research-social"
FIELD_VERSION_ID = "field:biotic:public-research@fixture-1"


def _project_root() -> Path:
    configured = os.environ.get("TESTFLIGHT_PROJECT_ROOT")
    return Path(configured).resolve() if configured else Path.cwd().resolve()


def _runtime_root() -> Path:
    configured = os.environ.get("TESTFLIGHT_BIOTIC_ARTIFACT_ROOT")
    if configured:
        return Path(configured).resolve()
    return _project_root() / ".data" / "biotic-artifacts"


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _svg(card_number: int, headline: str, body: str) -> str:
    """Render a deterministic image fixture, not an imitation of Biotic brand artwork."""

    safe_headline = html.escape(headline)
    safe_body = html.escape(body)
    lines = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1350"',
        ' viewBox="0 0 1080 1350">',
        '  <rect width="1080" height="1350" fill="#f3e7d3"/>',
        '  <circle cx="910" cy="210" r="170" fill="#d0dfc3"/>',
        '  <rect x="90" y="90" width="900" height="1170" rx="44"',
        '        fill="#fffaf1" stroke="#344638" stroke-width="6"/>',
        '  <text x="150" y="220" font-family="Arial, sans-serif" font-size="34"',
        f'        fill="#344638">PUBLIC-RESEARCH CONCEPT · {card_number}/5</text>',
        '  <text x="150" y="480" font-family="Arial, sans-serif" font-size="88"',
        f'        font-weight="700" fill="#203426">{safe_headline}</text>',
        '  <text x="150" y="650" font-family="Arial, sans-serif" font-size="42"',
        f'        fill="#344638">{safe_body}</text>',
        '  <text x="150" y="1160" font-family="Arial, sans-serif" font-size="30"',
        '        fill="#344638">Human review required before any use.</text>',
        "</svg>",
    )
    return "\n".join(lines)


class PublicBioticContextCompiler:
    async def execute(self, context: StepExecutionContext) -> StepResult:
        if WORKSPACE_ID not in context.step.access.workspace_ids:
            raise PermissionError("Biotic context step did not declare its workspace")
        if "knowledge.retrieve" not in context.step.capabilities:
            raise PermissionError("Biotic context step lacks retrieval capability")
        workspace_path = _project_root() / "workspaces" / "brand-hellobiotic-research"
        asset_context = workspace_path / "artifacts" / "asset-workflow-context.yaml"
        workspace_contract = workspace_path / "WORKSPACE.yaml"
        if not asset_context.exists() or not workspace_contract.exists():
            return StepResult(
                status=ResultStatus.HOLD,
                output={"reason": "missing_workspace_contract"},
                receipt={"workspace_id": WORKSPACE_ID, "status": "hold"},
            )
        recipe = yaml.safe_load(asset_context.read_text(encoding="utf-8"))
        workspace = yaml.safe_load(workspace_contract.read_text(encoding="utf-8"))
        return StepResult(
            status=ResultStatus.SUCCESS,
            output={
                "packet_id": f"packet:{context.run_id}:biotic-public",
                "workspace_id": WORKSPACE_ID,
                "brand_id": workspace["workspace"]["brand_id"],
                "objective": context.arguments["objective"],
                "audience": context.arguments["audience"],
                "channel": context.arguments["channel"],
                "scope": "public research only; proposal-only output",
                "required_entities": recipe["stage_recipes"][1]["always_include"]["entity_ids"],
                "limitations": [
                    (
                        "Visual, copy/claims, and audience overlays are public observations, "
                        "not owner-approved brand rules."
                    ),
                    (
                        "No medical efficacy, validated customer behavior, internal approval, "
                        "or causal effectiveness is inferred."
                    ),
                    (
                        "This local renderer uses no source imagery and does not assert a "
                        "production brand visual system."
                    ),
                ],
            },
            receipt={
                "workspace_id": WORKSPACE_ID,
                "sources": [str(asset_context), str(workspace_contract)],
                "operator_ids": ["creative/project-binding@1", "creative/field-projection@1"],
                "status": "success",
            },
        )


class SocialCarouselComposer:
    async def execute(self, context: StepExecutionContext) -> StepResult:
        source = context.arguments["context"]
        if source.get("workspace_id") != WORKSPACE_ID:
            return StepResult(
                status=ResultStatus.HOLD,
                output={"reason": "context_scope_mismatch"},
                receipt={"status": "hold"},
            )
        cards = (
            ("Feed your skin's ecosystem.", "A public-research concept for your daily ritual."),
            ("Your underarms are skin, too.", "A gentle prompt to treat the everyday with care."),
            (
                "A little reset, every day.",
                "A concept about consistency rather than a performance claim.",
            ),
            (
                "Made for the places that work hard.",
                "A human-scale expression, pending brand-owner review.",
            ),
            ("Hello, Biotic.", "Explore the daily ritual — concept copy only."),
        )
        return StepResult(
            status=ResultStatus.SUCCESS,
            output={
                "request_id": context.arguments["request_id"],
                "project_id": PROJECT_ID,
                "artifact_kind": "social-carousel",
                "context_packet_id": source["packet_id"],
                "copy": {
                    "objective": context.arguments["objective"],
                    "audience": context.arguments["audience"],
                    "channel": context.arguments["channel"],
                    "status": "public_research_concept_pending_human_review",
                    "cards": [
                        {"position": index, "headline": headline, "body": body}
                        for index, (headline, body) in enumerate(cards, start=1)
                    ],
                },
                "cards": [
                    {"position": index, "svg": _svg(index, headline, body)}
                    for index, (headline, body) in enumerate(cards, start=1)
                ],
                "limitations": source["limitations"],
            },
            receipt={
                "operator_ids": ["creative/connector-packet@1"],
                "image_mode": "deterministic_local_svg_fixture",
                "status": "success",
            },
        )


class LocalArtifactBundlePersister:
    async def execute(self, context: StepExecutionContext) -> StepResult:
        if not context.authority.proposal_write or not context.authority.external_action:
            raise PermissionError("workflow lacks local artifact persistence authority")
        if PERSIST_ACTION not in context.authority.action_ids:
            raise PermissionError("workflow lacks declared local artifact action")
        carousel = context.arguments["carousel"]
        root = _runtime_root()
        root.mkdir(parents=True, exist_ok=True)
        now = _now()
        invocation_id = f"invocation:{context.run_id}:local-render"
        derivation_id = f"derivation:{context.run_id}:biotic-carousel"
        outputs: list[CreativeOutput] = []
        with CreativeRepository(root / "creative.sqlite3") as repository:
            blobs = ContentAddressedBlobStore(root)
            copy_blob = blobs.put(
                (json.dumps(carousel["copy"], indent=2, sort_keys=True) + "\n").encode(),
                media_type="application/json",
            )
            copy_output = CreativeOutput(
                output_id=f"output:{context.run_id}:copy",
                invocation_id=invocation_id,
                packet_id=carousel["context_packet_id"],
                project_id=carousel["project_id"],
                request_id=carousel["request_id"],
                media_type=copy_blob.media_type,
                content_hash=copy_blob.content_hash,
                source_uri=copy_blob.uri,
                content_size=copy_blob.size,
                adapter_version="local-svg-renderer@1",
                status=ArtifactStatus.SUCCESS,
                derivation_id=derivation_id,
            )
            outputs.append(copy_output)
            for card in carousel["cards"]:
                blob = blobs.put(card["svg"].encode(), media_type="image/svg+xml")
                outputs.append(
                    CreativeOutput(
                        output_id=f"output:{context.run_id}:card-{card['position']}",
                        invocation_id=invocation_id,
                        packet_id=carousel["context_packet_id"],
                        project_id=carousel["project_id"],
                        request_id=carousel["request_id"],
                        media_type=blob.media_type,
                        content_hash=blob.content_hash,
                        source_uri=blob.uri,
                        content_size=blob.size,
                        adapter_version="local-svg-renderer@1",
                        status=ArtifactStatus.SUCCESS,
                        derivation_id=derivation_id,
                    )
                )
            bundle = ArtifactBundle(
                bundle_id=f"bundle:{context.run_id}",
                project_id=carousel["project_id"],
                request_id=carousel["request_id"],
                artifact_kind=carousel["artifact_kind"],
                revision=1,
                output_ids=tuple(item.output_id for item in outputs),
                field_version_id=FIELD_VERSION_ID,
                context_packet_id=carousel["context_packet_id"],
                authority_grant_id=f"grant:{context.run_id}",
                limitations=tuple(carousel["limitations"]),
                derivation_id=derivation_id,
            )
            repository.append_many([*outputs, bundle])
        return StepResult(
            status=ResultStatus.SUCCESS,
            output={
                "bundle_id": bundle.bundle_id,
                "project_id": bundle.project_id,
                "status": bundle.lifecycle_status.value,
                "review_required": True,
                "outputs": [item.model_dump(mode="json") for item in outputs],
                "limitations": list(bundle.limitations),
                "local_runtime_root": str(root),
            },
            receipt={
                "action_id": PERSIST_ACTION,
                "operator_ids": [
                    "guardrail/retry-idempotency@1",
                    "guardrail/workspace-isolation@1",
                ],
                "persisted_record_types": ["CreativeOutput", "ArtifactBundle"],
                "created_at": now,
            },
        )


def register_workflow_handlers(
    registry: HandlerRegistry, configuration: Mapping[str, Any] | None = None
) -> None:
    del configuration
    registry.register("biotic.compile_public_context", PublicBioticContextCompiler())
    registry.register("biotic.compose_social_carousel", SocialCarouselComposer())
    registry.register("biotic.persist_local_artifact_bundle", LocalArtifactBundlePersister())


__all__ = ["register_workflow_handlers"]
