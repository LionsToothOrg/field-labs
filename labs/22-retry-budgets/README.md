# Lab 22 — Retry Budgets

## Question

How can a caller keep retries from amplifying synthetic request volume without disabling retries entirely?

## Current slices

This lab starts with a deliberately small retry-budget model. Original attempts earn retry capacity at a configured ratio, and retry admission stops once that capacity is consumed. An optional minimum allowance makes bootstrap behavior explicit instead of hiding it in the implementation.

The second slice adds deterministic fixed-window rollover. Windowed budgets require an injected clock, so tests can advance fabricated time without sleeping or depending on wall-clock timing. When a window expires, its original demand, admitted retries, and rejected retries stop contributing to the active window. Large idle jumps advance directly to the current fixed-window boundary.

The model exposes a snapshot containing original attempts, admitted retries, rejected retries, the current retry limit, remaining capacity, and—when windowing is enabled—the active window start. That makes admission and rollover decisions inspectable in tests.

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
- rejected retries are counted;
- a synthetic clock rolls the budget exactly at the configured boundary;
- demand and retry usage from an expired window no longer contribute to the active window;
- idle time spanning multiple windows advances to the correct fixed-window boundary;
- backward clock movement is rejected rather than silently corrupting window accounting; and
- invalid ratios, allowances, and window configuration fail explicitly.

All counters, request activity, and clock values in this lab are fabricated. No production traffic or private system behavior is represented.

## Limitations and next experiments

The current implementation is a single-process fixed-window model. It does **not** model rolling/sliding windows, distributed coordination, per-endpoint policies, retry classification, concurrency, latency, or production traffic. A useful next increment is to distinguish retryable from non-retryable synthetic outcomes so budget consumption can be tied to an explicit retry policy rather than every retry request being treated identically.
