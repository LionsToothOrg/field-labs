# Lab 22 — Retry Budgets

## Question

How can a caller keep retries from amplifying synthetic request volume without disabling retries entirely?

## First slice

This lab starts with a deliberately small retry-budget model. Original attempts earn retry capacity at a configured ratio, and retry admission stops once that capacity is consumed. An optional minimum allowance makes bootstrap behavior explicit instead of hiding it in the implementation.

The model exposes a snapshot containing original attempts, admitted retries, rejected retries, the current retry limit, and remaining capacity. That makes each admission decision inspectable in tests.

## Run the tests

```bash
PYTHONPATH=labs/22-retry-budgets python -m unittest discover -s labs/22-retry-budgets/tests -v
```

## Evidence in this slice

The tests verify that:

- retry admission is bounded by the configured fraction of recorded original attempts;
- the budget grows predictably as additional original attempts are observed;
- fractional limits round down rather than silently over-admitting;
- a minimum retry allowance is opt-in and visible;
- rejected retries are counted; and
- invalid ratios and minimum allowances fail explicitly.

All counters and request activity in this lab are fabricated. No production traffic or private system behavior is represented.

## Limitations and next experiments

This first slice is a single in-memory accounting window. It does **not** yet model rolling time windows, distributed coordination, per-endpoint policies, retry classification, concurrency, latency, or production traffic. A useful next increment is to make window rollover deterministic with an injected synthetic clock and verify that old demand stops contributing retry capacity.
