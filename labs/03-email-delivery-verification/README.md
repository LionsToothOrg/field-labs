# Lab 03 — Email Delivery & Verification

## Question

What does an application actually know when it says an email was sent?

This lab separates application generation, provider acceptance, deferral, bounce, and delivery into explicit evidence states. It is intentionally provider-free and uses only fabricated events.

## Baseline

A common application-level shortcut is to treat successful message generation or provider acceptance as proof of delivery. Those events establish useful facts, but neither proves that the destination accepted the message.

The state model starts with five deliberately small states:

`generated -> accepted -> deferred | bounced | delivered`

A deferred message may remain deferred or later become bounced or delivered. Bounce and delivery are terminal in this model.

## Evidence established so far

The automated tests establish that:

- generation alone is not delivery evidence;
- provider acceptance alone is not delivery evidence;
- a deferred synthetic message can later reach delivered state;
- a bounced message cannot later be recorded as delivered;
- delivery cannot be recorded before provider acceptance;
- a duplicate synthetic provider event is applied only once;
- a stale event cannot overwrite newer delivery evidence;
- a contradictory later event cannot reverse a terminal delivery state;
- reconciliation decisions classify applied, duplicate, stale, and contradictory events without copying provider event detail into the decision record;
- persisted reconciliation state can reject duplicate and stale events after a simulated process restart;
- durable reconciliation state retains only the current delivery state, synthetic event IDs, and latest applied sequence, not provider event detail;
- two workers reading the same state can lose stronger delivery evidence when they write independently;
- a version-checked conditional write rejects an obsolete worker snapshot, allowing a retry from fresh state to preserve terminal delivery evidence;
- a bounded retry re-reads and re-reconciles after a synthetic conditional-write conflict;
- exhausting the retry budget raises an explicit failure without committing the pending event;
- deterministic synthetic retry delays are observable without sleeping or reading wall-clock time; and
- a retry is refused when its configured delay would cross the total synthetic deadline.

The reconciliation slice uses fabricated event IDs and monotonic sequence numbers to make ordering decisions explicit. Events are processed in arrival order: duplicate IDs are ignored, events at or below the latest applied sequence are treated as stale, and transitions that contradict the delivery state machine are ignored rather than rewriting stronger evidence.

Each processed event also produces a typed reconciliation decision containing only its synthetic event ID, sequence, and outcome. A separate immutable reconciliation state captures the minimum information this experiment needs across a process boundary: current delivery state, previously seen event IDs, and the latest applied sequence. `restore_trace` reconstructs a content-free runtime trace from that state so historical provider detail does not need to be persisted for reconciliation.

The concurrency experiment adds a deliberately tiny in-memory state-store boundary. `write_unchecked` exists only to reproduce a lost-update race: two workers can read the same accepted state, independently derive delivered and deferred states, then overwrite one another. `compare_and_swap` adds a version precondition so the second write fails when its read snapshot is obsolete. Retrying that event from the fresh delivered state lets the existing reconciliation rules classify the later deferral as contradictory instead of weakening delivery evidence.

`reconcile_with_retry` makes that retry behavior explicit and bounded. Each attempt reads a fresh version, re-runs reconciliation, and conditionally writes the result. A conflict consumes one attempt; exhausting the configured budget raises `RetryExhausted` rather than looping indefinitely or implying success.

`reconcile_with_timed_retry` adds deterministic scheduling policy without real sleeps. `RetryPolicy` supplies fabricated millisecond delays and a total deadline. The result records only attempts, elapsed synthetic time, and scheduled delays; if the next delay would cross the deadline, the helper raises `RetryDeadlineExceeded` before another attempt begins. This makes timing behavior repeatable while keeping wall-clock and queue behavior outside the experiment.

Run the focused tests from the repository root:

```bash
PYTHONPATH=labs/03-email-delivery-verification python -m unittest discover -s labs/03-email-delivery-verification/tests -v
```

## Limitations

This is a state-machine, restart-boundary, and concurrency experiment, not a deliverability simulator and not an integration with an email provider. The synthetic sequence is an explicit lab assumption; real providers may expose timestamps, attempt counters, webhook IDs, or other ordering semantics instead. `ReconciliationState` models what would need to survive a restart but does not itself provide storage or retention. `SyntheticStateStore` is process-local and deterministic; its version check demonstrates the conditional-write contract but does not establish database transaction semantics, distributed locking, crash recovery, multi-region consistency, or production-grade multi-worker coordination. Retry delays and deadlines are deterministic synthetic values: they do not model wall-clock drift, jitter, cancellation, queue redelivery, overload behavior, or a production scheduler. The lab does not model authentication records, suppression lists, complaint events, provider webhook signatures, mailbox placement, spam filtering, or cryptographic verification of event provenance.

All identifiers, event details, and mailbox behavior in this lab are synthetic. No real addresses, messages, provider payloads, or delivery logs are used.

## Next experiment

A useful next slice is to model retry cancellation as a separate explicit outcome, keeping cancellation deterministic and distinct from deadline exhaustion without claiming production queue semantics.
