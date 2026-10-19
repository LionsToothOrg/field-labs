# Lab 15 — Load Shedding Under Saturation

## Question

When a service has bounded execution and queue capacity, which requests should be admitted during a synthetic overload burst, and how can excess work be rejected before it consumes scarce capacity?

## Failure scenario

An overloaded service that accepts every request can turn a short burst into an ever-growing backlog. Requests may wait even when the system has no bounded capacity to serve them promptly.

This first slice models a deliberately small admission boundary: requests arriving in order may start immediately while execution slots remain, enter a bounded queue while queue slots remain, and are shed once both capacities are full.

## Approach

`admit_burst()` accepts fabricated request identifiers plus an execution limit and queue limit. It returns an explicit decision for every request:

- `running` — admitted directly to an execution slot;
- `queued` — admitted to bounded waiting capacity;
- `shed` — rejected at the admission boundary.

The model is deterministic and does not create threads, sockets, servers, or real queues. Its purpose is to make overload admission accounting inspectable before adding scheduling or priority policy.

## Run the tests

```bash
PYTHONPATH=labs/15-load-shedding python -m unittest discover -s labs/15-load-shedding/tests -v
```

## Synthetic-data note

All request identifiers and capacity values are fabricated for this lab. No production traffic, customer records, private systems, or external services are used.

## Evidence in this slice

The tests cover execution-slot admission, bounded queue admission, shedding after total capacity is exhausted, a zero-length queue, preservation of request order, empty bursts, and invalid capacity inputs.

Treat repository CI for the commit as the published validation record; do not infer passing status from this README alone.

## Limitations

This is an admission model, not a production load balancer or server. It does not model request duration, queue draining, timeouts, retries, priorities, fairness, distributed capacity, adaptive limits, or feedback from downstream dependencies. A queued request is only classified as admitted waiting work; this slice does not claim it will eventually complete.

A useful next slice could add deterministic service completion and queue draining so overload recovery can be measured without turning the lab into a framework.
