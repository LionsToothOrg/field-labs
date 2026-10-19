import unittest

from degradation import (
    DependencyState,
    FeaturePolicy,
    ResponseMode,
    evaluate_feature,
)


class GracefulDegradationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = FeaturePolicy(
            name="synthetic-search",
            required_dependencies=("catalog",),
            optional_dependencies=("recommendations", "analytics"),
        )

    def test_full_response_when_all_dependencies_are_healthy(self) -> None:
        result = evaluate_feature(
            self.policy,
            {
                "catalog": DependencyState.HEALTHY,
                "recommendations": DependencyState.HEALTHY,
                "analytics": DependencyState.HEALTHY,
            },
        )
        self.assertEqual(ResponseMode.FULL, result.mode)
        self.assertEqual((), result.unavailable_required)
        self.assertEqual((), result.unavailable_optional)

    def test_optional_failure_degrades_without_blocking_feature(self) -> None:
        result = evaluate_feature(
            self.policy,
            {
                "catalog": DependencyState.HEALTHY,
                "recommendations": DependencyState.UNAVAILABLE,
                "analytics": DependencyState.HEALTHY,
            },
        )
        self.assertEqual(ResponseMode.DEGRADED, result.mode)
        self.assertEqual(("recommendations",), result.unavailable_optional)

    def test_multiple_optional_failures_are_reported_in_policy_order(self) -> None:
        result = evaluate_feature(
            self.policy,
            {
                "catalog": DependencyState.HEALTHY,
                "recommendations": DependencyState.UNAVAILABLE,
                "analytics": DependencyState.UNAVAILABLE,
            },
        )
        self.assertEqual(ResponseMode.DEGRADED, result.mode)
        self.assertEqual(("recommendations", "analytics"), result.unavailable_optional)

    def test_required_failure_makes_feature_unavailable(self) -> None:
        result = evaluate_feature(
            self.policy,
            {
                "catalog": DependencyState.UNAVAILABLE,
                "recommendations": DependencyState.HEALTHY,
                "analytics": DependencyState.HEALTHY,
            },
        )
        self.assertEqual(ResponseMode.UNAVAILABLE, result.mode)
        self.assertEqual(("catalog",), result.unavailable_required)

    def test_missing_referenced_state_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "analytics"):
            evaluate_feature(
                self.policy,
                {
                    "catalog": DependencyState.HEALTHY,
                    "recommendations": DependencyState.HEALTHY,
                },
            )

    def test_dependency_cannot_be_required_and_optional(self) -> None:
        with self.assertRaisesRegex(ValueError, "both required and optional"):
            FeaturePolicy(
                name="invalid",
                required_dependencies=("catalog",),
                optional_dependencies=("catalog",),
            )

    def test_empty_feature_name_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "must not be empty"):
            FeaturePolicy(name="   ")


if __name__ == "__main__":
    unittest.main()
