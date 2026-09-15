from datetime import UTC, datetime, timedelta

import pytest
from testflight_semantic import (
    AuthorityGrant,
    Capability,
    ClaimKind,
    DecisionAlternative,
    RelationParticipant,
    SourceContentPolicy,
    TemporalInterval,
    WorldClaim,
    WorldDecision,
    WorldDecisionStatus,
    WorldEntity,
    WorldEvidence,
    WorldRelation,
    WorldSource,
    WorldState,
)
from testflight_world import (
    BranchConflictResolution,
    InMemoryAuthorityGrantResolver,
    InMemoryWorldRepository,
    MergeChoice,
    ReviewDisposition,
    WorldChangeSet,
    WorldProposalError,
    WorldRecordRef,
    WorldReview,
    WorldService,
)

NOW = datetime(2026, 9, 14, tzinfo=UTC)
WORKSPACE = "world://workspace/brand/biotic"


def authority_grant(**updates: object) -> AuthorityGrant:
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


def world_service(
    repository: InMemoryWorldRepository | None = None,
    *,
    grants: tuple[AuthorityGrant, ...] | None = None,
) -> WorldService:
    return WorldService(
        repository or InMemoryWorldRepository(),
        InMemoryAuthorityGrantResolver((authority_grant(),) if grants is None else grants),
    )


def entity() -> WorldEntity:
    return WorldEntity(
        id="entity:biotic",
        type_id="world://ontology/brand-world/type/Brand",
        workspace_id=WORKSPACE,
        module_id="world://ontology/module/brand-world/identity",
        created_at=NOW,
        created_by="user:talha",
        canonical_label="Biotic",
        definition="An identity-bearing Brand.",
    )


def proposal() -> WorldChangeSet:
    return WorldChangeSet(
        proposal_id="proposal:biotic-brand",
        workspace_id=WORKSPACE,
        proposed_by="agent:founder-world-interpreter",
        proposed_at=NOW,
        records=(entity(),),
        rationale="Create the proposed canonical Brand entity from reviewed capture.",
    )


def approval() -> WorldDecision:
    return WorldDecision(
        id="decision:approve-biotic-brand",
        type_id="world://semantic/decision",
        workspace_id=WORKSPACE,
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


def scoped_approval(branch_id: str, decision_id: str) -> WorldDecision:
    return approval().model_copy(update={"id": decision_id, "branch_id": branch_id})


def evidence_records(branch_id: str = "main") -> tuple[object, ...]:
    common = {
        "workspace_id": WORKSPACE,
        "branch_id": branch_id,
        "module_id": "world://ontology/module/brand-world/identity",
        "created_at": NOW,
        "created_by": "user:talha",
    }
    source = WorldSource(
        id="source:interview",
        type_id="world://semantic/source",
        locator="interview://founder/1",
        title="Founder interview",
        content_policy=SourceContentPolicy.RETAINED,
        captured_at=NOW,
        **common,
    )
    evidence = WorldEvidence(
        id="evidence:mission",
        type_id="world://semantic/evidence",
        source_id=source.id,
        locator="turn:12",
        excerpt="Biotic supports whole-body care.",
        **common,
    )
    brand = entity().model_copy(update={"branch_id": branch_id})
    claim = WorldClaim(
        id="claim:mission",
        type_id="world://ontology/brand-world/type/PurposeClaim",
        claim_kind=ClaimKind.NORMATIVE_COMMITMENT,
        subject_id=brand.id,
        predicate_id="world://ontology/brand-world/relation/has-purpose",
        object_value="Support whole-body care",
        evidence_ids=(evidence.id,),
        **common,
    )
    dependency = WorldRelation(
        id="relation:claim-depends-on-evidence",
        type_id="world://semantic/relation",
        relation_type_id="world://semantic/relation/depends-on",
        participants=(
            RelationParticipant(role_id="dependent", record_id=claim.id),
            RelationParticipant(role_id="dependency", record_id=evidence.id),
        ),
        evidence_ids=(evidence.id,),
        **common,
    )
    return source, evidence, brand, claim, dependency


def test_only_an_explicit_approved_decision_can_promote_a_change_set() -> None:
    repository = InMemoryWorldRepository()
    service = world_service(repository)
    service.propose(proposal())

    receipt = service.approve("proposal:biotic-brand", approval(), accepted_at=NOW)
    history = service.history("entity:biotic", workspace_id=WORKSPACE)

    assert receipt.accepted_record_ids == ("entity:biotic",)
    assert history[0].record.lifecycle_status.value == "accepted"
    assert history[0].record.record_version == 2
    assert history[0].record.authority_ref == "grant:biotic-founder"
    assert receipt.authority_grant_id == "grant:biotic-founder"
    assert receipt.authority_capability is Capability.PROMOTE


def test_accept_capability_can_authorize_approval_when_it_covers_every_record() -> None:
    service = world_service(grants=(authority_grant(capabilities=(Capability.ACCEPT,)),))
    service.propose(proposal())

    receipt = service.approve("proposal:biotic-brand", approval(), accepted_at=NOW)

    assert receipt.authority_capability is Capability.ACCEPT


@pytest.mark.parametrize(
    ("grant", "match"),
    (
        (None, "unknown authority grant"),
        (authority_grant(principal_id="user:someone-else"), "principal"),
        (authority_grant(capabilities=(Capability.PROPOSE,)), "accept or promote"),
        (authority_grant(object_selectors=("entity:other",)), "affected record"),
        (
            authority_grant(
                valid_time=TemporalInterval(
                    from_time=NOW - timedelta(days=1),
                    to_time=NOW,
                )
            ),
            "effective time",
        ),
    ),
)
def test_invalid_authority_grants_leave_no_accepted_history(
    grant: AuthorityGrant | None, match: str
) -> None:
    repository = InMemoryWorldRepository()
    grants = () if grant is None else (grant,)
    service = world_service(repository, grants=grants)
    service.propose(proposal())

    with pytest.raises(WorldProposalError, match=match):
        service.approve("proposal:biotic-brand", approval(), accepted_at=NOW)

    assert service.history("entity:biotic", workspace_id=WORKSPACE) == ()
    assert repository.get_proposal("proposal:biotic-brand").status.value == "proposed"


def test_context_scoped_grant_must_cover_every_record_context() -> None:
    repository = InMemoryWorldRepository()
    service = world_service(
        repository,
        grants=(authority_grant(context_selector=("context:eu",)),),
    )
    scoped = proposal().model_copy(
        update={"records": (entity().model_copy(update={"context_refs": ("context:us",)}),)}
    )
    service.propose(scoped)

    with pytest.raises(WorldProposalError, match="context"):
        service.approve(scoped.proposal_id, approval(), accepted_at=NOW)

    assert repository.history("entity:biotic", workspace_id=WORKSPACE, branch_id="main") == ()


def test_approval_without_a_resolver_fails_closed() -> None:
    repository = InMemoryWorldRepository()
    service = WorldService(repository)
    service.propose(proposal())

    with pytest.raises(WorldProposalError, match="AuthorityGrantResolver"):
        service.approve(proposal().proposal_id, approval(), accepted_at=NOW)

    assert repository.history("entity:biotic", workspace_id=WORKSPACE, branch_id="main") == ()


def test_rejection_is_explicit_and_blocks_later_approval() -> None:
    service = world_service()
    service.propose(proposal())
    rejected = service.reject("proposal:biotic-brand", "Founder requested a correction.")

    assert rejected.status.value == "rejected"
    with pytest.raises(WorldProposalError, match="not pending review"):
        service.approve("proposal:biotic-brand", approval(), accepted_at=NOW)


def test_approval_cannot_cross_workspace_boundaries() -> None:
    service = world_service()
    service.propose(proposal())
    cross_workspace = approval().model_copy(update={"workspace_id": "world://workspace/other"})

    with pytest.raises(WorldProposalError, match="workspace"):
        service.approve("proposal:biotic-brand", cross_workspace, accepted_at=NOW)


def test_reviews_are_append_only_and_do_not_promote_a_proposal() -> None:
    service = world_service()
    service.propose(proposal())
    review = WorldReview(
        review_id="review:1",
        proposal_id="proposal:biotic-brand",
        workspace_id=WORKSPACE,
        branch_id="main",
        reviewer_id="user:fde",
        reviewed_at=NOW,
        disposition=ReviewDisposition.READY,
        findings=("Identity and provenance are explicit.",),
    )

    service.review(review)

    assert service.reviews(review.proposal_id) == (review,)
    assert service._repository.get_proposal(review.proposal_id).status.value == "proposed"  # noqa: SLF001


def test_snapshot_reconstructs_branch_at_recorded_time_and_keeps_branches_isolated() -> None:
    service = world_service()
    service.propose(proposal())
    service.approve("proposal:biotic-brand", approval(), accepted_at=NOW)
    branch_entity = entity().model_copy(update={"branch_id": "research"})
    branch_proposal = proposal().model_copy(
        update={
            "proposal_id": "proposal:research",
            "branch_id": "research",
            "records": (branch_entity,),
        }
    )
    service.propose(branch_proposal)
    service.approve(
        branch_proposal.proposal_id,
        scoped_approval("research", "decision:research"),
        accepted_at=NOW + timedelta(hours=1),
    )

    assert service.snapshot(WORKSPACE, "main", recorded_at=NOW).records[0].branch_id == "main"
    assert service.snapshot(WORKSPACE, "research", recorded_at=NOW).records == ()
    assert (
        service.snapshot(WORKSPACE, "research", recorded_at=NOW + timedelta(hours=1))
        .records[0]
        .branch_id
        == "research"
    )


def test_supersede_creates_a_proposal_and_diff_preserves_history() -> None:
    service = world_service()
    service.propose(proposal())
    service.approve("proposal:biotic-brand", approval(), accepted_at=NOW)
    replacement = entity().model_copy(update={"definition": "The Biotic Brand identity."})
    superseding = service.supersede(
        "entity:biotic",
        replacement,
        proposal_id="proposal:refine-biotic",
        proposed_by="user:fde",
        proposed_at=NOW + timedelta(hours=1),
        rationale="Use the reviewed identity definition.",
    )

    assert superseding.records[0].record_version == 2
    assert (
        service.get("entity:biotic", workspace_id=WORKSPACE).definition
        == "An identity-bearing Brand."
    )

    service.approve(
        superseding.proposal_id,
        approval().model_copy(update={"id": "decision:refine-biotic"}),
        accepted_at=NOW + timedelta(hours=2),
    )
    difference = service.diff(
        WorldRecordRef(workspace_id=WORKSPACE, record_id="entity:biotic", record_version=2),
        WorldRecordRef(workspace_id=WORKSPACE, record_id="entity:biotic", record_version=3),
    )

    assert [
        entry.record_version for entry in service.history("entity:biotic", workspace_id=WORKSPACE)
    ] == [2, 3]
    assert "/definition" in {change.path for change in difference.changes}
    assert service.get("entity:biotic", workspace_id=WORKSPACE).supersedes_ref == "entity:biotic@2"


def test_evidence_relation_dependency_and_search_reads_are_bounded_and_typed() -> None:
    service = world_service()
    records = evidence_records()
    change_set = WorldChangeSet(
        proposal_id="proposal:grounded-world",
        workspace_id=WORKSPACE,
        proposed_by="user:fde",
        proposed_at=NOW,
        records=records,
        rationale="Persist a grounded identity slice.",
    )
    service.propose(change_set)
    service.approve(change_set.proposal_id, approval(), accepted_at=NOW)

    bundle = service.evidence("claim:mission", workspace_id=WORKSPACE)
    related = service.related("claim:mission", workspace_id=WORKSPACE)
    dependencies = service.dependencies(
        "claim:mission",
        workspace_id=WORKSPACE,
        dependency_relation_type_ids=("world://semantic/relation/depends-on",),
        role_ids=("dependent",),
    )
    hits = service.search("whole-body", workspace_id=WORKSPACE, semantic_kinds=("claim",))

    assert [item.id for item in bundle.evidence] == ["evidence:mission"]
    assert [item.id for item in bundle.sources] == ["source:interview"]
    assert related == dependencies
    assert [hit.record.id for hit in hits] == ["claim:mission"]


def test_dangling_canonical_references_are_rejected_before_persistence() -> None:
    service = world_service()
    dangling = WorldClaim(
        id="claim:dangling",
        type_id="world://semantic/claim",
        workspace_id=WORKSPACE,
        module_id="world://ontology/module/brand-world/identity",
        created_at=NOW,
        created_by="user:fde",
        claim_kind=ClaimKind.INTERPRETATION,
        subject_id="entity:missing",
        predicate_id="world://semantic/relation/means",
        object_value="Unsupported",
    )

    with pytest.raises(WorldProposalError, match="dangling"):
        service.propose(
            WorldChangeSet(
                proposal_id="proposal:dangling",
                workspace_id=WORKSPACE,
                proposed_by="user:fde",
                proposed_at=NOW,
                records=(dangling,),
                rationale="Invalid fixture.",
            )
        )


def test_state_read_applies_context_and_half_open_valid_time() -> None:
    service = world_service()
    brand = entity()
    state = WorldState(
        id="state:biotic-positioning",
        type_id="world://ontology/brand-world/type/PositioningState",
        workspace_id=WORKSPACE,
        module_id="world://ontology/module/brand-world/identity",
        created_at=NOW,
        created_by="user:fde",
        context_refs=("context:us-web",),
        valid_time=TemporalInterval(
            from_time=NOW,
            to_time=NOW + timedelta(days=1),
        ),
        subject_ids=(brand.id,),
        state_value="Active",
        state_schema_id="world://ontology/brand-world/state-schema/positioning",
    )
    change_set = WorldChangeSet(
        proposal_id="proposal:state",
        workspace_id=WORKSPACE,
        proposed_by="user:fde",
        proposed_at=NOW,
        records=(brand, state),
        rationale="Persist the bounded positioning state.",
    )
    service.propose(change_set)
    service.approve(change_set.proposal_id, approval(), accepted_at=NOW)

    assert service.get_state(
        brand.id,
        workspace_id=WORKSPACE,
        context_refs=("context:us-web",),
        valid_at=NOW + timedelta(hours=1),
    ) == (service.get(state.id, workspace_id=WORKSPACE),)
    assert (
        service.get_state(
            brand.id,
            workspace_id=WORKSPACE,
            valid_at=NOW + timedelta(days=1),
        )
        == ()
    )


def test_merge_requires_explicit_conflict_resolution_and_remains_proposed() -> None:
    service = world_service()
    for branch_id, definition in (("main", "Main definition"), ("research", "Research definition")):
        scoped_entity = entity().model_copy(
            update={"branch_id": branch_id, "definition": definition}
        )
        scoped_proposal = proposal().model_copy(
            update={
                "proposal_id": f"proposal:{branch_id}",
                "branch_id": branch_id,
                "records": (scoped_entity,),
            }
        )
        service.propose(scoped_proposal)
        service.approve(
            scoped_proposal.proposal_id,
            scoped_approval(branch_id, f"decision:{branch_id}"),
            accepted_at=NOW,
        )

    arguments = {
        "workspace_id": WORKSPACE,
        "source_branch_id": "research",
        "target_branch_id": "main",
        "proposal_id": "proposal:merge-research",
        "proposed_by": "user:fde",
        "proposed_at": NOW + timedelta(hours=1),
        "rationale": "Bring the reviewed research definition to main.",
    }
    with pytest.raises(WorldProposalError, match="explicit resolutions"):
        service.merge(**arguments)

    merged = service.merge(
        **arguments,
        resolutions=(
            BranchConflictResolution(
                record_id="entity:biotic",
                choice=MergeChoice.USE_SOURCE,
                rationale="Research wording was reviewed.",
            ),
        ),
    )

    assert merged.status.value == "proposed"
    assert merged.records[0].branch_id == "main"
    assert merged.records[0].definition == "Research definition"
