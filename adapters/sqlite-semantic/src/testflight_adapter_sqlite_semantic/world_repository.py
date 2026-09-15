"""SQLite implementation of the provider-neutral Brand World v3 repository port."""

from __future__ import annotations

import sqlite3
import threading
from datetime import UTC, datetime
from pathlib import Path

from testflight_semantic import WorldLifecycle
from testflight_world import (
    ProjectionJobStatus,
    ProposalStatus,
    WorldChangeSet,
    WorldHistoryEntry,
    WorldProjectionJob,
    WorldProposalError,
    WorldRepositoryError,
    WorldReview,
)


class SQLiteWorldRepository:
    """Append-oriented v3 store with transactional, workspace-isolated change sets."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._connection = sqlite3.connect(path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._initialize()

    def close(self) -> None:
        with self._lock:
            self._connection.close()

    def __enter__(self) -> SQLiteWorldRepository:
        return self

    def __exit__(self, _type: object, _value: object, _traceback: object) -> None:
        self.close()

    def put_proposal(self, change_set: WorldChangeSet) -> None:
        with self._lock, self._connection:
            try:
                self._connection.execute(
                    """
                    INSERT INTO world_proposals
                        (proposal_id, workspace_id, branch_id, status, payload_json)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        change_set.proposal_id,
                        change_set.workspace_id,
                        change_set.branch_id,
                        change_set.status.value,
                        change_set.model_dump_json(),
                    ),
                )
            except sqlite3.IntegrityError as error:
                raise WorldProposalError(
                    f"proposal already exists: {change_set.proposal_id}"
                ) from error

    def get_proposal(self, proposal_id: str) -> WorldChangeSet | None:
        with self._lock:
            row = self._connection.execute(
                "SELECT payload_json FROM world_proposals WHERE proposal_id = ?", (proposal_id,)
            ).fetchone()
            return None if row is None else WorldChangeSet.model_validate_json(row["payload_json"])

    def replace_proposal(self, change_set: WorldChangeSet) -> None:
        with self._lock, self._connection:
            updated = self._connection.execute(
                """
                UPDATE world_proposals
                SET workspace_id = ?, branch_id = ?, status = ?, payload_json = ?
                WHERE proposal_id = ?
                """,
                (
                    change_set.workspace_id,
                    change_set.branch_id,
                    change_set.status.value,
                    change_set.model_dump_json(),
                    change_set.proposal_id,
                ),
            ).rowcount
            if updated != 1:
                raise WorldProposalError(f"unknown proposal: {change_set.proposal_id}")

    def append_review(self, review: WorldReview) -> None:
        with self._lock, self._connection:
            proposal = self._connection.execute(
                "SELECT workspace_id, branch_id FROM world_proposals WHERE proposal_id = ?",
                (review.proposal_id,),
            ).fetchone()
            if proposal is None:
                raise WorldProposalError(f"unknown proposal: {review.proposal_id}")
            if (
                proposal["workspace_id"] != review.workspace_id
                or proposal["branch_id"] != review.branch_id
            ):
                raise WorldProposalError("review scope does not match proposal scope")
            try:
                self._connection.execute(
                    """
                    INSERT INTO world_reviews
                        (review_id, proposal_id, reviewed_at, payload_json)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        review.review_id,
                        review.proposal_id,
                        _iso(review.reviewed_at),
                        review.model_dump_json(),
                    ),
                )
            except sqlite3.IntegrityError as error:
                raise WorldProposalError(f"review already exists: {review.review_id}") from error

    def reviews(self, proposal_id: str) -> tuple[WorldReview, ...]:
        with self._lock:
            rows = self._connection.execute(
                """
                SELECT payload_json FROM world_reviews
                WHERE proposal_id = ? ORDER BY reviewed_at, review_id
                """,
                (proposal_id,),
            ).fetchall()
            return tuple(WorldReview.model_validate_json(row["payload_json"]) for row in rows)

    def accept_proposal(
        self,
        change_set: WorldChangeSet,
        history_entries: tuple[WorldHistoryEntry, ...],
        projection_job: WorldProjectionJob,
    ) -> None:
        with self._lock:
            self._connection.execute("BEGIN IMMEDIATE")
            try:
                row = self._connection.execute(
                    "SELECT status FROM world_proposals WHERE proposal_id = ?",
                    (change_set.proposal_id,),
                ).fetchone()
                if row is None:
                    raise WorldProposalError(f"unknown proposal: {change_set.proposal_id}")
                if row["status"] != ProposalStatus.PROPOSED.value:
                    raise WorldProposalError(
                        f"proposal is not pending review: {change_set.proposal_id}"
                    )
                for entry in history_entries:
                    self._validate_next_history_entry(entry)
                for entry in history_entries:
                    self._insert_history(entry)
                updated = self._connection.execute(
                    """
                    UPDATE world_proposals
                    SET status = ?, payload_json = ?
                    WHERE proposal_id = ? AND status = ?
                    """,
                    (
                        change_set.status.value,
                        change_set.model_dump_json(),
                        change_set.proposal_id,
                        ProposalStatus.PROPOSED.value,
                    ),
                ).rowcount
                if updated != 1:
                    raise WorldProposalError(
                        f"proposal is not pending review: {change_set.proposal_id}"
                    )
                self._insert_projection_job(projection_job)
                self._connection.commit()
            except BaseException:
                self._connection.rollback()
                raise

    def claim_projection_job(self) -> WorldProjectionJob | None:
        """Claim one pending projection atomically for the single graph writer."""

        with self._lock:
            self._connection.execute("BEGIN IMMEDIATE")
            try:
                row = self._connection.execute(
                    """
                    SELECT payload_json FROM world_projection_outbox
                    WHERE status = 'pending'
                    ORDER BY created_at, job_id
                    LIMIT 1
                    """
                ).fetchone()
                if row is None:
                    self._connection.commit()
                    return None
                job = WorldProjectionJob.model_validate_json(row["payload_json"])
                claimed = job.model_copy(
                    update={
                        "status": ProjectionJobStatus.RUNNING,
                        "attempts": job.attempts + 1,
                        "updated_at": datetime.now(UTC),
                    }
                )
                self._connection.execute(
                    """
                    UPDATE world_projection_outbox
                    SET status = ?, attempts = ?, payload_json = ?
                    WHERE job_id = ? AND status = 'pending'
                    """,
                    (
                        claimed.status.value,
                        claimed.attempts,
                        claimed.model_dump_json(),
                        claimed.job_id,
                    ),
                )
                self._connection.commit()
                return claimed
            except BaseException:
                self._connection.rollback()
                raise

    def complete_projection_job(
        self, job_id: str, *, error: str | None = None
    ) -> WorldProjectionJob:
        with self._lock, self._connection:
            row = self._connection.execute(
                "SELECT payload_json FROM world_projection_outbox WHERE job_id = ?", (job_id,)
            ).fetchone()
            if row is None:
                raise WorldProposalError(f"unknown projection job: {job_id}")
            job = WorldProjectionJob.model_validate_json(row["payload_json"])
            if job.status.value != "running":
                raise WorldProposalError(f"projection job is not running: {job_id}")
            completed = job.model_copy(
                update={
                    "status": ProjectionJobStatus.FAILED
                    if error
                    else ProjectionJobStatus.SUCCEEDED,
                    "last_error": error,
                    "updated_at": datetime.now(UTC),
                }
            )
            self._connection.execute(
                """
                UPDATE world_projection_outbox
                SET status = ?, last_error = ?, payload_json = ?
                WHERE job_id = ?
                """,
                (
                    completed.status.value,
                    completed.last_error,
                    completed.model_dump_json(),
                    job_id,
                ),
            )
            if error is None:
                self._connection.execute(
                    """
                    INSERT INTO world_projection_heads
                        (workspace_id, branch_id, job_id, source_revision, activated_at)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(workspace_id, branch_id) DO UPDATE SET
                        job_id = excluded.job_id,
                        source_revision = excluded.source_revision,
                        activated_at = excluded.activated_at
                    """,
                    (
                        completed.workspace_id,
                        completed.branch_id,
                        completed.job_id,
                        completed.source_revision,
                        _iso(completed.updated_at),
                    ),
                )
            return completed

    def active_projection_job(self, workspace_id: str, branch_id: str) -> WorldProjectionJob | None:
        with self._lock:
            row = self._connection.execute(
                """
                SELECT outbox.payload_json
                FROM world_projection_heads AS head
                JOIN world_projection_outbox AS outbox ON outbox.job_id = head.job_id
                WHERE head.workspace_id = ? AND head.branch_id = ?
                """,
                (workspace_id, branch_id),
            ).fetchone()
            return (
                None if row is None else WorldProjectionJob.model_validate_json(row["payload_json"])
            )

    def append_history(self, entry: WorldHistoryEntry) -> None:
        with self._lock, self._connection:
            self._validate_next_history_entry(entry)
            self._insert_history(entry)

    def history(
        self,
        record_id: str,
        *,
        workspace_id: str | None = None,
        branch_id: str | None = None,
        recorded_at: datetime | None = None,
    ) -> tuple[WorldHistoryEntry, ...]:
        clauses = ["record_id = ?"]
        parameters: list[object] = [record_id]
        if workspace_id is not None:
            clauses.append("workspace_id = ?")
            parameters.append(workspace_id)
        if branch_id is not None:
            clauses.append("branch_id = ?")
            parameters.append(branch_id)
        if recorded_at is not None:
            clauses.append("recorded_at <= ?")
            parameters.append(_iso(recorded_at))
        query = f"""
            SELECT payload_json FROM world_record_history
            WHERE {" AND ".join(clauses)}
            ORDER BY workspace_id, branch_id, record_version, recorded_at
        """
        with self._lock:
            rows = self._connection.execute(query, parameters).fetchall()
            return tuple(WorldHistoryEntry.model_validate_json(row["payload_json"]) for row in rows)

    def snapshot(
        self,
        workspace_id: str,
        branch_id: str,
        *,
        recorded_at: datetime | None = None,
    ) -> tuple[WorldHistoryEntry, ...]:
        cutoff = _iso(recorded_at) if recorded_at is not None else None
        with self._lock:
            rows = self._connection.execute(
                """
                WITH eligible AS (
                    SELECT payload_json, record_id, record_version,
                           ROW_NUMBER() OVER (
                               PARTITION BY record_id
                               ORDER BY record_version DESC, recorded_at DESC
                           ) AS rank
                    FROM world_record_history
                    WHERE workspace_id = ? AND branch_id = ?
                      AND (? IS NULL OR recorded_at <= ?)
                )
                SELECT payload_json FROM eligible
                WHERE rank = 1
                ORDER BY record_id
                """,
                (workspace_id, branch_id, cutoff, cutoff),
            ).fetchall()
        entries = tuple(WorldHistoryEntry.model_validate_json(row["payload_json"]) for row in rows)
        return tuple(
            sorted(
                (
                    entry
                    for entry in entries
                    if entry.record.lifecycle_status is WorldLifecycle.ACCEPTED
                ),
                key=lambda entry: (entry.record.kind, entry.record_id),
            )
        )

    def _initialize(self) -> None:
        with self._lock, self._connection:
            self._initialize_proposals()
            self._initialize_history()
            self._connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS world_reviews (
                    review_id TEXT PRIMARY KEY,
                    proposal_id TEXT NOT NULL,
                    reviewed_at TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    FOREIGN KEY (proposal_id) REFERENCES world_proposals(proposal_id)
                );
                CREATE INDEX IF NOT EXISTS world_history_snapshot_idx
                ON world_record_history (workspace_id, branch_id, recorded_at, record_id);
                CREATE INDEX IF NOT EXISTS world_reviews_proposal_idx
                ON world_reviews (proposal_id, reviewed_at, review_id);
                CREATE TABLE IF NOT EXISTS world_projection_outbox (
                    job_id TEXT PRIMARY KEY,
                    workspace_id TEXT NOT NULL,
                    branch_id TEXT NOT NULL,
                    source_proposal_id TEXT NOT NULL,
                    source_revision TEXT NOT NULL,
                    source_snapshot_root TEXT NOT NULL,
                    status TEXT NOT NULL,
                    attempts INTEGER NOT NULL,
                    last_error TEXT,
                    created_at TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS world_projection_outbox_pending_idx
                ON world_projection_outbox (status, created_at, job_id);
                CREATE TABLE IF NOT EXISTS world_projection_heads (
                    workspace_id TEXT NOT NULL,
                    branch_id TEXT NOT NULL,
                    job_id TEXT NOT NULL,
                    source_revision TEXT NOT NULL,
                    activated_at TEXT NOT NULL,
                    PRIMARY KEY (workspace_id, branch_id),
                    FOREIGN KEY (job_id) REFERENCES world_projection_outbox(job_id)
                );
                """
            )
            self._migrate_projection_outbox()

    def _migrate_projection_outbox(self) -> None:
        """Make pre-root jobs fail closed rather than projecting an unverifiable snapshot."""

        columns = {
            row["name"]
            for row in self._connection.execute(
                "PRAGMA table_info(world_projection_outbox)"
            ).fetchall()
        }
        if "source_snapshot_root" not in columns:
            self._connection.execute(
                "ALTER TABLE world_projection_outbox ADD COLUMN source_snapshot_root TEXT"
            )
            self._connection.execute(
                """
                UPDATE world_projection_outbox
                SET source_snapshot_root = ?,
                    payload_json = json_set(payload_json, '$.source_snapshot_root', ?)
                """,
                ("0" * 64, "0" * 64),
            )

    def _initialize_proposals(self) -> None:
        existing = self._connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'world_proposals'"
        ).fetchone()
        if existing is None:
            self._connection.execute(
                """
                CREATE TABLE world_proposals (
                    proposal_id TEXT PRIMARY KEY,
                    workspace_id TEXT NOT NULL,
                    branch_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                )
                """
            )
            return
        columns = {
            row["name"]
            for row in self._connection.execute("PRAGMA table_info(world_proposals)").fetchall()
        }
        for name, declaration in (
            ("workspace_id", "TEXT"),
            ("branch_id", "TEXT"),
            ("status", "TEXT"),
        ):
            if name not in columns:
                self._connection.execute(
                    f"ALTER TABLE world_proposals ADD COLUMN {name} {declaration}"
                )
        rows = self._connection.execute(
            "SELECT proposal_id, payload_json FROM world_proposals"
        ).fetchall()
        for row in rows:
            proposal = WorldChangeSet.model_validate_json(row["payload_json"])
            self._connection.execute(
                """
                UPDATE world_proposals
                SET workspace_id = ?, branch_id = ?, status = ?
                WHERE proposal_id = ?
                """,
                (
                    proposal.workspace_id,
                    proposal.branch_id,
                    proposal.status.value,
                    proposal.proposal_id,
                ),
            )

    def _initialize_history(self) -> None:
        existing = self._connection.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type = 'table' AND name = 'world_record_history'
            """
        ).fetchone()
        if existing is None:
            self._create_history_table()
            return
        columns = {
            row["name"]
            for row in self._connection.execute(
                "PRAGMA table_info(world_record_history)"
            ).fetchall()
        }
        if {"workspace_id", "branch_id", "recorded_at"}.issubset(columns):
            return
        rows = self._connection.execute("SELECT payload_json FROM world_record_history").fetchall()
        self._connection.execute(
            "ALTER TABLE world_record_history RENAME TO world_record_history_v0"
        )
        self._create_history_table()
        for row in rows:
            entry = WorldHistoryEntry.model_validate_json(row["payload_json"])
            self._insert_history(entry)
        self._connection.execute("DROP TABLE world_record_history_v0")

    def _create_history_table(self) -> None:
        self._connection.execute(
            """
            CREATE TABLE world_record_history (
                workspace_id TEXT NOT NULL,
                branch_id TEXT NOT NULL,
                record_id TEXT NOT NULL,
                record_version INTEGER NOT NULL,
                recorded_at TEXT NOT NULL,
                proposal_id TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                PRIMARY KEY (workspace_id, branch_id, record_id, record_version),
                FOREIGN KEY (proposal_id) REFERENCES world_proposals(proposal_id)
            )
            """
        )

    def _validate_next_history_entry(self, entry: WorldHistoryEntry) -> None:
        row = self._connection.execute(
            """
            SELECT MAX(record_version) AS latest_version
            FROM world_record_history
            WHERE workspace_id = ? AND branch_id = ? AND record_id = ?
            """,
            (entry.record.workspace_id, entry.record.branch_id, entry.record_id),
        ).fetchone()
        latest = row["latest_version"] if row else None
        expected = latest + 1 if latest is not None else 2
        if entry.record_version != expected:
            raise WorldRepositoryError(
                f"unexpected history version for {entry.record_id}: "
                f"expected {expected}, got {entry.record_version}"
            )

    def _insert_history(self, entry: WorldHistoryEntry) -> None:
        try:
            self._connection.execute(
                """
                INSERT INTO world_record_history
                    (workspace_id, branch_id, record_id, record_version,
                     recorded_at, proposal_id, payload_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry.record.workspace_id,
                    entry.record.branch_id,
                    entry.record_id,
                    entry.record_version,
                    _iso(entry.recorded_at),
                    entry.proposal_id,
                    entry.model_dump_json(),
                ),
            )
        except sqlite3.IntegrityError as error:
            raise WorldRepositoryError(
                f"history version already exists: "
                f"{entry.record.workspace_id}/{entry.record.branch_id}/"
                f"{entry.record_id}@{entry.record_version}"
            ) from error

    def _insert_projection_job(self, job: WorldProjectionJob) -> None:
        try:
            self._connection.execute(
                """
                INSERT INTO world_projection_outbox
                    (job_id, workspace_id, branch_id, source_proposal_id, source_revision,
                     source_snapshot_root, status, attempts, last_error, created_at, payload_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job.job_id,
                    job.workspace_id,
                    job.branch_id,
                    job.source_proposal_id,
                    job.source_revision,
                    job.source_snapshot_root,
                    job.status.value,
                    job.attempts,
                    job.last_error,
                    _iso(job.created_at),
                    job.model_dump_json(),
                ),
            )
        except sqlite3.IntegrityError as error:
            raise WorldRepositoryError(f"projection job already exists: {job.job_id}") from error


def _iso(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise WorldProposalError("recorded time must be timezone-aware")
    return value.astimezone(UTC).isoformat()


__all__ = ["SQLiteWorldRepository"]
