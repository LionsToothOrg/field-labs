# Lab 16 — Graceful Degradation

## Question

When a feature depends on several downstream capabilities, which failures should remove the feature entirely and which should produce a deliberately reduced response?

This first slice models that decision as a deterministic policy. It uses fabricated dependency names and states only; it does not contact external services.

## Baseline

Treating every downstream dependency as equally critical makes an optional failure indistinguishable from a failure that prevents the core feature from working. That all-or-nothing boundary can unnecessarily turn partial dependency loss into total feature loss.

## Experiment

`degradation.py` separates dependencies into two explicit sets:

- **required** — an unavailable dependency makes the feature unavailable;
- **optional** — an unavailable dependency changes the feature from `full` to `degraded` while preserving the core feature.

The evaluator returns the response mode plus the unavailable required and optional dependencies. Referenced dependencies must have an explicit state; missing state is rejected rather than silently assumed healthy.

Run the slice with:

```bash
PYTHONPATH=labs/16-graceful-degradation python -m unittest discover -s labs/16-graceful-degradation/tests -v
```

## Evidence

The automated tests verify:

- all healthy dependencies produce a full response;
- one or more optional failures produce a degraded response;
- a required failure makes the feature unavailable;
- unavailable dependencies are reported deterministically;
- missing dependency state and contradictory policy configuration are rejected.

## Limitations

This is a policy model, not a production dependency-health system. It does not yet model stale cached data, fallback values, dependency timeouts, recovery, partial response payloads, observability, or distributed failure detection. A `degraded` result proves only that this policy permits a reduced feature mode for the supplied synthetic state.

## Next experiment

A useful next slice can make the degradation concrete by defining safe fallback outputs and proving that unavailable optional data cannot leak into the reduced response.
