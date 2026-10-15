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
class ReconciliationState:
    current_state: DeliveryState
    seen_event_ids: frozenset[str]
    latest_sequence: int

    @classmethod
    def from_trace(cls, trace: DeliveryTrace) -> "ReconciliationState":
        return cls(trace.current_state, frozenset(), -1)


@dataclass(frozen=True)
class ReconciliationResult:
    trace: DeliveryTrace
    decisions: tuple[ReconciliationDecision, ...]
    state: ReconciliationState

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


def restore_trace(state: ReconciliationState) -> DeliveryTrace:
    """Restore only the delivery state needed to continue reconciliation.

    Historical provider detail is intentionally not part of durable reconciliation state.
    """
    return DeliveryTrace(
        (DeliveryEvent(state.current_state, "restored synthetic reconciliation state"),)
    )


def reconcile_provider_events(
    trace: DeliveryTrace,
    events: tuple[ProviderEvent, ...],
    state: ReconciliationState | None = None,
) -> ReconciliationResult:
    """Apply provider evidence and return content-minimizing durable state.

    Duplicate event IDs are ignored after their first occurrence, including across calls when
    the returned state is supplied again. Events at or below the latest applied sequence are
    stale. Contradictory transitions are ignored rather than rewriting stronger evidence.
    Durable state intentionally omits provider event detail and message content.
    """
    current = trace
    reconciliation_state = state or ReconciliationState.from_trace(trace)
    if reconciliation_state.current_state is not trace.current_state:
        raise ValueError("trace and reconciliation state disagree")

    seen_ids = set(reconciliation_state.seen_event_ids)
    decisions: list[ReconciliationDecision] = []
    latest_sequence = reconciliation_state.latest_sequence

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

    durable_state = ReconciliationState(
        current.current_state, frozenset(seen_ids), latest_sequence
    )
    return ReconciliationResult(current, tuple(decisions), durable_state)


def generated(message_id: str = "msg-synthetic-001") -> DeliveryTrace:
    return DeliveryTrace(
        (DeliveryEvent(DeliveryState.GENERATED, f"application created {message_id}"),)
    )
