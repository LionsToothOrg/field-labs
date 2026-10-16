# Lab 06 — Verified Document Pipeline

## Question

Can a generated document be treated as complete only after deterministic checks confirm that required synthetic source fields survived rendering?

## Synthetic baseline

This first slice uses a fabricated summary record and a plain-text renderer. There are no uploaded documents, real identities, client records, or external services.

`render_summary` turns the record into a small text artifact. Its `omit_reference` switch deliberately models a renderer defect that silently drops one required field. The renderer still returns a document, which demonstrates the core distinction this lab explores: **generation success is not verification success**.

## Deterministic verification

`verify_summary` derives the required lines from the same structured source record and checks the rendered artifact for each one. It returns a `VerificationResult` containing the missing field names instead of treating a non-empty document as proof of correctness.

The boundary is intentionally narrow. This slice verifies exact required fields in plain text; it does not claim semantic equivalence, layout correctness, PDF integrity, accessibility, signatures, or production document safety.

## Run the validation

From the repository root:

```bash
PYTHONPATH=labs/06-verified-document-pipeline python -m unittest discover -s labs/06-verified-document-pipeline/tests -v
```

The focused suite checks a complete render, deterministic detection of an omitted required field, and rejection of a wrong rendered value.

## What this slice establishes

A renderer returning content is a weak success signal. In this controlled fixture, a separate verification step can prove whether the exact required synthetic values made it into the artifact and can identify which field failed.

## Limitations

This is an in-memory text experiment, not a production document pipeline. It does not parse PDFs or office formats, validate visual layout, compare images, handle localization, verify optional fields, or prove that source data itself is correct. Later slices can add a serialized artifact boundary or richer checks only when each new claim has repeatable evidence.
