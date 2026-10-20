# Lab 17 — Request Coalescing

## Question

When several requests in the same synthetic arrival batch need the same resource, can they share one downstream load instead of independently multiplying work?

## Failure scenario

A cache miss or other expensive lookup can cause several callers to request the same key at nearly the same time. If every caller starts its own downstream load, identical demand is amplified precisely when the dependency may already be under pressure.

This first slice models that boundary without pretending to implement real concurrency. Requests are fabricated records in a deterministic batch.

## Experiment

`coalesce_requests` groups requests by resource key in arrival order:

- the first request for a key becomes its leader;
- later requests for that key become followers;
- each distinct key represents one downstream origin load;
- different keys remain isolated and do not coalesce;
- duplicate request identifiers and empty identifiers are rejected.

Run the lab with:

```bash
PYTHONPATH=labs/17-request-coalescing python -m unittest discover -s labs/17-request-coalescing/tests -v
```

## Evidence

The automated tests verify that three requests for one synthetic key produce one modeled origin load and two avoided duplicate loads. They also verify key isolation, deterministic leader/follower ordering, empty batches, and invalid identifier rejection.

The `origin_loads` and `avoided_origin_loads` values are counts derived from this deterministic model. They are not throughput, latency, or production measurements.

## Limitations

This slice does not execute concurrent work, cache values, propagate leader results, model leader failure, enforce timeouts, or coordinate across processes. It demonstrates only the admission/grouping boundary for a supplied synthetic batch.

## Next experiment

A useful next slice can model leader completion and result fan-out so followers receive the same successful value without issuing their own origin load, then make leader failure explicit rather than silently treating coalescing as success.
