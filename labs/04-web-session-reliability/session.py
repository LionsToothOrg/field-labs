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


class SyntheticSessionStore:
    """Tiny in-memory session model used to reproduce and constrain a refresh race."""

    def __init__(self, refresh_token: str = "refresh-synthetic-0") -> None:
        self._refresh_token = refresh_token
        self._generation = 0

    @property
    def current_refresh_token(self) -> str:
        return self._refresh_token

    @property
    def generation(self) -> int:
        return self._generation

    def begin_refresh(self, presented_token: str) -> RefreshAttempt:
        if presented_token != self._refresh_token:
            raise InvalidRefreshToken("refresh token is not current")
        return RefreshAttempt(presented_token, self._generation)

    def finish_refresh_unchecked(self, attempt: RefreshAttempt) -> RefreshResult:
        """Rotate without proving that the attempt still owns the observed generation."""
        return self._rotate()

    def finish_refresh(self, attempt: RefreshAttempt) -> RefreshResult:
        """Rotate only if the request still owns the generation it observed."""
        if attempt.observed_generation != self._generation:
            raise StaleRefreshAttempt("session generation advanced before refresh completed")
        if attempt.presented_token != self._refresh_token:
            raise StaleRefreshAttempt("refresh token changed before refresh completed")
        return self._rotate()

    def _rotate(self) -> RefreshResult:
        next_generation = self._generation + 1
        next_token = f"refresh-synthetic-{next_generation}"
        self._generation = next_generation
        self._refresh_token = next_token
        return RefreshResult(next_token, next_generation)
