# Lab 14 — Cooperative Cancellation

## Question

When a caller stops waiting, how much unnecessary downstream work continues if cancellation is not propagated, and how does cooperative cancellation change that behavior?

This first slice uses a deterministic synthetic model of parallel workers. It compares workers that ignore caller cancellation with workers that periodically check a shared cancellation signal.

## Failure scenario

A request can end while downstream work continues. Without propagation, the caller is gone but slow workers may still consume time and capacity until their original work finishes. Cooperative cancellation reduces that abandoned work, but detection is not instantaneous when workers only check periodically.

## Approach

`simulate_parallel_work()` starts fabricated workers together at synthetic time zero. Each worker has a planned duration. A caller cancellation occurs at `cancel_at`.

When propagation is disabled, workers run their full planned duration. When propagation is enabled, a worker that is still active stops at its first cancellation check at or after `cancel_at`. A worker that finishes before that check completes normally.

The model reports both wall-clock completion time and aggregate synthetic work so the difference between caller latency and consumed worker time stays explicit.

## Run the tests

From this directory:

```bash
PYTHONPATH=. python -m unittest discover -s tests -v
```

All names, durations, and events are fabricated for this lab. No network services, production identifiers, private systems, or real-person records are used.

## Evidence in this slice

The tests compare propagated and non-propagated cancellation, verify periodic-check detection delay, preserve normal completion for work that finishes before its next cancellation check, and reject invalid synthetic inputs.

Treat repository CI for the commit as the published validation record; do not infer passing status from this README alone.

## Limitations

This is a cancellation model, not a production concurrency runtime. It does not create threads or processes, cancel HTTP or RPC requests, interrupt blocking I/O, model cleanup handlers, propagate context across process boundaries, or measure scheduler overhead. Fixed check intervals are synthetic policy inputs rather than measured production behavior.

A later slice can investigate cancellation across nested work or cleanup behavior after this baseline is validated.
