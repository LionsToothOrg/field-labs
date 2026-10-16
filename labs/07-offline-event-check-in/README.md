# Lab 07 — Offline Event Check-In

## Question

What happens when two disconnected devices independently accept the same synthetic credential, then reconnect and reconcile their local decisions?

## Synthetic baseline

This lab uses fabricated credential IDs, device IDs, and integer timestamps. It has no real attendees, events, tickets, customer records, external services, or production identifiers.

`accept_offline` models the important offline constraint: a device can record an acceptance without knowing what another disconnected device has already accepted. That means two devices can each make a locally valid decision that cannot both remain authoritative after synchronization.

## Deterministic reconciliation

`reconcile` groups the disconnected decisions by credential through a deterministic ordering. The earliest synthetic timestamp wins; equal timestamps use the synthetic device ID as a stable tiebreaker. Any later acceptance for the same credential is surfaced explicitly as a conflict rather than silently discarded or treated as another successful admission.

This is intentionally a reconciliation experiment, not a claim that timestamp ordering is a complete real-world conflict policy. Device clocks can drift, identities need authentication, sync can be partial, and an operational system may require server-assigned ordering or manual resolution.

## Run the validation

From the repository root:

```bash
PYTHONPATH=labs/07-offline-event-check-in python -m unittest discover -s labs/07-offline-event-check-in/tests -v
```

The focused suite checks independent credentials, duplicate offline acceptance, input-order independence, and deterministic handling of equal timestamps.

## What this slice establishes

Offline acceptance changes the consistency model. In this controlled fixture, two devices can accept the same credential while disconnected, and reconciliation can preserve one deterministic winner while making the conflicting decision visible for follow-up.

## Limitations

This first slice does not model durable local storage, retries, incremental sync, clock skew correction, authenticated devices, credential signatures, revocation, capacity rules, manual conflict resolution, network partitions beyond the initial disconnected decisions, or production event operations. Later slices should add only the boundaries that can be demonstrated with repeatable evidence.
