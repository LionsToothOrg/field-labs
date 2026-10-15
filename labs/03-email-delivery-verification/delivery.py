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


def generated(message_id: str = "msg-synthetic-001") -> DeliveryTrace:
    return DeliveryTrace(
        (DeliveryEvent(DeliveryState.GENERATED, f"application created {message_id}"),)
    )
