from dataclasses import dataclass

from delivery import ReconciliationState


class VersionConflict(RuntimeError):
    """Raised when a worker tries to replace state from an obsolete snapshot."""


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
