# Lab 17 — Request Coalescing

## Question

When several requests in the same synthetic arrival batch need the same resource, can they share one downstream load instead of independently multiplying work?

## Failure scenario

A cache miss or other expensive lookup can cause several callers to request the same key at nearly the same time. If every caller starts its own downstream load, identical demand is amplified precisely when the dependency may already be under pressure.

This lab models that boundary without pretending to implement real concurrency. Requests, returned values, failures, and timeout values are fabricated records in a deterministic batch.

## Experiment

`coalesce_requests` groups requests by resource key in arrival order:

- the first request for a key becomes its leader;
- later requests for that key become followers;
- each distinct key represents one downstream origin load;
- different keys remain isolated and do not coalesce;
- duplicate request identifiers and empty identifiers are rejected.

`fan_out_successes` models successful leader completion, while `fan_out_failures` models explicit leader failure. In both cases one leader outcome is shared with the whole coalesced group, the leader is recorded as the source, and follower-supplied independent outcomes are rejected.

`fan_out_terminal_timeouts` adds a bounded terminal-timeout policy:

- exactly one positive timeout is supplied for each elected leader;
- the leader and every follower observe that same timeout;
- each timeout delivery records the elected leader as its source;
- followers cannot inject independent timeout decisions;
- missing, non-positive, boolean, or non-integer timeout values are rejected before delivery;
- timeout is terminal in this slice: no follower retry or replacement leader is modeled.

Run the lab with:

```bash
PYTHONPATH=labs/17-request-coalescing python -m unittest discover -s labs/17-request-coalescing/tests -v
```

## Evidence

The automated tests cover same-key coalescing, key isolation, deterministic leader/follower ordering, successful and failed leader fan-out, empty batches, and invalid identifier rejection.

The timeout tests verify shared terminal timeout delivery, isolation across keys, rejection of missing or follower-supplied timeout decisions, validation of timeout values, and preservation of the original modeled origin-load count. This demonstrates a no-retry timeout policy rather than a retry strategy.

The `origin_loads` and `avoided_origin_loads` values are counts derived from this deterministic model. Timeout values are synthetic policy inputs. None of these values are throughput, latency, or production measurements.

## Limitations

This lab does not execute concurrent work, cache values beyond the supplied batch, measure elapsed time, cancel real I/O, retry failed or timed-out leaders, elect replacement leaders, or coordinate across processes. Success, failure, and timeout fan-out are deterministic outcome models; they do not imply a production single-flight implementation.

## Next experiment

The current model now covers leader election plus shared success, failure, and terminal-timeout outcomes. A later slice could explore controlled replacement-leader election, but only if it can preserve the one-retry boundary without allowing followers to create a retry stampede.
