"""SQLite event store for offline P1 candidate jobs."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterator
from uuid import uuid4

from .state import STAGES, TERMINAL_STATES, next_state, validate_transition
from .json_safety import load_json_object_text


MIN_CANDIDATE_DURATION_SECONDS = 25
MAX_CANDIDATE_DURATION_SECONDS = 60
DEFAULT_CANDIDATE_DURATION_SECONDS = 40


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


class CandidateStore:
    """Small transactional store. Every lifecycle outcome also appends an event."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._run_claim: ContextVar[dict[str, Any] | None] = ContextVar('candidate_run_claim', default=None)

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path, timeout=5.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 5000")
        connection.execute("PRAGMA journal_mode = WAL")
        return connection

    @contextmanager
    def _transaction(self, *, check_claim: bool = True) -> Iterator[sqlite3.Connection]:
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            claim = self._run_claim.get() if check_claim else None
            if claim is not None:
                row = connection.execute(
                    'SELECT l.owner_token, l.attempt, j.attempt AS job_attempt FROM locks l '
                    'JOIN jobs j ON j.job_id=l.job_id WHERE l.lock_name=?',
                    (claim['lock_name'],),
                ).fetchone()
                if (row is None or row['owner_token'] != claim['owner_token']
                        or row['attempt'] != claim['attempt'] or row['job_attempt'] != claim['attempt']):
                    raise ValueError('job_execution_claim_stale')
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self) -> None:
        connection = self._connect()
        try:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                  job_id TEXT PRIMARY KEY,
                  idempotency_key TEXT NOT NULL UNIQUE,
                  fixture_id TEXT NOT NULL,
                  template TEXT NOT NULL,
                  topic TEXT NOT NULL,
                  state TEXT NOT NULL,
                  last_completed_state TEXT,
                  attempt INTEGER NOT NULL DEFAULT 0,
                  metadata_json TEXT NOT NULL DEFAULT '{}',
                  requested_duration_seconds INTEGER,
                  resolved_duration_seconds REAL,
                  render_contract_version TEXT NOT NULL DEFAULT '1.0',
                  created_at TEXT NOT NULL,
                  updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS job_events (
                  event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                  job_id TEXT NOT NULL REFERENCES jobs(job_id),
                  event_type TEXT NOT NULL,
                  from_state TEXT,
                  to_state TEXT,
                  reason TEXT,
                  payload_json TEXT NOT NULL DEFAULT '{}',
                  created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS artifacts (
                  artifact_id INTEGER PRIMARY KEY AUTOINCREMENT,
                  job_id TEXT NOT NULL REFERENCES jobs(job_id),
                  artifact_type TEXT NOT NULL,
                  relative_path TEXT NOT NULL,
                  sha256 TEXT NOT NULL,
                  created_at TEXT NOT NULL,
                  UNIQUE(job_id, artifact_type)
                );
                CREATE TABLE IF NOT EXISTS topic_history (
                  topic_id INTEGER PRIMARY KEY AUTOINCREMENT,
                  normalized_topic TEXT NOT NULL UNIQUE,
                  job_id TEXT REFERENCES jobs(job_id),
                  created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS source_records (
                  source_id INTEGER PRIMARY KEY AUTOINCREMENT,
                  job_id TEXT NOT NULL REFERENCES jobs(job_id),
                  source_type TEXT NOT NULL,
                  source_ref TEXT NOT NULL,
                  content_sha256 TEXT NOT NULL,
                  created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS inbound_messages (
                  message_id TEXT PRIMARY KEY,
                  job_id TEXT REFERENCES jobs(job_id),
                  received_at TEXT NOT NULL,
                  payload_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS deliveries (
                  delivery_id INTEGER PRIMARY KEY AUTOINCREMENT,
                  delivery_key TEXT NOT NULL UNIQUE,
                  job_id TEXT NOT NULL REFERENCES jobs(job_id),
                  mode TEXT NOT NULL,
                  status TEXT NOT NULL,
                  manifest_json TEXT NOT NULL,
                  created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS stage_attempts (
                  stage_attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
                  job_id TEXT NOT NULL REFERENCES jobs(job_id),
                  stage TEXT NOT NULL,
                  attempt INTEGER NOT NULL,
                  status TEXT NOT NULL,
                  started_at TEXT NOT NULL,
                  completed_at TEXT,
                  detail_json TEXT NOT NULL DEFAULT '{}',
                  UNIQUE(job_id, stage, attempt)
                );
                CREATE TABLE IF NOT EXISTS locks (
                  lock_name TEXT PRIMARY KEY,
                  job_id TEXT NOT NULL REFERENCES jobs(job_id),
                  acquired_at TEXT NOT NULL
                );
                """
            )
            columns = {
                str(row["name"])
                for row in connection.execute("PRAGMA table_info(jobs)").fetchall()
            }
            migrations = {
                "metadata_json": "ALTER TABLE jobs ADD COLUMN metadata_json TEXT NOT NULL DEFAULT '{}'",
                "requested_duration_seconds": "ALTER TABLE jobs ADD COLUMN requested_duration_seconds INTEGER",
                "resolved_duration_seconds": "ALTER TABLE jobs ADD COLUMN resolved_duration_seconds REAL",
                "render_contract_version": "ALTER TABLE jobs ADD COLUMN render_contract_version TEXT NOT NULL DEFAULT '1.0'",
            }
            for column, statement in migrations.items():
                if column not in columns:
                    connection.execute(statement)
            lock_columns = {str(row['name']) for row in connection.execute('PRAGMA table_info(locks)')}
            if 'owner_token' not in lock_columns:
                connection.execute("ALTER TABLE locks ADD COLUMN owner_token TEXT NOT NULL DEFAULT ''")
            if 'attempt' not in lock_columns:
                connection.execute('ALTER TABLE locks ADD COLUMN attempt INTEGER NOT NULL DEFAULT 0')
            connection.commit()
        finally:
            connection.close()

    @staticmethod
    def _job_id(idempotency_key: str) -> str:
        return f"job-{hashlib.sha256(idempotency_key.encode('utf-8')).hexdigest()[:24]}"

    @staticmethod
    def _event(
        connection: sqlite3.Connection,
        job_id: str,
        event_type: str,
        *,
        from_state: str | None = None,
        to_state: str | None = None,
        reason: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        connection.execute(
            """INSERT INTO job_events
            (job_id,event_type,from_state,to_state,reason,payload_json,created_at)
            VALUES (?,?,?,?,?,?,?)""",
            (
                job_id,
                event_type,
                from_state,
                to_state,
                reason,
                json.dumps(payload or {}, sort_keys=True),
                utc_now(),
            ),
        )

    @staticmethod
    def _requested_duration(value: int) -> int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError("candidate_duration_invalid")
        if not MIN_CANDIDATE_DURATION_SECONDS <= value <= MAX_CANDIDATE_DURATION_SECONDS:
            raise ValueError("candidate_duration_out_of_range")
        return value

    def create_job(
        self,
        fixture_id: str,
        idempotency_key: str,
        template: str,
        topic: str,
        *,
        requested_duration_seconds: int = DEFAULT_CANDIDATE_DURATION_SECONDS,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not all([fixture_id, idempotency_key, template, topic]):
            raise ValueError("candidate_job_fields_required")
        requested_duration_seconds = self._requested_duration(requested_duration_seconds)
        job_id = self._job_id(idempotency_key)
        with self._transaction() as connection:
            existing = connection.execute(
                "SELECT * FROM jobs WHERE idempotency_key = ?", (idempotency_key,)
            ).fetchone()
            if existing:
                result = dict(existing)
                result["metadata"] = json.loads(result.pop("metadata_json"))
                return {**result, "created": False}
            now = utc_now()
            connection.execute(
                """INSERT INTO jobs
                (job_id,idempotency_key,fixture_id,template,topic,state,last_completed_state,attempt,
                 metadata_json,requested_duration_seconds,resolved_duration_seconds,render_contract_version,created_at,updated_at)
                VALUES (?,?,?,?,?,'NEW',NULL,0,?,?,NULL,'2.0',?,?)""",
                (
                    job_id,
                    idempotency_key,
                    fixture_id,
                    template,
                    topic,
                    json.dumps(metadata or {}, ensure_ascii=False, sort_keys=True),
                    requested_duration_seconds,
                    now,
                    now,
                ),
            )
            self._event(
                connection,
                job_id,
                "job_created",
                to_state="NEW",
                payload={
                    "fixture_id": fixture_id,
                    "requested_duration_seconds": requested_duration_seconds,
                    "render_contract_version": "2.0",
                    "input_digest": str((metadata or {}).get("topic_digest", "")),
                },
            )
            return {**self._status_row(connection, job_id), "created": True}

    def set_resolved_duration(self, job_id: str, seconds: float) -> dict[str, Any]:
        if not MIN_CANDIDATE_DURATION_SECONDS <= seconds <= MAX_CANDIDATE_DURATION_SECONDS:
            raise ValueError("resolved_duration_out_of_range")
        with self._transaction() as connection:
            job = self._status_row(connection, job_id)
            if job["render_contract_version"] != "2.0":
                raise ValueError("legacy_job_duration_immutable")
            rounded = round(float(seconds), 3)
            connection.execute(
                "UPDATE jobs SET resolved_duration_seconds = ?, updated_at = ? WHERE job_id = ?",
                (rounded, utc_now(), job_id),
            )
            self._event(
                connection,
                job_id,
                "duration_resolved",
                payload={"resolved_duration_seconds": rounded},
            )
            return self._status_row(connection, job_id)

    def _status_row(self, connection: sqlite3.Connection, job_id: str) -> dict[str, Any]:
        row = connection.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
        if row is None:
            raise KeyError(f"job_not_found:{job_id}")
        result = dict(row)
        result["metadata"] = json.loads(result.pop("metadata_json"))
        return result

    def status(self, job_id: str) -> dict[str, Any]:
        connection = self._connect()
        try:
            return self._status_row(connection, job_id)
        finally:
            connection.close()

    def events(self, job_id: str) -> list[dict[str, Any]]:
        connection = self._connect()
        try:
            rows = connection.execute(
                "SELECT * FROM job_events WHERE job_id = ? ORDER BY event_id", (job_id,)
            ).fetchall()
        finally:
            connection.close()
        return [{**dict(row), "payload": json.loads(row["payload_json"])} for row in rows]

    def projection_snapshot(self, job_id: str) -> dict[str, Any]:
        """Read job, artifacts, and events from one SQLite read transaction."""
        connection = self._connect()
        try:
            connection.execute("BEGIN")
            job = self._status_row(connection, job_id)
            artifact_rows = connection.execute(
                "SELECT * FROM artifacts WHERE job_id = ? ORDER BY artifact_type", (job_id,)
            ).fetchall()
            event_rows = connection.execute(
                "SELECT * FROM job_events WHERE job_id = ? ORDER BY event_id", (job_id,)
            ).fetchall()
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
        return {
            "job": job,
            "artifacts": [dict(row) for row in artifact_rows],
            "events": [
                {**dict(row), "payload": json.loads(row["payload_json"])} for row in event_rows
            ],
        }

    def update_metadata(self, job_id: str, metadata: dict[str, Any]) -> dict[str, Any]:
        """Replace one job's metadata atomically without changing lifecycle state."""
        with self._transaction() as connection:
            self._status_row(connection, job_id)
            connection.execute(
                "UPDATE jobs SET metadata_json = ?, updated_at = ? WHERE job_id = ?",
                (json.dumps(metadata, ensure_ascii=False, sort_keys=True), utc_now(), job_id),
            )
            self._event(connection, job_id, "job_metadata_updated", payload={"fields": sorted(metadata)})
            return self._status_row(connection, job_id)

    def list_jobs(self) -> list[dict[str, Any]]:
        connection = self._connect()
        try:
            rows = connection.execute("SELECT * FROM jobs ORDER BY created_at, job_id").fetchall()
        finally:
            connection.close()
        return [
            {**dict(row), "metadata": json.loads(row["metadata_json"])}
            for row in rows
        ]

    def stage_attempts(self, job_id: str) -> list[dict[str, Any]]:
        connection = self._connect()
        try:
            rows = connection.execute(
                "SELECT * FROM stage_attempts WHERE job_id = ? ORDER BY stage_attempt_id", (job_id,)
            ).fetchall()
        finally:
            connection.close()
        return [{**dict(row), "detail": json.loads(row["detail_json"])} for row in rows]

    def advance(self, job_id: str, target: str, reason: str = "stage_completed") -> dict[str, Any]:
        with self._transaction() as connection:
            job = self._status_row(connection, job_id)
            validate_transition(job["state"], target)
            connection.execute(
                "UPDATE jobs SET state = ?, last_completed_state = ?, updated_at = ? WHERE job_id = ?",
                (target, job["state"], utc_now(), job_id),
            )
            self._event(
                connection,
                job_id,
                "state_advanced",
                from_state=job["state"],
                to_state=target,
                reason=reason,
            )
            return self._status_row(connection, job_id)

    def cancel(self, job_id: str, reason: str) -> dict[str, Any]:
        with self._transaction() as connection:
            job = self._status_row(connection, job_id)
            if job["state"] in TERMINAL_STATES:
                raise ValueError(f"cannot_cancel_terminal:{job['state']}")
            connection.execute(
                "UPDATE jobs SET state = 'CANCELLED', updated_at = ? WHERE job_id = ?",
                (utc_now(), job_id),
            )
            self._event(
                connection,
                job_id,
                "job_cancelled",
                from_state=job["state"],
                to_state="CANCELLED",
                reason=reason,
            )
            return self._status_row(connection, job_id)

    def fail(self, job_id: str, reason: str, *, retry_from: str | None = None) -> dict[str, Any]:
        with self._transaction() as connection:
            job = self._status_row(connection, job_id)
            if job["state"] in TERMINAL_STATES:
                raise ValueError(f"cannot_fail_terminal:{job['state']}")
            connection.execute(
                "UPDATE jobs SET state = 'FAILED', updated_at = ? WHERE job_id = ?",
                (utc_now(), job_id),
            )
            if retry_from is not None:
                if retry_from not in STAGES[:-1]:
                    raise ValueError('invalid_retry_stage')
                index = STAGES.index(retry_from)
                connection.execute('UPDATE jobs SET last_completed_state=? WHERE job_id=?',
                                   (STAGES[index - 1] if index else None, job_id))
            self._event(
                connection,
                job_id,
                "job_failed",
                from_state=job["state"],
                to_state="FAILED",
                reason=reason,
            )
            return self._status_row(connection, job_id)

    def retry(self, job_id: str, reason: str) -> dict[str, Any]:
        with self._transaction() as connection:
            job = self._status_row(connection, job_id)
            if job["state"] not in {"FAILED", "CANCELLED"}:
                raise ValueError(f"cannot_retry_state:{job['state']}")
            resume = (
                next_state(job["last_completed_state"]) if job["last_completed_state"] else "NEW"
            )
            connection.execute(
                "UPDATE jobs SET state = ?, attempt = attempt + 1, updated_at = ? WHERE job_id = ?",
                (resume, utc_now(), job_id),
            )
            connection.execute('DELETE FROM locks WHERE lock_name=? AND job_id=?',
                               (f'phase1-run:{job_id}', job_id))
            self._event(
                connection,
                job_id,
                "job_retried",
                from_state=job["state"],
                to_state=resume,
                reason=reason,
            )
            return self._status_row(connection, job_id)

    def start_stage_attempt(self, job_id: str, stage: str) -> int:
        if stage not in STAGES:
            raise ValueError(f"unknown_stage:{stage}")
        with self._transaction() as connection:
            attempt = connection.execute(
                "SELECT COALESCE(MAX(attempt), 0) + 1 FROM stage_attempts WHERE job_id = ? AND stage = ?",
                (job_id, stage),
            ).fetchone()[0]
            connection.execute(
                "INSERT INTO stage_attempts(job_id,stage,attempt,status,started_at) VALUES(?,?,?,?,?)",
                (job_id, stage, attempt, "started", utc_now()),
            )
            return int(attempt)

    def complete_stage_attempt(
        self, job_id: str, stage: str, attempt: int, status: str, detail: dict[str, Any]
    ) -> None:
        with self._transaction() as connection:
            cursor = connection.execute(
                """UPDATE stage_attempts SET status = ?, completed_at = ?, detail_json = ?
                WHERE job_id = ? AND stage = ? AND attempt = ? AND completed_at IS NULL""",
                (status, utc_now(), json.dumps(detail, sort_keys=True), job_id, stage, attempt),
            )
            if cursor.rowcount != 1:
                raise ValueError("stage_attempt_not_open")

    def record_artifact(
        self, job_id: str, artifact_type: str, relative_path: str, sha256: str
    ) -> None:
        with self._transaction() as connection:
            if self._run_claim.get() is not None and self._status_row(connection, job_id)['state'] == 'CANCELLED':
                raise ValueError('job_execution_cancelled')
            connection.execute(
                """INSERT INTO artifacts(job_id,artifact_type,relative_path,sha256,created_at)
                VALUES(?,?,?,?,?)
                ON CONFLICT(job_id,artifact_type) DO UPDATE SET
                relative_path=excluded.relative_path, sha256=excluded.sha256, created_at=excluded.created_at""",
                (job_id, artifact_type, relative_path, sha256, utc_now()),
            )

    @contextmanager
    def execution_claim(self, job_id: str) -> Iterator[None]:
        """One writer per attempt; explicit cancel/retry fences a returning worker."""
        lock_name, owner = f'phase1-run:{job_id}', uuid4().hex
        with self._transaction(check_claim=False) as connection:
            job = self._status_row(connection, job_id)
            if job['state'] in TERMINAL_STATES:
                raise ValueError('job_execution_terminal')
            if connection.execute('SELECT 1 FROM locks WHERE lock_name=?', (lock_name,)).fetchone():
                raise ValueError('job_execution_in_progress')
            connection.execute(
                'INSERT INTO locks(lock_name,job_id,acquired_at,owner_token,attempt) VALUES(?,?,?,?,?)',
                (lock_name, job_id, utc_now(), owner, job['attempt']),
            )
        claim = {'lock_name': lock_name, 'owner_token': owner, 'attempt': job['attempt']}
        context = self._run_claim.set(claim)
        try:
            yield
        finally:
            self._run_claim.reset(context)
            with self._transaction(check_claim=False) as connection:
                connection.execute('DELETE FROM locks WHERE lock_name=? AND owner_token=? AND attempt=?',
                                   (lock_name, owner, claim['attempt']))

    def publish_review_artifacts(self, job_id: str, artifacts: list[dict[str, str]],
                                 *, reason: str) -> dict[str, Any]:
        """Publish all verified artifact identities and review readiness in one transaction."""
        types = [item['artifact_type'] for item in artifacts]
        if len(set(types)) != len(types) or not {'final_master', 'review_package'} <= set(types):
            raise ValueError('review_artifacts_incomplete')
        with self._transaction() as connection:
            job = self._status_row(connection, job_id)
            validate_transition(job['state'], 'PENDING_REVIEW')
            for item in artifacts:
                connection.execute(
                    'INSERT INTO artifacts(job_id,artifact_type,relative_path,sha256,created_at) '
                    'VALUES(?,?,?,?,?) ON CONFLICT(job_id,artifact_type) DO UPDATE SET '
                    'relative_path=excluded.relative_path,sha256=excluded.sha256,created_at=excluded.created_at',
                    (job_id, item['artifact_type'], item['relative_path'], item['sha256'], utc_now()),
                )
            connection.execute('UPDATE jobs SET state=?,last_completed_state=?,updated_at=? WHERE job_id=?',
                               ('PENDING_REVIEW', job['state'], utc_now(), job_id))
            self._event(connection, job_id, 'state_advanced', from_state=job['state'],
                        to_state='PENDING_REVIEW', reason=reason,
                        payload={'attempt': job['attempt'], 'artifacts': artifacts})
            return self._status_row(connection, job_id)

    def invalidate_review(self, job_id: str, reason: str) -> dict[str, Any]:
        with self._transaction() as connection:
            job = self._status_row(connection, job_id)
            if job['state'] != 'PENDING_REVIEW':
                raise ValueError('review_invalidation_state_changed')
            connection.execute('UPDATE jobs SET state=?,last_completed_state=?,updated_at=? WHERE job_id=?',
                               ('FAILED', 'ASSETS', utc_now(), job_id))
            self._event(connection, job_id, 'review_invalidated', from_state='PENDING_REVIEW',
                        to_state='FAILED', reason=reason)
            return self._status_row(connection, job_id)

    def artifacts(self, job_id: str) -> list[dict[str, Any]]:
        connection = self._connect()
        try:
            return [
                dict(row)
                for row in connection.execute(
                    "SELECT * FROM artifacts WHERE job_id = ? ORDER BY artifact_type", (job_id,)
                ).fetchall()
            ]
        finally:
            connection.close()

    def create_delivery(
        self, delivery_key: str, job_id: str, manifest: dict[str, Any]
    ) -> dict[str, Any]:
        with self._transaction() as connection:
            existing = connection.execute(
                "SELECT * FROM deliveries WHERE delivery_key = ?", (delivery_key,)
            ).fetchone()
            if existing:
                return {
                    **dict(existing),
                    "created": False,
                    "manifest": load_json_object_text(existing["manifest_json"]),
                }
            now = utc_now()
            connection.execute(
                """INSERT INTO deliveries(delivery_key,job_id,mode,status,manifest_json,created_at)
                VALUES(?,?, 'dry-run', 'recorded', ?, ?)""",
                (
                    delivery_key,
                    job_id,
                    json.dumps(manifest, ensure_ascii=False, sort_keys=True),
                    now,
                ),
            )
            row = connection.execute(
                "SELECT * FROM deliveries WHERE delivery_key = ?", (delivery_key,)
            ).fetchone()
            self._event(
                connection,
                job_id,
                "delivery_dry_run_recorded",
                payload={"delivery_key": delivery_key},
            )
            return {**dict(row), "created": True, "manifest": manifest}

    def delivery(self, delivery_key: str) -> dict[str, Any] | None:
        """Return one dry-run delivery record without creating or changing it."""
        connection = self._connect()
        try:
            row = connection.execute(
                "SELECT * FROM deliveries WHERE delivery_key = ?", (delivery_key,)
            ).fetchone()
            if row is None:
                return None
            value = dict(row)
            value["manifest"] = load_json_object_text(value["manifest_json"])
            return value
        finally:
            connection.close()

    def connection_settings(self) -> dict[str, Any]:
        connection = self._connect()
        try:
            return {
                "journal_mode": connection.execute("PRAGMA journal_mode").fetchone()[0],
                "foreign_keys": connection.execute("PRAGMA foreign_keys").fetchone()[0],
                "busy_timeout": connection.execute("PRAGMA busy_timeout").fetchone()[0],
            }
        finally:
            connection.close()
