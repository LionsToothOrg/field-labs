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
