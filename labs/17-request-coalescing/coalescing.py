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
