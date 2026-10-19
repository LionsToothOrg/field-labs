import unittest

from degradation import (
    DependencyState,
    FeaturePolicy,
    ResponseMode,
    build_response,
    build_response_sequence,
    evaluate_feature,
)


class GracefulDegradationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = FeaturePolicy(
            name="synthetic-search",
            required_dependencies=("catalog",),
            optional_dependencies=("recommendations", "analytics"),
        )

    def states(self, *, catalog=DependencyState.HEALTHY, recommendations=DependencyState.HEALTHY, analytics=DependencyState.HEALTHY):
        return {"catalog": catalog, "recommendations": recommendations, "analytics": analytics}

    def test_full_response_when_all_dependencies_are_healthy(self) -> None:
        result = evaluate_feature(self.policy, self.states())
        self.assertEqual(ResponseMode.FULL, result.mode)
        self.assertEqual((), result.unavailable_required)
        self.assertEqual((), result.unavailable_optional)

    def test_optional_failure_degrades_without_blocking_feature(self) -> None:
        result = evaluate_feature(self.policy, self.states(recommendations=DependencyState.UNAVAILABLE))
        self.assertEqual(ResponseMode.DEGRADED, result.mode)
        self.assertEqual(("recommendations",), result.unavailable_optional)

    def test_multiple_optional_failures_are_reported_in_policy_order(self) -> None:
        result = evaluate_feature(
            self.policy,
            self.states(recommendations=DependencyState.UNAVAILABLE, analytics=DependencyState.UNAVAILABLE),
        )
        self.assertEqual(ResponseMode.DEGRADED, result.mode)
        self.assertEqual(("recommendations", "analytics"), result.unavailable_optional)

    def test_required_failure_makes_feature_unavailable(self) -> None:
        result = evaluate_feature(self.policy, self.states(catalog=DependencyState.UNAVAILABLE))
        self.assertEqual(ResponseMode.UNAVAILABLE, result.mode)
        self.assertEqual(("catalog",), result.unavailable_required)

    def test_missing_referenced_state_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "analytics"):
            evaluate_feature(
                self.policy,
                {"catalog": DependencyState.HEALTHY, "recommendations": DependencyState.HEALTHY},
            )

    def test_dependency_cannot_be_required_and_optional(self) -> None:
        with self.assertRaisesRegex(ValueError, "both required and optional"):
            FeaturePolicy(name="invalid", required_dependencies=("catalog",), optional_dependencies=("catalog",))

    def test_empty_feature_name_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "must not be empty"):
            FeaturePolicy(name="   ")

    def test_degraded_response_replaces_unavailable_optional_payload(self) -> None:
        result = build_response(
            self.policy,
            self.states(recommendations=DependencyState.UNAVAILABLE),
            core_payload={"items": ["synthetic-a"]},
            optional_payloads={
                "recommendations": {"items": ["must-not-leak"]},
                "analytics": {"trace": "synthetic-summary"},
            },
            fallback_values={"recommendations": {"items": []}},
        )
        self.assertEqual(ResponseMode.DEGRADED, result.mode)
        self.assertEqual({"items": []}, result.optional["recommendations"])
        self.assertNotIn("must-not-leak", repr(result))
        self.assertEqual({"trace": "synthetic-summary"}, result.optional["analytics"])

    def test_unavailable_response_omits_all_payloads(self) -> None:
        result = build_response(
            self.policy,
            self.states(catalog=DependencyState.UNAVAILABLE),
            core_payload={"items": ["must-not-leak"]},
            optional_payloads={"recommendations": {"items": ["x"]}, "analytics": {"trace": "y"}},
            fallback_values={},
        )
        self.assertEqual(ResponseMode.UNAVAILABLE, result.mode)
        self.assertIsNone(result.core)
        self.assertEqual({}, result.optional)
        self.assertNotIn("must-not-leak", repr(result))

    def test_missing_healthy_optional_payload_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "analytics"):
            build_response(
                self.policy,
                self.states(),
                core_payload={"items": []},
                optional_payloads={"recommendations": {"items": []}},
                fallback_values={},
            )

    def test_missing_fallback_for_unavailable_optional_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "recommendations"):
            build_response(
                self.policy,
                self.states(recommendations=DependencyState.UNAVAILABLE),
                core_payload={"items": []},
                optional_payloads={"analytics": {"trace": "ok"}},
                fallback_values={},
            )

    def test_recovery_sequence_removes_fallback_after_optional_dependency_recovers(self) -> None:
        responses = build_response_sequence(
            self.policy,
            [
                self.states(recommendations=DependencyState.UNAVAILABLE),
                self.states(),
            ],
            core_payload={"items": ["synthetic-a"]},
            optional_payloads={
                "recommendations": {"items": ["synthetic-recommendation"]},
                "analytics": {"trace": "synthetic-summary"},
            },
            fallback_values={"recommendations": {"items": []}},
        )
        self.assertEqual((ResponseMode.DEGRADED, ResponseMode.FULL), tuple(r.mode for r in responses))
        self.assertEqual({"items": []}, responses[0].optional["recommendations"])
        self.assertEqual({"items": ["synthetic-recommendation"]}, responses[1].optional["recommendations"])

    def test_repeated_degradation_does_not_reuse_previous_healthy_payload(self) -> None:
        responses = build_response_sequence(
            self.policy,
            [
                self.states(),
                self.states(recommendations=DependencyState.UNAVAILABLE),
                self.states(),
            ],
            core_payload={"items": ["synthetic-a"]},
            optional_payloads={
                "recommendations": {"items": ["synthetic-recommendation"]},
                "analytics": {"trace": "synthetic-summary"},
            },
            fallback_values={"recommendations": {"items": []}},
        )
        self.assertEqual(
            (ResponseMode.FULL, ResponseMode.DEGRADED, ResponseMode.FULL),
            tuple(r.mode for r in responses),
        )
        self.assertEqual({"items": []}, responses[1].optional["recommendations"])

    def test_empty_recovery_sequence_is_empty(self) -> None:
        responses = build_response_sequence(
            self.policy,
            [],
            core_payload={"items": []},
            optional_payloads={},
            fallback_values={},
        )
        self.assertEqual((), responses)


if __name__ == "__main__":
    unittest.main()
