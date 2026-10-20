from dataclasses import dataclass
from typing import Literal


SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


@dataclass(frozen=True)
class Request:
    request_id: str
    method: str
    primary_latency_ms: int
    hedge_after_ms: int


@dataclass(frozen=True)
class HedgeDecision:
    request_id: str
    hedge_started: bool
    attempt_count: int
    reason: Literal["primary_completed", "hedge_started", "unsafe_method"]


@dataclass(frozen=True)
class RaceOutcome:
    request_id: str
    winner: Literal["primary", "hedge"]
    completed_at_ms: int
    loser: Literal["primary", "hedge"] | None
    cancellation_requested: bool
    loser_work_may_have_started: bool


def plan_hedge(request: Request) -> HedgeDecision:
    """Return a deterministic hedge-admission decision for one synthetic request."""
    if not request.request_id.strip():
        raise ValueError("request_id must be non-empty")
    if request.primary_latency_ms < 0:
        raise ValueError("primary_latency_ms must be >= 0")
    if request.hedge_after_ms <= 0:
        raise ValueError("hedge_after_ms must be > 0")

    method = request.method.upper().strip()
    if not method:
        raise ValueError("method must be non-empty")

    if request.primary_latency_ms <= request.hedge_after_ms:
        return HedgeDecision(request.request_id, False, 1, "primary_completed")

    if method not in SAFE_METHODS:
        return HedgeDecision(request.request_id, False, 1, "unsafe_method")

    return HedgeDecision(request.request_id, True, 2, "hedge_started")


def resolve_race(
    decision: HedgeDecision,
    primary_completed_at_ms: int,
    hedge_completed_at_ms: int | None = None,
) -> RaceOutcome:
    """Select the first modeled completion and request cancellation of its loser."""
    if primary_completed_at_ms < 0:
        raise ValueError("primary_completed_at_ms must be >= 0")

    if not decision.hedge_started:
        if decision.attempt_count != 1:
            raise ValueError("non-hedged decisions must have one attempt")
        if hedge_completed_at_ms is not None:
            raise ValueError("hedge completion requires an admitted hedge")
        return RaceOutcome(
            decision.request_id,
            "primary",
            primary_completed_at_ms,
            None,
            False,
            False,
        )

    if decision.attempt_count != 2:
        raise ValueError("hedged decisions must have two attempts")
    if hedge_completed_at_ms is None:
        raise ValueError("hedge_completed_at_ms is required for an admitted hedge")
    if hedge_completed_at_ms < 0:
        raise ValueError("hedge_completed_at_ms must be >= 0")

    if primary_completed_at_ms <= hedge_completed_at_ms:
        winner, loser, completed_at_ms = "primary", "hedge", primary_completed_at_ms
    else:
        winner, loser, completed_at_ms = "hedge", "primary", hedge_completed_at_ms

    return RaceOutcome(
        decision.request_id,
        winner,
        completed_at_ms,
        loser,
        True,
        True,
    )
