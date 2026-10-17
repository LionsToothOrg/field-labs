# Lab 07 — Offline Event Check-In

## Question

What happens when disconnected devices independently accept synthetic credentials, then reconnect through a synchronization path that may retry or deliver overlapping batches?

## Synthetic baseline

This lab uses fabricated check-in IDs, credential IDs, device IDs, and integer timestamps. It has no real attendees, events, tickets, customer records, external services, or production identifiers.

`accept_offline` models the important offline constraint: a device can record an acceptance without knowing what another disconnected device has already accepted. That means two devices can each make a locally valid decision that cannot both remain authoritative after synchronization.

## Deterministic reconciliation

`reconcile` orders disconnected decisions deterministically. The earliest synthetic timestamp wins for each credential; equal timestamps use the synthetic device ID and then check-in ID as stable fixture tiebreakers. Any later acceptance for the same credential is surfaced explicitly as a conflict rather than silently discarded or treated as another successful admission.

This is intentionally a reconciliation experiment, not a claim that timestamp ordering is a complete real-world conflict policy. Device clocks can drift, identities need authentication, sync can be partial, and an operational system may require server-assigned ordering or manual resolution.

## Idempotent incremental sync

Each synthetic decision now has a stable `check_in_id`. `merge_sync` merges incoming batches by that identity, so replaying an already-observed batch does not create duplicate accepted decisions or duplicate conflict records. Overlapping batches add only unseen decisions.

A repeated check-in ID is accepted only when its payload is identical to the previously observed decision. Reusing an ID with different credential, device, or timestamp data fails closed with an error instead of silently overwriting history.

## Run the validation

From the repository root:

```bash
PYTHONPATH=labs/07-offline-event-check-in python -m unittest discover -s labs/07-offline-event-check-in/tests -v
```

The focused suite checks independent credentials, duplicate offline acceptance, input-order independence, deterministic equal-timestamp handling, replay idempotency, overlapping incremental batches, and conflicting identity reuse.

## What this slice establishes

Offline acceptance changes the consistency model, and synchronization must account for retry semantics as well as conflicts. In this controlled fixture, repeated delivery of the same synthetic decisions is idempotent, overlapping batches preserve unseen decisions, and conflicting reuse of a stable decision identity is rejected.

## Limitations

This slice does not model durable local storage, transactional persistence, concurrent server writers, clock skew correction, authenticated devices, credential signatures, revocation, capacity rules, manual conflict resolution, transport acknowledgements, pruning or retention, network partitions beyond the modeled disconnected decisions, or production event operations. Stable check-in IDs are supplied by the fixture; generation and authenticity of those IDs are outside this experiment.
