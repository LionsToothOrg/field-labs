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

## Third slice: sequential controller state

`run_feedback_trace` applies complete feedback windows in order and carries each decision's next limit into the following window. The returned `ControllerTrace` records the initial limit, final limit, and immutable decision sequence so a fabricated adaptation trace can be inspected without hidden state.

The trace uses the same validation and min/max bounds as an individual window. Empty traces and malformed windows fail explicitly rather than producing partial evidence. This slice demonstrates deterministic state propagation only; it does not introduce time, concurrency, or live traffic.

## Reproduce

```bash
PYTHONPATH=labs/20-adaptive-concurrency-limits \
  python -m unittest discover -s labs/20-adaptive-concurrency-limits/tests -v
```

The focused suite covers single-sample bounded feedback, healthy and degraded windows, overload precedence, sequential state propagation, repeated maximum clamping, and invalid trace/window inputs.

## What this evidence supports

The tests demonstrate deterministic behavior for these synthetic control rules, bounds, and sequential state transitions. They do not demonstrate that the constants, arithmetic mean, window size, or resulting limit path are appropriate for a real workload, or that the model improves production latency or throughput.

## Limitations and next experiments

This lab still does **not** model asynchronous requests, rolling/time-based windows, percentile estimation, minimum RTT, queueing delay, sample weighting, oscillation damping, distributed coordination, retries, cancellation, or downstream capacity. A later slice can examine oscillation or stabilization semantics on a bounded synthetic trace before any claim about real adaptive behavior is warranted.

All identifiers and measurements in this lab are fabricated for the experiment.
