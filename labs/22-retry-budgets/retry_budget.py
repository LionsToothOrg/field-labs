from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Callable


@dataclass(frozen=True)
class RetryBudgetSnapshot:
    """Inspectable counters for one synthetic retry-budget window."""

    originals: int
    retries_admitted: int
    retries_rejected: int
    retry_limit: int
    retries_remaining: int
    window_started_at: float | None = None


class RetryBudget:
    """Bound retry amplification relative to observed original attempts."""

    def __init__(
        self,
        ratio: float,
        minimum_retries: int = 0,
        *,
        window_seconds: float | None = None,
        clock: Callable[[], float] | None = None,
    ) -> None:
        if not isinstance(ratio, (int, float)) or isinstance(ratio, bool):
            raise TypeError("ratio must be a number")
        if not math.isfinite(ratio) or ratio < 0 or ratio > 1:
            raise ValueError("ratio must be between 0 and 1")
        if not isinstance(minimum_retries, int) or isinstance(minimum_retries, bool):
            raise TypeError("minimum_retries must be an integer")
        if minimum_retries < 0:
            raise ValueError("minimum_retries must be non-negative")
        if window_seconds is not None:
            if (
                not isinstance(window_seconds, (int, float))
                or isinstance(window_seconds, bool)
            ):
                raise TypeError("window_seconds must be a number")
            if not math.isfinite(window_seconds) or window_seconds <= 0:
                raise ValueError("window_seconds must be positive and finite")
            if clock is None or not callable(clock):
                raise TypeError("windowed budgets require an injected clock")
        elif clock is not None:
            raise ValueError("clock requires window_seconds")

        self._ratio = float(ratio)
        self._minimum_retries = minimum_retries
        self._window_seconds = (
            float(window_seconds) if window_seconds is not None else None
        )
        self._clock = clock
        self._window_started_at = self._read_clock() if clock is not None else None
        self._last_observed_at = self._window_started_at
        self._originals = 0
        self._retries_admitted = 0
        self._retries_rejected = 0

    def _read_clock(self) -> float:
        assert self._clock is not None
        now = self._clock()
        if not isinstance(now, (int, float)) or isinstance(now, bool):
            raise TypeError("clock must return a number")
        if not math.isfinite(now):
            raise ValueError("clock must return a finite value")
        return float(now)

    def _roll_window_if_needed(self) -> None:
        if self._window_seconds is None:
            return

        now = self._read_clock()
        assert self._window_started_at is not None
        assert self._last_observed_at is not None
        if now < self._last_observed_at:
            raise ValueError("clock must not move backwards")
        self._last_observed_at = now

        if now - self._window_started_at >= self._window_seconds:
            elapsed_windows = math.floor(
                (now - self._window_started_at) / self._window_seconds
            )
            self._window_started_at += elapsed_windows * self._window_seconds
            self._originals = 0
            self._retries_admitted = 0
            self._retries_rejected = 0

    @property
    def retry_limit(self) -> int:
        self._roll_window_if_needed()
        proportional = math.floor(self._originals * self._ratio)
        return max(self._minimum_retries, proportional)

    def record_original(self) -> None:
        """Record one synthetic non-retry attempt in the active window."""

        self._roll_window_if_needed()
        self._originals += 1

    def try_acquire_retry(self) -> bool:
        """Admit a retry only while the active synthetic window has capacity."""

        self._roll_window_if_needed()
        proportional = math.floor(self._originals * self._ratio)
        limit = max(self._minimum_retries, proportional)
        if self._retries_admitted >= limit:
            self._retries_rejected += 1
            return False
        self._retries_admitted += 1
        return True

    def snapshot(self) -> RetryBudgetSnapshot:
        self._roll_window_if_needed()
        proportional = math.floor(self._originals * self._ratio)
        limit = max(self._minimum_retries, proportional)
        return RetryBudgetSnapshot(
            originals=self._originals,
            retries_admitted=self._retries_admitted,
            retries_rejected=self._retries_rejected,
            retry_limit=limit,
            retries_remaining=max(0, limit - self._retries_admitted),
            window_started_at=self._window_started_at,
        )
