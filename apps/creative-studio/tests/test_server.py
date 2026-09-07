import base64
import hashlib
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from http.client import HTTPConnection
from pathlib import Path

from testflight_adapter_creative_connectors import ImageTargetAdapter
from testflight_adapter_sqlite_semantic import ContentAddressedBlobStore, CreativeRepository
from testflight_creative_field import (
    CreativeContextPacket,
    CreativeEvaluation,
    CreativeFieldProposal,
    CreativeFieldVersion,
    CreativeOutput,
    FeedbackRecord,
    FieldBinding,
    FieldDimension,
    FieldProjection,
    GenerationPacket,
    InvocationReceipt,
    OperatorExecution,
    OperatorPack,
    OperatorPackEntry,
    ProjectBinding,
    ReferenceAsset,
    ReviewDecision,
    SourceLicenseRecord,
)
from testflight_creative_studio import StudioStore, create_server, create_world_view_resolver
from testflight_creative_studio.server import MAX_COMMAND_BODY_BYTES


def _running_server(store: StudioStore):
    server = create_server(store=store, port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def _request(server, method: str, path: str, payload: dict | None = None):
    connection = HTTPConnection("127.0.0.1", server.server_port, timeout=5)
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {} if body is None else {"content-type": "application/json"}
    connection.request(method, path, body=body, headers=headers)
    response = connection.getresponse()
    content = response.read()
    status = response.status
    response_headers = dict(response.getheaders())
    connection.close()
    return status, response_headers, content


def _command(server, name: str, payload: dict) -> tuple[int, dict]:
    status, _headers, body = _request(
        server,
        "POST",
        "/api/command",
        {"command": name, "payload": payload},
    )
    return status, json.loads(body)


def _stop_server(server, thread) -> None:
    server.shutdown()
    thread.join(timeout=5)
    server.server_close()


def test_artifact_bridge_ui_exposes_scoped_handoff_controls() -> None:
    server, thread = _running_server(StudioStore(project_id="project:ui"))
    try:
        status, headers, body = _request(server, "GET", "/")
        page = body.decode("utf-8")
        assert status == 200
        assert headers["content-type"] == "text/html"
        assert "Compile context" in page
        assert "Prepare packet" in page
        assert "Evaluate output" in page
    finally:
        _stop_server(server, thread)


def test_static_page_uses_relative_assets_for_file_preview() -> None:
    server, thread = _running_server(StudioStore(project_id="project:static-preview"))
    try:
        status, _headers, body = _request(server, "GET", "/")
        page = body.decode("utf-8")
        assert status == 200
        assert 'href="styles.css"' in page
        assert 'src="app.js"' in page

        status, _headers, body = _request(server, "GET", "/app.js")
        script = body.decode("utf-8")
        assert status == 200
        assert "window.location.protocol === 'file:'" in script
        assert "Preview only" in script
    finally:
        _stop_server(server, thread)


class AnalysisExecutor:
    """Small provider-neutral fake for the Creative Studio analysis command."""

    def __init__(self) -> None:
        self.requests: list[dict] = []

    def execute(self, request: dict) -> OperatorExecution:
        self.requests.append(request)
        operator_id = request["operator_id"]
        receipt = {"operation_key": request["operation_key"], "provider": "fake"}
        if operator_id.endswith("observation-extraction"):
            asset_id = request["input"]["asset"]["asset_id"]
            return OperatorExecution(
                status="proposal",
                output={
                    "observed_features": [
                        {
                            "label": "controlled softness",
                            "dimension_id": "material",
                            "value": "softness held inside precise form",
                            "bounded_anchors": [f"{asset_id}#region:1"],
                        }
                    ]
                },
                receipt=receipt,
            )
        if operator_id.endswith("reference-interpretation"):
            asset_id = request["input"]["asset_id"]
            return OperatorExecution(
                status="proposal",
                output={
                    "proposed_role": "carry tactility, not the object",
                    "authority": "operator-proposal",
                    "evidence_refs": [f"{asset_id}#region:1"],
                    "dimension_contributions": [
                        {
                            "dimension_id": "material",
                            "role": "tactility",
                            "transfer_instruction": "preserve softness as a material cue",
                            "anti_transfer_instruction": "do not reproduce the reference object",
                            "polarity": "carry",
                            "weight": 0.9,
                            "evidence_refs": [f"{asset_id}#region:1"],
                        }
                    ],
                },
                receipt=receipt,
            )
        if operator_id.endswith("field-synthesis"):
            return OperatorExecution(
                status="proposal",
                output={
                    "principles": [
                        {
                            "statement": "Use precise form with soft tactility.",
                            "dimension_ids": ["material"],
                        }
                    ],
                    "tensions": [],
                    "exclusions": [
                        {
                            "statement": "Do not reproduce the reference object.",
                            "category": "literal-copy",
                        }
                    ],
                    "dimension_states": [
                        {
                            "dimension_id": "material",
                            "summary": "soft but controlled",
                            "values": {"intensity": "moderate"},
                        }
                    ],
                },
                receipt=receipt,
            )
        if operator_id.endswith("output-evaluation"):
            output_id = request["input"]["output"]["output_id"]
            return OperatorExecution(
                status="proposal",
                output={
                    "evaluation_id": f"evaluation:{output_id}",
                    "field_fidelity": {"material": {"status": "aligned"}},
                    "exclusion_findings": [],
                    "task_fitness": {"hero-image": {"status": "fit"}},
                    "execution_quality": {"technical": {"status": "usable"}},
                    "target_limitations": [],
                    "disagreements": ["reviewer:one and reviewer:two differ on warmth"],
                    "feedback": [
                        {
                            "target_id": output_id,
                            "category": "field-fidelity",
                            "instruction": "Preserve controlled softness in the next iteration.",
                            "proposed_change": {"dimension_id": "material"},
                        }
                    ],
                },
                receipt=receipt,
            )
        raise AssertionError(f"unexpected operator: {operator_id}")


def test_studio_commands_are_the_only_write_surface_and_keep_project_scope() -> None:
    store = StudioStore(project_id="project:client-a")
    state = store.command(
        "add_reference",
        {
            "asset_id": "asset:one",
            "source_id": "upload:one",
            "content_hash": "a" * 64,
            "source_uri": "local-upload://reference.png",
            "media_type": "image/png",
            "label": "reference.png",
        },
    )
    assert state["references"][0]["project_id"] == "project:client-a"
    assert state["events"][-1]["command"] == "add_reference"

    annotated = store.command(
        "annotate_reference",
        {"target_id": "asset:one", "text": "Keep the rhythm, not the literal object."},
    )
    assert annotated["annotations"][0]["project_id"] == "project:client-a"
    assert annotated["events"][-1]["command"] == "annotate_reference"


def test_studio_rejects_invalid_commands_without_mutating_state() -> None:
    store = StudioStore(project_id="project:client-a")
    before = store.snapshot()
    result = store.command("annotate_reference", {"target_id": "missing", "text": "x"})
    assert result["status"] == "held"
    assert store.snapshot() == before


def test_spatial_layout_persists_clusters_and_replays_without_semantic_inference(tmp_path) -> None:
    with CreativeRepository(tmp_path / "events.sqlite3") as repository:
        store = StudioStore(project_id="project:spatial", repository=repository)
        for asset_id in ("asset:one", "asset:two"):
            store.command(
                "add_reference",
                {
                    "asset_id": asset_id,
                    "source_id": f"upload:{asset_id}",
                    "content_hash": "a" * 64,
                    "source_uri": f"local-upload://{asset_id}.png",
                    "media_type": "image/png",
                    "label": f"{asset_id}.png",
                },
            )
        result = store.command(
            "update_board_layout",
            {
                "placements": [
                    {
                        "asset_id": "asset:one",
                        "x": 120,
                        "y": 80,
                        "width": 236,
                        "height": 178,
                        "z_index": 2,
                        "cluster_key": "material",
                    },
                    {
                        "asset_id": "asset:two",
                        "x": 420,
                        "y": 300,
                        "width": 236,
                        "height": 178,
                        "z_index": 3,
                        "cluster_key": None,
                    },
                ],
                "clusters": [{"key": "material", "label": "Material energy"}],
            },
        )
        assert result["revision"] == 3
        assert result["clusters"][0]["label"] == "Material energy"
        assert result["references"][0]["placement"]["x"] == 120
        assert (
            result["references"][0]["placement"]["cluster_id"]
            == result["clusters"][0]["cluster_id"]
        )
        assert result["references"][1]["placement"]["cluster_id"] is None

        replayed = StudioStore(project_id="project:spatial", repository=repository).snapshot()
        assert replayed["revision"] == 3
        assert replayed["clusters"] == result["clusters"]
        assert replayed["references"][0]["placement"]["x"] == 120
        assert replayed["events"][-1]["command"] == "update_board_layout"


def test_spatial_layout_rejects_partial_or_unknown_cluster_assignments() -> None:
    store = StudioStore(project_id="project:spatial")
    store.command(
        "add_reference",
        {
            "asset_id": "asset:one",
            "source_id": "upload:one",
            "content_hash": "a" * 64,
            "source_uri": "local-upload://one.png",
            "media_type": "image/png",
            "label": "one.png",
        },
    )
    before = store.snapshot()
    result = store.command("update_board_layout", {"placements": [], "clusters": []})
    assert result["status"] == "held"
    assert store.snapshot() == before


def test_studio_can_review_field_state_without_exposing_storage() -> None:
    store = StudioStore(project_id="project:client-a")
    result = store.command("review_field", {"action": "accept"})
    assert result["field"]["status"] == "accepted"
    assert result["events"][-1] == {"command": "review_field", "action": "accept"}


def test_analysis_command_runs_coordinator_and_persists_reviewable_proposal(tmp_path) -> None:
    with CreativeRepository(tmp_path / "events.sqlite3") as repository:
        executor = AnalysisExecutor()
        store = StudioStore(
            project_id="project:analysis",
            repository=repository,
            blob_store=ContentAddressedBlobStore(tmp_path / "assets"),
            operator_executor=executor,
            dimensions=(
                FieldDimension(
                    dimension_id="material",
                    label="Material",
                    definition="Tactility and surface behavior.",
                ),
            ),
            project_purpose="A quiet project launch.",
            authority_grant_id="authority:studio-test",
        )
        state = store.command(
            "add_reference",
            {
                "asset_id": "asset:analysis",
                "source_id": "upload:analysis",
                "media_type": "image/jpeg",
                "label": "analysis.jpg",
                "content_hash": "a" * 64,
                "source_uri": "local-upload://analysis.jpg",
                "license": {
                    "permitted_use": ["analysis"],
                    "retention_policy": "project_runtime",
                },
            },
        )
        assert state["revision"] == 1

        analyzed = store.command("analyze_field", {})

        assert analyzed["analysis"]["status"] == "success"
        assert analyzed["analysis"]["board_revision_id"].endswith(":revision:1")
        assert analyzed["field"]["status"] == "proposal_ready_for_review"
        assert analyzed["field"]["principles"] == ["Use precise form with soft tactility."]
        assert analyzed["field"]["proposal_id"]
        assert [request["operator_id"].rsplit("/", 1)[-1] for request in executor.requests] == [
            "observation-extraction",
            "reference-interpretation",
            "field-synthesis",
        ]
        assert all(request["project_id"] == "project:analysis" for request in executor.requests)
        assert repository.list(CreativeFieldProposal, project_id="project:analysis")
        assert repository.list(CreativeFieldVersion, project_id="project:analysis") == []

        replayed = store.command("analyze_field", {})
        assert replayed["analysis"]["run_id"] == analyzed["analysis"]["run_id"]
        assert len(executor.requests) == 3
        assert [event["command"] for event in replayed["events"]].count("analyze_field") == 1
        reviewed = store.command("review_field", {"action": "accept"})
        assert reviewed["field"]["status"] == "accepted"
        assert reviewed["field"]["version_id"] == "field:analysis@1"
        versions = repository.list(CreativeFieldVersion, project_id="project:analysis")
        assert len(versions) == 1
        assert versions[0].review_record_ids

    with CreativeRepository(tmp_path / "events.sqlite3") as repository:
        restarted = StudioStore(
            project_id="project:analysis",
            repository=repository,
            blob_store=ContentAddressedBlobStore(tmp_path / "assets"),
        )
        state = restarted.snapshot()
        assert state["analysis"]["status"] == "success"
        assert state["field"]["status"] == "accepted"
        assert state["field"]["principles"] == ["Use precise form with soft tactility."]


def test_analysis_command_holds_before_provider_when_runtime_is_not_configured(tmp_path) -> None:
    with CreativeRepository(tmp_path / "events.sqlite3") as repository:
        store = StudioStore(project_id="project:analysis-hold", repository=repository)
        result = store.command("analyze_field", {})
        assert result == {
            "status": "held",
            "error": "operator runtime is not configured",
        }


def test_analysis_attaches_bounded_image_media_parts_to_the_operator_request(tmp_path) -> None:
    payload = b"fake image bytes"
    with CreativeRepository(tmp_path / "events.sqlite3") as repository:
        executor = AnalysisExecutor()
        store = StudioStore(
            project_id="project:media",
            repository=repository,
            blob_store=ContentAddressedBlobStore(tmp_path / "assets"),
            operator_executor=executor,
            dimensions=(
                FieldDimension(
                    dimension_id="material",
                    label="Material",
                    definition="Tactility and surface behavior.",
                ),
            ),
        )
        store.command(
            "add_reference",
            {
                "asset_id": "asset:media",
                "source_id": "upload:media",
                "media_type": "image/png",
                "label": "media.png",
                "content_base64": base64.b64encode(payload).decode("ascii"),
                "license": {
                    "permitted_use": ["analysis"],
                    "retention_policy": "project_runtime",
                },
            },
        )

        result = store.command("analyze_field", {})

        assert result["analysis"]["status"] == "success"
        media_parts = executor.requests[0]["input"]["media_parts"]
        assert media_parts[0]["type"] == "image"
        assert media_parts[0]["data_url"].startswith("data:image/png;base64,")


def test_analysis_loads_yaml_contracts_and_selects_client_operator_entries(tmp_path) -> None:
    with CreativeRepository(tmp_path / "events.sqlite3") as repository:
        executor = AnalysisExecutor()
        store = StudioStore(
            project_id="project:contracts",
            repository=repository,
            blob_store=ContentAddressedBlobStore(tmp_path / "assets"),
            operator_executor=executor,
            operator_pack=OperatorPack(
                pack_id="operator-pack:contracts@1",
                version=1,
                workspace_id="world://workspace/brand/example",
                operators={
                    "interpret-reference-role": OperatorPackEntry(
                        vocabulary_refs=("vocabulary:example",),
                    ),
                },
            ),
            operator_index_path=Path("reasoning/operators/index.yaml"),
            dimensions=(
                FieldDimension(
                    dimension_id="material",
                    label="Material",
                    definition="Tactility and surface behavior.",
                ),
            ),
        )
        store.command(
            "add_reference",
            {
                "asset_id": "asset:contracts",
                "source_id": "upload:contracts",
                "media_type": "image/png",
                "label": "contracts.png",
                "content_hash": "c" * 64,
                "license": {
                    "permitted_use": ["analysis"],
                    "retention_policy": "project_runtime",
                },
            },
        )

        result = store.command("analyze_field", {})

        assert result["analysis"]["status"] == "success"
        config = executor.requests[1]["configuration"]
        assert config["operator_contracts"]["world://operator/creative/reference-interpretation"][
            "procedure"
        ]
        assert config["operator_pack_by_operator"][
            "world://operator/creative/reference-interpretation"
        ]["client_operator_config"]["vocabulary_refs"] == ["vocabulary:example"]


def test_world_model_resolver_keeps_entity_binding_separate_from_record_filter() -> None:
    root = Path(__file__).resolve().parents[3]
    resolver = create_world_view_resolver(
        root / "workspaces/brand-hellobiotic-research/artifacts/world-modeling.yaml"
    )

    result = resolver(
        {
            "workspace_id": "world://workspace/brand/hellobiotic-research",
            "context_id": "CTX-HELLOBIOTIC-DEODORANT-CURRENT",
            "branch_id": "research-main",
            "target_entity_ids": ["ENT-HB-ID-001"],
            "artifact_type": "product-landing-page",
            "channel": "website",
            "request": {
                "task_type": "create",
                "audience": "people-evaluating-natural-deodorant-alternatives",
            },
        }
    )

    assert result["status"] == "hit"
    assert "STATE-HELLOBIOTIC-PUBLIC-CORE-001" in result["selectedRecordIds"]
    assert "FRAME-HELLOBIOTIC-OFFER-EXPERIENCE-001" in result["selectedRecordIds"]


def test_accepting_a_proposal_requires_explicit_authority(tmp_path) -> None:
    with CreativeRepository(tmp_path / "events.sqlite3") as repository:
        store = StudioStore(
            project_id="project:authority",
            repository=repository,
            operator_executor=AnalysisExecutor(),
            dimensions=(
                FieldDimension(
                    dimension_id="material",
                    label="Material",
                    definition="Tactility and surface behavior.",
                ),
            ),
        )
        store.command(
            "add_reference",
            {
                "asset_id": "asset:authority",
                "source_id": "upload:authority",
                "media_type": "image/jpeg",
                "label": "authority.jpg",
                "content_hash": "c" * 64,
                "source_uri": "local-upload://authority.jpg",
                "license": {
                    "permitted_use": ["analysis"],
                    "retention_policy": "project_runtime",
                },
            },
        )
        analyzed = store.command("analyze_field", {})
        result = store.command("review_field", {"action": "accept"})
        assert analyzed["field"]["status"] == "proposal_ready_for_review"
        assert result == {
            "status": "held",
            "error": "accepting a proposal requires authority_grant_id",
        }
        assert repository.list(CreativeFieldVersion, project_id="project:authority") == []


def test_http_analysis_command_returns_proposal_state(tmp_path) -> None:
    with CreativeRepository(tmp_path / "events.sqlite3") as repository:
        store = StudioStore(
            project_id="project:http-analysis",
            repository=repository,
            blob_store=ContentAddressedBlobStore(tmp_path / "assets"),
            operator_executor=AnalysisExecutor(),
            dimensions=(
                FieldDimension(
                    dimension_id="material",
                    label="Material",
                    definition="Tactility and surface behavior.",
                ),
            ),
        )
        store.command(
            "add_reference",
            {
                "asset_id": "asset:http-analysis",
                "source_id": "upload:http-analysis",
                "media_type": "image/png",
                "label": "http-analysis.png",
                "content_hash": "b" * 64,
                "source_uri": "local-upload://http-analysis.png",
                "license": {
                    "permitted_use": ["analysis"],
                    "retention_policy": "project_runtime",
                },
            },
        )
        server, thread = _running_server(store)
        try:
            status, state = _command(server, "analyze_field", {})
            assert status == 200
            assert state["analysis"]["status"] == "success"
            assert state["field"]["proposal_id"]
        finally:
            _stop_server(server, thread)


def test_project_field_resolves_binding_and_compiles_context_packet(tmp_path) -> None:
    with CreativeRepository(tmp_path / "events.sqlite3") as repository:
        executor = AnalysisExecutor()
        world_requests = []

        def resolve_world_view(request):
            world_requests.append(request)
            return {
                "view_id": "world-view:resolver",
                "status": "hit",
                "workspace_id": request["workspace_id"],
                "context_id": request["context_id"],
                "branch_id": request["branch_id"],
                "selected_record_ids": ["brand:projection"],
                "citations": ["evidence:brand:projection"],
            }

        store = StudioStore(
            project_id="project:projection",
            repository=repository,
            blob_store=ContentAddressedBlobStore(tmp_path / "assets"),
            operator_executor=executor,
            dimensions=(
                FieldDimension(
                    dimension_id="material",
                    label="Material",
                    definition="Tactility and surface behavior.",
                ),
            ),
            authority_grant_id="authority:projection",
            target_adapters={
                "target:image:local": ImageTargetAdapter(lambda packet: b"generated png"),
            },
            world_view_resolver=resolve_world_view,
        )
        store.command(
            "add_reference",
            {
                "asset_id": "asset:projection",
                "source_id": "upload:projection",
                "media_type": "image/jpeg",
                "label": "projection.jpg",
                "content_hash": "d" * 64,
                "source_uri": "local-upload://projection.jpg",
                "license": {
                    "permitted_use": ["analysis", "generation"],
                    "disclosure_allowed": True,
                    "generation_allowed": True,
                    "retention_policy": "project_runtime",
                },
            },
        )
        store.command("analyze_field", {})
        accepted = store.command("review_field", {"action": "accept"})
        assert accepted["field"]["version_id"] == "field:projection@1"

        state = store.command(
            "project_field",
            {
                "workspace_id": "workspace:projection",
                "context_id": "context:projection",
                "branch_id": "branch:main",
                "privacy_policy_id": "policy:projection",
                "authority_grant_id": "authority:projection",
                "target_entity_ids": ["brand:projection"],
                "entities": [
                    {"entity_id": "brand:projection", "workspace_id": "workspace:projection"}
                ],
                "request": {
                    "request_id": "request:projection",
                    "task_type": "create",
                    "artifact_type": "hero-image",
                    "modality": "image",
                    "target": "image-provider",
                    "permission_context": {"disclosure_manifest_id": "disclosure:projection"},
                },
                "target_manifest": {
                    "target_id": "image-provider",
                    "adapter_version": "1",
                    "accepted_modalities": ["image"],
                    "privacy_policy_id": "policy:projection",
                },
                "lens": "hero-image",
                "disclosure_manifest_id": "disclosure:projection",
            },
        )

        assert state["projection"]["status"] == "success"
        assert state["projection"]["context_packet_id"] == "creative-context:request:projection"
        assert world_requests[0]["target_entity_ids"] == ["brand:projection"]
        assert repository.list(ProjectBinding, project_id="project:projection")
        assert repository.list(FieldBinding, project_id="project:projection")
        assert repository.list(FieldProjection, project_id=None)
        assert repository.list(CreativeContextPacket, project_id=None)

        generation = store.command(
            "prepare_generation",
            {
                "target_manifest": {
                    "target_id": "target:image:local",
                    "adapter_version": "1",
                    "accepted_modalities": ["image"],
                    "controls": {
                        "supported_control_ids": [
                            "principles",
                            "tensions",
                            "exclusions",
                            "dimensions",
                        ]
                    },
                    "privacy_policy_id": "policy:projection",
                },
                "disclosure_manifest_id": "disclosure:projection",
                "grounding_asset_ids": ["asset:projection"],
                "permitted_asset_ids": ["asset:projection"],
            },
        )
        assert generation["generation"]["status"] == "ready"
        assert generation["generation"]["target_id"] == "target:image:local"
        assert generation["generation"]["grounding_assets_sent"] == ["asset:projection"]
        assert repository.list(GenerationPacket, project_id=None)
        invoked = store.command("invoke_generation", {})
        assert invoked["generation"]["status"] == "success"
        assert invoked["generation"]["invocation_id"]
        assert invoked["generation"]["output_id"]
        receipts = repository.list(InvocationReceipt, project_id=None)
        outputs = repository.list(CreativeOutput, project_id="project:projection")
        assert len(receipts) == 1
        assert receipts[0].authority_grant_id == "authority:projection"
        assert receipts[0].output_id == outputs[0].output_id
        assert outputs[0].media_type == "image/png"
        assert store.read_output(outputs[0].output_id) == (b"generated png", "image/png")
        server, thread = _running_server(store)
        try:
            output_status, output_headers, output_body = _request(
                server, "GET", f"/api/output/{outputs[0].output_id}"
            )
            assert output_status == 200
            assert output_headers["content-type"] == "image/png"
            assert output_body == b"generated png"
        finally:
            _stop_server(server, thread)
        evaluated = store.command("evaluate_output", {})
        assert evaluated["evaluation"]["status"] == "success"
        assert evaluated["evaluation"]["output_id"] == outputs[0].output_id
        assert evaluated["evaluation"]["feedback_ids"]
        assert repository.list(CreativeEvaluation, project_id=None)
        assert repository.list(FeedbackRecord, project_id=None)
        assert [request["operator_id"].rsplit("/", 1)[-1] for request in executor.requests] == [
            "observation-extraction",
            "reference-interpretation",
            "field-synthesis",
            "output-evaluation",
        ]
        replayed_evaluation = store.command("evaluate_output", {})
        assert replayed_evaluation["evaluation"] == evaluated["evaluation"]
        replayed_invocation = store.command("invoke_generation", {})
        assert replayed_invocation["generation"] == invoked["generation"]
        unauthorized = StudioStore(
            project_id="project:projection",
            repository=repository,
            blob_store=ContentAddressedBlobStore(tmp_path / "assets"),
            target_adapters={
                "target:image:local": ImageTargetAdapter(lambda packet: b"must not run"),
            },
        )
        held = unauthorized.command("invoke_generation", {})
        assert held == {
            "status": "held",
            "error": "generation invocation requires authority_grant_id",
        }
        failed_store = StudioStore(
            project_id="project:projection",
            repository=repository,
            blob_store=ContentAddressedBlobStore(tmp_path / "assets"),
            authority_grant_id="authority:projection",
            target_adapters={
                "target:image:local": ImageTargetAdapter(
                    lambda packet: (_ for _ in ()).throw(RuntimeError("target unavailable"))
                ),
            },
        )
        failed = failed_store.command("invoke_generation", {"invocation_id": "invoke:failed"})
        assert failed["generation"]["status"] == "failed"
        assert failed["generation"]["output_id"] is None
        assert repository.get(InvocationReceipt, "invoke:failed").errors == ("target unavailable",)
        replayed = StudioStore(
            project_id="project:projection",
            repository=repository,
            blob_store=ContentAddressedBlobStore(tmp_path / "assets"),
        ).snapshot()
        assert replayed["projection"]["status"] == "success"
        assert (
            replayed["projection"]["context_packet_id"] == state["projection"]["context_packet_id"]
        )
        assert replayed["generation"] == failed["generation"]
        assert replayed["evaluation"] == evaluated["evaluation"]


def test_project_field_holds_without_an_accepted_version(tmp_path) -> None:
    with CreativeRepository(tmp_path / "events.sqlite3") as repository:
        store = StudioStore(project_id="project:projection-hold", repository=repository)
        result = store.command("project_field", {})
        assert result == {
            "status": "held",
            "error": "an accepted field version is required before projection",
        }


def test_studio_uploads_bytes_to_content_addressed_storage_before_recording_asset(tmp_path) -> None:
    with CreativeRepository(tmp_path / "events.sqlite3") as repository:
        store = StudioStore(
            project_id="project:client-a",
            repository=repository,
            blob_store=ContentAddressedBlobStore(tmp_path / "assets"),
        )
        payload = b"reference bytes"
        state = store.command(
            "add_reference",
            {
                "asset_id": "asset:bytes",
                "source_id": "upload:bytes",
                "media_type": "image/png",
                "label": "bytes.png",
                "content_base64": base64.b64encode(payload).decode("ascii"),
            },
        )
        assert state["references"][0]["source_uri"].startswith("blob://sha256/")
        stored = repository.get(ReferenceAsset, "asset:bytes")
        assert stored is not None
        assert len(stored.content_hash) == 64


def test_http_commands_are_durable_and_replayed_after_restart(tmp_path) -> None:
    database = tmp_path / "events.sqlite3"
    blobs = tmp_path / "assets"
    payload = b"browser reference"
    content_hash = hashlib.sha256(payload).hexdigest()
    with CreativeRepository(database) as repository:
        store = StudioStore(
            project_id="project:restart",
            repository=repository,
            blob_store=ContentAddressedBlobStore(blobs),
        )
        server, thread = _running_server(store)
        try:
            status, state = _command(
                server,
                "add_reference",
                {
                    "asset_id": "asset:restart",
                    "content_hash": content_hash,
                    "content_base64": base64.b64encode(payload).decode("ascii"),
                    "media_type": "image/jpeg",
                    "label": "reference.jpg",
                },
            )
            assert status == 200
            assert len(state["references"]) == 1
            status, state = _command(
                server,
                "annotate_reference",
                {"target_id": "asset:restart", "text": "Keep the rhythm."},
            )
            assert status == 200
            assert len(state["annotations"]) == 1
            status, state = _command(
                server,
                "review_field",
                {"action": "accept", "rationale": "Approved for this project."},
            )
            assert status == 200
            assert state["field"]["status"] == "accepted"
        finally:
            _stop_server(server, thread)

    with CreativeRepository(database) as repository:
        restarted = StudioStore(
            project_id="project:restart",
            repository=repository,
            blob_store=ContentAddressedBlobStore(blobs),
        )
        state = restarted.snapshot()
        assert [item["asset_id"] for item in state["references"]] == ["asset:restart"]
        assert state["annotations"][0]["text"] == "Keep the rhythm."
        assert state["field"]["status"] == "accepted"
        reviews = repository.list(ReviewDecision)
        assert len(reviews) == 1
        assert reviews[0].action.value == "accept"


def test_http_concurrent_uploads_commit_two_revisions_without_ghost_state(tmp_path) -> None:
    database = tmp_path / "events.sqlite3"
    blobs = tmp_path / "assets"
    with CreativeRepository(database) as repository:
        store = StudioStore(
            project_id="project:concurrent",
            repository=repository,
            blob_store=ContentAddressedBlobStore(blobs),
        )
        server, thread = _running_server(store)
        try:

            def upload(index: int) -> tuple[int, dict]:
                payload = f"reference-{index}".encode()
                return _command(
                    server,
                    "add_reference",
                    {
                        "asset_id": f"asset:{index}",
                        "content_hash": hashlib.sha256(payload).hexdigest(),
                        "content_base64": base64.b64encode(payload).decode("ascii"),
                        "media_type": "image/jpeg",
                        "label": f"reference-{index}.jpg",
                    },
                )

            with ThreadPoolExecutor(max_workers=2) as executor:
                results = list(executor.map(upload, (1, 2)))
            assert [status for status, _state in results] == [200, 200]
            assert len(store.snapshot()["references"]) == 2
            assert repository.latest_board_revision("moodboard:concurrent") == 2
            assert len(repository.list(ReferenceAsset, project_id="project:concurrent")) == 2
        finally:
            _stop_server(server, thread)


def test_blob_endpoint_is_project_scoped_and_returns_original_bytes(tmp_path) -> None:
    payload = b"image bytes"
    content_hash = hashlib.sha256(payload).hexdigest()
    with CreativeRepository(tmp_path / "events.sqlite3") as repository:
        store = StudioStore(
            project_id="project:blob",
            repository=repository,
            blob_store=ContentAddressedBlobStore(tmp_path / "assets"),
        )
        store.command(
            "add_reference",
            {
                "asset_id": "asset:blob",
                "content_hash": content_hash,
                "content_base64": base64.b64encode(payload).decode("ascii"),
                "media_type": "image/jpeg",
                "label": "blob.jpg",
            },
        )
        server, thread = _running_server(store)
        try:
            status, headers, body = _request(server, "GET", f"/api/blob/{content_hash}")
            assert status == 200
            assert headers["content-type"] == "image/jpeg"
            assert body == payload
            status, _headers, _body = _request(server, "GET", f"/api/blob/{'0' * 64}")
            assert status == 404
        finally:
            _stop_server(server, thread)


def test_reset_persists_an_empty_head_without_resurrecting_old_review_state(tmp_path) -> None:
    database = tmp_path / "events.sqlite3"
    with CreativeRepository(database) as repository:
        store = StudioStore(project_id="project:reset", repository=repository)
        store.command(
            "add_reference",
            {
                "asset_id": "asset:reset",
                "content_hash": "a" * 64,
                "source_uri": "local-upload://reset.jpg",
                "media_type": "image/jpeg",
                "label": "reset.jpg",
            },
        )
        store.command("review_field", {"action": "accept"})
        state = store.command("reset_demo", {})
        assert state["references"] == []
        assert state["field"]["status"] == "awaiting_reviewed_synthesis"

    with CreativeRepository(database) as repository:
        restarted = StudioStore(project_id="project:reset", repository=repository)
        state = restarted.snapshot()
        assert state["references"] == []
        assert state["field"]["status"] == "awaiting_reviewed_synthesis"
        assert repository.latest_board_revision("moodboard:reset") == 2


def test_upload_can_commit_an_explicit_source_license_with_the_asset(tmp_path) -> None:
    payload = b"licensed reference"
    with CreativeRepository(tmp_path / "events.sqlite3") as repository:
        store = StudioStore(
            project_id="project:licensed",
            repository=repository,
            blob_store=ContentAddressedBlobStore(tmp_path / "assets"),
        )
        state = store.command(
            "add_reference",
            {
                "asset_id": "asset:licensed",
                "content_base64": base64.b64encode(payload).decode("ascii"),
                "media_type": "image/jpeg",
                "label": "licensed.jpg",
                "license_record_id": "license:licensed",
                "license": {
                    "owner": "client",
                    "permitted_use": ["analysis", "generation"],
                    "disclosure_allowed": True,
                    "generation_allowed": True,
                    "retention_policy": "project_runtime",
                },
            },
        )
        assert state["references"][0]["license_record_id"] == "license:licensed"
        license_record = repository.get(SourceLicenseRecord, "license:licensed")
        assert license_record is not None
        assert license_record.generation_allowed is True


def test_unknown_license_identity_is_held_before_board_mutation(tmp_path) -> None:
    with CreativeRepository(tmp_path / "events.sqlite3") as repository:
        store = StudioStore(project_id="project:license-hold", repository=repository)
        result = store.command(
            "add_reference",
            {
                "asset_id": "asset:license-hold",
                "content_hash": "b" * 64,
                "source_uri": "local-upload://unknown.jpg",
                "media_type": "image/jpeg",
                "label": "unknown.jpg",
                "license_record_id": "license:missing",
            },
        )
        assert result["status"] == "held"
        assert store.snapshot()["references"] == []
        assert repository.latest_board_revision("moodboard:license-hold") == 0


def test_http_rejects_oversized_command_before_reading_the_body(tmp_path) -> None:
    with CreativeRepository(tmp_path / "events.sqlite3") as repository:
        store = StudioStore(project_id="project:size", repository=repository)
        server, thread = _running_server(store)
        try:
            connection = HTTPConnection("127.0.0.1", server.server_port, timeout=5)
            connection.putrequest("POST", "/api/command")
            connection.putheader("content-length", str(MAX_COMMAND_BODY_BYTES + 1))
            connection.endheaders()
            response = connection.getresponse()
            assert response.status == 413
            response.read()
            connection.close()
        finally:
            _stop_server(server, thread)
