"""Synthetic ledgers used to demonstrate duplicate-request races."""

from dataclasses import dataclass
from pathlib import Path
import sqlite3
from threading import Lock
import time
from typing import Callable

from retry_policy import RetryPolicyStore


@dataclass(frozen=True)
class ApplyResult:
    request_id: str
    applied: bool
    balance: int


@dataclass(frozen=True)
class OutboxMessage:
    request_id: str
    amount: int


class UnsafeLedger:
    """Intentionally raceable check-then-write implementation."""

    def __init__(self, balance: int = 0) -> None:
        self.balance = balance
        self._seen: set[str] = set()

    def apply(self, request_id: str, amount: int, pause_after_check: Callable[[], None] = lambda: None) -> ApplyResult:
        if request_id in self._seen:
            return ApplyResult(request_id, False, self.balance)
        pause_after_check()
        self.balance += amount
        self._seen.add(request_id)
        return ApplyResult(request_id, True, self.balance)


class IdempotentLedger:
    """Serializes duplicate detection and mutation within one process."""

    def __init__(self, balance: int = 0) -> None:
        self.balance = balance
        self._seen: set[str] = set()
        self._lock = Lock()

    def apply(self, request_id: str, amount: int) -> ApplyResult:
        with self._lock:
            if request_id in self._seen:
                return ApplyResult(request_id, False, self.balance)
            self.balance += amount
            self._seen.add(request_id)
            return ApplyResult(request_id, True, self.balance)


class DurableLedger:
    """Uses a SQLite transaction and unique request key as a durable boundary."""

    def __init__(self, database: str | Path, balance: int = 0) -> None:
        self.database = str(database)
        with self._connect() as connection:
            connection.execute("CREATE TABLE IF NOT EXISTS ledger_state (id INTEGER PRIMARY KEY CHECK (id = 1), balance INTEGER NOT NULL)")
            connection.execute("CREATE TABLE IF NOT EXISTS applied_requests (request_id TEXT PRIMARY KEY)")
            connection.execute("INSERT OR IGNORE INTO ledger_state (id, balance) VALUES (1, ?)", (balance,))

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database, timeout=5.0, isolation_level=None)

    def balance(self) -> int:
        with self._connect() as connection:
            row = connection.execute("SELECT balance FROM ledger_state WHERE id = 1").fetchone()
        assert row is not None
        return int(row[0])

    def apply(self, request_id: str, amount: int, before_mutation: Callable[[], None] = lambda: None) -> ApplyResult:
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            try:
                connection.execute("INSERT INTO applied_requests (request_id) VALUES (?)", (request_id,))
            except sqlite3.IntegrityError:
                connection.rollback()
                return ApplyResult(request_id, False, self.balance())
            before_mutation()
            connection.execute("UPDATE ledger_state SET balance = balance + ? WHERE id = 1", (amount,))
            row = connection.execute("SELECT balance FROM ledger_state WHERE id = 1").fetchone()
            assert row is not None
            connection.commit()
            return ApplyResult(request_id, True, int(row[0]))
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()


class OutboxLedger(DurableLedger):
    """Commits ledger state and a synthetic side-effect intent atomically."""

    def __init__(self, database: str | Path, balance: int = 0) -> None:
        super().__init__(database, balance)
        with self._connect() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS outbox ("
                "request_id TEXT PRIMARY KEY, amount INTEGER NOT NULL, sent INTEGER NOT NULL DEFAULT 0, "
                "claimed_by TEXT, lease_until REAL)"
            )
            columns = {row[1] for row in connection.execute("PRAGMA table_info(outbox)")}
            if "claimed_by" not in columns:
                connection.execute("ALTER TABLE outbox ADD COLUMN claimed_by TEXT")
            if "lease_until" not in columns:
                connection.execute("ALTER TABLE outbox ADD COLUMN lease_until REAL")
            connection.execute(
                "CREATE TABLE IF NOT EXISTS outbox_retry ("
                "request_id TEXT PRIMARY KEY, attempt_count INTEGER NOT NULL DEFAULT 0, "
                "next_attempt_at REAL, quarantined INTEGER NOT NULL DEFAULT 0)"
            )

    def apply(self, request_id: str, amount: int) -> ApplyResult:
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            try:
                connection.execute("INSERT INTO applied_requests (request_id) VALUES (?)", (request_id,))
            except sqlite3.IntegrityError:
                connection.rollback()
                return ApplyResult(request_id, False, self.balance())
            connection.execute("UPDATE ledger_state SET balance = balance + ? WHERE id = 1", (amount,))
            connection.execute("INSERT INTO outbox (request_id, amount) VALUES (?, ?)", (request_id, amount))
            row = connection.execute("SELECT balance FROM ledger_state WHERE id = 1").fetchone()
            assert row is not None
            connection.commit()
            return ApplyResult(request_id, True, int(row[0]))
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    def pending(self) -> list[OutboxMessage]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT request_id, amount FROM outbox WHERE sent = 0 ORDER BY request_id"
            ).fetchall()
        return [OutboxMessage(str(request_id), int(amount)) for request_id, amount in rows]

    def claim(self, worker_id: str, lease_seconds: float = 30.0, now: float | None = None) -> OutboxMessage | None:
        """Atomically lease one currently eligible message to a worker."""
        if lease_seconds <= 0:
            raise ValueError("lease_seconds must be positive")
        current_time = time.time() if now is None else now
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT o.request_id, o.amount FROM outbox AS o "
                "LEFT JOIN outbox_retry AS r ON r.request_id = o.request_id "
                "WHERE o.sent = 0 "
                "AND (o.claimed_by IS NULL OR o.lease_until <= ?) "
                "AND COALESCE(r.quarantined, 0) = 0 "
                "AND (r.next_attempt_at IS NULL OR r.next_attempt_at <= ?) "
                "ORDER BY o.request_id LIMIT 1",
                (current_time, current_time),
            ).fetchone()
            if row is None:
                connection.commit()
                return None
            request_id, amount = row
            connection.execute(
                "UPDATE outbox SET claimed_by = ?, lease_until = ? WHERE request_id = ?",
                (worker_id, current_time + lease_seconds, request_id),
            )
            connection.commit()
            return OutboxMessage(str(request_id), int(amount))
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    def acknowledge(self, worker_id: str, request_id: str) -> bool:
        """Mark a message sent only when the caller still owns its lease."""
        with self._connect() as connection:
            cursor = connection.execute(
                "UPDATE outbox SET sent = 1, claimed_by = NULL, lease_until = NULL "
                "WHERE request_id = ? AND sent = 0 AND claimed_by = ?",
                (request_id, worker_id),
            )
        return cursor.rowcount == 1

    def release(self, worker_id: str, request_id: str) -> bool:
        """Release a failed delivery for retry when its policy allows."""
        with self._connect() as connection:
            cursor = connection.execute(
                "UPDATE outbox SET claimed_by = NULL, lease_until = NULL "
                "WHERE request_id = ? AND sent = 0 AND claimed_by = ?",
                (request_id, worker_id),
            )
        return cursor.rowcount == 1

    def dispatch(
        self,
        deliver: Callable[[OutboxMessage], None],
        worker_id: str = "worker-1",
        lease_seconds: float = 30.0,
        *,
        max_attempts: int = 3,
        base_backoff_seconds: float = 1.0,
    ) -> int:
        """Claim, deliver, and acknowledge currently eligible intents.

        Failed deliveries persist retry state before releasing their lease. The
        claim query then enforces backoff or quarantine on the next dispatch.
        Delivery and acknowledgement remain separate operations, so a crash
        after delivery but before acknowledgement can still cause redelivery
        after lease expiry. The experiment therefore remains at-least-once.
        """
        retry_policy = RetryPolicyStore(self.database)
        delivered = 0
        while True:
            message = self.claim(worker_id, lease_seconds)
            if message is None:
                return delivered
            try:
                deliver(message)
            except BaseException:
                retry_policy.record_failure(
                    message.request_id,
                    max_attempts=max_attempts,
                    base_backoff_seconds=base_backoff_seconds,
                )
                if not self.release(worker_id, message.request_id):
                    raise RuntimeError("outbox lease ownership changed before failed delivery was released")
                raise
            if not self.acknowledge(worker_id, message.request_id):
                raise RuntimeError("outbox lease ownership changed before acknowledgement")
            delivered += 1
