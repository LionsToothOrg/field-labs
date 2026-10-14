import importlib.util
from pathlib import Path
import unittest


MODULE_PATH = Path(__file__).resolve().parents[1] / "boundary.py"
spec = importlib.util.spec_from_file_location("ai_boundary", MODULE_PATH)
boundary = importlib.util.module_from_spec(spec)
assert spec and spec.loader
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


if __name__ == "__main__":
    unittest.main()
