import importlib.util
from pathlib import Path
import sys
import unittest


MODULE_PATH = Path(__file__).resolve().parents[1] / "boundary.py"
spec = importlib.util.spec_from_file_location("ai_boundary", MODULE_PATH)
assert spec and spec.loader
boundary = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = boundary
spec.loader.exec_module(boundary)


class RecommendationBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.catalog = {
            "demo-lamp": boundary.CatalogItem(
                item_id="demo-lamp",
                name="Demo Lamp",
                attributes={"finish": "matte", "power": "12W"},
            ),
            "demo-desk": boundary.CatalogItem(
                item_id="demo-desk",
                name="Demo Desk",
                attributes={"width": "120cm", "material": "bamboo"},
            ),
            "demo-stool": boundary.CatalogItem(
                item_id="demo-stool",
                name="Demo Stool",
                attributes={"material": "bamboo", "finish": "matte"},
            ),
        }

    def test_accepts_claims_grounded_in_authoritative_catalog(self):
        candidate = boundary.Recommendation("demo-lamp", {"finish": "matte"})
        result = boundary.validate_recommendations(self.catalog, [candidate])
        self.assertEqual(result.accepted, (candidate,))
        self.assertEqual(result.rejected, ())

    def test_rejects_unknown_item(self):
        candidate = boundary.Recommendation("invented-item", {"finish": "matte"})
        result = boundary.validate_recommendations(self.catalog, [candidate])
        self.assertEqual(result.accepted, ())
        self.assertEqual(result.rejected[0][1], ("unknown item",))

    def test_rejects_invented_attribute(self):
        candidate = boundary.Recommendation("demo-desk", {"height": "75cm"})
        result = boundary.validate_recommendations(self.catalog, [candidate])
        self.assertEqual(result.rejected[0][1], ("unsupported attribute: height",))

    def test_rejects_attribute_value_that_conflicts_with_catalog(self):
        candidate = boundary.Recommendation("demo-lamp", {"power": "20W"})
        result = boundary.validate_recommendations(self.catalog, [candidate])
        self.assertEqual(result.rejected[0][1], ("attribute mismatch: power",))

    def test_mixed_candidates_preserve_valid_recommendations(self):
        valid = boundary.Recommendation("demo-desk", {"material": "bamboo"})
        invalid = boundary.Recommendation("demo-lamp", {"finish": "gloss"})
        result = boundary.validate_recommendations(self.catalog, [valid, invalid])
        self.assertEqual(result.accepted, (valid,))
        self.assertEqual(result.rejected[0][0], invalid)

    def test_filters_candidates_to_explicit_allowlist(self):
        constraints = boundary.CandidateConstraints(
            allowed_item_ids=frozenset({"demo-lamp", "demo-stool"})
        )
        result = boundary.filter_candidates(self.catalog, constraints)
        self.assertEqual(tuple(item.item_id for item in result.items), ("demo-lamp", "demo-stool"))

    def test_filters_candidates_by_authoritative_attributes(self):
        constraints = boundary.CandidateConstraints(required_attributes={"material": "bamboo"})
        result = boundary.filter_candidates(self.catalog, constraints)
        self.assertEqual(tuple(item.item_id for item in result.items), ("demo-desk", "demo-stool"))

    def test_combines_allowlist_and_attribute_constraints(self):
        constraints = boundary.CandidateConstraints(
            allowed_item_ids=frozenset({"demo-lamp", "demo-stool"}),
            required_attributes={"material": "bamboo"},
        )
        result = boundary.filter_candidates(self.catalog, constraints)
        self.assertEqual(tuple(item.item_id for item in result.items), ("demo-stool",))

    def test_unknown_required_attribute_produces_no_candidates(self):
        constraints = boundary.CandidateConstraints(required_attributes={"invented": "value"})
        result = boundary.filter_candidates(self.catalog, constraints)
        self.assertEqual(result.items, ())

    def test_handoff_exposes_only_eligible_item_ids(self):
        eligible = boundary.filter_candidates(
            self.catalog,
            boundary.CandidateConstraints(required_attributes={"material": "bamboo"}),
        )
        self.assertEqual(eligible.item_ids, frozenset({"demo-desk", "demo-stool"}))

    def test_ranked_output_cannot_reintroduce_filtered_item(self):
        eligible = boundary.filter_candidates(
            self.catalog,
            boundary.CandidateConstraints(required_attributes={"material": "bamboo"}),
        )
        filtered_out = boundary.Recommendation("demo-lamp", {"finish": "matte"})
        result = boundary.validate_ranked_recommendations(eligible, [filtered_out])
        self.assertEqual(result.accepted, ())
        self.assertEqual(result.rejected[0][1], ("unknown item",))

    def test_ranked_output_still_validates_authoritative_attributes(self):
        eligible = boundary.filter_candidates(
            self.catalog,
            boundary.CandidateConstraints(required_attributes={"material": "bamboo"}),
        )
        conflicting = boundary.Recommendation("demo-stool", {"finish": "gloss"})
        result = boundary.validate_ranked_recommendations(eligible, [conflicting])
        self.assertEqual(result.accepted, ())
        self.assertEqual(result.rejected[0][1], ("attribute mismatch: finish",))


if __name__ == "__main__":
    unittest.main()
