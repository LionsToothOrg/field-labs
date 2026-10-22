from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class RetryBudgetSnapshot:
    """Inspectable counters for one synthetic retry-budget window."""

    originals: int
    retries_admitted: int
    retries_rejected: int
    retry_limit: int
    retries_remaining: int


class RetryBudget:
    """Bound retry amplification relative to observed original attempts."""

    def __init__(self, ratio: float, minimum_retries: int = 0) -> None:
        if not isinstance(ratio, (int, float)) or isinstance(ratio, bool):
            raise TypeError("ratio must be a number")
        if not math.isfinite(ratio) or ratio < 0 or ratio > 1:
            raise ValueError("ratio must be between 0 and 1")
        if not isinstance(minimum_retries, int) or isinstance(minimum_retries, bool):
            raise TypeError("minimum_retries must be an integer")
        if minimum_retries < 0:
            raise ValueError("minimum_retries must be non-negative")

        self._ratio = float(ratio)
        self._minimum_retries = minimum_retries
        self._originals = 0
        self._retries_admitted = 0
        self._retries_rejected = 0

    @property
    def retry_limit(self) -> int:
        proportional = math.floor(self._originals * self._ratio)
        return max(self._minimum_retries, proportional)

    def record_original(self) -> None:
        """Record one synthetic non-retry attempt."""

        self._originals += 1

    def try_acquire_retry(self) -> bool:
        """Admit a retry only while the current synthetic budget has capacity."""

        if self._retries_admitted >= self.retry_limit:
            self._retries_rejected += 1
            return False
        self._retries_admitted += 1
        return True

    def snapshot(self) -> RetryBudgetSnapshot:
        limit = self.retry_limit
        return RetryBudgetSnapshot(
            originals=self._originals,
            retries_admitted=self._retries_admitted,
            retries_rejected=self._retries_rejected,
            retry_limit=limit,
            retries_remaining=max(0, limit - self._retries_admitted),
        )
