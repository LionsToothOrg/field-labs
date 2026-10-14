# Lab 01 · Transaction Reliability

## Question

A client times out after sending a state-changing request and retries with the same request identifier. If both attempts overlap, can a check-then-write implementation apply the change twice? What changes when the idempotency boundary must survive a process restart?

## Synthetic scenario

This lab models a tiny points ledger. `req-demo-001` adds 25 points to a fictional account. Two worker threads can submit that same logical request concurrently.

The intentionally unsafe implementation performs the familiar sequence:

1. check whether the request identifier was seen;
2. yield at a controlled synchronization point;
3. mutate the balance;
4. record the request identifier.

The synchronization point is test-only instrumentation that makes the race reproducible rather than timing-dependent. Both workers can pass the check before either records the identifier.

`IdempotentLedger` moves the duplicate check, state change, and request recording into one in-memory critical section. The operation therefore has a single in-process serialization point.

`DurableLedger` advances the same invariant into a local SQLite database. A unique request key and the balance mutation are committed in the same transaction. `BEGIN IMMEDIATE` establishes the write boundary before the request key is claimed, so concurrent writers cannot both commit the same logical request. Because the request record is persisted, a later process can still recognize the duplicate.

## Run the validation

From the repository root:

```bash
python -m unittest discover -s labs/01-transaction-reliability/tests -v
```

The suite checks behavior rather than publishing a benchmark. It reproduces the unsafe duplicate race, verifies the in-process fix, and exercises three durable cases:

- a duplicate submitted after a new `DurableLedger` instance opens the same database is ignored;
- concurrent duplicate submissions commit one mutation;
- a synthetic failure after claiming the request key but before mutation rolls back the whole transaction, allowing a later retry to succeed.

## What this establishes

An idempotency key is not sufficient when duplicate detection and state mutation are separate raceable operations. In the in-memory model, correctness comes from one critical section. In the durable model, correctness comes from a database uniqueness constraint and a transaction that owns both the request claim and the state mutation.

The failure-injection case is important: persisting the request key before the mutation in a separate transaction could permanently suppress a legitimate retry after a crash. Keeping the claim and mutation in one transaction means they commit or roll back together in this model.

## Limitations and next experiment

SQLite gives this lab a durable local transaction boundary, but it is still a deliberately small model. It does not demonstrate a distributed database, multiple service nodes coordinating remote side effects, message-broker delivery semantics, request-key expiration, response replay, or recovery when an external API succeeds while the local transaction fails.

A useful next step is an outbox-style experiment: commit local state and an intent to perform a synthetic external side effect atomically, then examine retries and worker crashes without pretending a local database transaction can make a remote call atomic.
