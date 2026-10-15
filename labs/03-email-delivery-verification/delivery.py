from dataclasses import dataclass
from enum import Enum


class DeliveryState(str, Enum):
    GENERATED = "generated"
    ACCEPTED = "accepted"
    DEFERRED = "deferred"
    BOUNCED = "bounced"
    DELIVERED = "delivered"


class ReconciliationOutcome(str, Enum):
    APPLIED = "applied"
    DUPLICATE = "duplicate"
    STALE = "stale"
    CONTRADICTORY = "contradictory"


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
class ReconciliationDecision:
    event_id: str
    sequence: int
    outcome: ReconciliationOutcome


@dataclass(frozen=True)
class ReconciliationResult:
    trace: DeliveryTrace
    decisions: tuple[ReconciliationDecision, ...]

    @property
    def applied_event_ids(self) -> tuple[str, ...]:
        return tuple(
            decision.event_id
            for decision in self.decisions
            if decision.outcome is ReconciliationOutcome.APPLIED
        )

    @property
    def ignored_event_ids(self) -> tuple[str, ...]:
        return tuple(
            decision.event_id
            for decision in self.decisions
            if decision.outcome is not ReconciliationOutcome.APPLIED
        )


def reconcile_provider_events(
    trace: DeliveryTrace, events: tuple[ProviderEvent, ...]
) -> ReconciliationResult:
    """Apply provider evidence and record content-minimizing reconciliation decisions.

    Duplicate event IDs are ignored after their first occurrence. Events at or below the
    latest applied sequence are stale. Contradictory transitions are ignored rather than
    rewriting stronger evidence already present in the trace. Decisions intentionally omit
    provider event detail so an audit trail does not require payload-content logging.
    """
    current = trace
    seen_ids: set[str] = set()
    decisions: list[ReconciliationDecision] = []
    latest_sequence = -1

    for event in events:
        if event.event_id in seen_ids:
            decisions.append(
                ReconciliationDecision(
                    event.event_id, event.sequence, ReconciliationOutcome.DUPLICATE
                )
            )
            continue
        seen_ids.add(event.event_id)

        if event.sequence <= latest_sequence:
            decisions.append(
                ReconciliationDecision(
                    event.event_id, event.sequence, ReconciliationOutcome.STALE
                )
            )
            continue

        candidate = DeliveryEvent(event.state, event.detail)
        try:
            current = current.record(candidate)
        except ValueError:
            decisions.append(
                ReconciliationDecision(
                    event.event_id, event.sequence, ReconciliationOutcome.CONTRADICTORY
                )
            )
            continue

        decisions.append(
            ReconciliationDecision(
                event.event_id, event.sequence, ReconciliationOutcome.APPLIED
            )
        )
        latest_sequence = event.sequence

    return ReconciliationResult(current, tuple(decisions))


def generated(message_id: str = "msg-synthetic-001") -> DeliveryTrace:
    return DeliveryTrace(
        (DeliveryEvent(DeliveryState.GENERATED, f"application created {message_id}"),)
    )
