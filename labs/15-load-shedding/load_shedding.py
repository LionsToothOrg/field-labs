from dataclasses import dataclass
from typing import Iterable, Literal


Decision = Literal["running", "queued", "shed"]


@dataclass(frozen=True)
class Admission:
    request_id: str
    decision: Decision


@dataclass(frozen=True)
class BurstResult:
    admissions: tuple[Admission, ...]
    running: int
    queued: int
    shed: int


def _require_capacity(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")


def admit_burst(
    request_ids: Iterable[str], *, concurrency_limit: int, queue_limit: int
) -> BurstResult:
    """Classify a synthetic arrival burst against bounded service capacity."""

    _require_capacity("concurrency_limit", concurrency_limit)
    _require_capacity("queue_limit", queue_limit)

    admissions: list[Admission] = []
    running = 0
    queued = 0
    shed = 0

    for request_id in request_ids:
        if not isinstance(request_id, str) or not request_id:
            raise ValueError("request_ids must contain non-empty strings")

        if running < concurrency_limit:
            decision: Decision = "running"
            running += 1
        elif queued < queue_limit:
            decision = "queued"
            queued += 1
        else:
            decision = "shed"
            shed += 1

        admissions.append(Admission(request_id=request_id, decision=decision))

    return BurstResult(
        admissions=tuple(admissions),
        running=running,
        queued=queued,
        shed=shed,
    )
