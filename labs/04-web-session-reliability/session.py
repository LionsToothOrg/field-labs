from dataclasses import dataclass


class InvalidRefreshToken(ValueError):
    """Raised when a refresh request presents a token that is no longer current."""


@dataclass(frozen=True)
class RefreshAttempt:
    presented_token: str
    observed_generation: int


@dataclass(frozen=True)
class RefreshResult:
    refresh_token: str
    generation: int


class SyntheticSessionStore:
    """Tiny in-memory session model used to reproduce a concurrent refresh race."""

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
        next_generation = self._generation + 1
        next_token = f"refresh-synthetic-{next_generation}"
        self._generation = next_generation
        self._refresh_token = next_token
        return RefreshResult(next_token, next_generation)
