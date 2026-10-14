"""Synthetic ledgers used to demonstrate duplicate-request races."""

from dataclasses import dataclass
from pathlib import Path
import sqlite3
from threading import Lock
from typing import Callable


@dataclass(frozen=True)
class ApplyResult:
    request_id: str
    applied: bool
    balance: int


class UnsafeLedger:
    """Intentionally raceable check-then-write implementation."""

    def __init__(self, balance: int = 0) -> None:
        self.balance = balance
        self._seen: set[str] = set()

    def apply(
        self,
        request_id: str,
        amount: int,
        pause_after_check: Callable[[], None] = lambda: None,
    ) -> ApplyResult:
        if request_id in self._seen:
            return ApplyResult(request_id, False, self.balance)

        # Test instrumentation can pause both workers after the duplicate check,
        # making the check-then-write race deterministic.
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
            connection.execute(
                "CREATE TABLE IF NOT EXISTS ledger_state ("
                "id INTEGER PRIMARY KEY CHECK (id = 1), "
                "balance INTEGER NOT NULL)"
            )
            connection.execute(
                "CREATE TABLE IF NOT EXISTS applied_requests ("
                "request_id TEXT PRIMARY KEY)"
            )
            connection.execute(
                "INSERT OR IGNORE INTO ledger_state (id, balance) VALUES (1, ?)",
                (balance,),
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database, timeout=5.0, isolation_level=None)

    def balance(self) -> int:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT balance FROM ledger_state WHERE id = 1"
            ).fetchone()
        assert row is not None
        return int(row[0])

    def apply(
        self,
        request_id: str,
        amount: int,
        before_mutation: Callable[[], None] = lambda: None,
    ) -> ApplyResult:
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            try:
                connection.execute(
                    "INSERT INTO applied_requests (request_id) VALUES (?)",
                    (request_id,),
                )
            except sqlite3.IntegrityError:
                connection.rollback()
                return ApplyResult(request_id, False, self.balance())

            # Test instrumentation can fail after the durable claim but before
            # mutation to demonstrate that both changes share one transaction.
            before_mutation()
            connection.execute(
                "UPDATE ledger_state SET balance = balance + ? WHERE id = 1",
                (amount,),
            )
            row = connection.execute(
                "SELECT balance FROM ledger_state WHERE id = 1"
            ).fetchone()
            assert row is not None
            connection.commit()
            return ApplyResult(request_id, True, int(row[0]))
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()
