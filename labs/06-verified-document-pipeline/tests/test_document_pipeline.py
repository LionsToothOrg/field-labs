import unittest

from document_pipeline import (
    SummaryRecord,
    render_summary,
    serialize_summary,
    verify_serialized_summary,
    verify_summary,
)


RECORD = SummaryRecord(
    report_id="RPT-EXAMPLE-0042",
    subject="Synthetic equipment review",
    status="Ready for review",
    reference="REF-TEST-118",
)


class VerifiedDocumentPipelineTests(unittest.TestCase):
    def test_complete_render_passes_verification(self):
        document = render_summary(RECORD)

        result = verify_summary(document, RECORD)

        self.assertTrue(result.is_valid)
        self.assertEqual((), result.missing_fields)

    def test_omitted_required_field_is_reported(self):
        document = render_summary(RECORD, omit_reference=True)

        result = verify_summary(document, RECORD)

        self.assertFalse(result.is_valid)
        self.assertEqual(("reference",), result.missing_fields)

    def test_wrong_rendered_value_does_not_satisfy_source_record(self):
        document = render_summary(RECORD).replace(
            "Status: Ready for review", "Status: Approved"
        )

        result = verify_summary(document, RECORD)

        self.assertFalse(result.is_valid)
        self.assertEqual(("status",), result.missing_fields)

    def test_serialized_artifact_passes_verification(self):
        artifact = serialize_summary(render_summary(RECORD))

        result = verify_serialized_summary(artifact, RECORD)

        self.assertTrue(result.is_valid)
        self.assertEqual((), result.missing_fields)

    def test_truncated_serialized_artifact_is_rejected(self):
        artifact = serialize_summary(render_summary(RECORD))
        truncated = artifact[: artifact.index(b"Reference:")]

        result = verify_serialized_summary(truncated, RECORD)

        self.assertFalse(result.is_valid)
        self.assertEqual(("reference",), result.missing_fields)

    def test_invalid_utf8_serialized_artifact_is_rejected(self):
        artifact = serialize_summary(render_summary(RECORD)) + b"\xff"

        result = verify_serialized_summary(artifact, RECORD)

        self.assertFalse(result.is_valid)
        self.assertEqual(("serialized_artifact",), result.missing_fields)


if __name__ == "__main__":
    unittest.main()
