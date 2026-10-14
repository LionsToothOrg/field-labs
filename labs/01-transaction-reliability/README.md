# Lab 01 · Transaction Reliability

## Question

A caller times out after sending a state-changing request and retries with the same request identifier. If attempts overlap, can a check-then-write implementation apply the change twice? What changes when the idempotency boundary must survive restart, and how can local state safely record and dispatch an intent for a separate side effect when multiple workers are present?

## Synthetic scenario

This lab models a tiny points ledger. `req-demo-001` adds 25 points to a fictional account. Two worker threads can submit that same logical request concurrently.

The intentionally unsafe implementation checks whether the request was seen, pauses at a controlled synchronization point, mutates the balance, and then records the request identifier. The test-only pause makes the race reproducible rather than timing-dependent.

`IdempotentLedger` puts duplicate detection and mutation in one in-process critical section.

`DurableLedger` advances the invariant into SQLite. A unique request key and balance mutation commit in the same transaction, so restart does not erase duplicate detection and concurrent writers cannot both commit the same logical request.

`OutboxLedger` adds one more boundary. The local state change and a synthetic side-effect intent are committed in the same transaction. Dispatch workers atomically claim pending intents with time-bounded leases before delivery. Successful delivery is acknowledged by the worker that owns the claim; failed delivery releases the claim for retry. An abandoned claim becomes available after its lease expires.

`RetryPolicyStore` isolates the next reliability question: what should happen when delivery keeps failing? It persists attempt counts, schedules deterministic exponential backoff, and quarantines a synthetic message when its configured attempt limit is reached. Deferred or quarantined work is not eligible for delivery, so a repeatedly failing message does not have to monopolize healthy work.

## Run the validation

From the repository root:

```bash
python -m unittest discover -s labs/01-transaction-reliability/tests -v
```

The suite covers the unsafe race, process-local idempotency, durable restart/concurrency/failure behavior, the transactional outbox boundary, concurrent outbox worker leases, and retry policy behavior. Outbox and retry cases verify that:

- committed state and its side-effect intent both survive restart;
- a successful synthetic delivery is acknowledged and removed from the pending set;
- a failed synthetic delivery remains recoverable and can be retried;
- a duplicate request creates only one local mutation and one outbox intent;
- competing workers do not concurrently own the same unexpired message lease;
- an abandoned message can be reclaimed after lease expiry;
- a stale worker cannot acknowledge a message after another worker has reclaimed it;
- retry delays grow deterministically with each failed attempt;
- retry state survives restart;
- a message is quarantined when its configured attempt limit is reached;
- deferred poison work does not make unrelated healthy work ineligible.

## What this establishes

An idempotency key is not enough when duplicate detection and mutation are separate raceable operations. Correctness requires a boundary that owns both decisions.

The durable model also shows why recording a request key separately from the mutation is dangerous: a crash between those writes can suppress a legitimate retry. Keeping them in one transaction makes the local changes commit or roll back together.

The outbox model extends that reasoning to side effects. Local state and an intent can be atomic even when the eventual delivery cannot be. Worker leases add bounded ownership so concurrent dispatchers can coordinate without holding a database transaction open across delivery, while expired leases make abandoned work recoverable.

The retry slice separates transient failure from permanently unhealthy work. Backoff prevents immediate hot-loop retries, while quarantine gives repeatedly failing messages an explicit terminal state for operator review instead of allowing them to consume every dispatch opportunity.

## Important delivery boundary

The dispatcher intentionally does **not** claim exactly-once remote delivery. Delivery and acknowledgement are separate operations. If a downstream system accepts a message and the worker crashes before marking it sent, that message can be delivered again after its lease expires.

That is an at-least-once boundary. A real consumer would need its own idempotency/deduplication strategy, or a protocol with stronger guarantees, when duplicate delivery matters.

Lease expiry also assumes workers have a sufficiently consistent notion of time. This local model accepts an injectable timestamp for deterministic recovery tests; it does not attempt to solve distributed clock skew.

The retry model deliberately uses deterministic exponential backoff so exact timing can be asserted. Production retry systems commonly add jitter to reduce synchronized retry storms. Quarantine here is a local state transition, not a production dead-letter queue or an operator workflow.

## Limitations and next experiment

This is still a local SQLite model with synchronous synthetic delivery. It does not demonstrate a distributed database, broker visibility timeouts, lease renewal for long-running work, jittered backoff, a real dead-letter queue, replay tooling, ordering, request-key expiration, response replay, or exactly-once remote side effects.

A useful next slice is to integrate retry eligibility directly into outbox claiming and add an explicit quarantine/replay workflow, while preserving the worker-lease guarantees already demonstrated here.
