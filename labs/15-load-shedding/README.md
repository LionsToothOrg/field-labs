# Lab 15 — Load Shedding Under Saturation

## Question

When a service has bounded execution and queue capacity, which requests should be admitted during a synthetic overload burst, and how does admitted work recover after the burst?

## Failure scenario

An overloaded service that accepts every request can turn a short burst into an ever-growing backlog. Requests may wait even when the system has no bounded capacity to serve them promptly.

The admission slice models a deliberately small boundary: requests arriving in order may start immediately while execution slots remain, enter a bounded queue while queue slots remain, and are shed once both capacities are full.

This slice adds deterministic recovery. A completion round finishes the currently running synthetic requests, then promotes queued work in FIFO order up to the concurrency limit. Shed requests never re-enter the system.

## Approach

`admit_burst()` accepts fabricated request identifiers plus an execution limit and queue limit. It returns an explicit decision for every request:

- `running` — admitted directly to an execution slot;
- `queued` — admitted to bounded waiting capacity;
- `shed` — rejected at the admission boundary.

`drain_admitted()` then advances only the admitted work through deterministic completion rounds. Each `RecoveryStep` records which requests completed, which queued requests were promoted, and the remaining running and queued sets.

The model is deterministic and does not create threads, sockets, servers, timers, or real queues. Its purpose is to make overload admission and recovery accounting inspectable before adding time-based scheduling policy.

## Run the tests

```bash
PYTHONPATH=labs/15-load-shedding python -m unittest discover -s labs/15-load-shedding/tests -v
```

## Synthetic-data note

All request identifiers and capacity values are fabricated for this lab. No production traffic, customer records, private systems, or external services are used.

## Evidence in this slice

The tests cover execution-slot admission, bounded queue admission, shedding after total capacity is exhausted, a zero-length queue, request-order preservation, empty bursts, invalid inputs, FIFO queue promotion, complete exclusion of shed work from recovery, empty recovery, and rejection of a recovery capacity that conflicts with already-admitted running work.

Treat repository CI for the commit as the published validation record; do not infer passing status from this README alone.

## Limitations

This is a deterministic admission-and-recovery model, not a production load balancer or server. Every running request completes together at the next modeled round, so the lab does not represent request duration, partial completion, timeouts, retries, priorities, fairness, distributed capacity, adaptive limits, or feedback from downstream dependencies. FIFO promotion describes this model only; it is not a claim about a production scheduler.

A useful next slice could introduce synthetic arrival and service ticks to measure sustained overload and recovery while keeping time and data fully deterministic.
