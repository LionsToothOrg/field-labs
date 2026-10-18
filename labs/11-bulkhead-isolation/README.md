# Lab 11 — Bulkhead Isolation

## Question

How can a caller cap concurrent work independently so saturation in one workload does not consume the capacity reserved for another?

This lab models that question as a deterministic, in-memory admission policy. It makes no network calls and uses only synthetic partition names and counters.

## Failure scenario

A single shared concurrency limit can prevent unbounded work, but one busy workload can still occupy every slot. A bulkhead divides capacity into explicit partitions:

1. Each partition has its own positive concurrency capacity.
2. Admitted work consumes one or more permits only from that partition.
3. Work is rejected locally when its requested permits would exceed partition capacity.
4. Saturation in one partition does not consume another partition's capacity.
5. Releasing admitted work restores the corresponding permits for that partition.

The isolation boundary matters because overload should remain bounded instead of spreading through unrelated work simply because both workloads share a process.

## Run the experiment

```bash
PYTHONPATH=labs/11-bulkhead-isolation \
  python -m unittest discover -s labs/11-bulkhead-isolation/tests -v
```

The tests exercise saturation rejection, cross-partition isolation, single- and multi-permit capacity restoration, scoped automatic release, exception cleanup, invalid releases, invalid permit requests, unknown partitions, invalid configuration, and inspectable partition state.

## Design choices

- **Independent partitions:** each named workload receives a separate concurrency budget.
- **Weighted permits:** callers may request more than one permit for synthetic work that should consume a larger share of a partition's budget.
- **Fail-fast saturation:** a request is rejected as a unit when its permits would exceed available capacity; this slice does not partially admit work or build a queue.
- **Explicit release:** callers can return the number of permits associated with admitted work.
- **Scoped admission:** the `admission()` context manager automatically returns all permits for admitted work, including when the caller raises an exception. A rejected scoped admission never releases capacity owned by existing work.
- **Defensive accounting:** non-positive permit counts and releases larger than current admitted capacity raise errors instead of corrupting counters.
- **Inspectable decisions:** admission results include the partition, requested permits, current in-flight count, capacity, and reason.
- **No transport coupling:** the policy does not know about HTTP, workers, threads, or a particular dependency client.

## What this slice demonstrates

The implementation demonstrates bounded per-partition admission, verifies that saturating one synthetic workload does not prevent admission to another partition with available capacity, supports atomic multi-permit requests, and provides a scoped path that avoids leaking admitted permits when work exits unexpectedly.

## Limitations

This is not a production concurrency limiter. It does not provide thread/process synchronization, distributed coordination, queues, fairness, priorities, cancellation, timeouts, lease ownership, metrics, or dynamic capacity changes. Permit weights are caller-supplied integers rather than measured resource costs.

The counters demonstrate the isolation policy boundary in one in-memory process. The scoped helper reduces release mistakes within that model, but it does not make the implementation safe for concurrent threads or processes. No claim is made about production throughput, latency, or overload prevention.
