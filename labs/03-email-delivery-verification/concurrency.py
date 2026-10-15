from dataclasses import dataclass

from delivery import ProviderEvent, ReconciliationState, reconcile_provider_events, restore_trace


class VersionConflict(RuntimeError):
    """Raised when a worker tries to replace state from an obsolete snapshot."""


class RetryExhausted(RuntimeError):
    """Raised when conditional-write conflicts consume the configured attempt budget."""


class RetryDeadlineExceeded(RetryExhausted):
    """Raised when the next synthetic retry delay would exceed the deadline."""


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
class TimedRetryResult:
    snapshot: VersionedState
    attempts: int
    elapsed_ms: int
    scheduled_delays_ms: tuple[int, ...]


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


def reconcile_with_timed_retry(
    store: SyntheticStateStore,
    event: ProviderEvent,
    policy: RetryPolicy,
) -> TimedRetryResult:
    """Reconcile with deterministic synthetic delays and a total retry deadline.

    No sleeping or wall-clock access occurs. Each configured delay represents time that would
    pass before the next attempt; a retry is refused when that delay would exceed the deadline.
    """
    elapsed_ms = 0
    scheduled_delays: list[int] = []

    for attempt in range(1, len(policy.delays_ms) + 2):
        snapshot = store.read()
        result = reconcile_provider_events(
            restore_trace(snapshot.state), (event,), snapshot.state
        )
        try:
            committed = store.compare_and_swap(snapshot.version, result.state)
            return TimedRetryResult(
                committed, attempt, elapsed_ms, tuple(scheduled_delays)
            )
        except VersionConflict as conflict:
            delay_index = attempt - 1
            if delay_index >= len(policy.delays_ms):
                raise RetryExhausted(
                    f"conditional write did not succeed after {attempt} attempts"
                ) from conflict

            delay_ms = policy.delays_ms[delay_index]
            if elapsed_ms + delay_ms > policy.deadline_ms:
                raise RetryDeadlineExceeded(
                    f"retry deadline of {policy.deadline_ms}ms would be exceeded"
                ) from conflict

            elapsed_ms += delay_ms
            scheduled_delays.append(delay_ms)

    raise AssertionError("timed retry loop exited unexpectedly")
