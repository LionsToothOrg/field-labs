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

A deterministic sequence helper applies the same response boundary independently to each supplied state. This makes recovery observable without adding clocks or external health checks: when an optional dependency changes from unavailable to healthy, the next response returns to `full` mode and uses the healthy synthetic payload instead of retaining the fallback. Repeated degradation similarly reselects the fallback rather than carrying forward a previously healthy response.

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
- missing healthy optional payloads and missing fallback values are rejected;
- degraded-to-full recovery removes fallback output when the optional dependency becomes healthy;
- a full-to-degraded-to-full sequence does not reuse stale healthy output during degradation;
- an empty state sequence produces no responses.

## Limitations

This is a policy and response-shaping model, not a production dependency-health system. Recovery is driven by supplied deterministic states rather than probes, timers, or distributed health signals. The lab does not model stale cached data, dependency timeouts, observability, serialization boundaries, mutable payload aliasing, hysteresis, or flapping protection. A `full` result after recovery proves only that this model selected healthy configured output for the supplied synthetic state.

## Stopping point

The lab now covers the intended policy boundary, safe fallback response shaping, and deterministic recovery without pretending to be a production health subsystem. Further resilience work is better isolated in a separate lab if it needs time-based health checks, hysteresis, or distributed failure detection.
