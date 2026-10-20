# Lab 18 — Stale Cache Fallback

## Question

Can a cache serve a bounded stale value during a synthetic dependency interruption without allowing arbitrarily old data to masquerade as fresh?

## Failure scenario

When an origin is slow or unavailable, an expired cache entry can still be useful for a short, explicit window. Serving every expired entry indefinitely hides freshness loss; rejecting every expired entry immediately can discard a safe fallback and amplify origin pressure. Concurrent stale readers can also amplify origin work if each reader independently starts the same refresh.

This lab models the decision boundary only. Cache values, timestamps, durations, request identifiers, and revalidation outcomes are fabricated inputs; no network request or production cache is involved.

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

`plan_stale_refreshes` models refresh deduplication for a batch of stale readers:

- the first request for each stale cache key becomes the synthetic refresh leader;
- later requests for that key become followers rather than additional origin refreshes;
- different cache keys elect independent leaders;
- fresh entries, misses, missing key mappings, duplicate request identifiers, and malformed requests fail validation rather than being treated as refresh work.

Run the lab with:

```bash
PYTHONPATH=labs/18-stale-cache-fallback python -m unittest discover -s labs/18-stale-cache-fallback/tests -v
```

## Evidence

The automated tests cover fresh and TTL boundaries, bounded stale delivery, the maximum-stale boundary, rejection beyond the stale budget, missing entries, a zero stale budget, invalid inputs, clock ordering, successful refresh replacement, failed refresh behavior on both sides of the stale boundary, contradictory revalidation inputs, same-key refresh deduplication, independent leaders across keys, non-stale rejection, duplicate request identifiers, and empty refresh batches.

The `age_ms`, `ttl_ms`, `max_stale_ms`, and `origin_refresh_count` values are deterministic model inputs or calculations. They are not latency, throughput, or production cache measurements. Revalidation outcomes and refresh requests are synthetic state transitions, not observations of an origin service.

## Limitations

This slice does not contact an origin, perform asynchronous revalidation, coordinate locks across threads or processes, model cache eviction, validate domain-specific data freshness, or execute follower wake-up after a leader completes. The refresh plan demonstrates deterministic leader election and bounded origin-work intent only; it does not claim production single-flight behavior.

## Next experiment

A later slice could connect the refresh plan to revalidation completion so followers observe one shared success or failure while the original maximum-stale boundary remains authoritative.
