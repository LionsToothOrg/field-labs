# Lab 05 — Document Annotation

## Question

How can an annotation stay attached to the intended synthetic text when document edits shift its original character offsets or introduce a duplicate quote?

## Synthetic baseline

This lab models a plain-text document and one annotation entirely in memory. The fixture is fabricated for this lab and contains no uploaded documents, client material, or real-person data.

`create_annotation` records the selected text, its start/end offsets, and a bounded 16-character neighborhood on each side. `resolve_by_offsets` deliberately demonstrates the fragile baseline: after text is inserted before the annotation, the old offsets point at the wrong characters.

## Quote-based re-anchoring

`resolve_by_unique_text` searches the revised document for the annotation's exact synthetic selection. When there is exactly one match, it returns the new offsets. The resolver fails closed when the selection is missing or appears more than once.

## Context-aware disambiguation

`resolve_by_context` addresses one narrow duplicate-quote case. It considers every exact quote match and accepts a candidate only when both its captured prefix and suffix still match. Recovery succeeds only when exactly one candidate retains that neighborhood.

This is intentionally conservative. If multiple candidates have the same neighborhood, or an edit changes the captured neighborhood, the resolver returns no anchor rather than guessing. Context is a disambiguation signal here, not proof of semantic identity.

## Run the validation

From the repository root:

```bash
PYTHONPATH=labs/05-document-annotation python -m unittest discover -s labs/05-document-annotation/tests -v
```

The focused suite checks initial capture, deterministic offset drift, unique-text recovery, quote-only ambiguity, context-based duplicate disambiguation, duplicate-context refusal, and refusal when the captured neighborhood changed.

## What this slice establishes

Absolute offsets alone are not stable identifiers for changing text. Exact quote matching can recover a moved unique selection, while a small captured neighborhood can safely distinguish a duplicated quote in the controlled fixture when exactly one occurrence preserves that context.

## Limitations

This is a synthetic text-anchoring experiment, not a document editor or production annotation system. It does not model PDFs, DOM ranges, rich text, OCR, page geometry, collaborative editing, edits inside the selection, fuzzy matching, revision history, persistence, permissions, or merge conflicts.

The fixed context window is deliberately simple. It does not rank partial matches or infer intent, and it fails closed when context is changed or duplicated. A later experiment could compare stronger anchoring strategies, but only with explicit synthetic cases and measurable acceptance rules.
