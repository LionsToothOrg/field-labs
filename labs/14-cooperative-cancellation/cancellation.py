"""Deterministic model of cooperative cancellation across synthetic work."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping, Sequence


@dataclass(frozen=True)
class WorkResult:
    worker: str
    planned: float
    elapsed: float
    completed: bool
    cancelled: bool


@dataclass(frozen=True)
class SimulationResult:
    workers: tuple[WorkResult, ...]
    wall_time: float
    total_work: float


@dataclass(frozen=True)
class NestedWorkResult:
    stages: tuple[WorkResult, ...]
    elapsed: float
    completed: bool
    cancelled: bool


@dataclass(frozen=True)
class FinalizedWorkResult:
    planned: float
    work_elapsed: float
    cleanup_elapsed: float
    elapsed: float
    completed: bool
    cancelled: bool
    cleanup_ran: bool


def _require_finite_nonnegative(name: str, value: float) -> None:
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"{name} must be finite and non-negative")


def _cancellation_observed_at(cancel_at: float, check_interval: float) -> float:
    return math.ceil(cancel_at / check_interval) * check_interval


def simulate_parallel_work(
    workloads: Mapping[str, float],
    *,
    cancel_at: float,
    check_interval: float,
    propagate_cancellation: bool,
) -> SimulationResult:
    """Model workers that either observe or ignore a caller cancellation."""

    _require_finite_nonnegative("cancel_at", cancel_at)
    if not math.isfinite(check_interval) or check_interval <= 0:
        raise ValueError("check_interval must be finite and greater than zero")
    if not workloads:
        raise ValueError("workloads must not be empty")

    results: list[WorkResult] = []
    for worker, planned in workloads.items():
        if not worker:
            raise ValueError("worker names must not be empty")
        _require_finite_nonnegative(f"workload for {worker}", planned)

        if not propagate_cancellation or planned <= cancel_at:
            elapsed = planned
            completed = True
            cancelled = False
        else:
            observed_at = _cancellation_observed_at(cancel_at, check_interval)
            elapsed = min(planned, observed_at)
            completed = planned <= observed_at
            cancelled = not completed

        results.append(
            WorkResult(
                worker=worker,
                planned=planned,
                elapsed=elapsed,
                completed=completed,
                cancelled=cancelled,
            )
        )

    return SimulationResult(
        workers=tuple(results),
        wall_time=max(result.elapsed for result in results),
        total_work=sum(result.elapsed for result in results),
    )


def simulate_nested_work(
    stages: Sequence[tuple[str, float]],
    *,
    cancel_at: float,
    check_interval: float,
    propagate_cancellation: bool,
) -> NestedWorkResult:
    """Model sequential nested stages sharing one caller cancellation signal.

    Cooperative stages observe cancellation on a global polling schedule measured
    from synthetic time zero. Once cancellation is observed, no later stage is
    admitted. Without propagation, every stage runs to completion.
    """

    _require_finite_nonnegative("cancel_at", cancel_at)
    if not math.isfinite(check_interval) or check_interval <= 0:
        raise ValueError("check_interval must be finite and greater than zero")
    if not stages:
        raise ValueError("stages must not be empty")

    observed_at = _cancellation_observed_at(cancel_at, check_interval)
    elapsed = 0.0
    results: list[WorkResult] = []

    for stage, planned in stages:
        if not stage:
            raise ValueError("stage names must not be empty")
        _require_finite_nonnegative(f"workload for {stage}", planned)

        if propagate_cancellation and elapsed >= observed_at:
            break

        if propagate_cancellation and elapsed < observed_at < elapsed + planned:
            stage_elapsed = observed_at - elapsed
            results.append(
                WorkResult(stage, planned, stage_elapsed, completed=False, cancelled=True)
            )
            elapsed = observed_at
            return NestedWorkResult(tuple(results), elapsed, completed=False, cancelled=True)

        results.append(
            WorkResult(stage, planned, planned, completed=True, cancelled=False)
        )
        elapsed += planned

    cancelled = propagate_cancellation and elapsed >= observed_at and len(results) < len(stages)
    return NestedWorkResult(
        stages=tuple(results),
        elapsed=elapsed,
        completed=len(results) == len(stages) and not cancelled,
        cancelled=cancelled,
    )


def simulate_finalized_work(
    *,
    planned: float,
    cleanup_duration: float,
    cancel_at: float,
    check_interval: float,
    propagate_cancellation: bool,
) -> FinalizedWorkResult:
    """Model cleanup that runs once after work completes or observes cancellation.

    Cleanup is intentionally non-cancellable in this model so the experiment can
    make its guarantee explicit: once admitted, finalization runs to completion.
    """

    _require_finite_nonnegative("planned", planned)
    _require_finite_nonnegative("cleanup_duration", cleanup_duration)
    _require_finite_nonnegative("cancel_at", cancel_at)
    if not math.isfinite(check_interval) or check_interval <= 0:
        raise ValueError("check_interval must be finite and greater than zero")

    if not propagate_cancellation or planned <= cancel_at:
        work_elapsed = planned
        completed = True
        cancelled = False
    else:
        observed_at = _cancellation_observed_at(cancel_at, check_interval)
        work_elapsed = min(planned, observed_at)
        completed = planned <= observed_at
        cancelled = not completed

    return FinalizedWorkResult(
        planned=planned,
        work_elapsed=work_elapsed,
        cleanup_elapsed=cleanup_duration,
        elapsed=work_elapsed + cleanup_duration,
        completed=completed,
        cancelled=cancelled,
        cleanup_ran=True,
    )
