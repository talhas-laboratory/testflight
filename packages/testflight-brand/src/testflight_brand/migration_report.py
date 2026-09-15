"""Deterministic integrity report for a proposed Brand World migration."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from testflight_semantic import (
    Context,
    WorldClaim,
    WorldDecision,
    WorldEvent,
    WorldEvidence,
    WorldLifecycle,
    WorldRelation,
    WorldSource,
    WorldState,
)
from testflight_world import WorldChangeSet

from .migration import LegacyMigrationLedger


class MigrationIntegrityReport(BaseModel):
    """Machine-readable migration gate with independently inspectable failure classes."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    record_count: int
    context_count: int
    legacy_record_count: int
    disposition_count: int
    disposition_coverage: float
    evidence_reference_count: int
    resolved_evidence_reference_count: int
    evidence_coverage: float
    dangling_record_refs: tuple[str, ...]
    dangling_evidence_refs: tuple[str, ...]
    dangling_source_refs: tuple[str, ...]
    dangling_context_refs: tuple[str, ...]
    dangling_provenance_refs: tuple[str, ...]
    missing_information: tuple[str, ...]
    contradiction_ids: tuple[str, ...]
    relation_integrity_errors: tuple[str, ...]
    unsupported_promotion_ids: tuple[str, ...]
    ready_for_authority_review: bool


def assess_migration(
    change_set: WorldChangeSet,
    *,
    contexts: tuple[Context, ...] = (),
    ledger: LegacyMigrationLedger | None = None,
) -> MigrationIntegrityReport:
    """Assess canonical references, epistemic safety, and ledger completeness."""

    records = change_set.records
    by_id = {record.id: record for record in records}
    known = set(by_id)
    evidence = {record.id for record in records if isinstance(record, WorldEvidence)}
    sources = {record.id for record in records if isinstance(record, WorldSource)}
    context_ids = {context.context_id for context in contexts}
    record_refs: set[str] = set()
    evidence_refs: list[str] = []
    source_refs: set[str] = set()
    context_refs: set[str] = set()
    provenance_refs: set[str] = set()
    missing: set[str] = set()
    contradictions: set[str] = set()
    relation_errors: set[str] = set()
    unsupported_promotions: set[str] = set()

    for record in records:
        context_refs.update(record.context_refs)
        provenance_refs.update(record.provenance_refs)
        if record.lifecycle_status is not WorldLifecycle.PROPOSED:
            unsupported_promotions.add(record.id)

        if isinstance(record, WorldClaim):
            record_refs.add(record.subject_id)
            if record.object_id:
                record_refs.add(record.object_id)
            evidence_refs.extend(record.evidence_ids)
            evidence_refs.extend(record.opposing_evidence_ids)
            missing.update(record.limitations)
            contradictions.update(record.contradiction_ids)
            if record.predicate_id.endswith("/contradicts"):
                contradictions.add(record.id)
        elif isinstance(record, WorldRelation):
            participant_ids = tuple(item.record_id for item in record.participants)
            record_refs.update(participant_ids)
            evidence_refs.extend(record.evidence_ids)
            if len(participant_ids) != len(set(participant_ids)):
                relation_errors.add(f"{record.id}: duplicate participant records")
        elif isinstance(record, WorldState):
            record_refs.update(record.subject_ids)
            record_refs.update(record.described_by_claim_ids)
            for claim_id in record.described_by_claim_ids:
                if claim_id in by_id and not isinstance(by_id[claim_id], WorldClaim):
                    relation_errors.add(f"{record.id}: described_by is not a claim: {claim_id}")
        elif isinstance(record, WorldEvent):
            record_refs.update(item.entity_id for item in record.participants)
            evidence_refs.extend(record.evidence_ids)
        elif isinstance(record, WorldEvidence):
            source_refs.add(record.source_id)
        elif isinstance(record, WorldDecision):
            record_refs.update(record.affected_record_ids)
            evidence_refs.extend(record.evidence_ids)

    for context in contexts:
        record_refs.update(
            item for item in (context.brand_id, context.offering_id, *context.audience_ids) if item
        )

    resolved_evidence = [item for item in evidence_refs if item in evidence]
    dangling_evidence = set(evidence_refs) - evidence
    dangling_records = (record_refs - known) - dangling_evidence
    dangling_provenance = provenance_refs - known
    dangling_contexts = context_refs - context_ids
    dangling_sources = source_refs - sources
    legacy_count = len(ledger.entries) if ledger else 0
    disposition_count = len({entry.legacy_id for entry in ledger.entries}) if ledger else 0
    disposition_coverage = disposition_count / legacy_count if legacy_count else 1.0
    evidence_coverage = len(resolved_evidence) / len(evidence_refs) if evidence_refs else 1.0
    ready = (
        ledger is not None
        and not any(
            (
                dangling_records,
                dangling_evidence,
                dangling_sources,
                dangling_contexts,
                dangling_provenance,
                relation_errors,
                unsupported_promotions,
            )
        )
        and disposition_coverage == 1.0
    )
    return MigrationIntegrityReport(
        record_count=len(records),
        context_count=len(contexts),
        legacy_record_count=legacy_count,
        disposition_count=disposition_count,
        disposition_coverage=disposition_coverage,
        evidence_reference_count=len(evidence_refs),
        resolved_evidence_reference_count=len(resolved_evidence),
        evidence_coverage=evidence_coverage,
        dangling_record_refs=tuple(sorted(dangling_records)),
        dangling_evidence_refs=tuple(sorted(dangling_evidence)),
        dangling_source_refs=tuple(sorted(dangling_sources)),
        dangling_context_refs=tuple(sorted(dangling_contexts)),
        dangling_provenance_refs=tuple(sorted(dangling_provenance)),
        missing_information=tuple(sorted(missing)),
        contradiction_ids=tuple(sorted(contradictions)),
        relation_integrity_errors=tuple(sorted(relation_errors)),
        unsupported_promotion_ids=tuple(sorted(unsupported_promotions)),
        ready_for_authority_review=ready,
    )


__all__ = ["MigrationIntegrityReport", "assess_migration"]
