from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Iterable


@dataclass(frozen=True)
class Node:
    """A fabricated routing member identified by a stable public-safe name."""

    name: str

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("node name must be a non-empty string")


@dataclass(frozen=True)
class MembershipTransition:
    """Measured key movement between two synthetic membership snapshots."""

    total_keys: int
    moved_keys: tuple[str, ...]

    @property
    def moved_count(self) -> int:
        return len(self.moved_keys)

    @property
    def movement_ratio(self) -> float:
        return self.moved_count / self.total_keys


@dataclass(frozen=True)
class OwnershipDistribution:
    """Inspectable ownership counts for one synthetic routing snapshot."""

    total_keys: int
    ownership: tuple[tuple[str, int], ...]

    @property
    def counts(self) -> dict[str, int]:
        return dict(self.ownership)

    @property
    def min_count(self) -> int:
        return min(count for _, count in self.ownership)

    @property
    def max_count(self) -> int:
        return max(count for _, count in self.ownership)

    @property
    def spread(self) -> int:
        return self.max_count - self.min_count


@dataclass(frozen=True)
class OwnershipTransition:
    """Ownership deltas across two synthetic membership snapshots."""

    total_keys: int
    before: OwnershipDistribution
    after: OwnershipDistribution
    deltas: tuple[tuple[str, int], ...]

    @property
    def delta_counts(self) -> dict[str, int]:
        return dict(self.deltas)


def _validate_key(key: str) -> None:
    if not isinstance(key, str) or not key:
        raise ValueError("key must be a non-empty string")


def _normalize_nodes(nodes: Iterable[Node]) -> tuple[Node, ...]:
    normalized = tuple(nodes)
    if not normalized:
        raise ValueError("at least one node is required")
    if any(not isinstance(node, Node) for node in normalized):
        raise TypeError("nodes must contain Node instances")

    names = [node.name for node in normalized]
    if len(names) != len(set(names)):
        raise ValueError("node names must be unique")
    return normalized


def _normalize_keys(keys: Iterable[str]) -> tuple[str, ...]:
    normalized = tuple(keys)
    if not normalized:
        raise ValueError("at least one key is required")
    for key in normalized:
        _validate_key(key)
    if len(normalized) != len(set(normalized)):
        raise ValueError("keys must be unique")
    return normalized


def rendezvous_score(key: str, node: Node) -> int:
    """Return a deterministic score for one synthetic key/node pair."""

    _validate_key(key)
    if not isinstance(node, Node):
        raise TypeError("node must be a Node instance")

    digest = hashlib.sha256(f"{key}\0{node.name}".encode("utf-8")).digest()
    return int.from_bytes(digest, byteorder="big", signed=False)


def route(key: str, nodes: Iterable[Node]) -> Node:
    """Select the highest-scoring node independent of input ordering."""

    _validate_key(key)
    normalized = _normalize_nodes(nodes)
    return max(normalized, key=lambda node: (rendezvous_score(key, node), node.name))


def measure_membership_transition(
    keys: Iterable[str],
    before_nodes: Iterable[Node],
    after_nodes: Iterable[Node],
) -> MembershipTransition:
    """Measure routing churn across two complete synthetic membership snapshots."""

    normalized_keys = _normalize_keys(keys)
    before = _normalize_nodes(before_nodes)
    after = _normalize_nodes(after_nodes)
    moved = tuple(
        key for key in normalized_keys if route(key, before) != route(key, after)
    )
    return MembershipTransition(total_keys=len(normalized_keys), moved_keys=moved)


def measure_ownership_distribution(
    keys: Iterable[str],
    nodes: Iterable[Node],
) -> OwnershipDistribution:
    """Count synthetic key ownership for one complete membership snapshot."""

    normalized_keys = _normalize_keys(keys)
    normalized_nodes = _normalize_nodes(nodes)
    counts = {node.name: 0 for node in normalized_nodes}
    for key in normalized_keys:
        counts[route(key, normalized_nodes).name] += 1

    ownership = tuple(sorted(counts.items()))
    return OwnershipDistribution(total_keys=len(normalized_keys), ownership=ownership)


def compare_ownership_snapshots(
    keys: Iterable[str],
    before_nodes: Iterable[Node],
    after_nodes: Iterable[Node],
) -> OwnershipTransition:
    """Compare ownership counts across two complete synthetic memberships."""

    normalized_keys = _normalize_keys(keys)
    before = measure_ownership_distribution(normalized_keys, before_nodes)
    after = measure_ownership_distribution(normalized_keys, after_nodes)
    before_counts = before.counts
    after_counts = after.counts
    names = sorted(set(before_counts) | set(after_counts))
    deltas = tuple(
        (name, after_counts.get(name, 0) - before_counts.get(name, 0))
        for name in names
    )
    return OwnershipTransition(
        total_keys=len(normalized_keys),
        before=before,
        after=after,
        deltas=deltas,
    )
