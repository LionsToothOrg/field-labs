from dataclasses import dataclass
from enum import Enum


class DeliveryState(str, Enum):
    GENERATED = "generated"
    ACCEPTED = "accepted"
    DEFERRED = "deferred"
    BOUNCED = "bounced"
    DELIVERED = "delivered"


@dataclass(frozen=True)
class DeliveryEvent:
    state: DeliveryState
    detail: str


@dataclass(frozen=True)
class ProviderEvent:
    event_id: str
    sequence: int
    state: DeliveryState
    detail: str


@dataclass(frozen=True)
class DeliveryTrace:
    events: tuple[DeliveryEvent, ...]

    @property
    def current_state(self) -> DeliveryState:
        return self.events[-1].state

    def record(self, event: DeliveryEvent) -> "DeliveryTrace":
        allowed = {
            DeliveryState.GENERATED: {DeliveryState.ACCEPTED},
            DeliveryState.ACCEPTED: {
                DeliveryState.DEFERRED,
                DeliveryState.BOUNCED,
                DeliveryState.DELIVERED,
            },
            DeliveryState.DEFERRED: {
                DeliveryState.DEFERRED,
                DeliveryState.BOUNCED,
                DeliveryState.DELIVERED,
            },
            DeliveryState.BOUNCED: set(),
            DeliveryState.DELIVERED: set(),
        }
        if event.state not in allowed[self.current_state]:
            raise ValueError(
                f"invalid delivery transition: {self.current_state.value} -> {event.state.value}"
            )
        return DeliveryTrace(self.events + (event,))


@dataclass(frozen=True)
class ReconciliationResult:
    trace: DeliveryTrace
    applied_event_ids: tuple[str, ...]
    ignored_event_ids: tuple[str, ...]


def reconcile_provider_events(
    trace: DeliveryTrace, events: tuple[ProviderEvent, ...]
) -> ReconciliationResult:
    """Apply provider evidence in sequence order without weakening state guarantees.

    Duplicate event IDs are ignored after their first occurrence. Events at or below the
    latest applied sequence are stale. Contradictory transitions are ignored rather than
    rewriting stronger evidence already present in the trace.
    """
    current = trace
    seen_ids: set[str] = set()
    applied: list[str] = []
    ignored: list[str] = []
    latest_sequence = -1

    for event in events:
        if event.event_id in seen_ids:
            ignored.append(event.event_id)
            continue
        seen_ids.add(event.event_id)

        if event.sequence <= latest_sequence:
            ignored.append(event.event_id)
            continue

        candidate = DeliveryEvent(event.state, event.detail)
        try:
            current = current.record(candidate)
        except ValueError:
            ignored.append(event.event_id)
            continue

        applied.append(event.event_id)
        latest_sequence = event.sequence

    return ReconciliationResult(current, tuple(applied), tuple(ignored))


def generated(message_id: str = "msg-synthetic-001") -> DeliveryTrace:
    return DeliveryTrace(
        (DeliveryEvent(DeliveryState.GENERATED, f"application created {message_id}"),)
    )
