"""Deterministic graceful-degradation policy for synthetic dependency states."""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class DependencyState(str, Enum):
    HEALTHY = "healthy"
    UNAVAILABLE = "unavailable"


class ResponseMode(str, Enum):
    FULL = "full"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class FeaturePolicy:
    name: str
    required_dependencies: tuple[str, ...] = ()
    optional_dependencies: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("feature name must not be empty")
        if set(self.required_dependencies) & set(self.optional_dependencies):
            raise ValueError("a dependency cannot be both required and optional")


@dataclass(frozen=True)
class Evaluation:
    mode: ResponseMode
    unavailable_required: tuple[str, ...]
    unavailable_optional: tuple[str, ...]


@dataclass(frozen=True)
class FeatureResponse:
    mode: ResponseMode
    core: Any | None
    optional: dict[str, Any]


def evaluate_feature(
    policy: FeaturePolicy,
    dependency_states: dict[str, DependencyState],
) -> Evaluation:
    """Evaluate one feature without calling any external system."""
    referenced = policy.required_dependencies + policy.optional_dependencies
    missing = [name for name in referenced if name not in dependency_states]
    if missing:
        raise ValueError(f"missing dependency state: {', '.join(sorted(missing))}")

    unavailable_required = tuple(
        name
        for name in policy.required_dependencies
        if dependency_states[name] is DependencyState.UNAVAILABLE
    )
    unavailable_optional = tuple(
        name
        for name in policy.optional_dependencies
        if dependency_states[name] is DependencyState.UNAVAILABLE
    )

    if unavailable_required:
        mode = ResponseMode.UNAVAILABLE
    elif unavailable_optional:
        mode = ResponseMode.DEGRADED
    else:
        mode = ResponseMode.FULL

    return Evaluation(mode, unavailable_required, unavailable_optional)


def build_response(
    policy: FeaturePolicy,
    dependency_states: dict[str, DependencyState],
    *,
    core_payload: Any,
    optional_payloads: dict[str, Any],
    fallback_values: dict[str, Any],
) -> FeatureResponse:
    """Build a synthetic response while isolating unavailable optional payloads."""
    evaluation = evaluate_feature(policy, dependency_states)
    if evaluation.mode is ResponseMode.UNAVAILABLE:
        return FeatureResponse(ResponseMode.UNAVAILABLE, None, {})

    optional: dict[str, Any] = {}
    for name in policy.optional_dependencies:
        if dependency_states[name] is DependencyState.HEALTHY:
            if name not in optional_payloads:
                raise ValueError(f"missing optional payload: {name}")
            optional[name] = optional_payloads[name]
        else:
            if name not in fallback_values:
                raise ValueError(f"missing fallback value: {name}")
            optional[name] = fallback_values[name]

    return FeatureResponse(evaluation.mode, core_payload, optional)


def build_response_sequence(
    policy: FeaturePolicy,
    dependency_state_sequence: list[dict[str, DependencyState]],
    *,
    core_payload: Any,
    optional_payloads: dict[str, Any],
    fallback_values: dict[str, Any],
) -> tuple[FeatureResponse, ...]:
    """Build independent responses for a deterministic dependency-state sequence."""
    return tuple(
        build_response(
            policy,
            states,
            core_payload=core_payload,
            optional_payloads=optional_payloads,
            fallback_values=fallback_values,
        )
        for states in dependency_state_sequence
    )
