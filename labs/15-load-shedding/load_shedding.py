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


@dataclass(frozen=True)
class RecoveryStep:
    completed: tuple[str, ...]
    promoted: tuple[str, ...]
    running: tuple[str, ...]
    queued: tuple[str, ...]


def _require_capacity(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")


def _require_request_ids(request_ids: Iterable[str]) -> tuple[str, ...]:
    values = tuple(request_ids)
    if any(not isinstance(request_id, str) or not request_id for request_id in values):
        raise ValueError("request_ids must contain non-empty strings")
    return values


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

    for request_id in _require_request_ids(request_ids):
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


def drain_admitted(
    result: BurstResult, *, concurrency_limit: int
) -> tuple[RecoveryStep, ...]:
    """Drain admitted synthetic work in deterministic FIFO completion rounds."""

    _require_capacity("concurrency_limit", concurrency_limit)
    if concurrency_limit == 0 and (result.running or result.queued):
        raise ValueError("concurrency_limit must be positive when admitted work exists")

    running = [
        admission.request_id
        for admission in result.admissions
        if admission.decision == "running"
    ]
    queued = [
        admission.request_id
        for admission in result.admissions
        if admission.decision == "queued"
    ]

    if len(running) > concurrency_limit:
        raise ValueError("concurrency_limit cannot be below the admitted running count")

    steps: list[RecoveryStep] = []
    while running:
        completed = tuple(running)
        running = []
        promoted: list[str] = []
        while queued and len(running) < concurrency_limit:
            request_id = queued.pop(0)
            running.append(request_id)
            promoted.append(request_id)
        steps.append(
            RecoveryStep(
                completed=completed,
                promoted=tuple(promoted),
                running=tuple(running),
                queued=tuple(queued),
            )
        )

    return tuple(steps)
