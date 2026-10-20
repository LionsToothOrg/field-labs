from dataclasses import dataclass
from enum import Enum


class CacheDecision(str, Enum):
    FRESH = "fresh"
    STALE = "stale"
    MISS = "miss"


class RevalidationOutcome(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"


@dataclass(frozen=True)
class CacheEntry:
    value: str
    stored_at_ms: int
    ttl_ms: int


@dataclass(frozen=True)
class CacheResult:
    decision: CacheDecision
    value: str | None
    age_ms: int | None
    revalidate: bool


@dataclass(frozen=True)
class RefreshRequest:
    request_id: str
    cache_key: str


@dataclass(frozen=True)
class RefreshGroup:
    cache_key: str
    leader_request_id: str
    follower_request_ids: tuple[str, ...]


@dataclass(frozen=True)
class RefreshPlan:
    groups: tuple[RefreshGroup, ...]
    origin_refresh_count: int


def evaluate_cache_entry(
    entry: CacheEntry | None,
    *,
    now_ms: int,
    max_stale_ms: int,
) -> CacheResult:
    """Apply a deterministic fresh/stale/miss policy to one synthetic cache entry."""
    if isinstance(now_ms, bool) or not isinstance(now_ms, int) or now_ms < 0:
        raise ValueError("now_ms must be a non-negative integer")
    if isinstance(max_stale_ms, bool) or not isinstance(max_stale_ms, int) or max_stale_ms < 0:
        raise ValueError("max_stale_ms must be a non-negative integer")

    if entry is None:
        return CacheResult(CacheDecision.MISS, None, None, False)

    if not isinstance(entry.value, str) or not entry.value:
        raise ValueError("entry value must be a non-empty string")
    for name, value in (("stored_at_ms", entry.stored_at_ms), ("ttl_ms", entry.ttl_ms)):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"{name} must be a non-negative integer")
    if entry.ttl_ms == 0:
        raise ValueError("ttl_ms must be positive")
    if now_ms < entry.stored_at_ms:
        raise ValueError("now_ms cannot precede stored_at_ms")

    age_ms = now_ms - entry.stored_at_ms
    if age_ms <= entry.ttl_ms:
        return CacheResult(CacheDecision.FRESH, entry.value, age_ms, False)

    stale_age_ms = age_ms - entry.ttl_ms
    if stale_age_ms <= max_stale_ms:
        return CacheResult(CacheDecision.STALE, entry.value, age_ms, True)

    return CacheResult(CacheDecision.MISS, None, age_ms, False)


def apply_revalidation_outcome(
    entry: CacheEntry,
    *,
    outcome: RevalidationOutcome,
    now_ms: int,
    max_stale_ms: int,
    refreshed_value: str | None = None,
) -> CacheResult:
    """Apply one synthetic refresh outcome without extending a stale entry's lifetime."""
    current = evaluate_cache_entry(entry, now_ms=now_ms, max_stale_ms=max_stale_ms)

    if not isinstance(outcome, RevalidationOutcome):
        raise ValueError("outcome must be a RevalidationOutcome")
    if current.decision is CacheDecision.FRESH:
        raise ValueError("revalidation requires an expired cache entry")

    if outcome is RevalidationOutcome.FAILURE:
        if refreshed_value is not None:
            raise ValueError("failed revalidation cannot provide a refreshed value")
        return current

    if not isinstance(refreshed_value, str) or not refreshed_value:
        raise ValueError("successful revalidation requires a non-empty refreshed value")

    refreshed_entry = CacheEntry(
        value=refreshed_value,
        stored_at_ms=now_ms,
        ttl_ms=entry.ttl_ms,
    )
    return evaluate_cache_entry(refreshed_entry, now_ms=now_ms, max_stale_ms=max_stale_ms)


def plan_stale_refreshes(
    requests: list[RefreshRequest],
    *,
    entries_by_key: dict[str, CacheEntry | None],
    now_ms: int,
    max_stale_ms: int,
) -> RefreshPlan:
    """Elect one synthetic refresh leader per stale cache key."""
    seen_request_ids: set[str] = set()
    grouped_request_ids: dict[str, list[str]] = {}

    for request in requests:
        if not isinstance(request, RefreshRequest):
            raise ValueError("requests must contain RefreshRequest values")
        if not isinstance(request.request_id, str) or not request.request_id:
            raise ValueError("request_id must be a non-empty string")
        if not isinstance(request.cache_key, str) or not request.cache_key:
            raise ValueError("cache_key must be a non-empty string")
        if request.request_id in seen_request_ids:
            raise ValueError("request_id values must be unique")
        seen_request_ids.add(request.request_id)

        if request.cache_key not in entries_by_key:
            raise ValueError("every request cache_key must have an explicit cache entry")
        decision = evaluate_cache_entry(
            entries_by_key[request.cache_key],
            now_ms=now_ms,
            max_stale_ms=max_stale_ms,
        )
        if decision.decision is not CacheDecision.STALE:
            raise ValueError("refresh planning requires stale cache entries")

        grouped_request_ids.setdefault(request.cache_key, []).append(request.request_id)

    groups = tuple(
        RefreshGroup(
            cache_key=cache_key,
            leader_request_id=request_ids[0],
            follower_request_ids=tuple(request_ids[1:]),
        )
        for cache_key, request_ids in grouped_request_ids.items()
    )
    return RefreshPlan(groups=groups, origin_refresh_count=len(groups))
