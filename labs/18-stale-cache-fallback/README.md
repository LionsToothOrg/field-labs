# Lab 18 — Stale Cache Fallback

## Question

Can a cache serve a bounded stale value during a synthetic dependency interruption without allowing arbitrarily old data to masquerade as fresh?

## Failure scenario

When an origin is slow or unavailable, an expired cache entry can still be useful for a short, explicit window. Serving every expired entry indefinitely hides freshness loss; rejecting every expired entry immediately can discard a safe fallback and amplify origin pressure.

This lab models the decision boundary only. Cache values, timestamps, and durations are fabricated inputs; no network request or production cache is involved.

## Experiment

`evaluate_cache_entry` classifies one entry at a supplied synthetic clock value:

- an entry at or inside its TTL is `fresh` and is served without revalidation;
- an expired entry inside the configured maximum-stale budget is `stale`, remains available, and requests revalidation;
- an entry beyond that budget is a `miss` and its value is not returned;
- a missing entry is a `miss`;
- invalid timestamps, TTLs, stale budgets, empty values, and clocks preceding storage time fail closed.

Run the lab with:

```bash
PYTHONPATH=labs/18-stale-cache-fallback python -m unittest discover -s labs/18-stale-cache-fallback/tests -v
```

## Evidence

The automated tests cover fresh and TTL boundaries, bounded stale delivery, the maximum-stale boundary, rejection beyond the stale budget, missing entries, a zero stale budget, invalid inputs, and clock ordering.

The `age_ms`, `ttl_ms`, and `max_stale_ms` values are deterministic model inputs and calculations. They are not latency measurements or production cache observations.

## Limitations

This slice does not contact an origin, perform asynchronous revalidation, deduplicate refresh work, model cache eviction, validate domain-specific data freshness, or coordinate across processes. Marking a stale result for revalidation demonstrates policy intent only; it does not claim that revalidation occurred.

## Next experiment

A later slice could model revalidation outcomes while preserving the rule that failed refresh work cannot extend stale data beyond the configured maximum-stale boundary.
