from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from boundary import (
    CandidateConstraints,
    CatalogItem,
    EligibleCandidates,
    FailureDecision,
    FailureKind,
    Recommendation,
    ValidationResult,
    decide_failure,
    filter_candidates,
    validate_ranked_recommendations,
)


@dataclass(frozen=True)
class WorkflowResult:
    eligible: EligibleCandidates
    validation: ValidationResult
    failure_decision: FailureDecision | None


def run_workflow(
    catalog: Mapping[str, CatalogItem],
    constraints: CandidateConstraints,
    ranked_recommendations: Sequence[Recommendation],
    *,
    failure_kind: FailureKind | None = None,
    attempt: int = 1,
    max_attempts: int = 2,
) -> WorkflowResult:
    """Exercise the lab boundary without delegating authoritative decisions.

    ``ranked_recommendations`` represents synthetic output from a flexible step.
    The workflow itself owns deterministic eligibility, factual validation, and
    the action selected for an already classified failure.
    """
    eligible = filter_candidates(catalog, constraints)

    if failure_kind is not None:
        return WorkflowResult(
            eligible=eligible,
            validation=ValidationResult((), ()),
            failure_decision=decide_failure(
                failure_kind,
                attempt=attempt,
                max_attempts=max_attempts,
            ),
        )

    return WorkflowResult(
        eligible=eligible,
        validation=validate_ranked_recommendations(eligible, ranked_recommendations),
        failure_decision=None,
    )
