from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
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


class WorkflowStage(str, Enum):
    ELIGIBILITY = "eligibility"
    FLEXIBLE_STEP = "flexible_step"
    VALIDATION = "validation"
    FAILURE_POLICY = "failure_policy"


@dataclass(frozen=True)
class StageEvent:
    stage: WorkflowStage
    outcome: str
    detail: str


@dataclass(frozen=True)
class WorkflowResult:
    eligible: EligibleCandidates
    validation: ValidationResult
    failure_decision: FailureDecision | None
    trace: tuple[StageEvent, ...]


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
    The workflow owns deterministic eligibility, factual validation, and the
    action selected for an already classified failure. The returned trace is
    deliberately structured and contains only stage outcomes, not provider or
    prompt content.
    """
    eligible = filter_candidates(catalog, constraints)
    trace = [
        StageEvent(
            WorkflowStage.ELIGIBILITY,
            "accepted",
            f"{len(eligible.item_ids)} candidate(s) eligible",
        )
    ]

    if failure_kind is not None:
        decision = decide_failure(
            failure_kind,
            attempt=attempt,
            max_attempts=max_attempts,
        )
        trace.extend(
            (
                StageEvent(
                    WorkflowStage.FLEXIBLE_STEP,
                    "failed",
                    f"classified failure: {failure_kind.value}",
                ),
                StageEvent(
                    WorkflowStage.FAILURE_POLICY,
                    decision.action.value,
                    decision.reason,
                ),
            )
        )
        return WorkflowResult(
            eligible=eligible,
            validation=ValidationResult((), ()),
            failure_decision=decision,
            trace=tuple(trace),
        )

    trace.append(
        StageEvent(
            WorkflowStage.FLEXIBLE_STEP,
            "received",
            f"{len(ranked_recommendations)} recommendation(s) received",
        )
    )
    validation = validate_ranked_recommendations(eligible, ranked_recommendations)
    trace.append(
        StageEvent(
            WorkflowStage.VALIDATION,
            "accepted" if not validation.rejected else "rejected",
            (
                f"{len(validation.accepted)} accepted; "
                f"{len(validation.rejected)} rejected"
            ),
        )
    )

    return WorkflowResult(
        eligible=eligible,
        validation=validation,
        failure_decision=None,
        trace=tuple(trace),
    )
