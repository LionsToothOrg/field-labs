# Lab 09 — Bounded API Retries

## Question

How can a client retry transient API failures without retrying permanent failures indefinitely, ignoring an explicit server backoff signal, replaying an operation that is unsafe to repeat, or scheduling more retry wait than the caller is willing to tolerate?

## Synthetic baseline

This lab uses fabricated HTTP-like status sequences only. It makes no network calls and contains no production endpoints, credentials, request payloads, customer data, or provider-specific behavior.

The current slices model a deterministic retry policy around five boundaries: which failures are retryable, whether the operation itself is safe to replay, how long each retry waits, how much cumulative retry delay may be scheduled, and when the attempt budget is exhausted.

## Retry boundary

`plan_retries` treats `429`, `500`, `502`, `503`, and `504` as transient for this experiment. Other non-success statuses stop immediately rather than consuming the remaining attempt budget.

A transient response is not enough to authorize a replay. When `operation_is_idempotent=False`, the planner records `unsafe_to_retry` and stops after the first transient failure. An idempotent operation remains eligible for the bounded retry policy. This is an explicit synthetic policy input rather than an attempt to infer request safety from an HTTP method or payload.

Retryable failures use exponential backoff capped by a configured per-delay maximum. When a synthetic response supplies `retry_after_seconds`, the client respects it when it requires a longer wait than the local backoff. A server hint never shortens the local safety delay.

When `max_total_delay_seconds` is configured, the planner also tracks cumulative scheduled retry delay. If the next local backoff or server-directed delay would exceed the remaining budget, it records `delay_budget_exhausted` instead of scheduling that retry. A delay that exactly consumes the remaining budget is allowed. This budget is intentionally separate from `max_attempts`: one bounds scheduled waiting, while the other bounds request attempts.

The final allowed failure is recorded as exhausted and does not schedule another retry.

## Run the validation

From the repository root:

```bash
PYTHONPATH=labs/09-bounded-api-retries python -m unittest discover -s labs/09-bounded-api-retries/tests -v
```

The focused suite checks transient retry behavior, immediate stop for permanent failures, attempt-budget exhaustion, longer `Retry-After` handling, protection against a shorter server hint, capped exponential backoff, rejection of negative retry delays, the idempotency replay boundary, cumulative delay-budget exhaustion, exact-budget behavior, and server guidance that would exceed the delay budget.

## What this slice establishes

Retry behavior can be explicit and bounded instead of being spread across request call sites. In this controlled fixture, transient classification alone does not make a replay safe: operation idempotency is a separate eligibility boundary. Attempt count and cumulative scheduled waiting are also independent limits. Backoff, server guidance, replay safety, delay-budget exhaustion, and attempt exhaustion remain inspectable decisions that can be tested without making real requests.

## Limitations

This slice does not make HTTP requests, parse `Retry-After` headers or dates, add jitter, measure request execution time, model a wall-clock deadline, infer idempotency from HTTP methods or idempotency keys, coordinate retries across clients, implement circuit breaking, persist retry state, or measure production latency. Status sequences, operation safety, and delay values are synthetic inputs chosen to isolate policy behavior.
