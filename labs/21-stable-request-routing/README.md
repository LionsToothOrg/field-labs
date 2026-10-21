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

## Reproduce

```bash
PYTHONPATH=labs/21-stable-request-routing \
  python -m unittest discover -s labs/21-stable-request-routing/tests -v
```

The focused suite checks deterministic selection, node-order independence, single-node routing, add/remove membership behavior, and invalid input handling over fabricated keys.

## What this evidence supports

The tests demonstrate deterministic routing and the expected rendezvous-hashing membership behavior for the synthetic cases exercised by the suite. They do not demonstrate production traffic balance, latency, failure detection, replication, availability, persistence, or coordination between processes.

## Next experiment

A later slice can make routing movement measurable over a fixed synthetic key corpus and compare membership transitions without turning the lab into a live networking system.

All identifiers and request keys in this lab are fabricated for the experiment.
