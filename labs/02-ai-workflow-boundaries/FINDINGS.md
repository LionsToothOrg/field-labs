# Lab 02 findings — AI Workflow Boundaries

## Scope

This lab uses a fabricated in-memory catalog and precomputed synthetic recommendation objects. It does not invoke an external model, measure model quality, or reproduce a production incident.

The experiment asks a narrower engineering question: which workflow decisions should remain deterministic around a flexible ranking step?

## Evidence map

| Boundary | Evidence exercised by the lab | What it establishes |
| --- | --- | --- |
| Eligibility before ranking | Tests apply allowlists and authoritative attribute constraints before the ranking handoff. | Hard constraints can narrow the candidate set before flexible processing. |
| Bounded handoff | Tests inspect the eligible candidate identifiers supplied to the synthetic ranking boundary. | The flexible step does not need access to catalog items that failed deterministic eligibility. |
| Post-ranking validation | Tests reject unknown, filtered-out, invented, and attribute-conflicting recommendations. | Structured output is not treated as authoritative merely because it has the expected shape. |
| Failure policy | Tests map already-classified recoverable and non-recoverable failures to bounded retry-or-fail decisions. | Retry policy can remain explicit application logic rather than a flexible-output decision. |
| Composed workflow | Tests exercise eligibility, synthetic ranking input, validation, and failure routing as one execution path. | Flexible output cannot bypass the deterministic boundaries when these pieces are composed. |
| Stage trace | Tests assert stage order and bounded event details on success and failure paths. | Boundary transitions can be observable without recording recommendation content or provider payloads. |

## Findings

### 1. Put hard constraints before flexible interpretation

When an application already knows an authoritative requirement, filtering it before a flexible step makes the contract smaller and easier to reason about. The lab's ranking boundary receives an explicit eligible set rather than the full catalog.

### 2. Validate facts after flexible output

A correctly shaped recommendation can still contain an unknown item or a conflicting attribute. The lab therefore treats recommendation content as a proposal until deterministic validation checks it against authoritative catalog data.

### 3. Keep retry policy explicit

For already-classified failures, retryability and attempt limits are deterministic policy. The lab represents the result as a typed action with a reason instead of asking flexible output to decide whether execution should continue.

### 4. Observe boundaries without retaining flexible content

The composed workflow emits stage events containing bounded counts, classifications, actions, and policy reasons. The tests demonstrate that execution order can be inspected without placing recommendation text or provider payloads into the trace.

## What this lab does not establish

This lab does **not** establish that a particular model or provider produces relevant, safe, fast, inexpensive, or accurate recommendations. It does not evaluate prompts, retrieval, embeddings, semantic matching, schema normalization, numeric/range constraints, persistence, backoff, jitter, provider exception parsing, or durable telemetry.

Failure classification is supplied by the caller. Ranking output is precomputed synthetic input. Stage events exist only in memory and are not an audit log.

## Stopping point

The original boundary question now has repeatable evidence at the individual and composed-workflow levels: eligibility is deterministic before the flexible step, factual acceptance is deterministic afterward, known failure classes route through explicit policy, and stage transitions are observable without retaining flexible content.

Further provider-specific work would change the experiment from a boundary study into model/provider evaluation. That is intentionally left outside this lab's current scope. The catalog can advance to the next planned investigation without implying those untested behaviors are solved.
