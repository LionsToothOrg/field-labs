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


@dataclass(frozen=True)
class ParallelCallBudget:
    call: int
    started_at: float
    duration: float
    elapsed: float
    budget: DeadlineBudget


@dataclass(frozen=True)
class ParallelFanoutBudget:
    calls: tuple[ParallelCallBudget, ...]
    completes_at: float
    remaining: float


def _finite_number(name: str, value: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a finite number")
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")
    return float(value)


def _durations(values: Iterable[float]) -> tuple[float, ...]:
    normalized: list[float] = []
    for duration in values:
        value = _finite_number("durations", duration)
        if value < 0:
            raise ValueError("durations must be non-negative")
        normalized.append(value)
    return tuple(normalized)


def budget_downstream_call(
    *,
    now: float,
    deadline: float,
    max_timeout: float,
    reserve: float = 0.0,
) -> DeadlineBudget:
    """Bound a downstream timeout by the caller's remaining synthetic deadline."""
    now = _finite_number("now", now)
    deadline = _finite_number("deadline", deadline)
    max_timeout = _finite_number("max_timeout", max_timeout)
    reserve = _finite_number("reserve", reserve)

    if max_timeout <= 0:
        raise ValueError("max_timeout must be greater than zero")
    if reserve < 0:
        raise ValueError("reserve must be non-negative")

    remaining = max(0.0, deadline - now)
    usable = remaining - reserve

    if usable <= 0:
        return DeadlineBudget(False, None, remaining, "deadline_exhausted")

    return DeadlineBudget(True, min(max_timeout, usable), remaining, "allowed")


def budget_sequential_calls(
    *,
    start: float,
    deadline: float,
    durations: Iterable[float],
    max_timeout: float,
    reserve: float = 0.0,
) -> tuple[SequentialCallBudget, ...]:
    """Budget sequential synthetic calls against one shared absolute deadline."""
    normalized = _durations(durations)
    now = _finite_number("start", start)
    results: list[SequentialCallBudget] = []

    for step, duration in enumerate(normalized, start=1):
        budget = budget_downstream_call(
            now=now,
            deadline=deadline,
            max_timeout=max_timeout,
            reserve=reserve,
        )
        results.append(SequentialCallBudget(step, now, duration, budget))
        if not budget.allowed:
            break
        now += min(duration, budget.timeout or 0.0)

    return tuple(results)


def budget_parallel_calls(
    *,
    start: float,
    deadline: float,
    durations: Iterable[float],
    max_timeout: float,
    reserve: float = 0.0,
) -> ParallelFanoutBudget:
    """Budget synthetic parallel fan-out against one shared absolute deadline.

    Every branch starts at the same synthetic instant and receives the same
    deadline-aware timeout. Fan-out wall time is therefore the slowest admitted
    branch, capped by that timeout, rather than the sum of branch durations.
    """
    normalized = _durations(durations)
    start = _finite_number("start", start)
    budget = budget_downstream_call(
        now=start,
        deadline=deadline,
        max_timeout=max_timeout,
        reserve=reserve,
    )

    calls: list[ParallelCallBudget] = []
    elapsed_values: list[float] = []
    for call, duration in enumerate(normalized, start=1):
        elapsed = min(duration, budget.timeout or 0.0) if budget.allowed else 0.0
        calls.append(ParallelCallBudget(call, start, duration, elapsed, budget))
        elapsed_values.append(elapsed)

    fanout_elapsed = max(elapsed_values, default=0.0)
    completes_at = start + fanout_elapsed
    remaining = max(0.0, _finite_number("deadline", deadline) - completes_at)
    return ParallelFanoutBudget(tuple(calls), completes_at, remaining)
