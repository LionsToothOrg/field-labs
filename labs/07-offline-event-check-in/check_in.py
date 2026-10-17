"""Synthetic offline check-in reconciliation for Lab 07."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CheckIn:
    check_in_id: str
    credential_id: str
    device_id: str
    accepted_at: int


@dataclass(frozen=True)
class ReconciliationResult:
    accepted: tuple[CheckIn, ...]
    conflicts: tuple[CheckIn, ...]


def accept_offline(
    check_in_id: str,
    credential_id: str,
    device_id: str,
    accepted_at: int,
) -> CheckIn:
    """Model a device accepting a credential while disconnected."""
    return CheckIn(
        check_in_id=check_in_id,
        credential_id=credential_id,
        device_id=device_id,
        accepted_at=accepted_at,
    )


def reconcile(check_ins: list[CheckIn]) -> ReconciliationResult:
    """Keep one deterministic winner per credential and surface later duplicates."""
    ordered = sorted(
        check_ins,
        key=lambda item: (item.accepted_at, item.device_id, item.check_in_id),
    )
    winners: dict[str, CheckIn] = {}
    conflicts: list[CheckIn] = []

    for check_in in ordered:
        if check_in.credential_id in winners:
            conflicts.append(check_in)
        else:
            winners[check_in.credential_id] = check_in

    return ReconciliationResult(
        accepted=tuple(winners.values()),
        conflicts=tuple(conflicts),
    )


def merge_sync(
    known_check_ins: list[CheckIn],
    incoming_check_ins: list[CheckIn],
) -> tuple[CheckIn, ...]:
    """Merge a sync batch by stable check-in identity so replay is idempotent.

    A repeated ID must carry the same payload. Conflicting reuse of an ID is
    rejected instead of silently replacing an already-observed decision.
    """
    merged = {item.check_in_id: item for item in known_check_ins}

    for item in incoming_check_ins:
        existing = merged.get(item.check_in_id)
        if existing is not None and existing != item:
            raise ValueError(f"conflicting payload for check-in ID {item.check_in_id}")
        merged[item.check_in_id] = item

    return tuple(sorted(merged.values(), key=lambda item: item.check_in_id))
