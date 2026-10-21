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
