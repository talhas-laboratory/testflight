#!/usr/bin/env python3
"""Certify the Creative Field source-to-artifact vertical slice without provider credentials."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from testflight_adapter_cognee.creative_field_projection import (
    build_creative_field_projection,
    compare_projection_drift,
    read_projection_manifest,
    write_projection_manifest,
)
from testflight_adapter_creative_connectors import (
    TEXT_TARGET_MANIFEST,
    TextTargetAdapter,
    compile_generation_packet,
)
from testflight_adapter_sqlite_semantic import CreativeRepository
from testflight_creative_field import (
    ArtifactStatus,
    BoardRevision,
    CreativeBindingResolver,
    CreativeContextCompiler,
    CreativeEvaluationWorkflow,
    CreativeFieldLifecycle,
    CreativeFieldVersion,
    CreativeProject,
    CreativeRequest,
    FieldBinding,
    FieldDimension,
    LifecycleStatus,
    Moodboard,
    OperatorExecution,
    Placement,
    ProjectBinding,
    ReferenceAsset,
    ReferenceInterpretationWorkflow,
    ReferenceObservationWorkflow,
    ReviewAction,
    ReviewDecision,
    SourceLicenseRecord,
    UserAnnotation,
)


class ScenarioExecutor:
    """Provider-neutral fixture executor; content remains untrusted to every workflow."""

    def execute(self, request: dict[str, Any]) -> OperatorExecution:
        operator_id = request["operator_id"]
        if operator_id.endswith("observation-extraction"):
            output = {
                "observed_features": [
                    {
                        "feature_id": "feature:softness",
                        "observation_id": "observation:one",
                        "dimension_id": "material",
                        "label": "controlled softness",
                        "value": "softness held inside precise form",
                        "bounded_anchors": ["asset:one#region:1"],
                    }
                ]
            }
        elif operator_id.endswith("reference-interpretation"):
            output = {
                "proposed_role": "carry tactility without copying the object",
                "authority": "operator-proposal",
                "evidence_refs": ["asset:one#region:1"],
                "carry_forward": ["softness", "restraint"],
                "anti_transfer": ["literal object silhouette"],
                "dimension_contributions": [
                    {
                        "contribution_id": "contribution:softness",
                        "dimension_id": "material",
                        "role": "tactility",
                        "transfer_instruction": "preserve softness as a material cue",
                        "anti_transfer_instruction": "do not reproduce the reference object",
                        "polarity": "carry",
                        "weight": 0.9,
                        "evidence_refs": ["asset:one#region:1"],
                    }
                ],
                "alternatives": [
                    {
                        "proposition": "softness may be atmospheric rather than material",
                        "rationale": "the reference is ambiguous",
                        "evidence_refs": ["asset:one#region:1"],
                    }
                ],
            }
        elif operator_id.endswith("field-synthesis"):
            output = {
                "source_contribution_ids": ["contribution:softness"],
                "principles": [
                    {
                        "principle_id": "principle:precise-soft",
                        "statement": "Use precise form with soft tactility.",
                        "dimension_ids": ["material"],
                        "source_contribution_ids": ["contribution:softness"],
                    }
                ],
                "tensions": [
                    {
                        "tension_id": "tension:precise-soft",
                        "statement": "Precision should hold softness, not erase it.",
                        "poles": ["precise", "soft"],
                        "source_contribution_ids": ["contribution:softness"],
                    }
                ],
                "exclusions": [
                    {
                        "exclusion_id": "exclusion:literal-copy",
                        "statement": "Do not reproduce the reference object.",
                        "category": "literal-copy",
                        "source_contribution_ids": ["contribution:softness"],
                    }
                ],
                "dimension_states": [
                    {
                        "dimension_id": "material",
                        "summary": "soft but controlled",
                        "values": {"intensity": "moderate"},
                        "source_contribution_ids": ["contribution:softness"],
                    }
                ],
            }
        else:
            output = {}
        return OperatorExecution(
            status="proposal",
            output=output,
            receipt={"operator_id": operator_id, "provider": "certification-fixture"},
        )


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def certify() -> dict[str, Any]:
    project_id = "project:creative-certification"
    workspace_id = "world://workspace/creative-certification"
    child_workspace_id = f"{workspace_id}/creative-field"
    now = "2026-09-03T00:00:00Z"
    asset = ReferenceAsset(
        asset_id="asset:one",
        project_id=project_id,
        source_id="upload:one",
        media_type="image/jpeg",
        label="client reference",
        content_hash="sha256:reference-one",
        source_uri="blob://sha256/reference-one",
        license_record_id="license:one",
        recorded_at=now,
    )
    license_record = SourceLicenseRecord(
        license_record_id="license:one",
        source_id=asset.source_id,
        permitted_use=("analysis", "reference"),
        disclosure_allowed=False,
        generation_allowed=False,
        retention_policy="project-lifetime",
        limitations=("reference-only",),
    )
    project = CreativeProject(
        project_id=project_id,
        workspace_id=workspace_id,
        context_id="context:one",
        name="Certification project",
        purpose="test the source-to-artifact path",
        privacy_policy_id="privacy:project",
        status=LifecycleStatus.ACTIVE,
    )
    moodboard = Moodboard(
        moodboard_id="moodboard:one",
        project_id=project_id,
        name="Certification board",
        purpose="bounded visual reference",
        privacy_classification="client-confidential",
    )
    board = BoardRevision(
        board_revision_id="board:one@1",
        moodboard_id=moodboard.moodboard_id,
        project_id=project_id,
        revision=1,
        reference_asset_ids=(asset.asset_id,),
        placements=(
            Placement(
                placement_id="placement:one",
                asset_id=asset.asset_id,
                x=0,
                y=0,
                width=100,
                height=100,
            ),
        ),
        created_at=now,
        created_by="actor:client",
        source_ids=(asset.source_id,),
    )
    annotation = UserAnnotation(
        annotation_id="annotation:one",
        project_id=project_id,
        target_id=asset.asset_id,
        text="Keep the softness, not the object.",
        desired_transfer="softness",
        anti_association="literal copy",
        actor_id="actor:client",
        created_at=now,
    )
    dimension = FieldDimension(
        dimension_id="material",
        label="Material",
        definition="tactility and surface behavior",
    )
    executor = ScenarioExecutor()
    observed = ReferenceObservationWorkflow().run(
        asset=asset,
        board=board,
        annotations=(annotation,),
        license_record=license_record,
        dimensions=(dimension,),
        project_purpose=project.purpose,
        derivation_id="derivation:observation",
        executor=executor,
    )
    _assert(observed.status is ArtifactStatus.SUCCESS, "observation did not succeed")
    interpretation = ReferenceInterpretationWorkflow().run(
        asset=asset,
        observations=observed.records,
        annotations=(annotation,),
        project_purpose=project.purpose,
        derivation_id="derivation:interpretation",
        executor=executor,
    )
    _assert(interpretation.status is ArtifactStatus.SUCCESS, "interpretation did not succeed")
    interpretation_record = interpretation.records[0]
    contributions = tuple(interpretation.records[1:])
    synthesis = CreativeFieldLifecycle().synthesize(
        project_id=project_id,
        field_id="field:one",
        interpretations=(interpretation_record,),
        contributions=contributions,
        dimensions=(dimension,),
        project_purpose=project.purpose,
        derivation_id="derivation:synthesis",
        executor=executor,
    )
    _assert(
        synthesis.status is ArtifactStatus.SUCCESS and synthesis.proposal is not None,
        "synthesis did not succeed",
    )
    decision = ReviewDecision(
        review_id="review:one",
        target_id=synthesis.proposal.proposal_id,
        action=ReviewAction.ACCEPT,
        actor_id="actor:creative-director",
        rationale="approved for bounded artifact generation",
        created_at=now,
        authority_grant_id="grant:creative-director",
    )
    version_result = CreativeFieldLifecycle().review_and_version(
        proposal=synthesis.proposal,
        decision=decision,
        version_id="field:one@1",
        reviewed_at=now,
    )
    _assert(
        version_result.status is ArtifactStatus.SUCCESS and version_result.version is not None,
        "version was not accepted",
    )
    version: CreativeFieldVersion = version_result.version
    project_binding = ProjectBinding(
        binding_id="project-binding:one",
        project_id=project_id,
        workspace_id=workspace_id,
        context_id="context:one",
        target_entity_ids=("entity:brand",),
        branch_id="branch:main",
        privacy_policy_id="privacy:project",
        authority_grant_id="grant:creative-director",
    )
    field_binding = FieldBinding(
        binding_id="field-binding:one",
        project_id=project_id,
        field_version_id=version.version_id,
        target_entity_ids=("entity:brand",),
        context_id="context:one",
        artifact_type_selectors=("brief",),
        authority_grant_id="grant:creative-director",
    )
    binding = CreativeBindingResolver().resolve_field(
        project_binding=project_binding,
        field_binding=field_binding,
        field_version=version,
        entities=[{"entity_id": "entity:brand", "workspace_id": workspace_id}],
        artifact_type="brief",
    )
    _assert(binding.status is ArtifactStatus.SUCCESS, "binding did not resolve")
    request = CreativeRequest(
        request_id="request:one",
        project_id=project_id,
        task_type="create",
        artifact_type="brief",
        modality="text",
        target=TEXT_TARGET_MANIFEST.target_id,
        permission_context={"disclosure_manifest_id": "disclosure:one"},
    )
    compiler = CreativeContextCompiler()
    resolved = compiler.resolve_request(
        request=request,
        project_binding_id=project_binding.binding_id,
        field_binding=field_binding,
        field_version=version,
        world_view_request_id="world-view-request:one",
        target_capability_manifest_id=TEXT_TARGET_MANIFEST.target_id,
        lens="brief",
    )
    _assert(resolved.resolved_request is not None, "request did not resolve")
    compiled = compiler.compile(
        resolved_request=resolved.resolved_request,
        request=request,
        field_version=version,
        field_binding=field_binding,
        world_view={
            "view_id": "world-view:one",
            "status": "hit",
            "selected_record_ids": ["entity:brand"],
            "citations": ["world-evidence:one"],
        },
        target_manifest=TEXT_TARGET_MANIFEST,
        disclosure_manifest_id="disclosure:one",
    )
    _assert(
        compiled.projection is not None and compiled.packet is not None,
        "context packet failed",
    )
    generation = compile_generation_packet(
        compiled.projection,
        TEXT_TARGET_MANIFEST,
        disclosure_manifest_id="disclosure:one",
    )
    connector = TextTargetAdapter(lambda _packet: "A precise brief with soft tactility.")
    output = connector.invoke(generation, invocation_id="invocation:one")
    _assert(output.output is not None, "connector did not return output")
    evaluation = CreativeEvaluationWorkflow().run(
        execution=OperatorExecution(
            status="proposal",
            output={
                "field_fidelity": {"material": "strong"},
                "exclusion_findings": [],
                "task_fitness": {"artifact": "fit"},
                "execution_quality": {"clarity": "good"},
                "feedback": [
                    {
                        "category": "tension",
                        "instruction": "Keep the precise/soft tension visible in the next brief.",
                    }
                ],
            },
            receipt={"operator_id": "world://operator/creative/output-evaluation"},
        ),
        output_id=output.output.output_id,
        request_id=request.request_id,
        field_version_id=version.version_id,
        projection_id=compiled.projection.projection_id,
        derivation_id="derivation:evaluation",
        actor_id="actor:reviewer",
        created_at=now,
    )
    _assert(
        evaluation.status is ArtifactStatus.SUCCESS and evaluation.evaluation is not None,
        "evaluation failed",
    )
    records = [
        project,
        moodboard,
        license_record,
        asset,
        board,
        annotation,
        dimension,
        *observed.records,
        *interpretation.records,
        synthesis.proposal,
        decision,
        version,
        project_binding,
        field_binding,
        request,
        resolved.resolved_request,
        compiled.projection,
        compiled.packet,
        generation,
        evaluation.evaluation,
        *evaluation.feedback,
    ]
    with TemporaryDirectory(prefix="testflight-creative-certification-") as temp_dir:
        repository_path = Path(temp_dir) / "creative.sqlite3"
        with CreativeRepository(repository_path) as repository:
            repository.put_board_revision(board)
            repository.append_many(record for record in records if record is not board)
            replay = repository.replay_board(moodboard.moodboard_id)
            _assert(replay == [board], "board replay is not reconstructable")
        manifest = build_creative_field_projection(
            records,
            child_workspace_id=child_workspace_id,
            parent_workspace_id=workspace_id,
            project_id=project_id,
            dataset_name="testflight_creative_field_certification_staging",
        )
        manifest_path = Path(temp_dir) / "projection-manifest.json"
        write_projection_manifest(manifest, manifest_path)
        drift = compare_projection_drift(manifest, read_projection_manifest(manifest_path))
        _assert(drift["status"] == "up_to_date", "projection rebuild is not idempotent")
        _assert(manifest.documents and manifest.custom_edges, "projection is empty")
        try:
            build_creative_field_projection(
                [
                    ReferenceAsset(
                        asset_id="asset:foreign",
                        project_id="project:foreign",
                        source_id="upload:foreign",
                        media_type="image/jpeg",
                        label="foreign",
                        content_hash="sha256:foreign",
                        source_uri="blob://foreign",
                        recorded_at=now,
                    )
                ],
                child_workspace_id=child_workspace_id,
                parent_workspace_id=workspace_id,
                project_id=project_id,
                dataset_name="testflight_creative_field_certification_staging",
            )
        except ValueError:
            isolation_probe = "passed"
        else:
            isolation_probe = "failed"
        _assert(isolation_probe == "passed", "cross-project projection was not rejected")

    return {
        "status": "passed",
        "project_id": project_id,
        "trace": {
            "board_revision_id": board.board_revision_id,
            "asset_id": asset.asset_id,
            "observation_ids": [record.observation_id for record in observed.records],
            "interpretation_id": interpretation_record.interpretation_id,
            "field_version_id": version.version_id,
            "binding_id": field_binding.binding_id,
            "context_packet_id": compiled.packet.packet_id,
            "generation_packet_id": generation.packet_id,
            "output_id": output.output.output_id,
            "evaluation_id": evaluation.evaluation.evaluation_id,
            "feedback_ids": [record.feedback_id for record in evaluation.feedback],
        },
        "projection": {
            "child_workspace_id": child_workspace_id,
            "dataset_name": "testflight_creative_field_certification_staging",
            "document_count": len(manifest.documents),
            "edge_count": len(manifest.custom_edges),
            "source_hash": manifest.source_hash,
            "idempotency": drift["status"],
            "cross_project_isolation": isolation_probe,
        },
        "live_provider_calls": False,
        "canonical_mutation": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = certify()
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
