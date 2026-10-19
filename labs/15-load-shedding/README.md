# Lab 15 — Load Shedding Under Saturation

## Question

When a service has bounded execution and queue capacity, which requests should be admitted during synthetic overload, and how does the balance between arrivals and service affect shedding over time?

## Failure scenario

An overloaded service that accepts every request can turn a short burst into an ever-growing backlog. Requests may wait even when the system has no bounded capacity to serve them promptly.

The admission slice models a deliberately small boundary: requests arriving in order may start immediately while execution slots remain, enter a bounded queue while queue slots remain, and are shed once both capacities are full.

The recovery slice adds deterministic completion rounds. Running synthetic requests complete, queued work is promoted in FIFO order, and shed requests never re-enter the system.

The sustained-load slice adds discrete synthetic ticks so arrivals and service can be compared repeatedly. At each tick, configured completions occur first, queued work is promoted into available execution slots, and then the new arrival batch is admitted against the remaining bounded capacity. This makes persistent saturation and cumulative shedding directly inspectable.

## Approach

`admit_burst()` accepts fabricated request identifiers plus an execution limit and queue limit. It returns an explicit decision for every request:

- `running` — admitted directly to an execution slot;
- `queued` — admitted to bounded waiting capacity;
- `shed` — rejected at the admission boundary.

`drain_admitted()` advances only admitted work through deterministic completion rounds. Each `RecoveryStep` records which requests completed, which queued requests were promoted, and the remaining running and queued sets.

`simulate_load()` accepts a sequence of fabricated arrival batches and a fixed number of completions per tick. Each `LoadTick` records arrivals, completions, promotions, admission decisions, current running and queued work, and cumulative shed count. Empty arrival batches can represent quiet ticks in which existing work continues to drain.

The model is deterministic and does not create threads, sockets, servers, timers, or real queues. Its purpose is to make overload policy and accounting inspectable without presenting synthetic timing as a benchmark.

## Run the tests

```bash
PYTHONPATH=labs/15-load-shedding python -m unittest discover -s labs/15-load-shedding/tests -v
```

## Synthetic-data note

All request identifiers, arrival batches, capacity values, and completion counts are fabricated for this lab. No production traffic, customer records, private systems, or external services are used.

## Evidence in this slice

The test suite covers execution-slot admission, bounded queue admission, shedding after total capacity is exhausted, a zero-length queue, request-order preservation, empty bursts, invalid inputs, FIFO queue promotion, exclusion of shed work from recovery, and recovery-capacity validation.

The sustained-load cases additionally verify that shedding accumulates when arrivals repeatedly exceed modeled service progress, that sufficient modeled service prevents shedding for a matching arrival pattern, that quiet ticks drain queued work before later arrivals, that zero completions expose persistent saturation, and that invalid completion capacity is rejected.

Treat repository CI for the commit as the published validation record; do not infer passing status from this README alone.

## Limitations

This is a deterministic discrete-time model, not a production load balancer, scheduler, queue, or benchmark. A tick is an ordering device rather than a unit of wall-clock time. `completions_per_tick` is a policy input, not a measured throughput rate. The model does not represent request durations, partial completion within a tick, timeouts, retries, priorities, fairness, adaptive limits, distributed capacity, downstream feedback, or stochastic arrivals.

With bounded admission, deterministic recovery, and sustained-load behavior represented, this lab has a sensible stopping point. A future lab should explore a distinct overload-control mechanism rather than adding production-like complexity to this synthetic scheduler.
