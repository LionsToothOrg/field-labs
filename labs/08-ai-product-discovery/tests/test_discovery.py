import unittest

from discovery import Candidate, Constraints, Product, discover


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

        self.assertEqual(["fixture-a"], [product.product_id for product in result])

    def test_semantic_score_cannot_override_hard_constraints(self):
        candidates = [Candidate("fixture-b", 0.99), Candidate("fixture-a", 0.60)]

        result = discover(CATALOG, candidates, Constraints("stand", minimum_load_kg=10))

        self.assertEqual(["fixture-a"], [product.product_id for product in result])

    def test_unknown_candidate_is_not_invented_into_catalog(self):
        candidates = [Candidate("retriever-only-id", 1.0), Candidate("fixture-a", 0.50)]

        result = discover(CATALOG, candidates, Constraints("stand", minimum_load_kg=10))

        self.assertEqual(["fixture-a"], [product.product_id for product in result])

    def test_outdoor_requirement_excludes_indoor_only_product(self):
        candidates = [Candidate("fixture-c", 0.95), Candidate("fixture-a", 0.70)]

        result = discover(
            CATALOG,
            candidates,
            Constraints("stand", minimum_load_kg=10, require_outdoor=True),
        )

        self.assertEqual(["fixture-a"], [product.product_id for product in result])

    def test_no_eligible_candidate_returns_empty_result(self):
        candidates = [Candidate("fixture-b", 0.99), Candidate("fixture-d", 0.98)]

        result = discover(CATALOG, candidates, Constraints("stand", minimum_load_kg=10))

        self.assertEqual([], result)


if __name__ == "__main__":
    unittest.main()
