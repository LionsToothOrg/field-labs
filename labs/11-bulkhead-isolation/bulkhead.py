from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator


@dataclass(frozen=True)
class Admission:
    allowed: bool
    partition: str
    permits: int
    in_flight: int
    capacity: int
    reason: str


class Bulkhead:
    def __init__(self, capacities: dict[str, int]):
        if not capacities:
            raise ValueError("at least one partition is required")
        if any(not name or capacity <= 0 for name, capacity in capacities.items()):
            raise ValueError("partition names must be non-empty and capacities must be positive")

        self._capacities = dict(capacities)
        self._in_flight = {name: 0 for name in capacities}

    def admit(self, partition: str, permits: int = 1) -> Admission:
        self._require_partition(partition)
        self._require_permits(permits)
        capacity = self._capacities[partition]
        current = self._in_flight[partition]

        if current + permits > capacity:
            return Admission(False, partition, permits, current, capacity, "partition_saturated")

        current += permits
        self._in_flight[partition] = current
        return Admission(True, partition, permits, current, capacity, "admitted")

    def release(self, partition: str, permits: int = 1) -> None:
        self._require_partition(partition)
        self._require_permits(permits)
        if permits > self._in_flight[partition]:
            raise RuntimeError("cannot release more permits than admitted")
        self._in_flight[partition] -= permits

    @contextmanager
    def admission(self, partition: str, permits: int = 1) -> Iterator[Admission]:
        decision = self.admit(partition, permits)
        try:
            yield decision
        finally:
            if decision.allowed:
                self.release(partition, permits)

    def snapshot(self) -> dict[str, tuple[int, int]]:
        return {
            name: (self._in_flight[name], capacity)
            for name, capacity in self._capacities.items()
        }

    def _require_partition(self, partition: str) -> None:
        if partition not in self._capacities:
            raise KeyError(f"unknown partition: {partition}")

    @staticmethod
    def _require_permits(permits: int) -> None:
        if permits <= 0:
            raise ValueError("permits must be positive")
