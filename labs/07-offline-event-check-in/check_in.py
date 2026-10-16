"""Synthetic offline check-in reconciliation for Lab 07."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CheckIn:
    credential_id: str
    device_id: str
    accepted_at: int


@dataclass(frozen=True)
class ReconciliationResult:
    accepted: tuple[CheckIn, ...]
    conflicts: tuple[CheckIn, ...]


def accept_offline(credential_id: str, device_id: str, accepted_at: int) -> CheckIn:
    """Model a device accepting a credential while disconnected."""
    return CheckIn(credential_id=credential_id, device_id=device_id, accepted_at=accepted_at)


def reconcile(check_ins: list[CheckIn]) -> ReconciliationResult:
    """Keep one deterministic winner per credential and surface later duplicates."""
    ordered = sorted(check_ins, key=lambda item: (item.accepted_at, item.device_id))
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
