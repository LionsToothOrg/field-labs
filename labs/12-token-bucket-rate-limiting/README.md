# Lab 12 — Token Bucket Rate Limiting

## Question

How can a caller admit short bursts of synthetic work while enforcing a bounded long-term request rate without depending on wall-clock sleeps or external services?

This lab models a token-bucket policy with an injected timestamp. The bucket starts full, spends tokens when work is admitted, and refills from elapsed time up to a fixed capacity.

## Model

1. `capacity` bounds the largest burst the bucket can hold.
2. `refill_rate` adds tokens per unit of elapsed synthetic time.
3. Each request consumes a positive token weight only when enough tokens are available.
4. Rejected requests leave available tokens untouched.
5. Refill never grows the bucket beyond capacity.
6. Time must be monotonic; a regressing timestamp is rejected before state changes.

## Run the focused tests

```bash
PYTHONPATH=labs/12-token-bucket-rate-limiting \
  python -m unittest discover -s labs/12-token-bucket-rate-limiting/tests -v
```

The tests cover burst consumption, exhaustion, elapsed-time refill, capacity capping, rejection accounting, clock regression, and invalid numeric inputs.

## Design choices

- **Injected time:** callers provide `now`, making refill behavior deterministic and testable without sleeping.
- **Weighted requests:** a synthetic operation may consume more than one token.
- **Fail-fast rejection:** insufficient capacity returns a decision immediately; this slice does not queue or delay work.
- **Monotonic clock contract:** timestamps older than the last accepted timestamp raise an error rather than manufacturing refill behavior from inconsistent time.
- **Finite numeric inputs:** booleans, infinities, NaN values, zero, and negative token quantities are rejected where they would make the policy ambiguous.
- **Inspectable state:** decisions expose requested tokens, remaining tokens, capacity, and a reason; `snapshot()` exposes current bucket state for tests and diagnostics.

## What this slice demonstrates

The implementation demonstrates deterministic burst admission and time-based replenishment. A request that exceeds currently available tokens is rejected without consuming the remainder, while elapsed synthetic time restores capacity only up to the configured maximum.

## Limitations

This is an in-memory policy experiment, not a production rate-limiting service. It does not provide cross-process coordination, persistence, fairness between callers, distributed clock handling, atomic storage semantics, retry headers, queueing, or transport integration. Floating-point arithmetic is sufficient for this bounded demonstration but would need an explicit precision strategy where exact fractional accounting matters.

All identities, timestamps, and workload behavior in this lab are synthetic. No network calls, production systems, client records, or private services are involved.
