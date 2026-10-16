# Lab 05 — Document Annotation

## Question

How can an annotation stay attached to the intended synthetic text when an earlier document edit shifts its original character offsets?

## Synthetic baseline

This slice models a plain-text document and one annotation entirely in memory. The fixture is fabricated for this lab and contains no uploaded documents, client material, or real-person data.

`create_annotation` records both the selected text and its start/end offsets. `resolve_by_offsets` deliberately demonstrates the fragile baseline: after text is inserted before the annotation, the old offsets point at the wrong characters.

## Quote-based re-anchoring

`resolve_by_unique_text` searches the revised document for the annotation's exact synthetic selection. When there is exactly one match, it returns the new offsets. This is intentionally a small recovery rule rather than a complete annotation format.

The resolver fails closed when the selection is missing or appears more than once. Guessing between duplicate matches would make the demo look more capable while hiding an unresolved anchoring problem.

## Run the validation

From the repository root:

```bash
PYTHONPATH=labs/05-document-annotation python -m unittest discover -s labs/05-document-annotation/tests -v
```

The focused suite checks initial capture, deterministic offset drift after an insertion, successful unique-text re-anchoring, and refusal to guess when the selected text is ambiguous.

## What this slice establishes

Absolute offsets alone are not stable identifiers for changing text. In the controlled fixture, inserting a synthetic preface moves the intended selection while the stored offsets remain unchanged. An exact unique-text quote is enough to recover this specific edit and produces repeatable new offsets.

## Limitations

This is a synthetic text-anchoring experiment, not a document editor or production annotation system. It does not model PDFs, DOM ranges, rich text, OCR, page geometry, collaborative editing, deletions inside the selection, fuzzy matching, revision history, persistence, permissions, or merge conflicts.

Exact-text recovery also has a deliberate boundary: duplicate or modified selections are unresolved. A later slice can add surrounding context as a disambiguation signal if it answers the next reliability question without pretending to solve arbitrary document revision.
