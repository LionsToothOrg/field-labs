import importlib.util
import sys
import unittest
from pathlib import Path

LAB_DIR = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


boundary = load_module("boundary", LAB_DIR / "boundary.py")
workflow = load_module("workflow", LAB_DIR / "workflow.py")


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.catalog = {
            "atlas": boundary.CatalogItem(
                "atlas", "Atlas", {"surface": "matte", "size": "compact"}
            ),
            "ember": boundary.CatalogItem(
                "ember", "Ember", {"surface": "gloss", "size": "compact"}
            ),
            "harbor": boundary.CatalogItem(
                "harbor", "Harbor", {"surface": "matte", "size": "large"}
            ),
        }

    def test_workflow_filters_then_validates_synthetic_ranking(self):
        result = workflow.run_workflow(
            self.catalog,
            boundary.CandidateConstraints(required_attributes={"surface": "matte"}),
            [
                boundary.Recommendation("atlas", {"size": "compact"}),
                boundary.Recommendation("ember", {"size": "compact"}),
            ],
        )

        self.assertEqual(result.eligible.item_ids, frozenset({"atlas", "harbor"}))
        self.assertEqual(
            tuple(item.item_id for item in result.validation.accepted),
            ("atlas",),
        )
        self.assertEqual(len(result.validation.rejected), 1)
        self.assertEqual(result.validation.rejected[0][0].item_id, "ember")
        self.assertEqual(result.validation.rejected[0][1], ("unknown item",))
        self.assertIsNone(result.failure_decision)

    def test_workflow_rejects_factual_claim_after_eligibility(self):
        result = workflow.run_workflow(
            self.catalog,
            boundary.CandidateConstraints(allowed_item_ids=frozenset({"atlas"})),
            [boundary.Recommendation("atlas", {"size": "large"})],
        )

        self.assertEqual(result.validation.accepted, ())
        self.assertEqual(
            result.validation.rejected[0][1],
            ("attribute mismatch: size",),
        )

    def test_workflow_exposes_retry_policy_for_classified_failure(self):
        result = workflow.run_workflow(
            self.catalog,
            boundary.CandidateConstraints(required_attributes={"size": "compact"}),
            [],
            failure_kind=boundary.FailureKind.TRANSIENT_PROVIDER,
            attempt=1,
            max_attempts=2,
        )

        self.assertEqual(result.eligible.item_ids, frozenset({"atlas", "ember"}))
        self.assertEqual(result.validation.accepted, ())
        self.assertEqual(result.validation.rejected, ())
        self.assertEqual(result.failure_decision.action, boundary.FailureAction.RETRY)

    def test_workflow_fails_nonrecoverable_failure_without_accepting_output(self):
        result = workflow.run_workflow(
            self.catalog,
            boundary.CandidateConstraints(),
            [boundary.Recommendation("atlas", {"size": "compact"})],
            failure_kind=boundary.FailureKind.POLICY_VIOLATION,
            attempt=1,
            max_attempts=3,
        )

        self.assertEqual(result.validation.accepted, ())
        self.assertEqual(result.validation.rejected, ())
        self.assertEqual(result.failure_decision.action, boundary.FailureAction.FAIL)


if __name__ == "__main__":
    unittest.main()
