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
