from dataclasses import dataclass


class InvalidRefreshToken(ValueError):
    """Raised when a refresh request presents a token that is no longer current."""


class StaleRefreshAttempt(RuntimeError):
    """Raised when another refresh has already advanced the observed generation."""


@dataclass(frozen=True)
class RefreshAttempt:
    presented_token: str
    observed_generation: int


@dataclass(frozen=True)
class RefreshResult:
    refresh_token: str
    generation: int


@dataclass(frozen=True)
class SessionSnapshot:
    refresh_token: str
    generation: int


class InMemorySessionStore:
    """Synthetic store with a single conditional-write boundary."""

    def __init__(self, refresh_token: str = "refresh-synthetic-0") -> None:
        self._snapshot = SessionSnapshot(refresh_token, 0)

    def read(self) -> SessionSnapshot:
        return self._snapshot

    def conditional_rotate(
        self, *, expected_token: str, expected_generation: int
    ) -> RefreshResult | None:
        """Rotate only when both expected values still match the current snapshot."""
        current = self._snapshot
        if current.generation != expected_generation:
            return None
        if current.refresh_token != expected_token:
            return None

        next_generation = current.generation + 1
        next_token = f"refresh-synthetic-{next_generation}"
        self._snapshot = SessionSnapshot(next_token, next_generation)
        return RefreshResult(next_token, next_generation)


class SyntheticSessionStore:
    """Session workflow used to reproduce and constrain a synthetic refresh race."""

    def __init__(
        self,
        refresh_token: str = "refresh-synthetic-0",
        storage: InMemorySessionStore | None = None,
    ) -> None:
        if storage is not None and refresh_token != "refresh-synthetic-0":
            raise ValueError("provide either a custom refresh token or storage, not both")
        self._storage = storage or InMemorySessionStore(refresh_token)

    @property
    def current_refresh_token(self) -> str:
        return self._storage.read().refresh_token

    @property
    def generation(self) -> int:
        return self._storage.read().generation

    def begin_refresh(self, presented_token: str) -> RefreshAttempt:
        current = self._storage.read()
        if presented_token != current.refresh_token:
            raise InvalidRefreshToken("refresh token is not current")
        return RefreshAttempt(presented_token, current.generation)

    def finish_refresh_unchecked(self, attempt: RefreshAttempt) -> RefreshResult:
        """Rotate without proving that the attempt still owns the observed generation."""
        current = self._storage.read()
        result = self._storage.conditional_rotate(
            expected_token=current.refresh_token,
            expected_generation=current.generation,
        )
        if result is None:  # unreachable for this deterministic in-memory baseline
            raise RuntimeError("unchecked rotation unexpectedly conflicted")
        return result

    def finish_refresh(self, attempt: RefreshAttempt) -> RefreshResult:
        """Rotate through the store's conditional-write boundary."""
        result = self._storage.conditional_rotate(
            expected_token=attempt.presented_token,
            expected_generation=attempt.observed_generation,
        )
        if result is None:
            raise StaleRefreshAttempt("session state changed before refresh completed")
        return result
