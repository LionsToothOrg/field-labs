from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence


@dataclass(frozen=True)
class CatalogItem:
    item_id: str
    name: str
    attributes: Mapping[str, str]


@dataclass(frozen=True)
class Recommendation:
    item_id: str
    claimed_attributes: Mapping[str, str]


@dataclass(frozen=True)
class CandidateConstraints:
    allowed_item_ids: frozenset[str] | None = None
    required_attributes: Mapping[str, str] | None = None


@dataclass(frozen=True)
class ValidationResult:
    accepted: tuple[Recommendation, ...]
    rejected: tuple[tuple[Recommendation, tuple[str, ...]], ...]


def filter_candidates(
    catalog: Mapping[str, CatalogItem],
    constraints: CandidateConstraints,
) -> tuple[CatalogItem, ...]:
    """Apply hard catalog constraints before flexible ranking or explanation."""
    required_attributes = constraints.required_attributes or {}
    candidates: list[CatalogItem] = []

    for item_id, item in catalog.items():
        if constraints.allowed_item_ids is not None and item_id not in constraints.allowed_item_ids:
            continue
        if any(item.attributes.get(key) != value for key, value in required_attributes.items()):
            continue
        candidates.append(item)

    return tuple(candidates)


def validate_recommendations(
    catalog: Mapping[str, CatalogItem],
    recommendations: Sequence[Recommendation],
) -> ValidationResult:
    """Keep interpretation flexible while enforcing catalog facts deterministically."""
    accepted: list[Recommendation] = []
    rejected: list[tuple[Recommendation, tuple[str, ...]]] = []

    for recommendation in recommendations:
        reasons: list[str] = []
        item = catalog.get(recommendation.item_id)
        if item is None:
            reasons.append("unknown item")
        else:
            for key, claimed_value in recommendation.claimed_attributes.items():
                authoritative_value = item.attributes.get(key)
                if authoritative_value is None:
                    reasons.append(f"unsupported attribute: {key}")
                elif claimed_value != authoritative_value:
                    reasons.append(f"attribute mismatch: {key}")

        if reasons:
            rejected.append((recommendation, tuple(reasons)))
        else:
            accepted.append(recommendation)

    return ValidationResult(tuple(accepted), tuple(rejected))
