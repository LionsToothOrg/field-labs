"""Deterministic circuit-breaker state transitions for synthetic dependency calls."""

from dataclasses import dataclass
from enum import Enum


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass(frozen=True)
class Decision:
    allowed: bool
    state: CircuitState
    reason: str
    retry_after_seconds: float | None = None


class CircuitBreaker:
    """Small state machine with an explicit caller-supplied clock.

    The breaker does not perform I/O. Callers ask whether a synthetic operation may
    start, then report its outcome with the same monotonic time source.
    """

    def __init__(self, *, failure_threshold: int, recovery_timeout_seconds: float):
        if failure_threshold < 1:
            raise ValueError("failure_threshold must be at least 1")
        if recovery_timeout_seconds < 0:
            raise ValueError("recovery_timeout_seconds cannot be negative")

        self.failure_threshold = failure_threshold
        self.recovery_timeout_seconds = recovery_timeout_seconds
        self.state = CircuitState.CLOSED
        self.consecutive_failures = 0
        self.opened_at: float | None = None
        self._probe_in_flight = False
        self._probe_started_at: float | None = None

    def before_call(self, *, now: float) -> Decision:
        if self.state is CircuitState.OPEN:
            assert self.opened_at is not None
            elapsed = now - self.opened_at
            if elapsed < 0:
                raise ValueError("now cannot precede the circuit open timestamp")
            if elapsed < self.recovery_timeout_seconds:
                return Decision(
                    False,
                    self.state,
                    "recovery_timeout_pending",
                    retry_after_seconds=self.recovery_timeout_seconds - elapsed,
                )
            self.state = CircuitState.HALF_OPEN

        if self.state is CircuitState.HALF_OPEN:
            if self._probe_in_flight:
                return Decision(False, self.state, "probe_in_flight")
            self._probe_in_flight = True
            self._probe_started_at = now
            return Decision(True, self.state, "probe_allowed")

        return Decision(True, self.state, "closed")

    def record_success(self) -> None:
        if self.state is CircuitState.OPEN:
            raise RuntimeError("cannot record a call outcome while the circuit is open")

        self.state = CircuitState.CLOSED
        self.consecutive_failures = 0
        self.opened_at = None
        self._probe_in_flight = False
        self._probe_started_at = None

    def record_failure(self, *, now: float) -> None:
        if self.state is CircuitState.OPEN:
            raise RuntimeError("cannot record a call outcome while the circuit is open")

        if self.state is CircuitState.HALF_OPEN:
            if self._probe_started_at is None:
                raise RuntimeError("cannot record a half-open failure without an admitted probe")
            if now < self._probe_started_at:
                raise ValueError("now cannot precede the half-open probe timestamp")
            self._open(now=now)
            return

        self.consecutive_failures += 1
        if self.consecutive_failures >= self.failure_threshold:
            self._open(now=now)

    def _open(self, *, now: float) -> None:
        self.state = CircuitState.OPEN
        self.opened_at = now
        self._probe_in_flight = False
        self._probe_started_at = None
