# Quarantine inspection and replay

This slice adds an intentionally small operator-facing recovery boundary to the synthetic outbox experiment.

`RetryPolicyStore.quarantined()` is the inspection surface. It returns only messages that have reached the configured attempt limit. `replay_quarantined()` can return one selected message to immediate eligibility, but it does **not** reset the durable attempt count. A replay is therefore a deliberate exception, not a way to erase failure history.

Every accepted replay writes a `quarantine_audit` event in the same SQLite transaction that changes eligibility. The event records the synthetic request identifier, action, timestamp, and attempt count observed at replay time. Unknown and non-quarantined request identifiers are rejected and do not create audit events.

If a replayed message fails again while its existing attempt count is already at or above the configured limit, the normal failure path quarantines it again. This keeps repeated failures bounded unless an operator explicitly chooses another replay.

## Validation

The focused tests live in `tests/test_quarantine_replay.py` and cover:

- restoring eligibility without resetting attempt history;
- durable audit-event creation for accepted replay;
- rejection of unknown and non-quarantined requests; and
- re-quarantine after a replayed message fails again.

Run the complete lab suite from the repository root:

```bash
python -m unittest discover -s labs/01-transaction-reliability/tests -v
```

## Boundary

This is not a production dead-letter queue, authorization system, or administrative UI. It does not model operator identity, approval policy, replay reasons, retention, bulk replay, or distributed audit storage. Those concerns remain outside this local SQLite experiment.
