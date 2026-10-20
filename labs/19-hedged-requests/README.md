# Lab 19 — Hedged Request Admission

## Question

When a read request is slower than an explicit latency threshold, can a client admit one duplicate attempt without turning every slow request into unbounded duplicate work?

This first slice models the **admission boundary only**. It uses synthetic request timings and does not perform network I/O.

## Failure scenario

A naive tail-latency strategy can duplicate every slow request, including mutation requests, or create more and more attempts while the original remains in flight. That trades latency pressure for correctness risk and downstream amplification.

## Model

`hedged_requests.py` makes the admission rule explicit:

- if the primary completes at or before the hedge threshold, no hedge starts;
- only `GET`, `HEAD`, and `OPTIONS` are treated as replay-safe in this lab;
- an eligible slow request starts exactly one hedge, so the modeled attempt count is capped at two;
- malformed identifiers, methods, timings, and thresholds fail validation.

The equality boundary is intentional: completion exactly at `hedge_after_ms` wins, so no duplicate attempt is admitted.

## Evidence

Run the focused tests with:

```bash
PYTHONPATH=labs/19-hedged-requests python -m unittest discover -s labs/19-hedged-requests/tests -v
```

The tests cover early completion, the exact threshold boundary, eligible slow reads, unsafe methods, case normalization, and invalid inputs.

## What this proves

For this deterministic synthetic model, hedge admission is bounded to one additional attempt and restricted to an explicit replay-safe method set after the configured delay.

## Limitations

This slice does **not** claim a production hedging implementation or a latency improvement. It does not model sockets, asynchronous execution, cancellation of losing attempts, response selection, downstream capacity, retries, distributed coordination, or measured tail latency. Those behaviors require separate evidence before making broader claims.

All identities and timings in this lab are synthetic.
