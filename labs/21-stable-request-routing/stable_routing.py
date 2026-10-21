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
