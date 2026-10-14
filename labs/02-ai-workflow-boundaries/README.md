# Lab 02 — AI Workflow Boundaries

## Question

When software uses AI to interpret a request or rank options, which decisions can remain flexible and which facts should be enforced by deterministic code?

This lab starts with two narrow boundaries: hard catalog constraints are applied before flexible ranking, and model-like recommendations may not invent catalog items or product attributes.

## Synthetic scenario

A fictional catalog contains a small set of fabricated items and authoritative attributes. An upstream AI step is represented only by structured `Recommendation` objects; this lab does **not** call an external model or claim model quality.

`filter_candidates` applies explicit item allowlists and required authoritative attributes before any flexible ranking or explanation step. `validate_recommendations` then checks each proposed item and claimed attribute against the authoritative catalog. Unknown items, unsupported attributes, and conflicting values are rejected with deterministic reasons.

That separation is intentional:

- **Deterministic work before AI-shaped work:** enforce hard eligibility constraints against authoritative data.
- **AI-shaped work:** rank eligible candidates or explain a recommendation.
- **Deterministic work after AI-shaped work:** verify factual catalog claims before accepting them as application facts.

## Run the validation

From the repository root:

```bash
python -m unittest discover -s labs/02-ai-workflow-boundaries/tests -v
```

The suite checks grounded claims, unknown items, invented attributes, conflicting values, mixed valid/invalid candidates, allowlist filtering, authoritative-attribute filtering, combined constraints, and unsupported required attributes.

## What these slices establish

Structured output is useful, but structure alone does not make generated facts authoritative. A recommendation can be perfectly shaped and still name an item that does not exist or attach a specification the source never supplied.

Likewise, hard requirements should not depend on a probabilistic component choosing to honor them. Candidate eligibility is narrowed deterministically first; flexible ranking can operate only on the surviving set, and its factual claims are validated afterward.

## Limitations and next experiment

This is a deterministic boundary test, not an evaluation of an AI provider, retrieval system, embedding model, or prompt. It does not measure recommendation relevance, semantic recall, latency, cost, or model accuracy. Constraints are exact string matches over a tiny in-memory catalog; there is no schema normalization, numeric/range comparison, policy engine, or persistence layer.

A useful next slice is to define a typed handoff between deterministic eligibility and the flexible ranking step so the ranking component cannot receive ineligible catalog items by construction.
