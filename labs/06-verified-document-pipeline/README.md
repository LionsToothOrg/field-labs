# Lab 06 — Verified Document Pipeline

## Question

Can a generated document be treated as complete only after deterministic checks confirm that required synthetic source fields survived rendering and serialization?

## Synthetic baseline

This lab uses a fabricated summary record and a plain-text renderer. There are no uploaded documents, real identities, client records, or external services.

`render_summary` turns the record into a small text artifact. Its `omit_reference` switch deliberately models a renderer defect that silently drops one required field. The renderer still returns a document, which demonstrates the core distinction this lab explores: **generation success is not verification success**.

## Deterministic verification

`verify_summary` derives the required lines from the same structured source record and checks the rendered artifact for each one. It returns a `VerificationResult` containing the missing field names instead of treating a non-empty document as proof of correctness.

The next boundary serializes that rendered text as UTF-8 bytes. `verify_serialized_summary` decodes those exact bytes strictly and then applies the same required-field checks. This makes verification operate on the artifact a downstream step would actually receive rather than only the renderer's in-memory string.

A truncated byte artifact therefore fails when a required line is lost, and malformed UTF-8 fails as a serialized-artifact error instead of being silently repaired. The boundary remains intentionally narrow: it does not claim transport durability, cryptographic integrity, semantic equivalence, layout correctness, PDF integrity, accessibility, signatures, or production document safety.

## Run the validation

From the repository root:

```bash
PYTHONPATH=labs/06-verified-document-pipeline python -m unittest discover -s labs/06-verified-document-pipeline/tests -v
```

The focused suite checks a complete render, deterministic detection of an omitted required field, rejection of a wrong rendered value, successful verification after serialization, rejection of truncation that removes a required field, and rejection of malformed UTF-8 bytes.

## What this slice establishes

A renderer returning content is a weak success signal. In this controlled fixture, a separate verification step can prove whether the exact required synthetic values made it through rendering and UTF-8 serialization, and can identify a missing field or an unreadable serialized artifact.

## Limitations

This is a text-and-bytes experiment, not a production document pipeline. It does not parse PDFs or office formats, validate visual layout, compare images, handle localization, verify optional fields, hash or sign artifacts, model storage or network transport, or prove that source data itself is correct. Later slices can add richer boundaries only when each new claim has repeatable evidence.
