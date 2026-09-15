"""Canonical World transitions and reads over a provider-neutral repository."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any

from testflight_semantic import (
    AuthorityGrant,
    Capability,
    WorldClaim,
    WorldDecision,
    WorldEvent,
    WorldEvidence,
    WorldLifecycle,
    WorldRecordType,
    WorldRelation,
    WorldSource,
    WorldState,
)

from .models import (
    ApprovalReceipt,
    BranchConflictResolution,
    DiffOperation,
    MergeChoice,
    ProjectionJobStatus,
    ProposalStatus,
    WorldChangeSet,
    WorldEvidenceBundle,
    WorldFieldChange,
    WorldHistoryEntry,
    WorldProjectionJob,
    WorldProposalError,
    WorldRecordDiff,
    WorldRecordRef,
    WorldReview,
    WorldSearchHit,
    WorldSnapshot,
    validate_approval_decision,
)
from .ports import AuthorityGrantResolver, WorldRepository
from .snapshot_identity import snapshot_leaves, snapshot_root


class InMemoryAuthorityGrantResolver:
    """Exact, immutable grant resolver for tests and local composition."""

    def __init__(self, grants: Iterable[AuthorityGrant] = ()) -> None:
        grant_list = tuple(grants)
        self._grants = {grant.grant_id: grant for grant in grant_list}
        if len(self._grants) != len(grant_list):
            raise WorldProposalError("authority grant IDs must be unique")

    def resolve(self, grant_id: str) -> AuthorityGrant | None:
        return self._grants.get(grant_id)


class InMemoryWorldRepository:
    """Deterministic reference repository; production persistence belongs in an adapter."""

    def __init__(self) -> None:
        self._proposals: dict[str, WorldChangeSet] = {}
        self._history: dict[tuple[str, str, str], list[WorldHistoryEntry]] = {}
        self._reviews: dict[str, list[WorldReview]] = {}
        self._projection_jobs: dict[str, WorldProjectionJob] = {}

    def put_proposal(self, change_set: WorldChangeSet) -> None:
        if change_set.proposal_id in self._proposals:
            raise WorldProposalError(f"proposal already exists: {change_set.proposal_id}")
        self._proposals[change_set.proposal_id] = change_set

    def get_proposal(self, proposal_id: str) -> WorldChangeSet | None:
        return self._proposals.get(proposal_id)

    def replace_proposal(self, change_set: WorldChangeSet) -> None:
        if change_set.proposal_id not in self._proposals:
            raise WorldProposalError(f"unknown proposal: {change_set.proposal_id}")
        self._proposals[change_set.proposal_id] = change_set

    def append_review(self, review: WorldReview) -> None:
        if any(
            item.review_id == review.review_id for item in self._reviews.get(review.proposal_id, ())
        ):
            raise WorldProposalError(f"review already exists: {review.review_id}")
        self._reviews.setdefault(review.proposal_id, []).append(review)

    def reviews(self, proposal_id: str) -> tuple[WorldReview, ...]:
        return tuple(
            sorted(
                self._reviews.get(proposal_id, ()),
                key=lambda item: (item.reviewed_at, item.review_id),
            )
        )

    def append_history(self, entry: WorldHistoryEntry) -> None:
        key = _history_key(entry)
        entries = self._history.setdefault(key, [])
        _validate_next_history_entry(entries, entry)
        entries.append(entry)

    def accept_proposal(
        self,
        change_set: WorldChangeSet,
        history_entries: tuple[WorldHistoryEntry, ...],
        projection_job: WorldProjectionJob,
    ) -> None:
        """Atomically validate then apply a complete accepted change set."""

        if change_set.proposal_id not in self._proposals:
            raise WorldProposalError(f"unknown proposal: {change_set.proposal_id}")
        staged: dict[tuple[str, str, str], list[WorldHistoryEntry]] = {}
        for entry in history_entries:
            key = _history_key(entry)
            entries = staged.setdefault(key, list(self._history.get(key, ())))
            _validate_next_history_entry(entries, entry)
            entries.append(entry)
        self._proposals[change_set.proposal_id] = change_set
        for key, entries in staged.items():
            self._history[key] = entries
        if projection_job.job_id in self._projection_jobs:
            raise WorldProposalError(f"projection job already exists: {projection_job.job_id}")
        self._projection_jobs[projection_job.job_id] = projection_job

    def claim_projection_job(self) -> WorldProjectionJob | None:
        pending = sorted(
            (job for job in self._projection_jobs.values() if job.status.value == "pending"),
            key=lambda job: (job.created_at, job.job_id),
        )
        if not pending:
            return None
        job = pending[0].model_copy(
            update={
                "status": ProjectionJobStatus.RUNNING,
                "attempts": pending[0].attempts + 1,
                "updated_at": datetime.now(UTC),
            }
        )
        self._projection_jobs[job.job_id] = job
        return job

    def complete_projection_job(
        self, job_id: str, *, error: str | None = None
    ) -> WorldProjectionJob:
        try:
            job = self._projection_jobs[job_id]
        except KeyError as failure:
            raise WorldProposalError(f"unknown projection job: {job_id}") from failure
        if job.status.value != "running":
            raise WorldProposalError(f"projection job is not running: {job_id}")
        completed = job.model_copy(
            update={
                "status": ProjectionJobStatus.FAILED if error else ProjectionJobStatus.SUCCEEDED,
                "last_error": error,
                "updated_at": datetime.now(UTC),
            }
        )
        self._projection_jobs[job_id] = completed
        return completed

    def active_projection_job(self, workspace_id: str, branch_id: str) -> WorldProjectionJob | None:
        candidates = [
            job
            for job in self._projection_jobs.values()
            if job.workspace_id == workspace_id
            and job.branch_id == branch_id
            and job.status.value == "succeeded"
        ]
        return max(candidates, key=lambda item: (item.created_at, item.job_id), default=None)

    def history(
        self,
        record_id: str,
        *,
        workspace_id: str | None = None,
        branch_id: str | None = None,
        recorded_at: datetime | None = None,
    ) -> tuple[WorldHistoryEntry, ...]:
        cutoff = _utc(recorded_at) if recorded_at else None
        entries = (
            item
            for (workspace, branch, candidate_id), history in self._history.items()
            if candidate_id == record_id
            and (workspace_id is None or workspace == workspace_id)
            and (branch_id is None or branch == branch_id)
            for item in history
            if cutoff is None or _utc(item.recorded_at) <= cutoff
        )
        return tuple(
            sorted(
                entries,
                key=lambda item: (
                    item.record.workspace_id,
                    item.record.branch_id,
                    item.record_version,
                    item.recorded_at,
                ),
            )
        )

    def snapshot(
        self,
        workspace_id: str,
        branch_id: str,
        *,
        recorded_at: datetime | None = None,
    ) -> tuple[WorldHistoryEntry, ...]:
        cutoff = _utc(recorded_at) if recorded_at else None
        current: list[WorldHistoryEntry] = []
        for (workspace, branch, _record_id), entries in self._history.items():
            if workspace != workspace_id or branch != branch_id:
                continue
            eligible = [
                item for item in entries if cutoff is None or _utc(item.recorded_at) <= cutoff
            ]
            if eligible and eligible[-1].record.lifecycle_status is WorldLifecycle.ACCEPTED:
                current.append(eligible[-1])
        return tuple(sorted(current, key=lambda item: (item.record.kind, item.record_id)))


class WorldService:
    """Human-governed World writes plus deterministic accepted-record reads."""

    def __init__(
        self,
        repository: WorldRepository,
        authority_grants: AuthorityGrantResolver | None = None,
    ) -> None:
        self._repository = repository
        self._authority_grants = authority_grants

    def propose(self, change_set: WorldChangeSet) -> WorldChangeSet:
        if change_set.status is not ProposalStatus.PROPOSED:
            raise WorldProposalError("only proposed change sets may enter the proposal operation")
        if any(
            record.lifecycle_status is not WorldLifecycle.PROPOSED for record in change_set.records
        ):
            raise WorldProposalError("new change-set records must have proposed lifecycle status")
        self._validate_expected_versions(change_set)
        self._validate_references(change_set)
        self._repository.put_proposal(change_set)
        return change_set

    def review(self, review: WorldReview) -> WorldReview:
        change_set = self._require_proposed(review.proposal_id)
        if (
            review.workspace_id != change_set.workspace_id
            or review.branch_id != change_set.branch_id
        ):
            raise WorldProposalError("review scope does not match proposal scope")
        self._repository.append_review(review)
        return review

    def reviews(self, proposal_id: str) -> tuple[WorldReview, ...]:
        return self._repository.reviews(proposal_id)

    def approve(
        self,
        proposal_id: str,
        decision: WorldDecision,
        *,
        accepted_at: datetime,
    ) -> ApprovalReceipt:
        change_set = self._require_proposed(proposal_id)
        validate_approval_decision(decision, change_set)
        _utc(accepted_at)
        self._validate_expected_versions(change_set)
        self._validate_references(change_set)
        authority_capability = self._authorize_approval(
            decision, change_set, accepted_at=accepted_at
        )

        accepted_records: list[WorldRecordType] = []
        for record in change_set.records:
            current = self.get(
                record.id,
                workspace_id=record.workspace_id,
                branch_id=record.branch_id,
            )
            update: dict[str, Any] = {
                "record_version": record.record_version + 1,
                "lifecycle_status": WorldLifecycle.ACCEPTED,
                "authority_ref": decision.authority_ref,
            }
            if current is not None:
                update["supersedes_ref"] = f"{current.id}@{current.record_version}"
            accepted_records.append(record.model_copy(update=update))

        accepted_change_set = change_set.model_copy(
            update={"status": ProposalStatus.ACCEPTED, "review_decision_id": decision.id}
        )
        history_entries = tuple(
            WorldHistoryEntry(
                record_id=record.id,
                record_version=record.record_version,
                proposal_id=proposal_id,
                recorded_at=accepted_at,
                record=record,
            )
            for record in accepted_records
        )
        source_revision = _projection_revision(history_entries)
        prior = {
            record.id: record
            for record in self.snapshot(change_set.workspace_id, change_set.branch_id).records
        }
        prior.update({record.id: record for record in accepted_records})
        target_records = tuple(prior.values())
        target_leaves = snapshot_leaves(target_records)
        target_snapshot_root = snapshot_root(
            workspace_id=change_set.workspace_id,
            branch_id=change_set.branch_id,
            lifecycle_scope=("accepted",),
            leaves=target_leaves,
        )
        projection_job = WorldProjectionJob(
            job_id=f"world-projection:{source_revision}",
            workspace_id=change_set.workspace_id,
            branch_id=change_set.branch_id,
            source_proposal_id=proposal_id,
            source_revision=source_revision,
            source_snapshot_root=target_snapshot_root,
            created_at=accepted_at,
            updated_at=accepted_at,
        )
        self._repository.accept_proposal(accepted_change_set, history_entries, projection_job)
        return ApprovalReceipt(
            proposal_id=proposal_id,
            decision_id=decision.id,
            authority_grant_id=decision.authority_ref,
            authority_capability=authority_capability,
            accepted_record_ids=tuple(record.id for record in accepted_records),
            accepted_at=accepted_at,
        )

    def reject(self, proposal_id: str, rationale: str) -> WorldChangeSet:
        change_set = self._require_proposed(proposal_id)
        if not rationale.strip():
            raise WorldProposalError("rejection requires a rationale")
        rejected = change_set.model_copy(
            update={"status": ProposalStatus.REJECTED, "rejection_rationale": rationale}
        )
        self._repository.replace_proposal(rejected)
        return rejected

    def supersede(
        self,
        record_id: str,
        replacement: WorldRecordType,
        *,
        proposal_id: str,
        proposed_by: str,
        proposed_at: datetime,
        rationale: str,
    ) -> WorldChangeSet:
        """Create a reviewable replacement proposal; approval remains a separate operation."""

        current = self.get(
            record_id,
            workspace_id=replacement.workspace_id,
            branch_id=replacement.branch_id,
        )
        if current is None:
            raise WorldProposalError(f"cannot supersede unknown accepted record: {record_id}")
        if replacement.id != record_id:
            raise WorldProposalError("a replacement must preserve the superseded record identity")
        candidate = replacement.model_copy(
            update={
                "record_version": current.record_version,
                "lifecycle_status": WorldLifecycle.PROPOSED,
                "authority_ref": None,
                "supersedes_ref": f"{current.id}@{current.record_version}",
            }
        )
        return self.propose(
            WorldChangeSet(
                proposal_id=proposal_id,
                workspace_id=current.workspace_id,
                branch_id=current.branch_id,
                proposed_by=proposed_by,
                proposed_at=proposed_at,
                records=(candidate,),
                rationale=rationale,
            )
        )

    def merge(
        self,
        *,
        workspace_id: str,
        source_branch_id: str,
        target_branch_id: str,
        proposal_id: str,
        proposed_by: str,
        proposed_at: datetime,
        rationale: str,
        resolutions: tuple[BranchConflictResolution, ...] = (),
    ) -> WorldChangeSet:
        """Compile a branch merge into a proposal without bypassing human approval."""

        if source_branch_id == target_branch_id:
            raise WorldProposalError("source and target branches must differ")
        resolution_by_id = {item.record_id: item for item in resolutions}
        if len(resolution_by_id) != len(resolutions):
            raise WorldProposalError("merge conflict resolutions must have unique record IDs")
        source = {
            record.id: record for record in self.snapshot(workspace_id, source_branch_id).records
        }
        target = {
            record.id: record for record in self.snapshot(workspace_id, target_branch_id).records
        }
        if not source:
            raise WorldProposalError("source branch has no accepted records")

        candidates: list[WorldRecordType] = []
        unresolved: list[str] = []
        for record_id, source_record in sorted(source.items()):
            target_record = target.get(record_id)
            if target_record is not None and _semantic_payload(target_record) != _semantic_payload(
                source_record
            ):
                resolution = resolution_by_id.get(record_id)
                if resolution is None:
                    unresolved.append(record_id)
                    continue
                if resolution.choice is MergeChoice.KEEP_TARGET:
                    continue
            elif target_record is not None:
                continue
            candidate_version = target_record.record_version if target_record else 1
            candidates.append(
                source_record.model_copy(
                    update={
                        "branch_id": target_branch_id,
                        "record_version": candidate_version,
                        "lifecycle_status": WorldLifecycle.PROPOSED,
                        "authority_ref": None,
                        "supersedes_ref": (
                            f"{target_record.id}@{target_record.record_version}"
                            if target_record
                            else None
                        ),
                    }
                )
            )
        if unresolved:
            raise WorldProposalError(
                "merge requires explicit resolutions for conflicting records: "
                + ", ".join(unresolved)
            )
        unused = sorted(set(resolution_by_id) - set(source))
        if unused:
            raise WorldProposalError(
                "merge resolutions reference unknown source records: " + ", ".join(unused)
            )
        if not candidates:
            raise WorldProposalError("merge produces no target changes")
        return self.propose(
            WorldChangeSet(
                proposal_id=proposal_id,
                workspace_id=workspace_id,
                branch_id=target_branch_id,
                proposed_by=proposed_by,
                proposed_at=proposed_at,
                records=tuple(candidates),
                rationale=rationale,
            )
        )

    def get(
        self,
        record_id: str,
        *,
        workspace_id: str,
        branch_id: str = "main",
        record_version: int | None = None,
        recorded_at: datetime | None = None,
    ) -> WorldRecordType | None:
        entries = self._repository.history(
            record_id,
            workspace_id=workspace_id,
            branch_id=branch_id,
            recorded_at=recorded_at,
        )
        if record_version is not None:
            return next(
                (item.record for item in entries if item.record_version == record_version), None
            )
        if not entries:
            return None
        record = entries[-1].record
        return record if record.lifecycle_status is WorldLifecycle.ACCEPTED else None

    def get_state(
        self,
        entity_id: str,
        *,
        workspace_id: str,
        branch_id: str = "main",
        context_refs: tuple[str, ...] = (),
        valid_at: datetime | None = None,
        recorded_at: datetime | None = None,
    ) -> tuple[WorldState, ...]:
        """Read states by subject, applicability context, valid time, and recorded time."""

        valid_instant = _utc(valid_at) if valid_at is not None else None
        required_contexts = set(context_refs)
        states = (
            record
            for record in self.snapshot(workspace_id, branch_id, recorded_at=recorded_at).records
            if isinstance(record, WorldState)
            and entity_id in record.subject_ids
            and required_contexts.issubset(record.context_refs)
            and _valid_at(record, valid_instant)
        )
        return tuple(sorted(states, key=lambda item: (item.state_schema_id, item.id)))

    def snapshot(
        self,
        workspace_id: str,
        branch_id: str = "main",
        *,
        recorded_at: datetime | None = None,
    ) -> WorldSnapshot:
        entries = self._repository.snapshot(
            workspace_id,
            branch_id,
            recorded_at=recorded_at,
        )
        records = tuple(item.record for item in entries)
        leaves = snapshot_leaves(records)
        return WorldSnapshot(
            workspace_id=workspace_id,
            branch_id=branch_id,
            recorded_at=recorded_at,
            records=records,
            leaves=leaves,
            snapshot_root=snapshot_root(
                workspace_id=workspace_id,
                branch_id=branch_id,
                lifecycle_scope=("accepted",),
                leaves=leaves,
            ),
        )

    def history(
        self,
        record_id: str,
        *,
        workspace_id: str,
        branch_id: str = "main",
        recorded_at: datetime | None = None,
    ) -> tuple[WorldHistoryEntry, ...]:
        return self._repository.history(
            record_id,
            workspace_id=workspace_id,
            branch_id=branch_id,
            recorded_at=recorded_at,
        )

    def diff(self, left: WorldRecordRef, right: WorldRecordRef) -> WorldRecordDiff:
        left_record = self._require_ref(left)
        right_record = self._require_ref(right)
        changes = tuple(
            _diff_values(left_record.model_dump(mode="json"), right_record.model_dump(mode="json"))
        )
        return WorldRecordDiff(
            left=_resolved_ref(left, left_record),
            right=_resolved_ref(right, right_record),
            changes=changes,
        )

    def evidence(
        self,
        record_id: str,
        *,
        workspace_id: str,
        branch_id: str = "main",
        recorded_at: datetime | None = None,
    ) -> WorldEvidenceBundle:
        record = self.get(
            record_id,
            workspace_id=workspace_id,
            branch_id=branch_id,
            recorded_at=recorded_at,
        )
        if record is None:
            raise WorldProposalError(f"unknown accepted record: {record_id}")
        evidence_ids = _evidence_ids(record)
        evidence: list[WorldEvidence] = []
        unresolved_evidence: list[str] = []
        for evidence_id in evidence_ids:
            candidate = self.get(
                evidence_id,
                workspace_id=workspace_id,
                branch_id=branch_id,
                recorded_at=recorded_at,
            )
            if isinstance(candidate, WorldEvidence):
                evidence.append(candidate)
            else:
                unresolved_evidence.append(evidence_id)
        sources: list[WorldSource] = []
        unresolved_sources: list[str] = []
        for item in evidence:
            candidate = self.get(
                item.source_id,
                workspace_id=workspace_id,
                branch_id=branch_id,
                recorded_at=recorded_at,
            )
            if isinstance(candidate, WorldSource):
                sources.append(candidate)
            else:
                unresolved_sources.append(item.source_id)
        return WorldEvidenceBundle(
            target=WorldRecordRef(
                workspace_id=workspace_id,
                branch_id=branch_id,
                record_id=record_id,
                record_version=record.record_version,
            ),
            evidence=tuple(sorted(evidence, key=lambda item: item.id)),
            sources=tuple(
                sorted({item.id: item for item in sources}.values(), key=lambda item: item.id)
            ),
            unresolved_evidence_ids=tuple(sorted(set(unresolved_evidence))),
            unresolved_source_ids=tuple(sorted(set(unresolved_sources))),
        )

    def related(
        self,
        record_id: str,
        *,
        workspace_id: str,
        branch_id: str = "main",
        relation_type_ids: tuple[str, ...] = (),
        role_ids: tuple[str, ...] = (),
        recorded_at: datetime | None = None,
    ) -> tuple[WorldRelation, ...]:
        relations = (
            record
            for record in self.snapshot(workspace_id, branch_id, recorded_at=recorded_at).records
            if isinstance(record, WorldRelation)
            and any(
                participant.record_id == record_id
                and (not role_ids or participant.role_id in role_ids)
                for participant in record.participants
            )
            and (not relation_type_ids or record.relation_type_id in relation_type_ids)
        )
        return tuple(sorted(relations, key=lambda item: item.id))

    def dependencies(
        self,
        record_id: str,
        *,
        workspace_id: str,
        dependency_relation_type_ids: tuple[str, ...],
        branch_id: str = "main",
        role_ids: tuple[str, ...] = (),
        recorded_at: datetime | None = None,
    ) -> tuple[WorldRelation, ...]:
        """Resolve dependencies using caller-declared relation types, never name heuristics."""

        if not dependency_relation_type_ids:
            raise WorldProposalError("dependency reads require declared dependency relation types")
        return self.related(
            record_id,
            workspace_id=workspace_id,
            branch_id=branch_id,
            relation_type_ids=dependency_relation_type_ids,
            role_ids=role_ids,
            recorded_at=recorded_at,
        )

    def search(
        self,
        query: str,
        *,
        workspace_id: str,
        branch_id: str = "main",
        semantic_kinds: tuple[str, ...] = (),
        module_ids: tuple[str, ...] = (),
        recorded_at: datetime | None = None,
        limit: int = 20,
    ) -> tuple[WorldSearchHit, ...]:
        """Bounded deterministic lexical retrieval; it performs no interpretation."""

        terms = tuple(dict.fromkeys(term.casefold() for term in query.split() if term.strip()))
        if not terms:
            raise WorldProposalError("search query must contain at least one term")
        if limit < 1 or limit > 100:
            raise WorldProposalError("search limit must be between 1 and 100")
        hits: list[WorldSearchHit] = []
        for record in self.snapshot(workspace_id, branch_id, recorded_at=recorded_at).records:
            if semantic_kinds and record.kind not in semantic_kinds:
                continue
            if module_ids and record.module_id not in module_ids:
                continue
            fields = _searchable_fields(record)
            matched = tuple(
                sorted(
                    field_name
                    for field_name, value in fields.items()
                    if any(term in value.casefold() for term in terms)
                )
            )
            score = sum(value.casefold().count(term) for value in fields.values() for term in terms)
            if matched and score:
                hits.append(WorldSearchHit(record=record, matched_fields=matched, score=score))
        return tuple(sorted(hits, key=lambda hit: (-hit.score, hit.record.id))[:limit])

    def _require_proposed(self, proposal_id: str) -> WorldChangeSet:
        change_set = self._repository.get_proposal(proposal_id)
        if change_set is None:
            raise WorldProposalError(f"unknown proposal: {proposal_id}")
        if change_set.status is not ProposalStatus.PROPOSED:
            raise WorldProposalError(f"proposal is not pending review: {proposal_id}")
        return change_set

    def _require_ref(self, reference: WorldRecordRef) -> WorldRecordType:
        record = self.get(
            reference.record_id,
            workspace_id=reference.workspace_id,
            branch_id=reference.branch_id,
            record_version=reference.record_version,
        )
        if record is None:
            raise WorldProposalError(f"unknown accepted record reference: {reference.model_dump()}")
        return record

    def _validate_expected_versions(self, change_set: WorldChangeSet) -> None:
        for record in change_set.records:
            current = self.get(
                record.id,
                workspace_id=record.workspace_id,
                branch_id=record.branch_id,
            )
            expected = current.record_version if current is not None else 1
            if record.record_version != expected:
                raise WorldProposalError(
                    f"unexpected record version for {record.id}: "
                    f"expected {expected}, got {record.record_version}"
                )

    def _validate_references(self, change_set: WorldChangeSet) -> None:
        available = {
            record.id
            for record in self.snapshot(change_set.workspace_id, change_set.branch_id).records
        } | {record.id for record in change_set.records}
        dangling: set[str] = set()
        for record in change_set.records:
            dangling.update(
                reference
                for reference in _canonical_references(record)
                if reference not in available
            )
        if dangling:
            raise WorldProposalError(
                "change set contains dangling canonical references: " + ", ".join(sorted(dangling))
            )

    def _authorize_approval(
        self,
        decision: WorldDecision,
        change_set: WorldChangeSet,
        *,
        accepted_at: datetime,
    ) -> Capability:
        if self._authority_grants is None:
            raise WorldProposalError("approval requires an AuthorityGrantResolver")
        grant_id = decision.authority_ref
        if grant_id is None:
            raise WorldProposalError("approval decision requires authority_ref")
        grant = self._authority_grants.resolve(grant_id)
        if grant is None or grant.grant_id != grant_id:
            raise WorldProposalError(f"unknown authority grant: {grant_id}")
        if grant.principal_id != decision.created_by:
            raise WorldProposalError(
                "authority grant principal does not match the approval decision actor"
            )
        for capability in (Capability.PROMOTE, Capability.ACCEPT):
            if all(
                _grant_allows_record(
                    grant,
                    capability,
                    record,
                    accepted_at=accepted_at,
                )
                for record in change_set.records
            ):
                return capability
        raise WorldProposalError(
            "authority grant does not allow accept or promote for every affected record, "
            "context, and effective time"
        )


def _history_key(entry: WorldHistoryEntry) -> tuple[str, str, str]:
    return (entry.record.workspace_id, entry.record.branch_id, entry.record_id)


def _validate_next_history_entry(
    entries: list[WorldHistoryEntry], entry: WorldHistoryEntry
) -> None:
    if entries and entry.record_version != entries[-1].record_version + 1:
        raise WorldProposalError("record history version must increase by exactly one")
    if not entries and entry.record_version != 2:
        raise WorldProposalError("the first accepted version must follow proposed version 1")


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise WorldProposalError("recorded time must be timezone-aware")
    return value.astimezone(UTC)


def _resolved_ref(reference: WorldRecordRef, record: WorldRecordType) -> WorldRecordRef:
    return reference.model_copy(update={"record_version": record.record_version})


JsonComparable = Any


def _semantic_payload(record: WorldRecordType) -> dict[str, JsonComparable]:
    ignored = {
        "branch_id",
        "record_version",
        "lifecycle_status",
        "authority_ref",
        "supersedes_ref",
    }
    return {
        key: value for key, value in record.model_dump(mode="json").items() if key not in ignored
    }


def _diff_values(
    left: JsonComparable, right: JsonComparable, path: str = ""
) -> Iterable[WorldFieldChange]:
    if isinstance(left, dict) and isinstance(right, dict):
        for key in sorted(set(left) | set(right)):
            child_path = f"{path}/{key.replace('~', '~0').replace('/', '~1')}"
            if key not in left:
                yield WorldFieldChange(
                    path=child_path, operation=DiffOperation.ADDED, after=right[key]
                )
            elif key not in right:
                yield WorldFieldChange(
                    path=child_path, operation=DiffOperation.REMOVED, before=left[key]
                )
            else:
                yield from _diff_values(left[key], right[key], child_path)
    elif left != right:
        yield WorldFieldChange(
            path=path or "/", operation=DiffOperation.CHANGED, before=left, after=right
        )


def _evidence_ids(record: WorldRecordType) -> tuple[str, ...]:
    if isinstance(record, WorldClaim):
        return tuple(dict.fromkeys((*record.evidence_ids, *record.opposing_evidence_ids)))
    if isinstance(record, (WorldRelation, WorldEvent, WorldDecision)):
        return record.evidence_ids
    if isinstance(record, WorldEvidence):
        return (record.id,)
    return ()


def _canonical_references(record: WorldRecordType) -> tuple[str, ...]:
    if isinstance(record, WorldState):
        return (*record.subject_ids, *record.described_by_claim_ids)
    if isinstance(record, WorldEvent):
        return (*(item.entity_id for item in record.participants), *record.evidence_ids)
    if isinstance(record, WorldRelation):
        return (*(item.record_id for item in record.participants), *record.evidence_ids)
    if isinstance(record, WorldClaim):
        return (
            record.subject_id,
            *((record.object_id,) if record.object_id else ()),
            *((record.perspective_id,) if record.perspective_id else ()),
            *record.evidence_ids,
            *record.opposing_evidence_ids,
            *record.contradiction_ids,
        )
    if isinstance(record, WorldEvidence):
        return (record.source_id,)
    if isinstance(record, WorldDecision):
        return (*record.evidence_ids, *record.affected_record_ids)
    return ()


def _searchable_fields(record: WorldRecordType) -> dict[str, str]:
    fields: dict[str, str] = {}

    def collect(value: JsonComparable, path: str) -> None:
        if isinstance(value, dict):
            for name, child in sorted(value.items()):
                collect(child, f"{path}.{name}" if path else name)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                collect(child, f"{path}[{index}]")
        elif value is not None:
            fields[path] = str(value)

    collect(record.model_dump(mode="json"), "")
    return fields


def _valid_at(record: WorldState, instant: datetime | None) -> bool:
    if instant is None or record.valid_time is None:
        return True
    start = record.valid_time.from_time
    end = record.valid_time.to_time
    return (start is None or start <= instant) and (end is None or instant < end)


def _grant_allows_record(
    grant: AuthorityGrant,
    capability: Capability,
    record: WorldRecordType,
    *,
    accepted_at: datetime,
) -> bool:
    contexts: tuple[str | None, ...] = record.context_refs or (None,)
    return all(
        grant.allows(
            capability,
            record.id,
            context_id=context_id,
            at_time=accepted_at,
        )
        for context_id in contexts
    )


def _projection_revision(entries: tuple[WorldHistoryEntry, ...]) -> str:
    """Stable identity for the exact accepted snapshot that triggered a rebuild."""

    payload = [
        {
            "id": entry.record_id,
            "version": entry.record_version,
            "recorded_at": entry.recorded_at.astimezone(UTC).isoformat(),
        }
        for entry in sorted(entries, key=lambda item: item.record_id)
    ]
    digest = hashlib.sha256(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    ).hexdigest()[:24]
    return f"{entries[0].record.workspace_id}:{entries[0].record.branch_id}:{digest}"


__all__ = ["InMemoryAuthorityGrantResolver", "InMemoryWorldRepository", "WorldService"]
