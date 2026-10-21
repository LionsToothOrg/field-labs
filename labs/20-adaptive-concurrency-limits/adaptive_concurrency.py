"""Deterministic adaptive concurrency-limit model for synthetic experiments."""

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class LimitPolicy:
    minimum: int
    maximum: int
    increase_by: int = 1
    decrease_ratio: float = 0.5
    latency_tolerance_ms: int = 0

    def __post_init__(self) -> None:
        if self.minimum < 1:
            raise ValueError("minimum must be at least 1")
        if self.maximum < self.minimum:
            raise ValueError("maximum must be at least minimum")
        if self.increase_by < 1:
            raise ValueError("increase_by must be at least 1")
        if not 0 < self.decrease_ratio < 1:
            raise ValueError("decrease_ratio must be between 0 and 1")
        if self.latency_tolerance_ms < 0:
            raise ValueError("latency_tolerance_ms must be non-negative")


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


@dataclass(frozen=True)
class ControllerTrace:
    initial_limit: int
    final_limit: int
    decisions: tuple[LimitDecision, ...]


def _validate_current_limit(current_limit: int, policy: LimitPolicy) -> None:
    if not policy.minimum <= current_limit <= policy.maximum:
        raise ValueError("current_limit must be within policy bounds")


def _decrease(current_limit: int, policy: LimitPolicy) -> int:
    return max(policy.minimum, int(current_limit * policy.decrease_ratio))


def _increase(current_limit: int, policy: LimitPolicy) -> int:
    return min(policy.maximum, current_limit + policy.increase_by)


def update_limit(current_limit: int, sample: Sample, policy: LimitPolicy) -> LimitDecision:
    """Update a bounded limit from one synthetic feedback sample."""
    _validate_current_limit(current_limit, policy)

    if sample.overloaded:
        return LimitDecision(current_limit, _decrease(current_limit, policy), "overload")

    if policy.latency_tolerance_ms:
        lower = sample.target_latency_ms - policy.latency_tolerance_ms
        upper = sample.target_latency_ms + policy.latency_tolerance_ms
        if lower <= sample.latency_ms <= upper:
            return LimitDecision(current_limit, current_limit, "within_tolerance")
        if sample.latency_ms > upper:
            return LimitDecision(current_limit, _decrease(current_limit, policy), "latency_above_target")
    elif sample.latency_ms > sample.target_latency_ms:
        return LimitDecision(current_limit, _decrease(current_limit, policy), "latency_above_target")

    return LimitDecision(current_limit, _increase(current_limit, policy), "healthy")


def update_limit_from_window(
    current_limit: int, samples: Sequence[Sample], policy: LimitPolicy
) -> LimitDecision:
    """Update once from a complete synthetic feedback window.

    All samples must use the same target. Any explicit overload signal wins over
    latency aggregation. Otherwise the arithmetic mean latency is compared with
    the shared target and optional tolerance without rounding.
    """
    _validate_current_limit(current_limit, policy)
    if not samples:
        raise ValueError("feedback window must contain at least one sample")

    target = samples[0].target_latency_ms
    if any(sample.target_latency_ms != target for sample in samples):
        raise ValueError("feedback window samples must share one target latency")

    if any(sample.overloaded for sample in samples):
        return LimitDecision(current_limit, _decrease(current_limit, policy), "window_overload")

    total_latency = sum(sample.latency_ms for sample in samples)
    sample_count = len(samples)
    if policy.latency_tolerance_ms:
        lower_total = (target - policy.latency_tolerance_ms) * sample_count
        upper_total = (target + policy.latency_tolerance_ms) * sample_count
        if lower_total <= total_latency <= upper_total:
            return LimitDecision(current_limit, current_limit, "window_within_tolerance")
        if total_latency > upper_total:
            return LimitDecision(
                current_limit, _decrease(current_limit, policy), "window_latency_above_target"
            )
    elif total_latency > target * sample_count:
        return LimitDecision(
            current_limit, _decrease(current_limit, policy), "window_latency_above_target"
        )

    return LimitDecision(current_limit, _increase(current_limit, policy), "window_healthy")


def run_feedback_trace(
    initial_limit: int,
    windows: Sequence[Sequence[Sample]],
    policy: LimitPolicy,
) -> ControllerTrace:
    """Apply complete feedback windows sequentially to one bounded controller state."""
    _validate_current_limit(initial_limit, policy)
    if not windows:
        raise ValueError("feedback trace must contain at least one window")

    current_limit = initial_limit
    decisions: list[LimitDecision] = []
    for samples in windows:
        decision = update_limit_from_window(current_limit, samples, policy)
        decisions.append(decision)
        current_limit = decision.next_limit

    return ControllerTrace(initial_limit, current_limit, tuple(decisions))


def admit(in_flight: int, concurrency_limit: int) -> bool:
    """Return whether one more synthetic request may enter."""
    if in_flight < 0:
        raise ValueError("in_flight must be non-negative")
    if concurrency_limit < 1:
        raise ValueError("concurrency_limit must be at least 1")
    return in_flight < concurrency_limit
