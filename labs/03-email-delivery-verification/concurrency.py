from dataclasses import dataclass
from enum import Enum

from delivery import ProviderEvent, ReconciliationState, reconcile_provider_events, restore_trace


class RetryOutcome(str, Enum):
    SUCCEEDED = "succeeded"
    EXHAUSTED = "exhausted"
    DEADLINE_EXCEEDED = "deadline_exceeded"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class RetryMetric:
    """Content-free evidence describing one synthetic retry run."""

    outcome: RetryOutcome
    attempts: int
    elapsed_ms: int
    scheduled_delays_ms: tuple[int, ...]


class VersionConflict(RuntimeError):
    """Raised when a worker tries to replace state from an obsolete snapshot."""


class RetryExhausted(RuntimeError):
    """Raised when conditional-write conflicts consume the configured attempt budget."""

    def __init__(self, message: str, metric: RetryMetric | None = None):
        super().__init__(message)
        self.metric = metric


class RetryDeadlineExceeded(RetryExhausted):
    """Raised when the next synthetic retry delay would exceed the deadline."""


class RetryCancelled(RuntimeError):
    """Raised when deterministic cancellation stops reconciliation before an attempt."""

    def __init__(self, message: str, metric: RetryMetric):
        super().__init__(message)
        self.metric = metric


@dataclass(frozen=True)
class VersionedState:
    version: int
    state: ReconciliationState


@dataclass(frozen=True)
class RetryPolicy:
    """Deterministic retry timing for the lab; values are synthetic milliseconds."""

    delays_ms: tuple[int, ...]
    deadline_ms: int

    def __post_init__(self):
        if any(delay < 0 for delay in self.delays_ms):
            raise ValueError("retry delays must be non-negative")
        if self.deadline_ms < 0:
            raise ValueError("deadline_ms must be non-negative")


@dataclass(frozen=True)
class RetryCancellation:
    """Synthetic cancellation signal that becomes active before a numbered attempt."""

    cancel_before_attempt: int

    def __post_init__(self):
        if self.cancel_before_attempt < 1:
            raise ValueError("cancel_before_attempt must be at least 1")

    def is_cancelled(self, attempt: int) -> bool:
        return attempt >= self.cancel_before_attempt


@dataclass(frozen=True)
class TimedRetryResult:
    snapshot: VersionedState
    metric: RetryMetric

    @property
    def attempts(self) -> int:
        return self.metric.attempts

    @property
    def elapsed_ms(self) -> int:
        return self.metric.elapsed_ms

    @property
    def scheduled_delays_ms(self) -> tuple[int, ...]:
        return self.metric.scheduled_delays_ms


class SyntheticStateStore:
    """Small in-memory store for demonstrating read/write races.

    This is deliberately not a persistence implementation. ``write_unchecked`` exists only to
    reproduce the lost-update baseline; ``compare_and_swap`` models a conditional-write boundary.
    """

    def __init__(self, initial_state: ReconciliationState):
        self._snapshot = VersionedState(0, initial_state)

    def read(self) -> VersionedState:
        return self._snapshot

    def write_unchecked(self, state: ReconciliationState) -> VersionedState:
        self._snapshot = VersionedState(self._snapshot.version + 1, state)
        return self._snapshot

    def compare_and_swap(
        self, expected_version: int, state: ReconciliationState
    ) -> VersionedState:
        if self._snapshot.version != expected_version:
            raise VersionConflict(
                f"state version changed: expected {expected_version}, "
                f"found {self._snapshot.version}"
            )
        self._snapshot = VersionedState(expected_version + 1, state)
        return self._snapshot


def reconcile_with_retry(
    store: SyntheticStateStore, event: ProviderEvent, max_attempts: int = 3
) -> VersionedState:
    """Reconcile one event with a bounded number of conditional-write attempts.

    Every retry re-reads state and re-runs reconciliation so an obsolete decision is never
    written against a newer snapshot. This lab intentionally models no timing or backoff policy.
    """
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")

    for attempt in range(1, max_attempts + 1):
        snapshot = store.read()
        result = reconcile_provider_events(
            restore_trace(snapshot.state), (event,), snapshot.state
        )
        try:
            return store.compare_and_swap(snapshot.version, result.state)
        except VersionConflict as conflict:
            if attempt == max_attempts:
                raise RetryExhausted(
                    f"conditional write did not succeed after {max_attempts} attempts"
                ) from conflict

    raise AssertionError("bounded retry loop exited unexpectedly")


def _retry_metric(
    outcome: RetryOutcome,
    attempts: int,
    elapsed_ms: int,
    scheduled_delays: list[int],
) -> RetryMetric:
    return RetryMetric(outcome, attempts, elapsed_ms, tuple(scheduled_delays))


def reconcile_with_timed_retry(
    store: SyntheticStateStore,
    event: ProviderEvent,
    policy: RetryPolicy,
    cancellation: RetryCancellation | None = None,
) -> TimedRetryResult:
    """Reconcile with deterministic timing and content-free terminal observations.

    No sleeping or wall-clock access occurs. Cancellation is checked before each attempt, so a
    cancelled attempt never reads, reconciles, or writes state. Each terminal path exposes only
    outcome, attempt count, elapsed synthetic time, and scheduled delays; provider and message
    detail are intentionally excluded.
    """
    elapsed_ms = 0
    scheduled_delays: list[int] = []

    for attempt in range(1, len(policy.delays_ms) + 2):
        completed_attempts = attempt - 1
        if cancellation is not None and cancellation.is_cancelled(attempt):
            metric = _retry_metric(
                RetryOutcome.CANCELLED,
                completed_attempts,
                elapsed_ms,
                scheduled_delays,
            )
            raise RetryCancelled(f"retry cancelled before attempt {attempt}", metric)

        snapshot = store.read()
        result = reconcile_provider_events(
            restore_trace(snapshot.state), (event,), snapshot.state
        )
        try:
            committed = store.compare_and_swap(snapshot.version, result.state)
            metric = _retry_metric(
                RetryOutcome.SUCCEEDED, attempt, elapsed_ms, scheduled_delays
            )
            return TimedRetryResult(committed, metric)
        except VersionConflict as conflict:
            delay_index = attempt - 1
            if delay_index >= len(policy.delays_ms):
                metric = _retry_metric(
                    RetryOutcome.EXHAUSTED, attempt, elapsed_ms, scheduled_delays
                )
                raise RetryExhausted(
                    f"conditional write did not succeed after {attempt} attempts", metric
                ) from conflict

            delay_ms = policy.delays_ms[delay_index]
            if elapsed_ms + delay_ms > policy.deadline_ms:
                metric = _retry_metric(
                    RetryOutcome.DEADLINE_EXCEEDED,
                    attempt,
                    elapsed_ms,
                    scheduled_delays,
                )
                raise RetryDeadlineExceeded(
                    f"retry deadline of {policy.deadline_ms}ms would be exceeded", metric
                ) from conflict

            elapsed_ms += delay_ms
            scheduled_delays.append(delay_ms)

    raise AssertionError("timed retry loop exited unexpectedly")
