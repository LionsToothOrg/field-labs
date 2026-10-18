from dataclasses import dataclass


@dataclass(frozen=True)
class Admission:
    allowed: bool
    partition: str
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

    def admit(self, partition: str) -> Admission:
        self._require_partition(partition)
        capacity = self._capacities[partition]
        current = self._in_flight[partition]

        if current >= capacity:
            return Admission(False, partition, current, capacity, "partition_saturated")

        current += 1
        self._in_flight[partition] = current
        return Admission(True, partition, current, capacity, "admitted")

    def release(self, partition: str) -> None:
        self._require_partition(partition)
        if self._in_flight[partition] == 0:
            raise RuntimeError("cannot release a partition with no admitted work")
        self._in_flight[partition] -= 1

    def snapshot(self) -> dict[str, tuple[int, int]]:
        return {
            name: (self._in_flight[name], capacity)
            for name, capacity in self._capacities.items()
        }

    def _require_partition(self, partition: str) -> None:
        if partition not in self._capacities:
            raise KeyError(f"unknown partition: {partition}")
