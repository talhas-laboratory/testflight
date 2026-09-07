from collections.abc import Iterable

from testflight_creative_field import (
    ArtifactStatus,
    BoardRevision,
    CreativeFieldRunCoordinator,
    FieldDimension,
    ObservedFeature,
    OperatorExecution,
    Placement,
    ReferenceAsset,
    ReferenceContribution,
    ReferenceInterpretation,
    SourceLicenseRecord,
)

_IDENTITY_FIELDS = {
    "BoardRevision": "board_revision_id",
    "CreativeFieldProposal": "proposal_id",
    "ObservedFeature": "feature_id",
    "ReferenceAsset": "asset_id",
    "ReferenceContribution": "contribution_id",
    "ReferenceInterpretation": "interpretation_id",
    "ReviewDecision": "review_id",
    "SourceLicenseRecord": "license_record_id",
}


class MemoryRepository:
    def __init__(self) -> None:
        self.records: dict[tuple[str, str], object] = {}

    def append(self, record, *, project_id=None) -> None:
        del project_id
        record_type = type(record).__name__
        record_id = str(getattr(record, _IDENTITY_FIELDS[record_type]))
        self.records.setdefault((record_type, record_id), record)

    def append_many(self, records: Iterable[object]) -> None:
        for record in records:
            self.append(record)

    def get(self, model, record_id: str):
        return self.records.get((model.__name__, record_id))

    def list(self, model, *, project_id=None):
        values = [
            record
            for (record_type, _record_id), record in self.records.items()
            if record_type == model.__name__
        ]
        if project_id is not None:
            values = [
                record
                for record in values
                if getattr(record, "project_id", project_id) == project_id
            ]
        return values

    def replay_board(self, moodboard_id: str):
        revisions = [
            record
            for (record_type, _record_id), record in self.records.items()
            if record_type == "BoardRevision" and record.moodboard_id == moodboard_id
        ]
        return sorted(revisions, key=lambda record: record.revision)


class ScenarioExecutor:
    def __init__(self, *, fail_stage: str | None = None) -> None:
        self.fail_stage = fail_stage
        self.requests: list[dict] = []

    def execute(self, request: dict) -> OperatorExecution:
        self.requests.append(request)
        operator_id = request["operator_id"]
        if self.fail_stage and operator_id.endswith(self.fail_stage):
            return OperatorExecution(
                status="failed",
                errors=(f"{self.fail_stage} provider unavailable",),
                receipt={"operation_key": request["operation_key"]},
            )
        if operator_id.endswith("observation-extraction"):
            return OperatorExecution(
                status="proposal",
                output={
                    "observed_features": [
                        {
                            "label": "controlled softness",
                            "dimension_id": "material",
                            "value": "softness held inside precise form",
                            "bounded_anchors": [
                                f"{request['input']['asset']['asset_id']}#region:1"
                            ],
                        }
                    ]
                },
                receipt={"operation_key": request["operation_key"], "provider": "fake"},
            )
        if operator_id.endswith("reference-interpretation"):
            asset_id = request["input"]["asset_id"]
            return OperatorExecution(
                status="proposal",
                output={
                    "proposed_role": "carry tactility, not the object",
                    "authority": "operator-proposal",
                    "evidence_refs": [f"{asset_id}#region:1"],
                    "carry_forward": ["softness", "restraint"],
                    "anti_transfer": ["literal object silhouette"],
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
                receipt={"operation_key": request["operation_key"], "provider": "fake"},
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
                    "tensions": [
                        {
                            "statement": "Precision should hold softness, not erase it.",
                            "poles": ["precise", "soft"],
                        }
                    ],
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
                receipt={"operation_key": request["operation_key"], "provider": "fake"},
            )
        raise AssertionError(f"unexpected operator: {operator_id}")


def _asset(asset_id: str, project_id: str = "project:one") -> ReferenceAsset:
    return ReferenceAsset(
        asset_id=asset_id,
        project_id=project_id,
        source_id=f"source:{asset_id}",
        media_type="image/jpeg",
        label=asset_id,
        content_hash=f"hash:{asset_id}",
        source_uri=f"blob://{asset_id}",
        license_record_id=f"license:{asset_id}",
        recorded_at="2026-09-03T00:00:00Z",
    )


def _board(*assets: ReferenceAsset, project_id: str = "project:one") -> BoardRevision:
    return BoardRevision(
        board_revision_id="board:one@1",
        moodboard_id="moodboard:one",
        project_id=project_id,
        revision=1,
        reference_asset_ids=tuple(asset.asset_id for asset in assets),
        placements=tuple(
            Placement(
                placement_id=f"placement:{asset.asset_id}",
                asset_id=asset.asset_id,
                x=index * 10,
                y=0,
                width=100,
                height=100,
            )
            for index, asset in enumerate(assets)
        ),
        created_at="2026-09-03T00:00:00Z",
        created_by="actor:one",
    )


def _seed(repository: MemoryRepository, *assets: ReferenceAsset) -> None:
    for asset in assets:
        repository.append(asset)
        repository.append(
            SourceLicenseRecord(
                license_record_id=asset.license_record_id,
                source_id=asset.source_id,
                permitted_use=("analysis",),
                retention_policy="project-runtime",
            )
        )
    repository.append(_board(*assets))


def _coordinator(repository, executor, *, operator_configuration=None):
    return CreativeFieldRunCoordinator(
        repository=repository,
        project_id="project:one",
        project_purpose="A quiet launch system",
        dimensions=(
            FieldDimension(
                dimension_id="material",
                label="Material",
                definition="tactility and surface behavior",
            ),
        ),
        executor=executor,
        field_id="field:one",
        operator_configuration=operator_configuration,
    )


def test_run_composes_three_stages_and_persists_typed_proposals() -> None:
    repository = MemoryRepository()
    _seed(repository, _asset("asset:one"), _asset("asset:two"))
    executor = ScenarioExecutor()

    result = _coordinator(repository, executor).run(run_id="run:one", moodboard_id="moodboard:one")

    assert result.status is ArtifactStatus.SUCCESS
    assert result.proposal is not None
    assert result.proposal.project_id == "project:one"
    assert len(repository.list(ObservedFeature)) == 2
    assert len(repository.list(ReferenceInterpretation)) == 2
    assert len(repository.list(ReferenceContribution)) == 2
    assert repository.get(type(result.proposal), result.proposal.proposal_id) is not None
    assert [request["operator_id"] for request in executor.requests] == [
        "world://operator/creative/observation-extraction",
        "world://operator/creative/reference-interpretation",
        "world://operator/creative/observation-extraction",
        "world://operator/creative/reference-interpretation",
        "world://operator/creative/field-synthesis",
    ]
    assert all(request["project_id"] == "project:one" for request in executor.requests)
    assert all(request["disclosure_refs"] for request in executor.requests)
    assert all(stage.receipt["provider"] == "fake" for stage in result.stages if stage.receipt)


def test_client_operator_configuration_reaches_every_transform_stage() -> None:
    repository = MemoryRepository()
    _seed(repository, _asset("asset:configured"))
    executor = ScenarioExecutor()
    configuration = {
        "operator_pack": {
            "pack_id": "operator-pack:example@1",
            "operator_pack_version": 1,
        }
    }

    result = _coordinator(
        repository,
        executor,
        operator_configuration=configuration,
    ).run(run_id="run:configured", moodboard_id="moodboard:one")

    assert result.status is ArtifactStatus.SUCCESS
    assert all(request["configuration"] == configuration for request in executor.requests)


def test_missing_rights_holds_before_provider_and_skips_synthesis() -> None:
    repository = MemoryRepository()
    asset = _asset("asset:no-rights").model_copy(update={"license_record_id": None})
    repository.append(asset)
    repository.append(_board(asset))
    executor = ScenarioExecutor()

    result = _coordinator(repository, executor).run(
        run_id="run:rights", moodboard_id="moodboard:one"
    )

    assert result.status is ArtifactStatus.HELD
    assert result.hold_reason == "rights_missing"
    assert result.stages[0].stage == "observation"
    assert executor.requests == []
    assert repository.list(ObservedFeature) == []
    assert repository.list(ReferenceInterpretation) == []


def test_foreign_board_is_held_before_provider_execution() -> None:
    repository = MemoryRepository()
    foreign_asset = _asset("asset:foreign", project_id="project:other")
    repository.append(foreign_asset)
    repository.append(_board(foreign_asset, project_id="project:other"))
    executor = ScenarioExecutor()

    result = _coordinator(repository, executor).run(
        run_id="run:scope", moodboard_id="moodboard:one"
    )

    assert result.status is ArtifactStatus.HELD
    assert result.hold_reason == "scope_mismatch"
    assert executor.requests == []


def test_provider_failure_keeps_receipt_and_creates_no_downstream_records() -> None:
    repository = MemoryRepository()
    _seed(repository, _asset("asset:one"))
    executor = ScenarioExecutor(fail_stage="observation-extraction")

    result = _coordinator(repository, executor).run(
        run_id="run:failure", moodboard_id="moodboard:one"
    )

    assert result.status is ArtifactStatus.FAILED
    assert result.errors == ("observation-extraction provider unavailable",)
    assert result.stages[0].receipt["operation_key"].endswith("asset:one")
    assert repository.list(ObservedFeature) == []
    assert repository.list(ReferenceInterpretation) == []
    assert repository.list(ReferenceContribution) == []


def test_empty_board_returns_unavailable_without_provider_call() -> None:
    repository = MemoryRepository()
    repository.append(_board())
    executor = ScenarioExecutor()

    result = _coordinator(repository, executor).run(
        run_id="run:empty", moodboard_id="moodboard:one"
    )

    assert result.status is ArtifactStatus.UNAVAILABLE
    assert result.hold_reason == "no_contributions"
    assert executor.requests == []
