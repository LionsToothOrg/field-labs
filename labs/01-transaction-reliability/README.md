# Lab 01 · Transaction Reliability

## Question

A caller times out after sending a state-changing request and retries with the same request identifier. If attempts overlap, can a check-then-write implementation apply the change twice? What changes when the idempotency boundary must survive restart, and how can local state safely record an intent for a separate side effect?

## Synthetic scenario

This lab models a tiny points ledger. `req-demo-001` adds 25 points to a fictional account. Two worker threads can submit that same logical request concurrently.

The intentionally unsafe implementation checks whether the request was seen, pauses at a controlled synchronization point, mutates the balance, and then records the request identifier. The test-only pause makes the race reproducible rather than timing-dependent.

`IdempotentLedger` puts duplicate detection and mutation in one in-process critical section.

`DurableLedger` advances the invariant into SQLite. A unique request key and balance mutation commit in the same transaction, so restart does not erase duplicate detection and concurrent writers cannot both commit the same logical request.

`OutboxLedger` adds one more boundary. The local state change and a synthetic side-effect intent are committed in the same transaction. A separate dispatcher later delivers pending intents and acknowledges successful delivery. This avoids pretending that a local database transaction can atomically include an external system.

## Run the validation

From the repository root:

```bash
python -m unittest discover -s labs/01-transaction-reliability/tests -v
```

The suite covers the unsafe race, process-local idempotency, durable restart/concurrency/failure behavior, and the outbox boundary. Outbox cases verify that:

- committed state and its side-effect intent both survive restart;
- a successful synthetic delivery is acknowledged and removed from the pending set;
- a failed synthetic delivery remains pending and can be retried;
- a duplicate request creates only one local mutation and one outbox intent.

## What this establishes

An idempotency key is not enough when duplicate detection and mutation are separate raceable operations. Correctness requires a boundary that owns both decisions.

The durable model also shows why recording a request key separately from the mutation is dangerous: a crash between those writes can suppress a legitimate retry. Keeping them in one transaction makes the local changes commit or roll back together.

The outbox model extends that reasoning to side effects. Local state and an intent can be atomic even when the eventual delivery cannot be. A failed delivery therefore remains recoverable instead of losing the intent.

## Important delivery boundary

The dispatcher intentionally does **not** claim exactly-once remote delivery. Delivery and acknowledgement are separate operations. If a downstream system accepts a message and the worker crashes before marking it sent, that message can be delivered again after restart.

That is an at-least-once boundary. A real consumer would need its own idempotency/deduplication strategy, or a protocol with stronger guarantees, when duplicate delivery matters.

## Limitations and next experiment

This is still a local SQLite model with a synchronous synthetic dispatcher. It does not demonstrate a distributed database, broker visibility timeouts, multiple dispatch workers, leases, backoff, dead-letter handling, ordering, request-key expiration, response replay, or exactly-once remote side effects.

A useful next slice is safe concurrent outbox dispatch: introduce message claiming/leases and reproduce what happens when multiple workers compete for pending work or a worker dies while holding a claim.
