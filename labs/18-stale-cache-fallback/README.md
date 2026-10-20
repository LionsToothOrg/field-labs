# Lab 18 — Stale Cache Fallback

## Question

Can a cache serve a bounded stale value during a synthetic dependency interruption without allowing arbitrarily old data to masquerade as fresh?

## Failure scenario

When an origin is slow or unavailable, an expired cache entry can still be useful for a short, explicit window. Serving every expired entry indefinitely hides freshness loss; rejecting every expired entry immediately can discard a safe fallback and amplify origin pressure.

This lab models the decision boundary only. Cache values, timestamps, durations, and revalidation outcomes are fabricated inputs; no network request or production cache is involved.

## Experiment

`evaluate_cache_entry` classifies one entry at a supplied synthetic clock value:

- an entry at or inside its TTL is `fresh` and is served without revalidation;
- an expired entry inside the configured maximum-stale budget is `stale`, remains available, and requests revalidation;
- an entry beyond that budget is a `miss` and its value is not returned;
- a missing entry is a `miss`;
- invalid timestamps, TTLs, stale budgets, empty values, and clocks preceding storage time fail closed.

`apply_revalidation_outcome` then models one explicit refresh result for an expired entry:

- a successful refresh requires a new non-empty synthetic value and returns it as fresh at the supplied clock time;
- a failed refresh preserves the stale value only while the original entry is still inside its maximum-stale budget;
- once that budget is exceeded, a failed refresh returns a miss and withholds the old value rather than extending its lifetime;
- contradictory outcomes, such as a failed refresh carrying a replacement value, fail validation.

Run the lab with:

```bash
PYTHONPATH=labs/18-stale-cache-fallback python -m unittest discover -s labs/18-stale-cache-fallback/tests -v
```

## Evidence

The automated tests cover fresh and TTL boundaries, bounded stale delivery, the maximum-stale boundary, rejection beyond the stale budget, missing entries, a zero stale budget, invalid inputs, clock ordering, successful refresh replacement, failed refresh behavior on both sides of the stale boundary, and contradictory revalidation inputs.

The `age_ms`, `ttl_ms`, and `max_stale_ms` values are deterministic model inputs and calculations. They are not latency measurements or production cache observations. Revalidation outcomes are synthetic state transitions, not observations of an origin service.

## Limitations

This slice does not contact an origin, perform asynchronous revalidation, deduplicate refresh work, model cache eviction, validate domain-specific data freshness, or coordinate across processes. A successful synthetic outcome models replacement semantics only; it does not claim that network refresh work occurred.

## Next experiment

A later slice could combine bounded stale fallback with refresh deduplication so concurrent readers do not create a revalidation stampede.
