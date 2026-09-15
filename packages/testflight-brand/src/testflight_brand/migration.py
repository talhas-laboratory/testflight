"""Deterministic v1/v2-to-v3 migration accounting.

The ledger records a disposition for every legacy record before a v3 cutover. It does not infer a
semantic mapping, mutate a legacy source, or make a record writable.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class LegacyDisposition(StrEnum):
    MIGRATED = "migrated"
    ARCHIVED_ONLY = "archived_only"
    QUARANTINED = "quarantined"
    REJECTED = "rejected"


class LegacyRecordDisposition(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    legacy_id: str = Field(min_length=1)
    legacy_version: str = Field(min_length=1)
    disposition: LegacyDisposition
    migration_rule_id: str = Field(min_length=1)
    input_hash: str = Field(min_length=1)
    output_hash: str | None = None
    target_ids: tuple[str, ...] = ()
    information_loss: tuple[str, ...] = ()
    rationale: str = Field(min_length=1)
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None

    @model_validator(mode="after")
    def require_complete_disposition(self) -> LegacyRecordDisposition:
        if self.disposition is LegacyDisposition.MIGRATED:
            if not self.target_ids or not self.output_hash:
                raise ValueError("migrated legacy records require target_ids and output_hash")
        elif self.target_ids or self.output_hash:
            raise ValueError("only migrated legacy records may carry target IDs or output hashes")
        if self.disposition is LegacyDisposition.QUARANTINED and not self.reviewed_by:
            raise ValueError("quarantined legacy records require a named reviewer")
        return self


class LegacyMigrationLedger(BaseModel):
    """A complete, append-only disposition inventory for one legacy snapshot."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    ledger_id: str = Field(min_length=1)
    workspace_id: str = Field(min_length=1)
    snapshot_hash: str = Field(min_length=1)
    generated_at: datetime
    entries: tuple[LegacyRecordDisposition, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def require_unique_legacy_ids(self) -> LegacyMigrationLedger:
        legacy_ids = [entry.legacy_id for entry in self.entries]
        if len(legacy_ids) != len(set(legacy_ids)):
            raise ValueError("legacy migration ledger contains duplicate legacy IDs")
        return self

    def covers(self, legacy_ids: tuple[str, ...]) -> bool:
        """Return whether every supplied legacy ID has exactly one disposition."""

        return {entry.legacy_id for entry in self.entries} == set(legacy_ids)


__all__ = ["LegacyDisposition", "LegacyMigrationLedger", "LegacyRecordDisposition"]
