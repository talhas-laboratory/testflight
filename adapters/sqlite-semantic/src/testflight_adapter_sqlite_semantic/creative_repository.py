"""SQLite persistence for immutable Moodboard and Creative Field records."""

from __future__ import annotations

import json
import sqlite3
import threading
from collections.abc import Iterable
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel
from testflight_creative_field import BoardRevision, CreativeRecord

RecordT = TypeVar("RecordT", bound=CreativeRecord)


class RevisionConflictError(ValueError):
    """Raised when a board write races with a newer revision."""


_IDENTITY_FIELDS: dict[str, str] = {
    "CreativeProject": "project_id",
    "Moodboard": "moodboard_id",
    "SourceLicenseRecord": "license_record_id",
    "ReferenceAsset": "asset_id",
    "Placement": "placement_id",
    "ReferenceCluster": "cluster_id",
    "UserAnnotation": "annotation_id",
    "BoardRevision": "board_revision_id",
    "ObservedFeature": "feature_id",
    "InterpretationAlternative": "alternative_id",
    "ReferenceContribution": "contribution_id",
    "ReferenceInterpretation": "interpretation_id",
    "ReviewDecision": "review_id",
    "FieldDimension": "dimension_id",
    "DimensionState": "dimension_id",
    "Principle": "principle_id",
    "Tension": "tension_id",
    "Exclusion": "exclusion_id",
    "FieldConflict": "conflict_id",
    "MissingDimension": "dimension_id",
    "CreativeFieldProposal": "proposal_id",
    "CreativeFieldRun": "run_id",
    "CreativeFieldVersion": "version_id",
    "ProjectBinding": "binding_id",
    "FieldBinding": "binding_id",
    "LocalOverride": "override_id",
    "CreativeRequest": "request_id",
    "ResolvedCreativeRequest": "request_id",
    "FieldProjection": "projection_id",
    "CreativeContextPacket": "packet_id",
    "TargetCapabilityManifest": "target_id",
    "GenerationPacket": "packet_id",
    "InvocationReceipt": "invocation_id",
    "CreativeOutput": "output_id",
    "CreativeEvaluation": "evaluation_id",
    "FeedbackRecord": "feedback_id",
}


class CreativeRepository:
    """Append-only creative record store with optimistic board-revision writes."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._connection = sqlite3.connect(path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._initialize()

    def close(self) -> None:
        with self._lock:
            self._connection.close()

    def __enter__(self) -> CreativeRepository:
        return self

    def __exit__(self, _type: object, _value: object, _traceback: object) -> None:
        self.close()

    def append(self, record: CreativeRecord, *, project_id: str | None = None) -> None:
        with self._lock, self._connection:
            self._insert_record(record, project_id=project_id)

    def append_many(self, records: Iterable[CreativeRecord]) -> None:
        with self._lock, self._connection:
            for record in records:
                self._insert_record(record)

    def get(self, model: type[RecordT], record_id: str) -> RecordT | None:
        with self._lock:
            record_type = model.__name__
            self._identity_field(model)
            row = self._connection.execute(
                "SELECT payload_json FROM creative_records WHERE record_type = ? AND record_id = ?",
                (record_type, record_id),
            ).fetchone()
            return None if row is None else model.model_validate(json.loads(row["payload_json"]))

    def list(self, model: type[RecordT], *, project_id: str | None = None) -> list[RecordT]:
        with self._lock:
            record_type = model.__name__
            self._identity_field(model)
            if project_id is None:
                rows = self._connection.execute(
                    """
                    SELECT payload_json FROM creative_records
                    WHERE record_type = ? ORDER BY record_id
                    """,
                    (record_type,),
                ).fetchall()
            else:
                rows = self._connection.execute(
                    """
                    SELECT payload_json FROM creative_records
                    WHERE record_type = ? AND project_id = ?
                    ORDER BY record_id
                    """,
                    (record_type, project_id),
                ).fetchall()
            return [model.model_validate(json.loads(row["payload_json"])) for row in rows]

    def put_board_revision(
        self, revision: BoardRevision, *, expected_revision: int | None = None
    ) -> None:
        with self._lock:
            self._put_board_revision_locked(revision, expected_revision=expected_revision)

    def append_with_board_revision(
        self,
        record: CreativeRecord,
        revision: BoardRevision,
        *,
        expected_revision: int | None = None,
        project_id: str | None = None,
    ) -> None:
        """Commit a record and its board head update in one transaction."""

        self.append_records_with_board_revision(
            (record,),
            revision,
            expected_revision=expected_revision,
            project_id=project_id,
        )

    def append_records_with_board_revision(
        self,
        records: Iterable[CreativeRecord],
        revision: BoardRevision,
        *,
        expected_revision: int | None = None,
        project_id: str | None = None,
    ) -> None:
        """Commit related records and their board-head update in one transaction."""

        with self._lock:
            expected = 0 if expected_revision is None else expected_revision
            records = tuple(records)
            for record in records:
                self._identity_field(record)
            self._identity_field(revision)
            self._connection.execute("BEGIN IMMEDIATE")
            try:
                self._assert_board_revision_head(revision, expected)
                for record in records:
                    self._insert_record(record, project_id=project_id)
                self._insert_record(revision)
                self._update_board_head(revision)
                self._connection.commit()
            except BaseException:
                self._connection.rollback()
                raise

    def replay_board(self, moodboard_id: str) -> list[BoardRevision]:
        with self._lock:
            rows = self._connection.execute(
                """
                SELECT payload_json FROM creative_records
                WHERE record_type = 'BoardRevision'
                  AND json_extract(payload_json, '$.moodboard_id') = ?
                ORDER BY json_extract(payload_json, '$.revision')
                """,
                (moodboard_id,),
            ).fetchall()
            return [BoardRevision.model_validate(json.loads(row["payload_json"])) for row in rows]

    def latest_board_revision(self, moodboard_id: str) -> int:
        with self._lock:
            row = self._connection.execute(
                "SELECT current_revision FROM creative_board_heads WHERE moodboard_id = ?",
                (moodboard_id,),
            ).fetchone()
            return 0 if row is None else int(row["current_revision"])

    def _put_board_revision_locked(
        self, revision: BoardRevision, *, expected_revision: int | None = None
    ) -> None:
        expected = 0 if expected_revision is None else expected_revision
        self._identity_field(revision)
        self._connection.execute("BEGIN IMMEDIATE")
        try:
            self._assert_board_revision_head(revision, expected)
            self._insert_record(revision)
            self._update_board_head(revision)
            self._connection.commit()
        except BaseException:
            self._connection.rollback()
            raise

    def _assert_board_revision_head(self, revision: BoardRevision, expected: int) -> None:
        row = self._connection.execute(
            "SELECT current_revision FROM creative_board_heads WHERE moodboard_id = ?",
            (revision.moodboard_id,),
        ).fetchone()
        current = 0 if row is None else int(row["current_revision"])
        if current != expected:
            raise RevisionConflictError(
                f"moodboard {revision.moodboard_id} is at revision {current}; expected {expected}"
            )
        if revision.revision != expected + 1:
            raise ValueError(
                f"board revision must advance by one: expected {expected + 1}, "
                f"got {revision.revision}"
            )

    def _update_board_head(self, revision: BoardRevision) -> None:
        self._connection.execute(
            """
            INSERT INTO creative_board_heads(moodboard_id, current_revision, board_revision_id)
            VALUES (?, ?, ?)
            ON CONFLICT(moodboard_id) DO UPDATE SET
                current_revision = excluded.current_revision,
                board_revision_id = excluded.board_revision_id
            """,
            (revision.moodboard_id, revision.revision, revision.board_revision_id),
        )

    def _initialize(self) -> None:
        self._connection.executescript(
            """
            PRAGMA foreign_keys = ON;
            CREATE TABLE IF NOT EXISTS creative_records (
                record_type TEXT NOT NULL,
                record_id TEXT NOT NULL,
                project_id TEXT,
                payload_json TEXT NOT NULL,
                PRIMARY KEY (record_type, record_id)
            );
            CREATE INDEX IF NOT EXISTS creative_records_project_idx
                ON creative_records(project_id, record_type, record_id);
            CREATE TABLE IF NOT EXISTS creative_board_heads (
                moodboard_id TEXT PRIMARY KEY,
                current_revision INTEGER NOT NULL,
                board_revision_id TEXT NOT NULL
            );
            """
        )
        self._connection.commit()

    def _insert_record(self, record: CreativeRecord, *, project_id: str | None = None) -> None:
        record_type = type(record).__name__
        identity_field = self._identity_field(record)
        record_id = str(getattr(record, identity_field))
        payload = record.model_dump_json()
        derived_project_id = project_id
        if derived_project_id is None:
            derived_project_id = getattr(record, "project_id", None)
        existing = self._connection.execute(
            "SELECT payload_json FROM creative_records WHERE record_type = ? AND record_id = ?",
            (record_type, record_id),
        ).fetchone()
        if existing is not None:
            if existing["payload_json"] != payload:
                raise ValueError(f"creative record identity conflict: {record_type}/{record_id}")
            return
        self._connection.execute(
            """
            INSERT INTO creative_records(record_type, record_id, project_id, payload_json)
            VALUES (?, ?, ?, ?)
            """,
            (record_type, record_id, derived_project_id, payload),
        )

    @staticmethod
    def _identity_field(record_or_model: CreativeRecord | type[BaseModel]) -> str:
        record_type = (
            record_or_model.__name__
            if isinstance(record_or_model, type)
            else type(record_or_model).__name__
        )
        try:
            return _IDENTITY_FIELDS[record_type]
        except KeyError as error:
            raise TypeError(f"unsupported creative record type: {record_type}") from error


__all__ = ["CreativeRepository", "RevisionConflictError"]
