import sqlite3
from datetime import UTC, datetime, timedelta

import pytest
from testflight_adapter_sqlite_semantic import SQLiteWorldRepository
from testflight_semantic import (
    AuthorityGrant,
    Capability,
    DecisionAlternative,
    TemporalInterval,
    WorldDecision,
    WorldDecisionStatus,
    WorldEntity,
    WorldLifecycle,
)
from testflight_world import (
    InMemoryAuthorityGrantResolver,
    ProposalStatus,
    ReviewDisposition,
    WorldChangeSet,
    WorldHistoryEntry,
    WorldProposalError,
    WorldReview,
    WorldService,
)

NOW = datetime(2026, 9, 14, tzinfo=UTC)
WORKSPACE = "world://workspace/brand/biotic"


def _grant(**updates: object) -> AuthorityGrant:
    values = {
        "grant_id": "grant:biotic-founder",
        "principal_id": "user:talha",
        "capabilities": (Capability.PROMOTE,),
        "object_selectors": ("*",),
        "issued_by": "authority:biotic",
        "policy_version": "authority-v1",
    }
    values.update(updates)
    return AuthorityGrant.model_validate(values)


def _world_service(
    repository: SQLiteWorldRepository,
    grant: AuthorityGrant | None = None,
) -> WorldService:
    return WorldService(
        repository,
        InMemoryAuthorityGrantResolver((grant or _grant(),)),
    )


def _entity(record_id: str = "entity:biotic") -> WorldEntity:
    return WorldEntity(
        id=record_id,
        type_id="world://ontology/brand-world/type/Brand",
        workspace_id=WORKSPACE,
        module_id="world://ontology/module/brand-world/identity",
        created_at=NOW,
        created_by="user:talha",
        canonical_label="Biotic",
        definition="An identity-bearing Brand.",
    )


def _proposal(
    *records: WorldEntity,
    proposal_id: str = "proposal:biotic-brand",
    branch_id: str = "main",
) -> WorldChangeSet:
    return WorldChangeSet(
        proposal_id=proposal_id,
        workspace_id=WORKSPACE,
        branch_id=branch_id,
        proposed_by="agent:founder-world-interpreter",
        proposed_at=NOW,
        records=records,
        rationale="Create proposed records from reviewed capture.",
    )


def _approval(
    branch_id: str = "main", decision_id: str = "decision:approve-biotic-brand"
) -> WorldDecision:
    return WorldDecision(
        id=decision_id,
        type_id="world://semantic/decision",
        workspace_id=WORKSPACE,
        branch_id=branch_id,
        module_id="world://ontology/module/brand-world/governance-decisions",
        created_at=NOW,
        created_by="user:talha",
        authority_ref="grant:biotic-founder",
        question="Approve the initial Biotic Brand entity?",
        alternatives=(
            DecisionAlternative(id="approve", label="Approve"),
            DecisionAlternative(id="reject", label="Reject"),
        ),
        selected_alternative_id="approve",
        status=WorldDecisionStatus.APPROVED,
    )


def test_sqlite_world_repository_replays_accepted_history_after_reopen(tmp_path) -> None:
    path = tmp_path / "world.sqlite3"
    with SQLiteWorldRepository(path) as repository:
        service = _world_service(repository)
        service.propose(_proposal(_entity()))
        service.approve("proposal:biotic-brand", _approval(), accepted_at=NOW)

    with SQLiteWorldRepository(path) as repository:
        history = repository.history("entity:biotic")
        accepted = repository.get_proposal("proposal:biotic-brand")

    assert history[0].record.lifecycle_status.value == "accepted"
    assert accepted is not None and accepted.status.value == "accepted"


def test_acceptance_atomically_enqueues_and_activates_one_projection_job(tmp_path) -> None:
    path = tmp_path / "world.sqlite3"
    with SQLiteWorldRepository(path) as repository:
        service = _world_service(repository)
        service.propose(_proposal(_entity()))
        service.approve("proposal:biotic-brand", _approval(), accepted_at=NOW)

        job = repository.claim_projection_job()
        assert job is not None
        assert job.workspace_id == WORKSPACE
        assert job.branch_id == "main"
        assert job.status.value == "running"
        assert repository.active_projection_job(WORKSPACE, "main") is None
        completed = repository.complete_projection_job(job.job_id)
        assert completed.status.value == "succeeded"
        assert repository.active_projection_job(WORKSPACE, "main") == completed

    with SQLiteWorldRepository(path) as repository:
        assert repository.active_projection_job(WORKSPACE, "main") is not None


def test_sqlite_acceptance_rolls_back_proposal_status_when_history_conflicts(tmp_path) -> None:
    with SQLiteWorldRepository(tmp_path / "world.sqlite3") as repository:
        service = _world_service(repository)
        service.propose(_proposal(_entity()))
        service.propose(
            _proposal(_entity()).model_copy(update={"proposal_id": "proposal:biotic-brand-2"})
        )
        service.approve("proposal:biotic-brand", _approval(), accepted_at=NOW)

        with pytest.raises(Exception, match="unexpected record version"):
            service.approve("proposal:biotic-brand-2", _approval(), accepted_at=NOW)

        pending = repository.get_proposal("proposal:biotic-brand-2")

    assert pending is not None
    assert pending.status.value == "proposed"


@pytest.mark.parametrize(
    ("grants", "match"),
    (
        ((), "unknown authority grant"),
        (
            (
                _grant(
                    valid_time=TemporalInterval(
                        from_time=NOW - timedelta(days=1),
                        to_time=NOW,
                    )
                ),
            ),
            "effective time",
        ),
        ((_grant(object_selectors=("entity:other",)),), "affected record"),
    ),
)
def test_sqlite_authority_failure_leaves_zero_partial_writes(
    tmp_path, grants: tuple[AuthorityGrant, ...], match: str
) -> None:
    path = tmp_path / "world.sqlite3"
    with SQLiteWorldRepository(path) as repository:
        service = WorldService(repository, InMemoryAuthorityGrantResolver(grants))
        service.propose(_proposal(_entity()))

        with pytest.raises(WorldProposalError, match=match):
            service.approve("proposal:biotic-brand", _approval(), accepted_at=NOW)

        assert repository.history("entity:biotic", workspace_id=WORKSPACE, branch_id="main") == ()
        assert repository.get_proposal("proposal:biotic-brand").status.value == "proposed"

    with SQLiteWorldRepository(path) as repository:
        assert repository.history("entity:biotic", workspace_id=WORKSPACE, branch_id="main") == ()


def test_sqlite_snapshots_are_branch_and_recorded_time_isolated_after_reopen(tmp_path) -> None:
    path = tmp_path / "world.sqlite3"
    later = NOW + timedelta(hours=1)
    with SQLiteWorldRepository(path) as repository:
        service = _world_service(repository)
        service.propose(_proposal(_entity(), proposal_id="proposal:main"))
        service.approve("proposal:main", _approval(decision_id="decision:main"), accepted_at=NOW)
        research = _entity().model_copy(update={"branch_id": "research"})
        service.propose(_proposal(research, proposal_id="proposal:research", branch_id="research"))
        service.approve(
            "proposal:research",
            _approval("research", "decision:research"),
            accepted_at=later,
        )

    with SQLiteWorldRepository(path) as repository:
        service = _world_service(repository)
        assert service.snapshot(WORKSPACE, "main", recorded_at=NOW).records[0].branch_id == "main"
        assert service.snapshot(WORKSPACE, "research", recorded_at=NOW).records == ()
        assert (
            service.snapshot(WORKSPACE, "research", recorded_at=later).records[0].branch_id
            == "research"
        )


def test_sqlite_reviews_round_trip_without_promoting_proposal(tmp_path) -> None:
    path = tmp_path / "world.sqlite3"
    review = WorldReview(
        review_id="review:biotic",
        proposal_id="proposal:biotic-brand",
        workspace_id=WORKSPACE,
        branch_id="main",
        reviewer_id="user:fde",
        reviewed_at=NOW,
        disposition=ReviewDisposition.CHANGES_REQUESTED,
        findings=("Clarify the definition.",),
    )
    with SQLiteWorldRepository(path) as repository:
        service = _world_service(repository)
        service.propose(_proposal(_entity()))
        service.review(review)

    with SQLiteWorldRepository(path) as repository:
        assert repository.reviews(review.proposal_id) == (review,)
        assert repository.get_proposal(review.proposal_id).status.value == "proposed"


def test_sqlite_migrates_the_initial_unscoped_history_schema_without_data_loss(tmp_path) -> None:
    path = tmp_path / "world.sqlite3"
    candidate = _proposal(_entity())
    accepted_record = _entity().model_copy(
        update={
            "record_version": 2,
            "lifecycle_status": WorldLifecycle.ACCEPTED,
            "authority_ref": "grant:founder",
        }
    )
    accepted_proposal = candidate.model_copy(
        update={
            "status": ProposalStatus.ACCEPTED,
            "review_decision_id": "decision:legacy",
        }
    )
    entry = WorldHistoryEntry(
        record_id=accepted_record.id,
        record_version=accepted_record.record_version,
        proposal_id=candidate.proposal_id,
        recorded_at=NOW,
        record=accepted_record,
    )
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE world_proposals (
            proposal_id TEXT PRIMARY KEY,
            payload_json TEXT NOT NULL
        );
        CREATE TABLE world_record_history (
            record_id TEXT NOT NULL,
            record_version INTEGER NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (record_id, record_version)
        );
        """
    )
    connection.execute(
        "INSERT INTO world_proposals (proposal_id, payload_json) VALUES (?, ?)",
        (accepted_proposal.proposal_id, accepted_proposal.model_dump_json()),
    )
    connection.execute(
        """
        INSERT INTO world_record_history (record_id, record_version, payload_json)
        VALUES (?, ?, ?)
        """,
        (entry.record_id, entry.record_version, entry.model_dump_json()),
    )
    connection.commit()
    connection.close()

    with SQLiteWorldRepository(path) as repository:
        restored = repository.snapshot(WORKSPACE, "main")

    assert restored == (entry,)
