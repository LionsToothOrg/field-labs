# Lab 02 — AI Workflow Boundaries

## Question

When software uses AI to interpret a request or rank options, which decisions can remain flexible and which facts should be enforced by deterministic code?

This lab explores three narrow boundaries: hard catalog constraints are applied before flexible ranking, the ranking handoff contains only eligible candidates, and model-like recommendations may not invent catalog items or product attributes.

## Synthetic scenario

A fictional catalog contains a small set of fabricated items and authoritative attributes. An upstream AI step is represented only by structured `Recommendation` objects; this lab does **not** call an external model or claim model quality.

`filter_candidates` applies explicit item allowlists and required authoritative attributes and returns an `EligibleCandidates` handoff. A flexible ranking step can operate on that bounded set. `validate_ranked_recommendations` then validates ranking output against the same eligible set, while `validate_recommendations` checks factual claims against authoritative catalog attributes.

That separation is intentional:

- **Deterministic work before AI-shaped work:** enforce hard eligibility constraints against authoritative data.
- **Typed handoff:** carry only the catalog items that passed deterministic eligibility.
- **AI-shaped work:** rank eligible candidates or explain a recommendation.
- **Deterministic work after AI-shaped work:** reject filtered-out items and verify factual catalog claims before accepting them as application facts.

## Run the validation

From the repository root:

```bash
python -m unittest discover -s labs/02-ai-workflow-boundaries/tests -v
```

The suite checks grounded claims, unknown items, invented attributes, conflicting values, mixed valid/invalid candidates, deterministic filtering, the eligible-candidate handoff, rejection of a filtered-out item after ranking, and authoritative-attribute validation after the handoff.

## What these slices establish

Structured output is useful, but structure alone does not make generated facts authoritative. A recommendation can be perfectly shaped and still name an item that does not exist or attach a specification the source never supplied.

Likewise, hard requirements should not depend on a probabilistic component choosing to honor them. Candidate eligibility is narrowed deterministically first. The explicit handoff makes that boundary visible in the interface, and post-ranking validation prevents a flexible component from reintroducing an item that was filtered out.

## Limitations and next experiment

This is a deterministic boundary test, not an evaluation of an AI provider, retrieval system, embedding model, or prompt. It does not measure recommendation relevance, semantic recall, latency, cost, or model accuracy. Constraints are exact string matches over a tiny in-memory catalog; there is no schema normalization, numeric/range comparison, policy engine, persistence layer, or runtime sandbox around an external model.

A useful next slice is to add deterministic policy decisions that distinguish recoverable model-output errors from hard workflow failures, while keeping those decisions observable and testable without calling an external provider.
