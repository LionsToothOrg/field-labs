# Lab 13 — Request Deadline Budgeting

## Question

When one request has a fixed end-to-end deadline, how should a service choose timeouts for downstream calls without accidentally giving dependencies more time than the request has left?

This lab models deadline budgeting with deterministic synthetic timestamps. It calculates bounded downstream timeouts, preserves an explicit reserve for work after calls, and rejects work when no usable budget remains.

## Failure scenario

A locally configured dependency timeout can outlive the caller's remaining request budget. The risk compounds across sequential calls: reusing the same per-hop timeout without reconsidering the shared deadline can authorize more waiting than the original request can afford. Parallel fan-out has a different shape: branches consume wall-clock time concurrently, but every branch still needs to inherit the same absolute deadline and reserve.

## Approach

`budget_downstream_call()` bounds one dependency timeout by `deadline - now - reserve`, capped at the configured `max_timeout`.

`budget_sequential_calls()` applies that rule before each synthetic call. The synthetic clock advances by the smaller of the supplied duration and the timeout granted for that step, so every subsequent decision is recomputed against the original absolute deadline.

`budget_parallel_calls()` gives synthetic fan-out branches one deadline-aware budget at their shared start time. Fan-out elapsed time is the slowest admitted branch, capped by the granted timeout, rather than the sum of branch durations. This makes the sequential-versus-parallel timing distinction explicit without pretending to implement a real concurrency runtime.

## Run the tests

From this directory:

```bash
python -m unittest discover -s tests -v
```

The tests use only fabricated timestamps and local deterministic calculations. No network services, production identifiers, or private systems are involved.

## Evidence in this slice

The automated tests cover single-call timeout capping, reserve preservation, exhausted deadlines, invalid configuration, sequential shared-deadline recomputation, timeout-capped synthetic durations, and parallel fan-out behavior. Parallel cases verify that branches share one start/deadline budget, wall time follows the slowest branch rather than summed durations, a timed-out branch cannot consume reserved time, and exhausted fan-out is not admitted.

Treat the repository CI result for the commit as the validation record; do not infer passing status from this README alone.

## Limitations

This is a budgeting model, not a production request runtime. It does not launch concurrent work, cancel running work, propagate deadlines over HTTP or RPC, model clock synchronization between hosts, choose different per-branch priorities, account for connection/setup overhead, or guarantee that a dependency returns within the selected timeout. Synthetic durations represent elapsed work for the experiment only, and the reserve is caller policy rather than a measured latency requirement.

With single-call, sequential, and parallel deadline policies represented, this lab now covers the core budgeting comparison. A separate lab is a better place for deeper concurrency, cancellation, or backpressure behavior.
