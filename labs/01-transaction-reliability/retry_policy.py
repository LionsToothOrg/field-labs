"""Bounded retry policy for the synthetic transactional-outbox lab."""

from dataclasses import dataclass
from pathlib import Path
import sqlite3
import time


@dataclass(frozen=True)
class RetryDecision:
    request_id: str
    attempt_count: int
    next_attempt_at: float | None
    quarantined: bool


class RetryPolicyStore:
    """Persist retry scheduling separately from delivery implementation details.

    This deliberately small store lets the lab isolate retry/backoff behavior
    without pretending that a local SQLite model is a production queue.
    """

    def __init__(self, database: str | Path) -> None:
        self.database = str(database)
        with self._connect() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS outbox_retry ("
                "request_id TEXT PRIMARY KEY, attempt_count INTEGER NOT NULL DEFAULT 0, "
                "next_attempt_at REAL, quarantined INTEGER NOT NULL DEFAULT 0)"
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database, timeout=5.0)

    def record_failure(
        self,
        request_id: str,
        *,
        max_attempts: int = 3,
        base_backoff_seconds: float = 1.0,
        now: float | None = None,
    ) -> RetryDecision:
        """Record a failed attempt and return its deterministic retry decision.

        Backoff is exponential and intentionally has no jitter so tests can
        make exact assertions. Production systems commonly add jitter to avoid
        synchronized retry storms.
        """
        if max_attempts <= 0:
            raise ValueError("max_attempts must be positive")
        if base_backoff_seconds <= 0:
            raise ValueError("base_backoff_seconds must be positive")

        current_time = time.time() if now is None else now
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT attempt_count FROM outbox_retry WHERE request_id = ?",
                (request_id,),
            ).fetchone()
            attempt_count = (int(row[0]) if row else 0) + 1
            quarantined = attempt_count >= max_attempts
            next_attempt_at = None if quarantined else current_time + base_backoff_seconds * (2 ** (attempt_count - 1))
            connection.execute(
                "INSERT INTO outbox_retry (request_id, attempt_count, next_attempt_at, quarantined) "
                "VALUES (?, ?, ?, ?) "
                "ON CONFLICT(request_id) DO UPDATE SET "
                "attempt_count = excluded.attempt_count, "
                "next_attempt_at = excluded.next_attempt_at, "
                "quarantined = excluded.quarantined",
                (request_id, attempt_count, next_attempt_at, int(quarantined)),
            )
            connection.commit()
        return RetryDecision(request_id, attempt_count, next_attempt_at, quarantined)

    def is_deliverable(self, request_id: str, *, now: float | None = None) -> bool:
        """Return whether a message is eligible for another delivery attempt."""
        current_time = time.time() if now is None else now
        with self._connect() as connection:
            row = connection.execute(
                "SELECT next_attempt_at, quarantined FROM outbox_retry WHERE request_id = ?",
                (request_id,),
            ).fetchone()
        if row is None:
            return True
        next_attempt_at, quarantined = row
        if bool(quarantined):
            return False
        return next_attempt_at is None or float(next_attempt_at) <= current_time

    def quarantined(self) -> list[RetryDecision]:
        """Return quarantined synthetic messages for explicit operator review."""
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT request_id, attempt_count FROM outbox_retry "
                "WHERE quarantined = 1 ORDER BY request_id"
            ).fetchall()
        return [RetryDecision(str(request_id), int(attempt_count), None, True) for request_id, attempt_count in rows]
