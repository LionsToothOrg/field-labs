# Lab 22 — Retry Budgets

## Question

How can a caller keep retries from amplifying synthetic request volume without disabling retries entirely?

## Current slices

This lab starts with a deliberately small retry-budget model. Original attempts earn retry capacity at a configured ratio, and retry admission stops once that capacity is consumed. An optional minimum allowance makes bootstrap behavior explicit instead of hiding it in the implementation.

The second slice adds deterministic fixed-window rollover. Windowed budgets require an injected clock, so tests can advance fabricated time without sleeping or depending on wall-clock timing. When a window expires, its original demand, admitted retries, rejected retries, and policy-skipped retries stop contributing to the active window. Large idle jumps advance directly to the current fixed-window boundary.

The third slice makes retry policy explicit. Synthetic outcomes are classified as retryable or non-retryable before budget admission. Retryable outcomes compete for the same bounded capacity as before; non-retryable outcomes are skipped without consuming capacity and are counted separately from retries rejected because the budget is exhausted.

The fourth slice exposes each policy check as an immutable structured decision. A decision records its synthetic classification, whether it was admitted, policy-skipped, or budget-rejected, the retry limit and remaining capacity after the decision, and the active fabricated window boundary when windowing is enabled. Existing boolean admission methods delegate to the same decision path, so inspectability does not create a second policy implementation.

The model also exposes aggregate snapshots for the active window. Together, decisions and snapshots make policy, admission, rollover, and capacity changes inspectable without logging infrastructure or production observability dependencies.

## Run the tests

```bash
PYTHONPATH=labs/22-retry-budgets python -m unittest discover -s labs/22-retry-budgets/tests -v
```

## Evidence in this lab

The tests verify that:

- retry admission is bounded by the configured fraction of recorded original attempts;
- the budget grows predictably as additional original attempts are observed;
- fractional limits round down rather than silently over-admitting;
- a minimum retry allowance is opt-in and visible;
- budget-rejected retries are counted;
- non-retryable synthetic outcomes do not consume retry capacity;
- policy-skipped outcomes remain distinguishable from budget rejection;
- retryable synthetic outcomes still obey the configured budget;
- structured decisions distinguish admission, policy skips, and budget rejection;
- structured decisions report post-decision capacity and the active synthetic window;
- boolean admission methods use the same decision path;
- unsupported classification values fail explicitly;
- a synthetic clock rolls the budget exactly at the configured boundary;
- demand and retry accounting from an expired window no longer contribute to the active window;
- idle time spanning multiple windows advances to the correct fixed-window boundary;
- backward clock movement is rejected rather than silently corrupting window accounting; and
- invalid ratios, allowances, and window configuration fail explicitly.

All counters, classifications, decisions, request activity, and clock values in this lab are fabricated. No production traffic or private system behavior is represented.

## Limitations and next experiments

The current implementation is a single-process fixed-window model with a deliberately binary retry policy and in-memory decision evidence. It does **not** model rolling/sliding windows, distributed coordination, per-endpoint policies, protocol-specific status codes, concurrency, latency, backoff scheduling, persistent event storage, or production traffic. A useful next increment is to define a concise stopping point for the lab and add a deterministic decision-sequence scenario that demonstrates how capacity changes across mixed synthetic outcomes before cataloging the completed experiment.
