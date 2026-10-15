# Lab 02 — AI Workflow Boundaries

## Question

When software uses AI to interpret a request or rank options, which decisions can remain flexible and which facts and workflow actions should be enforced by deterministic code?

This lab explores five narrow boundaries: hard catalog constraints are applied before flexible ranking, the ranking handoff contains only eligible candidates, model-like recommendations may not invent catalog items or product attributes, classified workflow failures map to deterministic retry-or-fail decisions, and the composed workflow emits a structured trace showing which boundary handled each transition.

## Synthetic scenario

A fictional catalog contains a small set of fabricated items and authoritative attributes. An upstream AI step is represented only by structured `Recommendation` objects; this lab does **not** call an external model or claim model quality.

`filter_candidates` applies explicit item allowlists and required authoritative attributes and returns an `EligibleCandidates` handoff. A flexible ranking step can operate on that bounded set. `validate_ranked_recommendations` then validates ranking output against the same eligible set, while `validate_recommendations` checks factual claims against authoritative catalog attributes.

`decide_failure` takes an already classified failure and a bounded attempt count. Malformed output and transient provider failures are recoverable only while retry budget remains. Policy violations and invalid workflow state fail immediately. Every decision returns a typed action and reason so the policy can be logged or measured by a caller without parsing exception text.

`run_workflow` composes those boundaries into one small execution path. It filters the authoritative catalog first, accepts a synthetic ranking result only as flexible input, validates that result against the eligible handoff, and exposes the deterministic failure decision when the flexible step is represented as failed. A failed flexible step never contributes accepted recommendations.

The workflow also returns immutable `StageEvent` records for eligibility, the flexible step, validation, and failure policy. These events make execution order and boundary outcomes testable without logging prompt content, provider payloads, or recommendation details.

That separation is intentional:

- **Deterministic work before AI-shaped work:** enforce hard eligibility constraints against authoritative data.
- **Typed handoff:** carry only the catalog items that passed deterministic eligibility.
- **AI-shaped work:** rank eligible candidates or explain a recommendation.
- **Deterministic work after AI-shaped work:** reject filtered-out items and verify factual catalog claims before accepting them as application facts.
- **Deterministic failure policy:** retry only explicitly recoverable failure classes and stop when their bounded budget is exhausted.
- **Structured observability:** record which boundary ran and its outcome without turning flexible content into authoritative telemetry.

## Run the validation

From the repository root:

```bash
python -m unittest discover -s labs/02-ai-workflow-boundaries/tests -v
```

The suite checks grounded claims, unknown items, invented attributes, conflicting values, mixed valid/invalid candidates, deterministic filtering, the eligible-candidate handoff, rejection of a filtered-out item after ranking, authoritative-attribute validation after the handoff, recoverable failure retries, retry-budget exhaustion, hard workflow failures, invalid retry counters, the composed workflow across success and failure paths, and the stage trace emitted for those paths.

## What these slices establish

Structured output is useful, but structure alone does not make generated facts authoritative. A recommendation can be perfectly shaped and still name an item that does not exist or attach a specification the source never supplied.

Likewise, hard requirements should not depend on a probabilistic component choosing to honor them. Candidate eligibility is narrowed deterministically first. The explicit handoff makes that boundary visible in the interface, and post-ranking validation prevents a flexible component from reintroducing an item that was filtered out.

Failure handling benefits from the same boundary. Whether a known failure class is retryable is application policy, not a decision to delegate to generated output. A small typed decision object makes the chosen action and rationale observable while keeping retry limits deterministic.

The composed workflow makes the sequence itself testable: eligibility happens before flexible output is considered, flexible output cannot expand the eligible set, factual claims are checked before acceptance, and a classified failure produces policy output rather than partially accepting ranking data.

The stage trace adds evidence about *how* a result was reached. Tests can assert that validation followed the flexible handoff on a normal path, or that failure policy replaced validation after a classified failure. The trace intentionally records counts, classifications, actions, and reasons rather than generated content.

## Limitations and next experiment

This is a deterministic boundary test, not an evaluation of an AI provider, retrieval system, embedding model, or prompt. It does not measure recommendation relevance, semantic recall, latency, cost, or model accuracy. Constraints are exact string matches over a tiny in-memory catalog; there is no schema normalization, numeric/range comparison, persistence layer, or runtime sandbox around an external model.

The workflow receives a precomputed synthetic ranking result rather than invoking a model, and failure classification is still supplied by the caller. It does not parse provider exceptions, perform backoff or jitter, persist attempts, execute retries, or define provider-specific semantics. Stage events are in-memory teaching artifacts rather than a durable telemetry or audit system. Those behaviors should remain separate until there is evidence that adding them improves the experiment rather than obscuring the boundary being studied.

A useful next slice is to close Lab 02 with a concise findings document that maps each tested boundary to its evidence and explicitly distinguishes what the lab establishes from what remains untested before advancing the catalog.
