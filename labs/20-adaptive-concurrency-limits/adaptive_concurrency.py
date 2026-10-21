"""Deterministic adaptive concurrency-limit model for synthetic experiments."""

from dataclasses import dataclass


@dataclass(frozen=True)
class LimitPolicy:
    minimum: int
    maximum: int
    increase_by: int = 1
    decrease_ratio: float = 0.5

    def __post_init__(self) -> None:
        if self.minimum < 1:
            raise ValueError("minimum must be at least 1")
        if self.maximum < self.minimum:
            raise ValueError("maximum must be at least minimum")
        if self.increase_by < 1:
            raise ValueError("increase_by must be at least 1")
        if not 0 < self.decrease_ratio < 1:
            raise ValueError("decrease_ratio must be between 0 and 1")


@dataclass(frozen=True)
class Sample:
    latency_ms: int
    target_latency_ms: int
    overloaded: bool = False

    def __post_init__(self) -> None:
        if self.latency_ms < 0:
            raise ValueError("latency_ms must be non-negative")
        if self.target_latency_ms <= 0:
            raise ValueError("target_latency_ms must be positive")


@dataclass(frozen=True)
class LimitDecision:
    previous_limit: int
    next_limit: int
    reason: str


def update_limit(current_limit: int, sample: Sample, policy: LimitPolicy) -> LimitDecision:
    """Update a bounded limit from one synthetic feedback sample.

    Overload or latency above the target causes multiplicative decrease.
    Healthy latency at or below the target causes additive increase.
    The result is always clamped to the configured bounds.
    """
    if not policy.minimum <= current_limit <= policy.maximum:
        raise ValueError("current_limit must be within policy bounds")

    if sample.overloaded or sample.latency_ms > sample.target_latency_ms:
        proposed = int(current_limit * policy.decrease_ratio)
        next_limit = max(policy.minimum, proposed)
        reason = "overload" if sample.overloaded else "latency_above_target"
    else:
        next_limit = min(policy.maximum, current_limit + policy.increase_by)
        reason = "healthy"

    return LimitDecision(current_limit, next_limit, reason)


def admit(in_flight: int, concurrency_limit: int) -> bool:
    """Return whether one more synthetic request may enter."""
    if in_flight < 0:
        raise ValueError("in_flight must be non-negative")
    if concurrency_limit < 1:
        raise ValueError("concurrency_limit must be at least 1")
    return in_flight < concurrency_limit
