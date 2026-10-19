from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable


@dataclass(frozen=True)
class DeadlineBudget:
    allowed: bool
    timeout: float | None
    remaining: float
    reason: str


@dataclass(frozen=True)
class SequentialCallBudget:
    step: int
    started_at: float
    duration: float
    budget: DeadlineBudget


def budget_downstream_call(
    *,
    now: float,
    deadline: float,
    max_timeout: float,
    reserve: float = 0.0,
) -> DeadlineBudget:
    """Bound a downstream timeout by the caller's remaining synthetic deadline."""
    values = {
        "now": now,
        "deadline": deadline,
        "max_timeout": max_timeout,
        "reserve": reserve,
    }
    for name, value in values.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"{name} must be a finite number")
        if not math.isfinite(value):
            raise ValueError(f"{name} must be finite")

    if max_timeout <= 0:
        raise ValueError("max_timeout must be greater than zero")
    if reserve < 0:
        raise ValueError("reserve must be non-negative")

    remaining = max(0.0, float(deadline) - float(now))
    usable = remaining - float(reserve)

    if usable <= 0:
        return DeadlineBudget(False, None, remaining, "deadline_exhausted")

    return DeadlineBudget(
        True,
        min(float(max_timeout), usable),
        remaining,
        "allowed",
    )


def budget_sequential_calls(
    *,
    start: float,
    deadline: float,
    durations: Iterable[float],
    max_timeout: float,
    reserve: float = 0.0,
) -> tuple[SequentialCallBudget, ...]:
    """Budget sequential synthetic calls against one shared absolute deadline.

    Each admitted call advances the synthetic clock by at most the timeout it was
    granted. This models deadline-aware sequencing without claiming that a real
    dependency will honor cancellation or return within its timeout.
    """
    initial = budget_downstream_call(
        now=start,
        deadline=deadline,
        max_timeout=max_timeout,
        reserve=reserve,
    )

    normalized: list[float] = []
    for duration in durations:
        if isinstance(duration, bool) or not isinstance(duration, (int, float)):
            raise TypeError("durations must contain finite numbers")
        if not math.isfinite(duration):
            raise ValueError("durations must contain finite numbers")
        if duration < 0:
            raise ValueError("durations must be non-negative")
        normalized.append(float(duration))

    now = float(start)
    results: list[SequentialCallBudget] = []
    for step, duration in enumerate(normalized, start=1):
        budget = (
            initial
            if step == 1
            else budget_downstream_call(
                now=now,
                deadline=deadline,
                max_timeout=max_timeout,
                reserve=reserve,
            )
        )
        results.append(SequentialCallBudget(step, now, duration, budget))
        if not budget.allowed:
            break
        now += min(duration, budget.timeout or 0.0)

    return tuple(results)
