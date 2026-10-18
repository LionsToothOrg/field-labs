# Lab 11 — Bulkhead Isolation

## Question

How can a caller cap concurrent work independently so saturation in one workload does not consume the capacity reserved for another?

This lab models that question as a deterministic, in-memory admission policy. It makes no network calls and uses only synthetic partition names and counters.

## Failure scenario

A single shared concurrency limit can prevent unbounded work, but one busy workload can still occupy every slot. A bulkhead divides capacity into explicit partitions:

1. Each partition has its own positive concurrency capacity.
2. Admitted work increments only that partition's in-flight count.
3. Work is rejected locally when its partition is saturated.
4. Saturation in one partition does not consume another partition's capacity.
5. Releasing admitted work restores capacity for that partition.

The isolation boundary matters because overload should remain bounded instead of spreading through unrelated work simply because both workloads share a process.

## Run the experiment

```bash
PYTHONPATH=labs/11-bulkhead-isolation \
  python -m unittest discover -s labs/11-bulkhead-isolation/tests -v
```

The tests exercise saturation rejection, cross-partition isolation, capacity restoration, invalid releases, unknown partitions, invalid configuration, and inspectable partition state.

## Design choices

- **Independent partitions:** each named workload receives a separate concurrency budget.
- **Fail-fast saturation:** this slice rejects excess work instead of building an unbounded queue.
- **Explicit release:** callers return capacity after admitted work finishes.
- **Defensive accounting:** releasing capacity that was never admitted raises an error instead of silently producing a negative count.
- **Inspectable decisions:** admission results include the partition, current in-flight count, capacity, and reason.
- **No transport coupling:** the policy does not know about HTTP, workers, threads, or a particular dependency client.

## What this slice demonstrates

The implementation demonstrates bounded per-partition admission and verifies that saturating one synthetic workload does not prevent admission to another partition with available capacity.

## Limitations

This is not a production concurrency limiter. It does not yet provide thread/process synchronization, distributed coordination, weighted work, queues, fairness, priorities, cancellation, timeouts, lease ownership, automatic release, metrics, or dynamic capacity changes.

The counters demonstrate the isolation policy boundary in one in-memory process. No claim is made about production throughput, latency, or overload prevention.
