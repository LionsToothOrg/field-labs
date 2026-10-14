# Lab 02 — AI Workflow Boundaries

## Question

When software uses AI to interpret a request or rank options, which decisions can remain flexible and which facts should be enforced by deterministic code?

This lab starts with one narrow boundary: a model-like component may propose recommendations, but it may not invent catalog items or product attributes.

## Synthetic scenario

A fictional catalog contains a small set of fabricated items and authoritative attributes. An upstream AI step is represented only by structured `Recommendation` objects; this slice does **not** call an external model or claim model quality.

`validate_recommendations` checks each proposed item and claimed attribute against the authoritative catalog. A grounded recommendation passes through. Unknown items, unsupported attributes, and conflicting values are rejected with deterministic reasons.

That separation is intentional:

- **AI-shaped work:** interpret intent and propose candidates.
- **Deterministic work:** decide whether factual catalog claims are supported.

## Run the validation

From the repository root:

```bash
python -m unittest discover -s labs/02-ai-workflow-boundaries/tests -v
```

The initial suite checks grounded claims, unknown items, invented attributes, conflicting values, and mixed valid/invalid candidates.

## What this slice establishes

Structured output is useful, but structure alone does not make generated facts authoritative. A recommendation can be perfectly shaped and still name an item that does not exist or attach a specification the source never supplied.

The first boundary therefore treats the catalog as the source of truth and generated claims as untrusted proposals that must be checked before they can become application facts.

## Limitations and next experiment

This is a deterministic boundary test, not an evaluation of an AI provider, retrieval system, embedding model, or prompt. It does not measure recommendation relevance, semantic recall, latency, cost, or model accuracy.

A useful next slice is constraint-aware candidate selection: apply deterministic requirements such as allowed item IDs or required authoritative attributes before an AI interpretation step can rank or explain the surviving candidates.
