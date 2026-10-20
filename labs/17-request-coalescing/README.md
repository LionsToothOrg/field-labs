# Lab 17 — Request Coalescing

## Question

When several requests in the same synthetic arrival batch need the same resource, can they share one downstream load instead of independently multiplying work?

## Failure scenario

A cache miss or other expensive lookup can cause several callers to request the same key at nearly the same time. If every caller starts its own downstream load, identical demand is amplified precisely when the dependency may already be under pressure.

This lab models that boundary without pretending to implement real concurrency. Requests and returned values are fabricated records in a deterministic batch.

## Experiment

`coalesce_requests` groups requests by resource key in arrival order:

- the first request for a key becomes its leader;
- later requests for that key become followers;
- each distinct key represents one downstream origin load;
- different keys remain isolated and do not coalesce;
- duplicate request identifiers and empty identifiers are rejected.

`fan_out_successes` then models successful leader completion:

- exactly one supplied value is accepted for each leader;
- the leader and all of its followers receive that same value;
- every delivery records the leader request as its source;
- follower-supplied independent values are rejected;
- incomplete leader results are rejected before any deliveries are returned.

Run the lab with:

```bash
PYTHONPATH=labs/17-request-coalescing python -m unittest discover -s labs/17-request-coalescing/tests -v
```

## Evidence

The automated tests verify that three requests for one synthetic key produce one modeled origin load and two avoided duplicate loads. They also verify key isolation, deterministic leader/follower ordering, empty batches, and invalid identifier rejection.

The fan-out tests verify that followers receive the leader's synthetic value without introducing additional modeled origin loads, separate keys receive only their own leader values, missing leader results fail closed, and followers cannot inject independent origin values.

The `origin_loads` and `avoided_origin_loads` values are counts derived from this deterministic model. They are not throughput, latency, or production measurements.

## Limitations

This slice does not execute concurrent work, cache values beyond the supplied batch, model leader failure, enforce timeouts, or coordinate across processes. Result fan-out represents successful leader completion only; it does not imply a production single-flight implementation.

## Next experiment

A useful next slice can make leader failure explicit and prove that every follower in the affected group observes the same failure outcome without silently retrying duplicate origin work.
