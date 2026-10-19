# Lab 14 — Cooperative Cancellation

## Question

When a caller stops waiting, how much unnecessary downstream work continues if cancellation is not propagated, and how does cooperative cancellation change that behavior?

This lab uses deterministic synthetic models to compare work that ignores caller cancellation with work that periodically checks a shared cancellation signal.

## Failure scenario

A request can end while downstream work continues. Without propagation, the caller is gone but slow workers may still consume time and capacity until their original work finishes. The same problem compounds across nested stages: later work may start even though the originating request has already been cancelled.

Cooperative cancellation reduces abandoned work, but detection is not instantaneous when work only checks periodically.

## Approach

`simulate_parallel_work()` starts fabricated workers together at synthetic time zero. Each worker has a planned duration and either observes or ignores caller cancellation.

`simulate_nested_work()` models sequential nested stages that share the same cancellation signal and global polling schedule. With propagation enabled, an active stage stops when cancellation is observed and later stages are not admitted. Without propagation, every stage runs to completion.

Both models keep timing deterministic and report consumed synthetic work explicitly. They do not invoke network services or real concurrency primitives.

## Run the tests

From this directory:

```bash
PYTHONPATH=. python -m unittest discover -s tests -v
```

All names, durations, and events are fabricated for this lab. No network services, production identifiers, private systems, or real-person records are used.

## Evidence in this slice

The tests cover parallel propagated and non-propagated cancellation, periodic-check detection delay, normal completion before the next cancellation check, nested cancellation during an active stage, prevention of later-stage admission, nested work without propagation, and invalid synthetic inputs.

Treat repository CI for the commit as the published validation record; do not infer passing status from this README alone.

## Limitations

This is a cancellation model, not a production concurrency runtime. It does not create threads or processes, cancel HTTP or RPC requests, interrupt blocking I/O, model cleanup handlers, propagate context across process boundaries, or measure scheduler overhead. Fixed check intervals are synthetic policy inputs rather than measured production behavior.

The nested model intentionally uses sequential stages and one shared polling schedule. A later slice could investigate cleanup/finalization guarantees or independently polling child operations without turning this lab into a framework.
