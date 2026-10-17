# Lab 09 — Bounded API Retries

## Question

How can a client retry transient API failures without retrying permanent failures indefinitely or ignoring an explicit server backoff signal?

## Synthetic baseline

This lab uses fabricated HTTP-like status sequences only. It makes no network calls and contains no production endpoints, credentials, request payloads, customer data, or provider-specific behavior.

The first slice models a deterministic retry policy around three boundaries: which failures are retryable, how long the client waits, and when the attempt budget is exhausted.

## Retry boundary

`plan_retries` treats `429`, `500`, `502`, `503`, and `504` as transient for this experiment. Other non-success statuses stop immediately rather than consuming the remaining attempt budget.

Retryable failures use exponential backoff capped by a configured maximum. When a synthetic response supplies `retry_after_seconds`, the client respects it when it requires a longer wait than the local backoff. A server hint never shortens the local safety delay.

The final allowed failure is recorded as exhausted and does not schedule another retry.

## Run the validation

From the repository root:

```bash
PYTHONPATH=labs/09-bounded-api-retries python -m unittest discover -s labs/09-bounded-api-retries/tests -v
```

The focused suite checks transient retry behavior, immediate stop for permanent failures, attempt-budget exhaustion, longer `Retry-After` handling, protection against a shorter server hint, capped exponential backoff, and rejection of negative retry delays.

## What this slice establishes

Retry behavior can be explicit and bounded instead of being spread across request call sites. In this controlled fixture, transient classification, backoff, server guidance, and exhaustion produce inspectable decisions that can be tested without making real requests.

## Limitations

This slice does not make HTTP requests, parse `Retry-After` headers or dates, add jitter, model deadlines, distinguish idempotent from non-idempotent operations, coordinate retries across clients, implement circuit breaking, persist retry state, or measure production latency. Status sequences and delay values are synthetic inputs chosen to isolate policy behavior.
