# Lab 02 — AI Workflow Boundaries

## Question

When software uses AI to interpret a request or rank options, which decisions can remain flexible and which facts and workflow actions should be enforced by deterministic code?

This lab explores four narrow boundaries: hard catalog constraints are applied before flexible ranking, the ranking handoff contains only eligible candidates, model-like recommendations may not invent catalog items or product attributes, and classified workflow failures map to deterministic retry-or-fail decisions.

## Synthetic scenario

A fictional catalog contains a small set of fabricated items and authoritative attributes. An upstream AI step is represented only by structured `Recommendation` objects; this lab does **not** call an external model or claim model quality.

`filter_candidates` applies explicit item allowlists and required authoritative attributes and returns an `EligibleCandidates` handoff. A flexible ranking step can operate on that bounded set. `validate_ranked_recommendations` then validates ranking output against the same eligible set, while `validate_recommendations` checks factual claims against authoritative catalog attributes.

`decide_failure` takes an already classified failure and a bounded attempt count. Malformed output and transient provider failures are recoverable only while retry budget remains. Policy violations and invalid workflow state fail immediately. Every decision returns a typed action and reason so the policy can be logged or measured by a caller without parsing exception text.

That separation is intentional:

- **Deterministic work before AI-shaped work:** enforce hard eligibility constraints against authoritative data.
- **Typed handoff:** carry only the catalog items that passed deterministic eligibility.
- **AI-shaped work:** rank eligible candidates or explain a recommendation.
- **Deterministic work after AI-shaped work:** reject filtered-out items and verify factual catalog claims before accepting them as application facts.
- **Deterministic failure policy:** retry only explicitly recoverable failure classes and stop when their bounded budget is exhausted.

## Run the validation

From the repository root:

```bash
python -m unittest discover -s labs/02-ai-workflow-boundaries/tests -v
```

The suite checks grounded claims, unknown items, invented attributes, conflicting values, mixed valid/invalid candidates, deterministic filtering, the eligible-candidate handoff, rejection of a filtered-out item after ranking, authoritative-attribute validation after the handoff, recoverable failure retries, retry-budget exhaustion, hard workflow failures, and invalid retry counters.

## What these slices establish

Structured output is useful, but structure alone does not make generated facts authoritative. A recommendation can be perfectly shaped and still name an item that does not exist or attach a specification the source never supplied.

Likewise, hard requirements should not depend on a probabilistic component choosing to honor them. Candidate eligibility is narrowed deterministically first. The explicit handoff makes that boundary visible in the interface, and post-ranking validation prevents a flexible component from reintroducing an item that was filtered out.

Failure handling benefits from the same boundary. Whether a known failure class is retryable is application policy, not a decision to delegate to generated output. A small typed decision object makes the chosen action and rationale observable while keeping retry limits deterministic.

## Limitations and next experiment

This is a deterministic boundary test, not an evaluation of an AI provider, retrieval system, embedding model, or prompt. It does not measure recommendation relevance, semantic recall, latency, cost, or model accuracy. Constraints are exact string matches over a tiny in-memory catalog; there is no schema normalization, numeric/range comparison, persistence layer, or runtime sandbox around an external model.

The failure policy also assumes classification has already happened. It does not parse provider exceptions, perform backoff or jitter, persist attempts, execute retries, or define provider-specific semantics. Those behaviors should remain separate from this policy until there is evidence that coupling them improves the experiment.

A useful next slice is to exercise the boundary as a small end-to-end workflow: deterministic filtering, a synthetic ranking result, factual validation, and failure-policy output, while preserving the current no-provider and synthetic-only scope.
