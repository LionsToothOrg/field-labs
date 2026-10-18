from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class DeadlineBudget:
    allowed: bool
    timeout: float | None
    remaining: float
    reason: str


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
