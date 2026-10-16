"""Synthetic document generation and deterministic verification for Lab 06."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SummaryRecord:
    report_id: str
    subject: str
    status: str
    reference: str


@dataclass(frozen=True)
class VerificationResult:
    is_valid: bool
    missing_fields: tuple[str, ...]


def render_summary(record: SummaryRecord, *, omit_reference: bool = False) -> str:
    """Render a small synthetic summary, optionally injecting one known defect."""
    lines = [
        f"Report ID: {record.report_id}",
        f"Subject: {record.subject}",
        f"Status: {record.status}",
    ]
    if not omit_reference:
        lines.append(f"Reference: {record.reference}")
    return "\n".join(lines) + "\n"


def verify_summary(document: str, record: SummaryRecord) -> VerificationResult:
    """Require every exact source-derived field line to appear in the artifact."""
    required = {
        "report_id": f"Report ID: {record.report_id}",
        "subject": f"Subject: {record.subject}",
        "status": f"Status: {record.status}",
        "reference": f"Reference: {record.reference}",
    }
    document_lines = set(document.splitlines())
    missing = tuple(name for name, line in required.items() if line not in document_lines)
    return VerificationResult(is_valid=not missing, missing_fields=missing)
