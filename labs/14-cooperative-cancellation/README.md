# Lab 14 — Cooperative Cancellation

## Question

When a caller stops waiting, how much unnecessary downstream work continues if cancellation is not propagated, and how does cooperative cancellation change that behavior?

This lab uses deterministic synthetic models to compare work that ignores caller cancellation with work that periodically checks a shared cancellation signal.

## Failure scenario

A request can end while downstream work continues. Without propagation, the caller is gone but slow workers may still consume time and capacity until their original work finishes. The same problem compounds across nested stages: later work may start even though the originating request has already been cancelled.

Cooperative cancellation reduces abandoned work, but detection is not instantaneous when work only checks periodically. Cancellation also creates a second responsibility: required finalization still needs to run after interrupted work.

## Approach

`simulate_parallel_work()` starts fabricated workers together at synthetic time zero. Each worker has a planned duration and either observes or ignores caller cancellation.

`simulate_nested_work()` models sequential nested stages that share the same cancellation signal and global polling schedule. With propagation enabled, an active stage stops when cancellation is observed and later stages are not admitted. Without propagation, every stage runs to completion.

`simulate_finalized_work()` models one operation with required cleanup. Work may finish normally or stop when cancellation is observed; cleanup is then admitted exactly once and runs to completion. The model deliberately treats finalization as non-cancellable so the cleanup guarantee and its latency cost are visible rather than implicit.

All models keep timing deterministic and report consumed synthetic work explicitly. They do not invoke network services or real concurrency primitives.

## Run the tests

From this directory:

```bash
PYTHONPATH=. python -m unittest discover -s tests -v
```

All names, durations, and events are fabricated for this lab. No network services, production identifiers, private systems, or real-person records are used.

## Evidence in this slice

The tests cover parallel propagated and non-propagated cancellation, periodic-check detection delay, normal completion before the next cancellation check, nested cancellation during an active stage, prevention of later-stage admission, nested work without propagation, cleanup after cancellation, cleanup after normal completion, cleanup when cancellation is not propagated, and invalid synthetic inputs.

Treat repository CI for the commit as the published validation record; do not infer passing status from this README alone.

## Limitations

This is a cancellation model, not a production concurrency runtime. It does not create threads or processes, cancel HTTP or RPC requests, interrupt blocking I/O, propagate context across process boundaries, or measure scheduler overhead. Fixed check intervals and cleanup durations are synthetic policy inputs rather than measured production behavior.

The finalization model demonstrates control-flow guarantees only. It does not model cleanup failure, retries, partial rollback, process termination, or externally durable compensation. Real cleanup can fail and should not be described as guaranteed merely because a language-level finalizer was entered.

With parallel propagation, nested admission, and explicit finalization now represented, this lab has a coherent stopping point. A future lab can explore durable compensation or cleanup failure as a separate reliability problem rather than expanding this cancellation model into a framework.
