from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
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
class EligibleCandidates:
    """Candidate set that has passed deterministic eligibility checks."""

    items: tuple[CatalogItem, ...]

    @property
    def item_ids(self) -> frozenset[str]:
        return frozenset(item.item_id for item in self.items)


@dataclass(frozen=True)
class ValidationResult:
    accepted: tuple[Recommendation, ...]
    rejected: tuple[tuple[Recommendation, tuple[str, ...]], ...]


class FailureKind(str, Enum):
    MALFORMED_OUTPUT = "malformed_output"
    TRANSIENT_PROVIDER = "transient_provider"
    POLICY_VIOLATION = "policy_violation"
    INVALID_WORKFLOW_STATE = "invalid_workflow_state"


class FailureAction(str, Enum):
    RETRY = "retry"
    FAIL = "fail"


@dataclass(frozen=True)
class FailureDecision:
    kind: FailureKind
    action: FailureAction
    reason: str


def decide_failure(kind: FailureKind, *, attempt: int, max_attempts: int) -> FailureDecision:
    """Map a classified workflow failure to a deterministic, observable action."""
    if attempt < 1 or max_attempts < 1:
        raise ValueError("attempt and max_attempts must be positive")

    recoverable = kind in {FailureKind.MALFORMED_OUTPUT, FailureKind.TRANSIENT_PROVIDER}
    if recoverable and attempt < max_attempts:
        return FailureDecision(kind, FailureAction.RETRY, "recoverable failure within retry budget")
    if recoverable:
        return FailureDecision(kind, FailureAction.FAIL, "recoverable failure exhausted retry budget")
    return FailureDecision(kind, FailureAction.FAIL, "non-recoverable workflow failure")


def filter_candidates(
    catalog: Mapping[str, CatalogItem],
    constraints: CandidateConstraints,
) -> EligibleCandidates:
    """Apply hard catalog constraints before flexible ranking or explanation."""
    required_attributes = constraints.required_attributes or {}
    candidates: list[CatalogItem] = []

    for item_id, item in catalog.items():
        if constraints.allowed_item_ids is not None and item_id not in constraints.allowed_item_ids:
            continue
        if any(item.attributes.get(key) != value for key, value in required_attributes.items()):
            continue
        candidates.append(item)

    return EligibleCandidates(tuple(candidates))


def validate_ranked_recommendations(
    eligible: EligibleCandidates,
    recommendations: Sequence[Recommendation],
) -> ValidationResult:
    """Validate ranking output against only the deterministically eligible catalog slice."""
    catalog = {item.item_id: item for item in eligible.items}
    return validate_recommendations(catalog, recommendations)


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
