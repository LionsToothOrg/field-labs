from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class AttemptResult:
    status_code: int
    retry_after_seconds: int | None = None


@dataclass(frozen=True)
class RetryDecision:
    attempt: int
    status_code: int
    action: str
    delay_seconds: int | None


RETRYABLE_STATUS_CODES = frozenset({429, 500, 502, 503, 504})


def _backoff_seconds(attempt: int, base_delay_seconds: int, max_delay_seconds: int) -> int:
    return min(base_delay_seconds * (2 ** (attempt - 1)), max_delay_seconds)


def plan_retries(
    results: Iterable[AttemptResult],
    *,
    max_attempts: int = 4,
    base_delay_seconds: int = 1,
    max_delay_seconds: int = 30,
) -> list[RetryDecision]:
    """Build deterministic retry decisions from a synthetic sequence of responses."""
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")
    if base_delay_seconds < 0 or max_delay_seconds < 0:
        raise ValueError("delay bounds cannot be negative")

    decisions: list[RetryDecision] = []

    for attempt, result in enumerate(results, start=1):
        if attempt > max_attempts:
            break

        if 200 <= result.status_code < 300:
            decisions.append(RetryDecision(attempt, result.status_code, "succeed", None))
            break

        if result.status_code not in RETRYABLE_STATUS_CODES:
            decisions.append(RetryDecision(attempt, result.status_code, "stop", None))
            break

        if attempt == max_attempts:
            decisions.append(RetryDecision(attempt, result.status_code, "exhaust", None))
            break

        backoff = _backoff_seconds(attempt, base_delay_seconds, max_delay_seconds)
        retry_after = result.retry_after_seconds
        if retry_after is not None and retry_after < 0:
            raise ValueError("retry_after_seconds cannot be negative")

        delay = max(backoff, retry_after or 0)
        decisions.append(RetryDecision(attempt, result.status_code, "retry", delay))

    return decisions
