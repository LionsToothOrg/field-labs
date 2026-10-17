# Lab 10 — Circuit Breaker Recovery

## Question

How can a caller stop repeatedly sending work to a failing dependency, then test recovery without allowing a burst of simultaneous probe traffic?

This lab models that question as a deterministic state machine. It makes no network calls and uses only synthetic call outcomes and caller-supplied timestamps.

## Failure scenario

Retries bound one operation, but repeated operations can still keep hitting a dependency that is already failing. A circuit breaker adds a boundary across calls:

1. While **closed**, calls are allowed and consecutive failures are counted.
2. At the configured failure threshold, the circuit becomes **open** and calls fail fast locally.
3. After the recovery timeout, the circuit becomes **half-open** and permits one probe.
4. A successful probe closes the circuit and clears the failure count.
5. A failed probe reopens the circuit and starts a new recovery timeout.

The single-probe gate matters because a timeout expiring should not turn recovery into a thundering herd.

## Run the experiment

```bash
PYTHONPATH=labs/10-circuit-breaker-recovery \
  python -m unittest discover -s labs/10-circuit-breaker-recovery/tests -v
```

The tests exercise threshold opening, failure-count reset, timeout gating, single-probe admission, successful recovery, failed-probe reopening, and invalid configuration.

## Design choices

- **Explicit time:** the caller supplies `now`; tests do not sleep or depend on wall-clock timing.
- **Consecutive failures:** a success resets the closed-state failure count.
- **One half-open probe:** additional calls are rejected while a probe outcome is pending.
- **Inspectable decisions:** rejected calls explain whether the recovery timeout is pending or a probe is already in flight.
- **No transport coupling:** the breaker does not decide which HTTP statuses or exceptions count as failures. That classification belongs at the caller boundary.

## What this slice demonstrates

The implementation demonstrates deterministic circuit-state transitions and probe admission under synthetic outcomes. Automated tests can repeatedly verify those state-machine rules.

## Limitations

This is not a production circuit-breaker library. It does not yet model distributed breaker state, rolling failure-rate windows, request volume thresholds, per-dependency partitioning, cancellation, persistence, metrics, or concurrent thread/process synchronization. The in-memory single-probe flag demonstrates the policy boundary, not a cross-process lock.

No claim is made about real dependency availability, latency improvement, or production incident prevention.
