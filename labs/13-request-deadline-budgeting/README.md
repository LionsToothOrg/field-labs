# Lab 13 — Request Deadline Budgeting

## Question

When one request has a fixed end-to-end deadline, how should a service choose timeouts for downstream calls without accidentally giving dependencies more time than the request has left?

This lab models deadline budgeting with deterministic synthetic timestamps. It calculates bounded downstream timeouts, preserves an explicit reserve for work after calls, and rejects work when no usable budget remains.

## Failure scenario

A locally configured dependency timeout can outlive the caller's remaining request budget. The risk compounds across sequential calls: reusing the same per-hop timeout without reconsidering the shared deadline can authorize more waiting than the original request can afford.

## Approach

`budget_downstream_call()` receives:

- `now`: the synthetic current timestamp;
- `deadline`: the caller's absolute synthetic deadline;
- `max_timeout`: the local upper bound for the dependency call;
- `reserve`: time intentionally retained for work after the dependency returns.

The usable budget is `deadline - now - reserve`. A call is admitted only when that value is positive, and its timeout is the smaller of the usable budget and the configured maximum.

`budget_sequential_calls()` applies that same rule before each synthetic call. The synthetic clock advances by the smaller of the supplied duration and the timeout granted for that step, so every subsequent decision is recomputed against the original absolute deadline rather than a stale per-hop budget.

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
5. invalid and non-finite configuration values;
6. sequential calls recomputing their budget from one shared deadline;
7. sequencing stopping once only reserved time remains;
8. synthetic call duration being capped by its granted timeout;
9. invalid synthetic durations being rejected.

Treat the repository CI result for the commit as the validation record; do not infer passing status from this README alone.

## Limitations

This is a budgeting model, not a production request runtime. It does not cancel running work, propagate deadlines over HTTP or RPC, model clock synchronization between hosts, allocate budgets across parallel fan-out, or guarantee that a dependency returns within the selected timeout. Synthetic durations represent elapsed work for the experiment only, and the reserve is caller policy rather than a measured latency requirement.

A useful next experiment would compare sequential and parallel fan-out policies while keeping one explicit end-to-end deadline.
