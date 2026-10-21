# Lab 21 — Stable Request Routing

## Question

How can a service route a synthetic request key to one member of a changing node set while keeping membership changes from remapping unrelated keys?

This lab uses fabricated node names and request keys only. It is a deterministic routing experiment, not a production load balancer or distributed-system benchmark.

## First slice: rendezvous routing

`stable_routing.py` implements rendezvous (highest-random-weight) hashing with SHA-256:

- each request key is scored independently against every available node;
- the node with the highest deterministic score owns the key;
- input order does not affect the selected node;
- duplicate or empty node sets fail explicitly instead of creating ambiguous routing state.

The useful membership property is narrow and testable. When one node is added, a key either stays on its previous node or moves to the new node. When one node is removed, only keys previously owned by that node need to move. The implementation does not claim even load distribution for every key set.

## Second slice: measurable membership transitions

`measure_membership_transition` compares two complete membership snapshots over one explicit synthetic key corpus. It returns the corpus size, the exact keys that moved, a movement count, and a movement ratio. Empty or duplicate-key corpora are rejected so a measurement cannot silently use an ambiguous denominator.

For the checked-in corpus of 100 fabricated keys (`item-000` through `item-099`), adding fabricated `node-d` to the original three-node membership moves exactly 19 keys. That `19%` value is a deterministic observation for this specific corpus and hash function, not a general performance or balance claim. An unchanged membership, including a different input ordering, measures zero movement.

## Third slice: inspectable ownership distribution

`measure_ownership_distribution` counts how the same explicit synthetic corpus is assigned across one complete membership snapshot. The report retains every member, including nodes that own zero keys, and exposes the minimum count, maximum count, and absolute count spread without interpreting those values as a production balancing guarantee.

For the checked-in 100-key corpus and the original three fabricated nodes, ownership is `node-a: 38`, `node-b: 32`, and `node-c: 30`, for a count spread of `8`. Those values are deterministic observations for this corpus and hash function only. They are not throughput, capacity, utilization, latency, or statistical-uniformity measurements.

## Fourth slice: ownership changes across membership

`compare_ownership_snapshots` measures before/after ownership counts over the same explicit corpus and reports a signed delta for every node present in either membership. This makes the count-level effect of a membership change inspectable without hiding added or removed members.

For the checked-in 100-key corpus, adding fabricated `node-d` changes ownership from `38/32/30` to `32/25/24/19`. The corresponding deltas are `node-a: -6`, `node-b: -7`, `node-c: -6`, and `node-d: +19`; they sum to zero because the corpus size is unchanged. These are deterministic corpus-specific observations, not capacity or production-load measurements.

## Reproduce

```bash
PYTHONPATH=labs/21-stable-request-routing \
  python -m unittest discover -s labs/21-stable-request-routing/tests -v
```

The focused suite checks deterministic selection, node-order independence, single-node routing, add/remove membership behavior, exact transition measurement, exact ownership counts, before/after ownership deltas over the fixed fabricated corpus, zero-ownership visibility, and invalid input handling.

## What this evidence supports

The tests demonstrate deterministic routing, inspectable membership movement, ownership counts, and ownership deltas for the synthetic cases exercised by the suite. All measured values describe only the checked-in fabricated corpus. They do not demonstrate production traffic balance, latency, failure detection, replication, availability, persistence, weighted capacity, utilization, or coordination between processes.

## Stopping point

Lab 21 now covers deterministic rendezvous routing, measurable membership churn, ownership distribution, and ownership deltas across a membership transition. Weighted capacity, failure detection, replication, and live traffic behavior are intentionally left outside this lab so the evidence stays bounded to the deterministic synthetic model.

All identifiers and request keys in this lab are fabricated for the experiment.
