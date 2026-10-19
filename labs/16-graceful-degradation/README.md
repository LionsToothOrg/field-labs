# Lab 16 — Graceful Degradation

## Question

When a feature depends on several downstream capabilities, which failures should remove the feature entirely and which should produce a deliberately reduced response?

This lab models that decision with fabricated dependency names, states, and payloads only; it does not contact external services.

## Baseline

Treating every downstream dependency as equally critical makes an optional failure indistinguishable from a failure that prevents the core feature from working. That all-or-nothing boundary can unnecessarily turn partial dependency loss into total feature loss. A second risk appears when a system declares itself degraded but still carries data from the unavailable capability into its response.

## Experiment

`degradation.py` separates dependencies into two explicit sets:

- **required** — an unavailable dependency makes the feature unavailable;
- **optional** — an unavailable dependency changes the feature from `full` to `degraded` while preserving the core feature.

The evaluator returns the response mode plus the unavailable required and optional dependencies. Referenced dependencies must have an explicit state; missing state is rejected rather than silently assumed healthy.

The response builder then makes that policy concrete. Healthy optional dependencies contribute their synthetic payloads. Unavailable optional dependencies contribute only an explicitly configured fallback value, so their supplied payload is not copied into the reduced response. If a required dependency is unavailable, the builder returns no core or optional payload. Missing healthy payloads and missing fallbacks are rejected rather than guessed.

Run the lab with:

```bash
PYTHONPATH=labs/16-graceful-degradation python -m unittest discover -s labs/16-graceful-degradation/tests -v
```

## Evidence

The automated tests verify:

- all healthy dependencies produce a full response;
- one or more optional failures produce a degraded response;
- a required failure makes the feature unavailable;
- unavailable dependencies are reported deterministically;
- missing dependency state and contradictory policy configuration are rejected;
- an unavailable optional payload is replaced by its configured fallback and does not appear in the reduced response;
- a required failure omits both core and optional payloads;
- missing healthy optional payloads and missing fallback values are rejected.

## Limitations

This is a policy and response-shaping model, not a production dependency-health system. It does not model stale cached data, dependency timeouts, recovery, observability, distributed failure detection, serialization boundaries, or mutable payload aliasing. A `degraded` result proves only that this model selected configured fallback output for the supplied synthetic state.

## Next experiment

A useful next slice can model recovery from degraded to full mode across a deterministic sequence of dependency states and verify that fallback output is removed once the optional capability is healthy again.
