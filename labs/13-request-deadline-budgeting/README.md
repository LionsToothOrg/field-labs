# Lab 13 — Request Deadline Budgeting

## Question

When one request has a fixed end-to-end deadline, how should a service choose a timeout for a downstream call without accidentally giving that dependency more time than the request has left?

This first slice models deadline budgeting with deterministic synthetic timestamps. The goal is deliberately narrow: calculate a bounded downstream timeout, preserve an explicit reserve for work after the call, and reject work when no usable budget remains.

## Failure scenario

A locally configured dependency timeout can outlive the caller's remaining request budget. For example, a service may permit a 10-second dependency call even though the request has only 4 seconds left. The dependency timeout is valid in isolation but invalid in the end-to-end context.

## Approach

`budget_downstream_call()` receives:

- `now`: the synthetic current timestamp;
- `deadline`: the caller's absolute synthetic deadline;
- `max_timeout`: the local upper bound for the dependency call;
- `reserve`: time intentionally retained for work after the dependency returns.

The usable budget is `deadline - now - reserve`. A call is admitted only when that value is positive, and its timeout is the smaller of the usable budget and the configured maximum.

## Run the tests

From this directory:

```bash
python -m unittest discover -s tests -v
```

The tests use only fabricated timestamps and local deterministic calculations. No network services, production identifiers, or private systems are involved.

## Evidence in this slice

The automated tests cover:

1. a dependency timeout capped by its configured maximum;
2. a timeout shortened by the caller's remaining deadline;
3. preservation of a post-call reserve;
4. rejection after deadline exhaustion;
5. invalid and non-finite configuration values.

Treat the repository CI result for the commit as the validation record; do not infer passing status from this README alone.

## Limitations

This is a budgeting primitive, not a production request runtime. It does not cancel running work, propagate deadlines over HTTP or RPC, model clock synchronization between hosts, allocate budgets across parallel fan-out, or guarantee that a dependency returns within the selected timeout. The reserve is caller policy, not a measured latency requirement.

A useful next experiment would apply the same budget across a sequence of synthetic downstream calls and show how stale per-hop timeouts can exceed the original end-to-end deadline.
