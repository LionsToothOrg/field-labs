"""Deterministic model of cooperative cancellation across parallel work."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping


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


def _require_finite_nonnegative(name: str, value: float) -> None:
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"{name} must be finite and non-negative")


def simulate_parallel_work(
    workloads: Mapping[str, float],
    *,
    cancel_at: float,
    check_interval: float,
    propagate_cancellation: bool,
) -> SimulationResult:
    """Model workers that either observe or ignore a caller cancellation.

    Workers start together at synthetic time zero. Cooperative workers check for
    cancellation at fixed intervals. A worker that finishes before its next
    check completes normally; otherwise it stops at the first check at or after
    ``cancel_at``. Non-propagating workers run their full planned duration.
    """

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
            observed_at = math.ceil(cancel_at / check_interval) * check_interval
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
