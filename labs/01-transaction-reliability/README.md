# Lab 01 · Transaction Reliability

## Question

A client times out after sending a state-changing request and retries with the same request identifier. If both attempts overlap, can a check-then-write implementation apply the change twice? What is the smallest mechanism that prevents it inside one process?

## Synthetic scenario

This lab models a tiny in-memory points ledger. `req-demo-001` adds 25 points to a fictional account. Two worker threads submit that same logical request concurrently.

The intentionally unsafe implementation performs the familiar sequence:

1. check whether the request identifier was seen;
2. yield at a controlled synchronization point;
3. mutate the balance;
4. record the request identifier.

The synchronization point is test-only instrumentation that makes the race reproducible rather than timing-dependent. Both workers can pass the check before either records the identifier.

`IdempotentLedger` moves the duplicate check, state change, and request recording into one critical section. The operation therefore has a single in-process serialization point.

## Run the validation

From the repository root:

```bash
python -m unittest discover -s labs/01-transaction-reliability/tests -v
```

The tests assert the behavior rather than publishing a benchmark: the controlled unsafe race applies the 25-point mutation twice, while the idempotent implementation applies it once. Additional tests verify that distinct request identifiers still apply independently and that a later retry is ignored.

## What this establishes

An idempotency key is not sufficient when the duplicate check and state mutation are separate raceable operations. In this model, correctness comes from making the check-and-apply decision atomic relative to competing workers.

## Limitations and next experiment

A Python `Lock` protects only one process. It does not coordinate multiple application instances, survive a process crash, or make a remote side effect atomic with local persistence. A production design normally needs a durable uniqueness/transaction boundary (for example, a database uniqueness constraint plus transaction) and a deliberate policy for request-key retention and response replay.

The next useful slice is to reproduce the same invariant against a durable local datastore and examine crash/retry behavior without introducing any external service or private infrastructure.
