"""Synthetic ledgers used to demonstrate duplicate-request races."""

from dataclasses import dataclass
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
