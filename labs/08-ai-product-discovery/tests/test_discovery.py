import unittest

from discovery import Candidate, Constraints, Product, QualificationEvidence, discover


CATALOG = {
    "fixture-a": Product("fixture-a", "Northwind Stand", "stand", 12, False),
    "fixture-b": Product("fixture-b", "Cedar Stand", "stand", 6, False),
    "fixture-c": Product("fixture-c", "Studio Stand", "stand", 18, True),
    "fixture-d": Product("fixture-d", "Northwind Case", "case", 20, False),
}


class DiscoveryTests(unittest.TestCase):
    def test_returns_authoritative_products_that_meet_constraints(self):
        candidates = [Candidate("fixture-a", 0.81), Candidate("fixture-b", 0.72)]

        result = discover(CATALOG, candidates, Constraints("stand", minimum_load_kg=10))

        self.assertEqual(["fixture-a"], [item.product.product_id for item in result])

    def test_semantic_score_cannot_override_hard_constraints(self):
        candidates = [Candidate("fixture-b", 0.99), Candidate("fixture-a", 0.60)]

        result = discover(CATALOG, candidates, Constraints("stand", minimum_load_kg=10))

        self.assertEqual(["fixture-a"], [item.product.product_id for item in result])

    def test_unknown_candidate_is_not_invented_into_catalog(self):
        candidates = [Candidate("retriever-only-id", 1.0), Candidate("fixture-a", 0.50)]

        result = discover(CATALOG, candidates, Constraints("stand", minimum_load_kg=10))

        self.assertEqual(["fixture-a"], [item.product.product_id for item in result])

    def test_outdoor_requirement_excludes_indoor_only_product(self):
        candidates = [Candidate("fixture-c", 0.95), Candidate("fixture-a", 0.70)]

        result = discover(
            CATALOG,
            candidates,
            Constraints("stand", minimum_load_kg=10, require_outdoor=True),
        )

        self.assertEqual(["fixture-a"], [item.product.product_id for item in result])

    def test_no_eligible_candidate_returns_empty_result(self):
        candidates = [Candidate("fixture-b", 0.99), Candidate("fixture-d", 0.98)]

        result = discover(CATALOG, candidates, Constraints("stand", minimum_load_kg=10))

        self.assertEqual([], result)

    def test_explanation_evidence_is_derived_from_authoritative_catalog_fields(self):
        result = discover(
            CATALOG,
            [Candidate("fixture-a", 0.81)],
            Constraints("stand", minimum_load_kg=10, require_outdoor=True),
        )

        self.assertEqual(
            (
                QualificationEvidence("category", "category", "stand"),
                QualificationEvidence("minimum_load_kg", "max_load_kg", "12"),
                QualificationEvidence("outdoor_use", "indoor_only", "false"),
            ),
            result[0].evidence,
        )

    def test_semantic_score_is_not_presented_as_catalog_evidence(self):
        result = discover(
            CATALOG,
            [Candidate("fixture-a", 0.999)],
            Constraints("stand", minimum_load_kg=10),
        )

        evidence_fields = {item.catalog_field for item in result[0].evidence}
        evidence_values = {item.observed_value for item in result[0].evidence}
        self.assertNotIn("semantic_score", evidence_fields)
        self.assertNotIn("0.999", evidence_values)


if __name__ == "__main__":
    unittest.main()
