from dataclasses import dataclass

from delivery import ProviderEvent, ReconciliationState, reconcile_provider_events, restore_trace


class VersionConflict(RuntimeError):
    """Raised when a worker tries to replace state from an obsolete snapshot."""


class RetryExhausted(RuntimeError):
    """Raised when conditional-write conflicts consume the configured attempt budget."""


@dataclass(frozen=True)
class VersionedState:
    version: int
    state: ReconciliationState


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
