# Lab 20 — Adaptive Concurrency Limits

## Question

How can a service adjust a bounded concurrency limit from explicit feedback without allowing overload signals to increase admitted work?

This lab uses synthetic latency samples and overload flags only. It is a deterministic control-model experiment, not a production traffic controller.

## First slice: bounded feedback

`adaptive_concurrency.py` models two related decisions:

- `admit` permits another request only while current in-flight work is below the active limit.
- `update_limit` applies a deliberately small additive-increase/multiplicative-decrease policy to one synthetic feedback sample.

A healthy sample at or below the target latency increases the limit by the configured step, capped at the maximum. Latency above the target or an explicit overload signal decreases the limit by the configured ratio, floored at the minimum. Explicit overload takes precedence even when the observed latency is low.

The policy rejects malformed bounds, invalid samples, and current limits outside the configured range rather than silently inventing a valid state.

## Reproduce

```bash
PYTHONPATH=labs/20-adaptive-concurrency-limits \
  python -m unittest discover -s labs/20-adaptive-concurrency-limits/tests -v
```

The focused suite covers healthy growth, the target boundary, maximum/minimum clamping, latency-driven reduction, explicit overload precedence, admission at the limit, and invalid inputs.

## What this evidence supports

The tests demonstrate deterministic behavior for this synthetic control rule and its bounds. They do not demonstrate that these constants are appropriate for a real workload or that the model improves production latency or throughput.

## Limitations and next experiments

This slice intentionally does **not** model asynchronous requests, rolling latency windows, percentile estimation, minimum RTT, queueing delay, sample weighting, oscillation damping, distributed coordination, retries, cancellation, or downstream capacity. A later slice can explore feedback-window semantics before any claim about adaptive behavior under a trace is warranted.

All identifiers and measurements in this lab are fabricated for the experiment.
