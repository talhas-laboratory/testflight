"""Small append-oriented semantic repository using only SQLite."""

import hashlib
import json
import sqlite3
from collections.abc import Iterable
from pathlib import Path

from testflight_brand import BrandAssertion
from testflight_semantic import EvidenceEnvelope, EvidenceSpan


class SemanticRepository:
    """Persist canonical evidence and accepted assertions outside Cognee."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(path)
        self._connection.row_factory = sqlite3.Row
        self._initialize()

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> "SemanticRepository":
        return self

    def __exit__(self, _type: object, _value: object, _traceback: object) -> None:
        self.close()

    def _initialize(self) -> None:
        self._connection.executescript(
            """
            PRAGMA foreign_keys = ON;
            CREATE TABLE IF NOT EXISTS evidence_envelopes (
                source_id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                source_uri TEXT NOT NULL,
                media_type TEXT NOT NULL,
                source_time TEXT,
                recorded_time TEXT NOT NULL,
                actor_id TEXT,
                access_classification TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS evidence_content (
                source_id TEXT PRIMARY KEY REFERENCES evidence_envelopes(source_id),
                content TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS evidence_spans (
                span_id TEXT PRIMARY KEY,
                envelope_id TEXT NOT NULL REFERENCES evidence_envelopes(source_id),
                quote TEXT NOT NULL,
                start_offset INTEGER NOT NULL,
                end_offset INTEGER NOT NULL,
                document_path TEXT NOT NULL,
                section_id TEXT NOT NULL,
                window_id TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS assertions (
                assertion_id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                brand_id TEXT NOT NULL,
                status TEXT NOT NULL,
                payload_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS run_attempts (
                attempt_id TEXT PRIMARY KEY,
                semantic_identity TEXT NOT NULL,
                workspace_id TEXT NOT NULL,
                status TEXT NOT NULL,
                result_json TEXT,
                created_at TEXT NOT NULL
            );
            """
        )
        self._connection.commit()

    def put_envelope(self, envelope: EvidenceEnvelope, content: str) -> None:
        actual_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        if actual_hash != envelope.content_hash:
            raise ValueError("content hash does not match evidence envelope")
        payload = envelope.model_dump(mode="json")
        existing = self._connection.execute(
            """
            SELECT workspace_id, content_hash, source_uri, media_type, source_time,
                   recorded_time, actor_id, access_classification
            FROM evidence_envelopes
            WHERE source_id = ?
            """,
            (envelope.source_id,),
        ).fetchone()
        if existing is not None:
            expected = {
                "workspace_id": envelope.workspace_id,
                "content_hash": envelope.content_hash,
                "source_uri": envelope.source_uri,
                "media_type": envelope.media_type,
                "source_time": payload["source_time"],
                "recorded_time": payload["recorded_time"],
                "actor_id": envelope.actor_id,
                "access_classification": envelope.access_classification,
            }
            if any(existing[key] != value for key, value in expected.items()):
                raise ValueError("evidence source identity is immutable")
        try:
            with self._connection:
                self._connection.execute(
                    """
                    INSERT INTO evidence_envelopes
                    (source_id, workspace_id, content_hash, source_uri, media_type, source_time,
                     recorded_time, actor_id, access_classification)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(source_id) DO NOTHING
                    """,
                    (
                        envelope.source_id,
                        envelope.workspace_id,
                        envelope.content_hash,
                        envelope.source_uri,
                        envelope.media_type,
                        payload["source_time"],
                        payload["recorded_time"],
                        envelope.actor_id,
                        envelope.access_classification,
                    ),
                )
                self._connection.execute(
                    "INSERT OR IGNORE INTO evidence_content(source_id, content) VALUES (?, ?)",
                    (envelope.source_id, content),
                )
        except sqlite3.IntegrityError as error:
            raise ValueError("evidence envelope violates repository constraints") from error

    def put_span(self, span_id: str, span: EvidenceSpan) -> None:
        with self._connection:
            self._connection.execute(
                """
                INSERT OR IGNORE INTO evidence_spans
                (
                    span_id, envelope_id, quote, start_offset, end_offset,
                    document_path, section_id, window_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    span_id,
                    span.envelope_id,
                    span.quote,
                    span.start,
                    span.end,
                    span.document_path,
                    span.section_id,
                    span.window_id,
                ),
            )

    def append_assertions(self, records: Iterable[BrandAssertion]) -> None:
        rows = list(records)
        for record in rows:
            if record.status != "accepted":
                raise ValueError("only accepted assertions may enter canonical state")
        with self._connection:
            for record in rows:
                payload = record.model_dump_json()
                existing = self._connection.execute(
                    "SELECT payload_json FROM assertions WHERE assertion_id = ?",
                    (record.assertion_id,),
                ).fetchone()
                if existing is not None:
                    if existing["payload_json"] != payload:
                        raise ValueError(f"assertion identity conflict: {record.assertion_id}")
                    continue
                self._connection.execute(
                    """
                    INSERT INTO assertions(
                        assertion_id, workspace_id, brand_id, status, payload_json
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        record.assertion_id,
                        record.workspace_id,
                        record.brand_id,
                        record.status,
                        payload,
                    ),
                )

    def list_assertions(self, workspace_id: str, brand_id: str) -> list[BrandAssertion]:
        rows = self._connection.execute(
            """
            SELECT payload_json FROM assertions
            WHERE workspace_id = ? AND brand_id = ?
            ORDER BY assertion_id
            """,
            (workspace_id, brand_id),
        ).fetchall()
        return [BrandAssertion.model_validate(json.loads(row["payload_json"])) for row in rows]


__all__ = ["SemanticRepository"]
