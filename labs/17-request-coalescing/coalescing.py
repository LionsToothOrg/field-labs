from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Request:
    request_id: str
    key: str


@dataclass(frozen=True)
class CoalescedGroup:
    key: str
    leader: Request
    followers: tuple[Request, ...]

    @property
    def origin_loads(self) -> int:
        return 1


@dataclass(frozen=True)
class CoalescingResult:
    groups: tuple[CoalescedGroup, ...]

    @property
    def request_count(self) -> int:
        return sum(1 + len(group.followers) for group in self.groups)

    @property
    def origin_loads(self) -> int:
        return sum(group.origin_loads for group in self.groups)

    @property
    def avoided_origin_loads(self) -> int:
        return self.request_count - self.origin_loads


@dataclass(frozen=True)
class DeliveredResult:
    request_id: str
    key: str
    value: str
    source_request_id: str


@dataclass(frozen=True)
class FanoutResult:
    deliveries: tuple[DeliveredResult, ...]
    origin_loads: int


@dataclass(frozen=True)
class DeliveredFailure:
    request_id: str
    key: str
    error: str
    source_request_id: str


@dataclass(frozen=True)
class FailureFanoutResult:
    deliveries: tuple[DeliveredFailure, ...]
    origin_loads: int


def coalesce_requests(requests: Iterable[Request]) -> CoalescingResult:
    """Group a deterministic synthetic arrival batch by resource key.

    The first request for each key is the leader that would perform the
    downstream load. Later requests for that same key become followers.
    """
    ordered = tuple(requests)
    seen_ids: set[str] = set()
    grouped: dict[str, list[Request]] = {}

    for request in ordered:
        if not request.request_id:
            raise ValueError("request_id must not be empty")
        if not request.key:
            raise ValueError("key must not be empty")
        if request.request_id in seen_ids:
            raise ValueError(f"duplicate request_id: {request.request_id}")
        seen_ids.add(request.request_id)
        grouped.setdefault(request.key, []).append(request)

    groups = tuple(
        CoalescedGroup(key=key, leader=members[0], followers=tuple(members[1:]))
        for key, members in grouped.items()
    )
    return CoalescingResult(groups=groups)


def fan_out_successes(
    result: CoalescingResult,
    leader_values: dict[str, str],
) -> FanoutResult:
    """Deliver each successful synthetic leader value to its coalesced group.

    Values are keyed by leader request ID so followers cannot accidentally
    supply independent origin results. Every group must have exactly one
    supplied leader value before any deliveries are returned.
    """
    expected_leaders = {group.leader.request_id for group in result.groups}
    supplied_leaders = set(leader_values)

    missing = expected_leaders - supplied_leaders
    unexpected = supplied_leaders - expected_leaders
    if missing:
        raise ValueError(f"missing leader value: {sorted(missing)[0]}")
    if unexpected:
        raise ValueError(f"unexpected leader value: {sorted(unexpected)[0]}")

    deliveries: list[DeliveredResult] = []
    for group in result.groups:
        value = leader_values[group.leader.request_id]
        for request in (group.leader, *group.followers):
            deliveries.append(
                DeliveredResult(
                    request_id=request.request_id,
                    key=group.key,
                    value=value,
                    source_request_id=group.leader.request_id,
                )
            )

    return FanoutResult(deliveries=tuple(deliveries), origin_loads=result.origin_loads)


def fan_out_failures(
    result: CoalescingResult,
    leader_errors: dict[str, str],
) -> FailureFanoutResult:
    """Deliver each synthetic leader failure to its whole coalesced group.

    Failures are keyed only by leader request ID. Every group must have one
    non-empty failure before any delivery is returned, preventing followers
    from supplying independent outcomes or implying duplicate origin work.
    """
    expected_leaders = {group.leader.request_id for group in result.groups}
    supplied_leaders = set(leader_errors)

    missing = expected_leaders - supplied_leaders
    unexpected = supplied_leaders - expected_leaders
    if missing:
        raise ValueError(f"missing leader failure: {sorted(missing)[0]}")
    if unexpected:
        raise ValueError(f"unexpected leader failure: {sorted(unexpected)[0]}")

    empty_errors = sorted(leader_id for leader_id, error in leader_errors.items() if not error)
    if empty_errors:
        raise ValueError(f"empty leader failure: {empty_errors[0]}")

    deliveries: list[DeliveredFailure] = []
    for group in result.groups:
        error = leader_errors[group.leader.request_id]
        for request in (group.leader, *group.followers):
            deliveries.append(
                DeliveredFailure(
                    request_id=request.request_id,
                    key=group.key,
                    error=error,
                    source_request_id=group.leader.request_id,
                )
            )

    return FailureFanoutResult(deliveries=tuple(deliveries), origin_loads=result.origin_loads)
