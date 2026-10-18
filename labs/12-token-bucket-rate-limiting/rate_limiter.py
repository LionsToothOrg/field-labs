from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Decision:
    allowed: bool
    requested: float
    remaining: float
    capacity: float
    reason: str
    retry_after: float | None


class TokenBucket:
    def __init__(self, capacity: float, refill_rate: float, start_time: float = 0.0):
        self._require_positive_number(capacity, "capacity")
        self._require_positive_number(refill_rate, "refill_rate")
        self._require_time(start_time)
        self._capacity = float(capacity)
        self._refill_rate = float(refill_rate)
        self._tokens = float(capacity)
        self._last_updated = float(start_time)

    def allow(self, now: float, tokens: float = 1.0) -> Decision:
        self._require_time(now)
        self._require_positive_number(tokens, "tokens")
        now = float(now)
        requested = float(tokens)

        if now < self._last_updated:
            raise ValueError("now cannot move backward")

        elapsed = now - self._last_updated
        self._tokens = min(
            self._capacity,
            self._tokens + elapsed * self._refill_rate,
        )
        self._last_updated = now

        if requested > self._capacity:
            return Decision(
                False,
                requested,
                self._tokens,
                self._capacity,
                "request_exceeds_capacity",
                None,
            )

        if requested > self._tokens:
            retry_after = (requested - self._tokens) / self._refill_rate
            return Decision(
                False,
                requested,
                self._tokens,
                self._capacity,
                "insufficient_tokens",
                retry_after,
            )

        self._tokens -= requested
        return Decision(
            True,
            requested,
            self._tokens,
            self._capacity,
            "allowed",
            0.0,
        )

    def snapshot(self) -> tuple[float, float, float]:
        return (self._tokens, self._capacity, self._last_updated)

    @staticmethod
    def _is_finite_number(value: object) -> bool:
        return (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(value)
        )

    @classmethod
    def _require_positive_number(cls, value: object, name: str) -> None:
        if not cls._is_finite_number(value) or value <= 0:
            raise ValueError(f"{name} must be a positive finite number")

    @classmethod
    def _require_time(cls, value: object) -> None:
        if not cls._is_finite_number(value):
            raise ValueError("time must be a finite number")
