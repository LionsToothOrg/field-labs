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

`apply_revalidation_outcome` models one explicit refresh result for an expired entry. Success requires a new non-empty synthetic value. Failure preserves the original value only while its original maximum-stale budget remains valid.

`plan_stale_refreshes` elects the first request for each stale key as refresh leader. Later same-key readers become followers, while different keys remain independent.

`complete_stale_refreshes` connects that plan to one completion per elected leader:

- a leader success is delivered as the same fresh replacement to the leader and all followers;
- a leader failure is delivered as the same bounded stale result to the whole group;
- if completion occurs after the original maximum-stale boundary, every reader receives a miss and the old value is withheld;
- completion mappings must match elected leaders exactly, preventing followers or unknown request IDs from injecting independent outcomes;
- separate keys retain independent completion results.

Run the lab with:

```bash
PYTHONPATH=labs/18-stale-cache-fallback python -m unittest discover -s labs/18-stale-cache-fallback/tests -v
```

## Evidence

Automated tests cover freshness boundaries, bounded stale delivery, revalidation success and failure, refresh deduplication, and shared completion. Shared-completion cases verify success fan-out, failure fan-out on both sides of the stale boundary, per-key isolation, exact leader matching, malformed completion rejection, missing entries, and an empty plan.

The `age_ms`, `ttl_ms`, `max_stale_ms`, and `origin_refresh_count` values are deterministic model inputs or calculations. They are not latency, throughput, or production cache measurements. Revalidation outcomes and refresh requests are synthetic state transitions, not observations of an origin service.

## Limitations

This lab does not contact an origin, perform asynchronous revalidation, coordinate locks across threads or processes, model cache eviction, validate domain-specific freshness, or implement real follower wake-up. The refresh plan and completion fan-out are deterministic state models; they do not claim production single-flight behavior or measured performance.

## Next experiment

A later slice could model cancellation or timeout while followers await a refresh leader, while keeping the maximum-stale boundary authoritative.
