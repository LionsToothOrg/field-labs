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

## Second slice: feedback windows

`update_limit_from_window` makes one limit decision from a non-empty sequence of synthetic samples rather than changing the limit after every observation. Samples in a window must share one target latency.

An explicit overload signal anywhere in the window causes a decrease. Otherwise, the arithmetic mean latency is compared with the shared target: a mean at or below target permits one additive increase, while a mean above target causes one multiplicative decrease. The comparison uses the exact latency sum rather than a rounded mean.

This makes the experiment's aggregation boundary explicit: an isolated slow sample does not automatically force a decrease when the complete window remains healthy, while an overload signal is never averaged away.

## Reproduce

```bash
PYTHONPATH=labs/20-adaptive-concurrency-limits \
  python -m unittest discover -s labs/20-adaptive-concurrency-limits/tests -v
```

The focused suite covers single-sample bounded feedback plus healthy and degraded windows, the exact target boundary, isolated slow observations, overload precedence, empty windows, and inconsistent targets.

## What this evidence supports

The tests demonstrate deterministic behavior for these synthetic control rules and their bounds. They do not demonstrate that the constants, arithmetic mean, or any particular window size are appropriate for a real workload, or that the model improves production latency or throughput.

## Limitations and next experiments

This lab still does **not** model asynchronous requests, rolling/time-based windows, percentile estimation, minimum RTT, queueing delay, sample weighting, oscillation damping, distributed coordination, retries, cancellation, or downstream capacity. A later slice can model sequential windows and explicit controller state before making any claim about adaptation across a synthetic trace.

All identifiers and measurements in this lab are fabricated for the experiment.
