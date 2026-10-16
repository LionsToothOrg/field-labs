import unittest

from annotation import (
    create_annotation,
    resolve_by_context,
    resolve_by_offsets,
    resolve_by_unique_text,
)


BASE_DOCUMENT = (
    "Synthetic report: alpha section. "
    "Beta finding needs review. "
    "Gamma appendix."
)
SELECTION = "Beta finding needs review."


class AnnotationAnchoringTests(unittest.TestCase):
    def test_annotation_captures_original_unique_selection(self):
        annotation = create_annotation(BASE_DOCUMENT, SELECTION)

        self.assertEqual(SELECTION, resolve_by_offsets(BASE_DOCUMENT, annotation))

    def test_original_offsets_drift_after_text_is_inserted_before_selection(self):
        annotation = create_annotation(BASE_DOCUMENT, SELECTION)
        revised = BASE_DOCUMENT.replace(
            "alpha section. ",
            "inserted preface. alpha section. ",
            1,
        )

        self.assertNotEqual(SELECTION, resolve_by_offsets(revised, annotation))

    def test_unique_text_reanchors_selection_after_offset_drift(self):
        annotation = create_annotation(BASE_DOCUMENT, SELECTION)
        revised = BASE_DOCUMENT.replace(
            "alpha section. ",
            "inserted preface. alpha section. ",
            1,
        )

        resolved = resolve_by_unique_text(revised, annotation)

        self.assertIsNotNone(resolved)
        self.assertEqual(SELECTION, revised[resolved.start_offset : resolved.end_offset])
        self.assertGreater(resolved.start_offset, annotation.start_offset)

    def test_duplicate_selection_is_left_unresolved_by_quote_only(self):
        annotation = create_annotation(BASE_DOCUMENT, SELECTION)
        ambiguous = f"{BASE_DOCUMENT} Repeated note: {SELECTION}"

        self.assertIsNone(resolve_by_unique_text(ambiguous, annotation))

    def test_context_disambiguates_duplicate_quote_when_one_neighborhood_matches(self):
        annotation = create_annotation(BASE_DOCUMENT, SELECTION)
        revised = f"Preface. {BASE_DOCUMENT} Repeated note: {SELECTION}"

        resolved = resolve_by_context(revised, annotation)

        self.assertIsNotNone(resolved)
        self.assertEqual(SELECTION, revised[resolved.start_offset : resolved.end_offset])
        self.assertEqual(revised.index(SELECTION), resolved.start_offset)

    def test_context_fails_closed_when_duplicate_neighborhoods_match(self):
        annotation = create_annotation(BASE_DOCUMENT, SELECTION)
        repeated_segment = "alpha section. Beta finding needs review. Gamma appendix."
        ambiguous = f"Synthetic report: {repeated_segment} Copy: {repeated_segment}"

        self.assertIsNone(resolve_by_context(ambiguous, annotation))

    def test_context_fails_closed_when_neighborhood_changed(self):
        annotation = create_annotation(BASE_DOCUMENT, SELECTION)
        revised = BASE_DOCUMENT.replace("Gamma appendix.", "Delta appendix.", 1)

        self.assertIsNone(resolve_by_context(revised, annotation))


if __name__ == "__main__":
    unittest.main()
