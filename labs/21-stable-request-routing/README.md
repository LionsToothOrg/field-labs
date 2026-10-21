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

## Reproduce

```bash
PYTHONPATH=labs/21-stable-request-routing \
  python -m unittest discover -s labs/21-stable-request-routing/tests -v
```

The focused suite checks deterministic selection, node-order independence, single-node routing, add/remove membership behavior, exact transition measurement over the fixed fabricated corpus, unchanged-membership movement, and invalid input handling.

## What this evidence supports

The tests demonstrate deterministic routing and inspectable membership movement for the synthetic cases exercised by the suite. The measured movement ratio describes only the checked-in fabricated corpus. It does not demonstrate production traffic balance, latency, failure detection, replication, availability, persistence, weighted capacity, or coordination between processes.

## Next experiment

A later slice can compare multiple synthetic membership transitions or make ownership distribution inspectable while keeping corpus-specific observations clearly separate from production claims.

All identifiers and request keys in this lab are fabricated for the experiment.
