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

`apply_follower_exits` models a follower that stops waiting before refresh completion:

- a follower may explicitly time out or cancel;
- its departure removes only that follower from later completion delivery;
- the elected leader and modeled origin-refresh count remain unchanged, so a follower departure cannot cancel shared work or elect replacement work;
- leaders and unknown request identifiers cannot be submitted as follower exits;
- separate cache keys remain isolated.

`complete_stale_refreshes` connects the active plan to one completion per elected leader:

- a leader success is delivered as the same fresh replacement to the leader and all active followers;
- a leader failure is delivered as the same bounded stale result to the active group;
- if completion occurs after the original maximum-stale boundary, every active reader receives a miss and the old value is withheld;
- completion mappings must match elected leaders exactly, preventing followers or unknown request IDs from injecting independent outcomes;
- separate keys retain independent completion results.

Run the lab with:

```bash
PYTHONPATH=labs/18-stale-cache-fallback python -m unittest discover -s labs/18-stale-cache-fallback/tests -v
```

## Evidence

Automated tests cover freshness boundaries, bounded stale delivery, revalidation success and failure, refresh deduplication, shared completion, and follower timeout/cancellation boundaries. Follower-exit cases verify that departures do not change elected origin work, departed followers receive no later completion delivery, separate keys stay isolated, leaders cannot exit through the follower path, malformed reasons fail closed, and an unchanged wait set preserves the original plan.

The `age_ms`, `ttl_ms`, `max_stale_ms`, and `origin_refresh_count` values are deterministic model inputs or calculations. They are not latency, throughput, or production cache measurements. Revalidation outcomes, refresh requests, and follower exits are synthetic state transitions, not observations of an origin service.

## Limitations

This lab does not contact an origin, perform asynchronous revalidation, coordinate locks across threads or processes, model cache eviction, validate domain-specific freshness, or implement real timers, cancellation propagation, or follower wake-up. The refresh plan, follower exits, and completion fan-out are deterministic state models; they do not claim production single-flight behavior or measured performance.

## Stopping point

The lab now covers bounded stale serving, explicit revalidation outcomes, per-key refresh deduplication, shared completion, and follower timeout/cancellation without weakening the original maximum-stale boundary. Further work should move to a separate lab unless a concrete defect in these modeled boundaries is found.
