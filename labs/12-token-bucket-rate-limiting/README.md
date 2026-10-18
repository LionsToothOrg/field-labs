# Lab 12 — Token Bucket Rate Limiting

## Question

How can a caller admit short bursts of synthetic work while enforcing a bounded long-term request rate without depending on wall-clock sleeps or external services?

This lab models a token-bucket policy with an injected timestamp. By default the bucket starts full, but a caller may provide a bounded initial token count to model a cold start or restored quota state. Admitted work spends tokens, and elapsed time refills the bucket up to a fixed capacity.

## Model

1. `capacity` bounds the largest burst the bucket can hold.
2. `refill_rate` adds tokens per unit of elapsed synthetic time.
3. `initial_tokens` defaults to capacity and may be set from zero through capacity.
4. Each request consumes a positive token weight only when enough tokens are available.
5. Rejected requests leave available tokens untouched.
6. Refill never grows the bucket beyond capacity.
7. Time must be monotonic; a regressing timestamp is rejected before state changes.
8. A retryable rejection reports how much synthetic time must elapse before the requested weight can be admitted.
9. A request larger than total bucket capacity is explicitly non-retryable because refill can never satisfy it.
10. `inspect(now)` projects capacity at a synthetic timestamp without consuming tokens or advancing bucket state.

## Run the focused tests

```bash
PYTHONPATH=labs/12-token-bucket-rate-limiting \
  python -m unittest discover -s labs/12-token-bucket-rate-limiting/tests -v
```

The tests cover full, partial, and empty initialization; burst consumption; exhaustion; elapsed-time refill; capacity capping; non-mutating capacity inspection; rejection accounting; weighted retry timing; permanently oversized requests; clock regression; and invalid numeric inputs.

## Design choices

- **Injected time:** callers provide `now`, making refill behavior deterministic and testable without sleeping.
- **Bounded initialization:** `initial_tokens` supports deterministic cold-start and restored-state scenarios without allowing initial state above capacity.
- **Weighted requests:** a synthetic operation may consume more than one token.
- **Actionable rejection:** a temporary rejection reports `retry_after` from the exact token deficit and refill rate. An admitted request reports `0.0`.
- **Impossible-request distinction:** requests larger than bucket capacity return `request_exceeds_capacity` with no retry delay instead of suggesting that waiting can make them admissible.
- **Non-mutating inspection:** `inspect(now)` reports projected tokens at a valid synthetic timestamp without spending capacity or advancing the internal refill clock.
- **Fail-fast rejection:** insufficient capacity returns a decision immediately; this slice does not queue or delay work.
- **Monotonic clock contract:** timestamps older than the last accepted timestamp raise an error rather than manufacturing refill behavior from inconsistent time.
- **Finite numeric inputs:** booleans, infinities, NaN values, negative initial state, zero, and negative token quantities are rejected where they would make the policy ambiguous.
- **Inspectable state:** decisions expose requested tokens, remaining tokens, capacity, a reason, and retry timing; `inspect()` exposes projected capacity while `snapshot()` exposes committed bucket state for tests and diagnostics.

## What this slice demonstrates

The implementation demonstrates deterministic burst admission, bounded initialization, time-based replenishment, caller-facing retry guidance, and side-effect-free capacity inspection. A caller can observe projected availability before deciding whether to attempt work without changing later admission behavior. A request that exceeds currently available tokens is rejected without consuming the remainder and receives the minimum synthetic delay required to refill its deficit. Requests that can never fit in the bucket are distinguished from temporary saturation.

## Limitations

This is an in-memory policy experiment, not a production rate-limiting service. `initial_tokens` is caller-provided state, not durable persistence or a trusted restore mechanism. `inspect()` is informational only and does not reserve the capacity it reports, so another admission could change availability before a subsequent request in a concurrent implementation. The lab does not provide cross-process coordination, persistence, fairness between callers, distributed clock handling, atomic storage semantics, HTTP retry headers, queueing, or transport integration. `retry_after` is expressed in the same synthetic time unit used by `now`; adapting it to a transport such as HTTP would require an explicit unit and rounding policy. Floating-point arithmetic is sufficient for this bounded demonstration but would need an explicit precision strategy where exact fractional accounting matters.

All identities, timestamps, and workload behavior in this lab are synthetic. No network calls, production systems, client records, or private services are involved.
